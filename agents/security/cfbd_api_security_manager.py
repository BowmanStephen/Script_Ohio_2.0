#!/usr/bin/env python3
"""
CFBD API Security Manager - Advanced API Security with Rate Limiting and Audit
Provides enterprise-grade API access control, rate limiting, and comprehensive auditing
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid
import threading
from collections import defaultdict, deque
import jwt
import redis.asyncio as redis
from pathlib import Path
import secrets
import ipaddress
import aiofiles

from ..core.event_stream_manager import (
    EventStreamManager, Event, EventPriority, EventSubscription
)
from ..core.enhanced_agent_framework import EnhancedBaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityLevel(Enum):
    """API security levels"""
    PUBLIC = "public"           # Open access with basic rate limiting
    AUTHENTICATED = "authenticated"  # Requires API key authentication
    RESTRICTED = "restricted"   # Limited access to specific endpoints
    PREMIUM = "premium"         # High-volume access with enhanced monitoring
    INTERNAL = "internal"       # Internal service access

class RateLimitType(Enum):
    """Rate limiting algorithms"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

class AuditLevel(Enum):
    """Audit logging levels"""
    MINIMAL = "minimal"         # Basic request/response logging
    STANDARD = "standard"       # Full request/response with metadata
    COMPREHENSIVE = "comprehensive"  # Include full payload and system state
    FORENSIC = "forensic"       # Everything plus internal system metrics

@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_window: int
    window_seconds: int
    burst_capacity: Optional[int] = None
    algorithm: RateLimitType = RateLimitType.SLIDING_WINDOW
    penalty_seconds: int = 60  # Penalty for exceeding limits

@dataclass
class APICredential:
    """API credential for authentication"""
    credential_id: str
    api_key: str
    api_secret: str
    security_level: SecurityLevel
    rate_limits: Dict[str, RateLimitConfig] = field(default_factory=dict)
    allowed_endpoints: Set[str] = field(default_factory=set)
    allowed_ips: Set[str] = field(default_factory=set)
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIRequest:
    """API request representation for auditing"""
    request_id: str
    credential_id: Optional[str]
    endpoint: str
    method: str
    ip_address: str
    user_agent: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request_size: int = 0
    response_status: Optional[int] = None
    response_size: int = 0
    processing_time_ms: int = 0
    rate_limited: bool = False
    blocked: bool = False
    security_violations: List[str] = field(default_factory=list)
    request_hash: Optional[str] = None

@dataclass
class SecurityAlert:
    """Security alert for policy violations"""
    alert_id: str
    alert_type: str
    severity: str
    credential_id: Optional[str]
    ip_address: str
    description: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[DateTime] = None

class CFBDAPISecurityManager(EnhancedBaseAgent):
    """
    Advanced CFBD API security manager with rate limiting, authentication,
    and comprehensive audit logging integrated with event-driven architecture
    """

    def __init__(self, agent_id: str = "cfbd_api_security_manager"):
        super().__init__(
            agent_id=agent_id,
            agent_name="CFBD API Security Manager",
            permission_level=self.PermissionLevel.ADMIN
        )

        # Security configuration
        self.security_config = {
            "encryption_key": secrets.token_bytes(32),
            "jwt_secret": secrets.token_urlsafe(32),
            "token_expiry_hours": 24,
            "max_failed_attempts": 5,
            "lockout_duration_minutes": 15,
            "default_audit_level": AuditLevel.STANDARD,
            "security_headers": {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'"
            }
        }

        # Credential management
        self.credentials: Dict[str, APICredential] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}

        # Rate limiting
        self.rate_limiters: Dict[str, Dict[str, Any]] = {}
        self.rate_limit_storage: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))

        # IP reputation and blocking
        self.blocked_ips: Set[str] = set()
        self.ip_reputation: Dict[str, Dict[str, Any]] = {}
        self.suspicious_patterns: Dict[str, Dict[str, Any]] = {}

        # Audit logging
        self.audit_log: deque = deque(maxlen=100000)
        self.security_alerts: Dict[str, SecurityAlert] = {}

        # Event integration
        self.event_manager: Optional[EventStreamManager] = None

        # Performance monitoring
        self.security_metrics = {
            "requests_processed": 0,
            "requests_blocked": 0,
            "rate_limit_violations": 0,
            "auth_failures": 0,
            "security_alerts_generated": 0,
            "average_processing_time_ms": 0.0
        }

        # Background processing
        self.cleanup_task: Optional[asyncio.Task] = None
        self.monitoring_task: Optional[asyncio.Task] = None

    def _define_capabilities(self) -> List['AgentCapability']:
        """Define security manager capabilities"""
        return [
            self.AgentCapability(
                name="manage_api_credentials",
                description="Create, update, and manage API credentials and access policies",
                execution_time_estimate=3.0,
                required_permissions=[self.PermissionLevel.ADMIN],
                parameters=["action", "credential_data", "security_level"],
                returns={"status": "string", "credential_id": "string", "api_key": "string"}
            ),
            self.AgentCapability(
                name="enforce_rate_limits",
                description="Enforce rate limiting policies across all API endpoints",
                execution_time_estimate=1.0,
                required_permissions=[self.PermissionLevel.READ_EXECUTE],
                parameters=["credential_id", "endpoint", "request_context"],
                returns={"allowed": "bool", "limit_info": "dict", "retry_after": "int"}
            ),
            self.AgentCapability(
                name="audit_api_access",
                description="Comprehensive audit logging of all API access and security events",
                execution_time_estimate=2.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["request_data", "response_data", "security_events"],
                returns={"audit_id": "string", "logged": "bool"}
            ),
            self.AgentCapability(
                name="detect_threats",
                description="Advanced threat detection using pattern analysis and anomaly detection",
                execution_time_estimate=5.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["request_pattern", "behavior_analysis", "context"],
                returns={"threat_level": "string", "recommendations": "list", "blocked": "bool"}
            )
        ]

    async def initialize(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize the CFBD API security manager

        Args:
            config: Configuration dictionary

        Returns:
            Initialization status
        """
        try:
            # Update security configuration
            if "security" in config:
                self.security_config.update(config["security"])

            # Initialize event stream manager
            if "event_stream" in config:
                event_config = config["event_stream"]
                self.event_manager = EventStreamManager(event_config)
                await self.event_manager.initialize()
                await self._setup_security_subscriptions()

            # Initialize rate limiters
            await self._initialize_rate_limiters(config.get("rate_limiting", {}))

            # Load existing credentials
            await self._load_credentials(config.get("credentials_file", "security_credentials.json"))

            # Start background tasks
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())

            # Create default credentials for internal use
            await self._create_default_credentials()

            logger.info("CFBD API Security Manager initialized successfully")
            return {
                "status": "success",
                "credentials_loaded": len(self.credentials),
                "rate_limiters_initialized": len(self.rate_limiters),
                "security_level": "enterprise_grade",
                "audit_enabled": True
            }

        except Exception as e:
            logger.error(f"Failed to initialize CFBD API Security Manager: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    async def _setup_security_subscriptions(self) -> None:
        """Setup event subscriptions for security monitoring"""
        # API access events
        api_subscription = EventSubscription(
            subscriber_id="security_api_access",
            event_types={
                "api.request.received",
                "api.response.sent",
                "api.auth.attempt",
                "api.rate_limit.exceeded"
            },
            priority_filter={EventPriority.HIGH, EventPriority.CRITICAL}
        )
        await self.event_manager.subscribe_to_events(api_subscription)

        # Security threat events
        threat_subscription = EventSubscription(
            subscriber_id="security_threats",
            event_types={
                "security.threat.detected",
                "security.violation",
                "suspicious.activity",
                "ip.blocked",
                "credential.compromised"
            },
            priority_filter={EventPriority.HIGH, EventPriority.CRITICAL}
        )
        await self.event_manager.subscribe_to_events(threat_subscription)

    async def _initialize_rate_limiters(self, rate_config: Dict[str, Any]) -> None:
        """Initialize rate limiting configurations"""
        default_limits = {
            SecurityLevel.PUBLIC: RateLimitConfig(
                requests_per_window=100,
                window_seconds=3600,  # 100 requests per hour
                burst_capacity=10,
                algorithm=RateLimitType.SLIDING_WINDOW
            ),
            SecurityLevel.AUTHENTICATED: RateLimitConfig(
                requests_per_window=1000,
                window_seconds=3600,  # 1000 requests per hour
                burst_capacity=50,
                algorithm=RateLimitType.TOKEN_BUCKET
            ),
            SecurityLevel.RESTRICTED: RateLimitConfig(
                requests_per_window=500,
                window_seconds=3600,  # 500 requests per hour
                burst_capacity=25,
                algorithm=RateLimitType.TOKEN_BUCKET
            ),
            SecurityLevel.PREMIUM: RateLimitConfig(
                requests_per_window=10000,
                window_seconds=3600,  # 10000 requests per hour
                burst_capacity=200,
                algorithm=RateLimitType.TOKEN_BUCKET
            ),
            SecurityLevel.INTERNAL: RateLimitConfig(
                requests_per_window=50000,
                window_seconds=3600,  # 50000 requests per hour
                burst_capacity=500,
                algorithm=RateLimitType.TOKEN_BUCKET
            )
        }

        # Apply custom configurations
        for level, config in rate_config.get("custom_limits", {}).items():
            if level in [sl.value for sl in SecurityLevel]:
                security_level = SecurityLevel(level)
                default_limits[security_level] = RateLimitConfig(**config)

        self.rate_limiters = {level: {} for level in SecurityLevel}

        for level, limit_config in default_limits.items():
            self.rate_limiters[level] = {
                "config": limit_config,
                "counters": defaultdict(int),
                "windows": defaultdict(lambda: deque(maxlen=limit_config.requests_per_window * 2)),
                "tokens": defaultdict(lambda: limit_config.burst_capacity or limit_config.requests_per_window),
                "last_refill": defaultdict(time.time)
            }

    async def _load_credentials(self, credentials_file: str) -> None:
        """Load existing API credentials from file"""
        try:
            credentials_path = Path(credentials_file)
            if credentials_path.exists():
                async with aiofiles.open(credentials_path, 'r') as f:
                    content = await f.read()
                    credentials_data = json.loads(content)

                for cred_data in credentials_data.get("credentials", []):
                    credential = APICredential(**cred_data)
                    self.credentials[credential.credential_id] = credential

                logger.info(f"Loaded {len(self.credentials)} credentials from {credentials_file}")
            else:
                logger.info(f"Credentials file {credentials_file} not found, starting with empty credentials")

        except Exception as e:
            logger.warning(f"Failed to load credentials from {credentials_file}: {e}")

    async def _create_default_credentials(self) -> None:
        """Create default credentials for internal system use"""
        internal_credential = APICredential(
            credential_id="internal_system",
            api_key=secrets.token_urlsafe(32),
            api_secret=secrets.token_urlsafe(32),
            security_level=SecurityLevel.INTERNAL,
            allowed_endpoints={"*"},  # All endpoints
            allowed_ips={"127.0.0.1", "::1"},  # Localhost only
            metadata={"purpose": "internal_system_access", "created_by": "security_manager"}
        )

        self.credentials[internal_credential.credential_id] = internal_credential
        logger.info("Created internal system credential")

    async def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute security manager actions"""
        try:
            if action == "manage_api_credentials":
                return await self._manage_api_credentials(parameters, user_context)
            elif action == "enforce_rate_limits":
                return await self._enforce_rate_limits(parameters, user_context)
            elif action == "audit_api_access":
                return await self._audit_api_access(parameters, user_context)
            elif action == "detect_threats":
                return await self._detect_threats(parameters, user_context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error executing action '{action}': {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id
            }

    async def _manage_api_credentials(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Manage API credentials creation, updates, and access control"""
        action = parameters.get("action")
        credential_data = parameters.get("credential_data", {})

        try:
            if action == "create":
                return await self._create_credential(credential_data)
            elif action == "update":
                credential_id = parameters.get("credential_id")
                return await self._update_credential(credential_id, credential_data)
            elif action == "revoke":
                credential_id = parameters.get("credential_id")
                return await self._revoke_credential(credential_id)
            elif action == "list":
                return await self._list_credentials(parameters.get("security_level"))
            elif action == "rotate_keys":
                credential_id = parameters.get("credential_id")
                return await self._rotate_credential_keys(credential_id)
            else:
                raise ValueError(f"Unknown credential action: {action}")

        except Exception as e:
            logger.error(f"Failed to manage API credentials: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action": action
            }

    async def _create_credential(self, credential_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new API credential"""
        try:
            # Validate input
            required_fields = ["security_level", "purpose"]
            for field in required_fields:
                if field not in credential_data:
                    raise ValueError(f"Missing required field: {field}")

            # Create credential
            credential_id = f"cred_{uuid.uuid4().hex[:12]}"
            api_key = secrets.token_urlsafe(32)
            api_secret = secrets.token_urlsafe(32)

            security_level = SecurityLevel(credential_data["security_level"])

            credential = APICredential(
                credential_id=credential_id,
                api_key=api_key,
                api_secret=api_secret,
                security_level=security_level,
                allowed_endpoints=set(credential_data.get("allowed_endpoints", [])),
                allowed_ips=set(credential_data.get("allowed_ips", [])),
                metadata={
                    "purpose": credential_data["purpose"],
                    "created_by": credential_data.get("created_by", "system"),
                    "description": credential_data.get("description", "")
                }
            )

            # Set custom rate limits if provided
            if "rate_limits" in credential_data:
                custom_limits = {}
                for endpoint, limit_data in credential_data["rate_limits"].items():
                    custom_limits[endpoint] = RateLimitConfig(**limit_data)
                credential.rate_limits = custom_limits

            # Set expiry if provided
            if "expires_at" in credential_data:
                credential.expires_at = datetime.fromisoformat(credential_data["expires_at"])

            self.credentials[credential_id] = credential

            # Publish credential creation event
            if self.event_manager:
                event = Event(
                    type="security.credential.created",
                    source="cfbd_api_security_manager",
                    data={
                        "credential_id": credential_id,
                        "security_level": security_level.value,
                        "purpose": credential_data["purpose"],
                        "created_at": credential.created_at.isoformat()
                    },
                    priority=EventPriority.NORMAL
                )
                await self.event_manager.publish_event(event)

            logger.info(f"Created API credential: {credential_id} ({security_level.value})")

            return {
                "status": "success",
                "credential_id": credential_id,
                "api_key": api_key,
                "api_secret": api_secret,
                "security_level": security_level.value,
                "message": "API credential created successfully"
            }

        except Exception as e:
            logger.error(f"Failed to create credential: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _enforce_rate_limits(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Enforce rate limiting for API requests"""
        credential_id = parameters.get("credential_id")
        endpoint = parameters.get("endpoint", "/unknown")
        request_context = parameters.get("request_context", {})

        try:
            # Get credential
            credential = None
            if credential_id:
                credential = self.credentials.get(credential_id)

            if not credential:
                # Use public rate limiting for unauthenticated requests
                security_level = SecurityLevel.PUBLIC
            else:
                security_level = credential.security_level

            # Check IP blocking
            ip_address = request_context.get("ip_address", "0.0.0.0")
            if self._is_ip_blocked(ip_address):
                return {
                    "allowed": False,
                    "blocked": True,
                    "reason": "IP address blocked due to security violations",
                    "retry_after": self.security_config["lockout_duration_minutes"] * 60
                }

            # Apply rate limiting
            rate_limit_result = await self._apply_rate_limiting(
                credential_id or "anonymous",
                endpoint,
                security_level,
                credential.rate_limits if credential else {}
            )

            # Update metrics
            self.security_metrics["requests_processed"] += 1

            # Log rate limit violations
            if not rate_limit_result["allowed"]:
                self.security_metrics["rate_limit_violations"] += 1

                # Publish rate limit event
                if self.event_manager:
                    event = Event(
                        type="api.rate_limit.exceeded",
                        source="cfbd_api_security_manager",
                        data={
                            "credential_id": credential_id,
                            "endpoint": endpoint,
                            "ip_address": ip_address,
                            "limit_type": rate_limit_result.get("limit_type"),
                            "retry_after": rate_limit_result.get("retry_after", 60)
                        },
                        priority=EventPriority.HIGH
                    )
                    await self.event_manager.publish_event(event)

            return rate_limit_result

        except Exception as e:
            logger.error(f"Failed to enforce rate limits: {e}")
            return {
                "status": "error",
                "error": str(e),
                "allowed": False
            }

    async def _apply_rate_limiting(
        self,
        identifier: str,
        endpoint: str,
        security_level: SecurityLevel,
        custom_limits: Dict[str, RateLimitConfig]
    ) -> Dict[str, Any]:
        """Apply rate limiting algorithm"""
        # Get appropriate rate limit config
        rate_limit_config = custom_limits.get(endpoint)
        if not rate_limit_config:
            # Use default rate limit for security level
            rate_limiter = self.rate_limiters.get(security_level)
            if rate_limiter:
                rate_limit_config = rate_limiter["config"]
            else:
                # Fallback to public limits
                rate_limit_config = RateLimitConfig(
                    requests_per_window=100,
                    window_seconds=3600,
                    algorithm=RateLimitType.SLIDING_WINDOW
                )

        # Apply the configured algorithm
        if rate_limit_config.algorithm == RateLimitType.SLIDING_WINDOW:
            return self._apply_sliding_window_limit(identifier, rate_limit_config)
        elif rate_limit_config.algorithm == RateLimitType.TOKEN_BUCKET:
            return self._apply_token_bucket_limit(identifier, rate_limit_config)
        elif rate_limit_config.algorithm == RateLimitType.FIXED_WINDOW:
            return self._apply_fixed_window_limit(identifier, rate_limit_config)
        else:
            # Default to sliding window
            return self._apply_sliding_window_limit(identifier, rate_limit_config)

    def _apply_sliding_window_limit(self, identifier: str, config: RateLimitConfig) -> Dict[str, Any]:
        """Apply sliding window rate limiting"""
        current_time = time.time()
        window_start = current_time - config.window_seconds

        # Get request history for this identifier
        request_times = self.rate_limit_storage[f"sliding_{identifier}"]

        # Remove old requests outside the window
        while request_times and request_times[0] < window_start:
            request_times.popleft()

        # Check if adding current request would exceed limit
        if len(request_times) >= config.requests_per_window:
            # Calculate retry after (when oldest request expires)
            retry_after = int(request_times[0] + config.window_seconds - current_time) + 1

            return {
                "allowed": False,
                "limit_type": "sliding_window",
                "current_count": len(request_times),
                "limit": config.requests_per_window,
                "window_seconds": config.window_seconds,
                "retry_after": max(retry_after, 1)
            }

        # Add current request
        request_times.append(current_time)

        return {
            "allowed": True,
            "limit_type": "sliding_window",
            "current_count": len(request_times),
            "limit": config.requests_per_window,
            "window_seconds": config.window_seconds,
            "remaining": config.requests_per_window - len(request_times)
        }

    def _apply_token_bucket_limit(self, identifier: str, config: RateLimitConfig) -> Dict[str, Any]:
        """Apply token bucket rate limiting"""
        current_time = time.time()
        bucket_key = f"bucket_{identifier}"

        # Get current tokens
        tokens = self.rate_limit_storage.get(bucket_key, [config.burst_capacity or config.requests_per_window])[0]

        # Refill tokens based on time elapsed
        last_refill = self.rate_limit_storage.get(f"refill_{bucket_key}", [current_time])[0]
        time_elapsed = current_time - last_refill

        if time_elapsed > 0:
            # Calculate tokens to add (rate = requests/second)
            refill_rate = config.requests_per_window / config.window_seconds
            tokens_to_add = time_elapsed * refill_rate
            tokens = min(tokens + tokens_to_add, config.burst_capacity or config.requests_per_window)

        # Check if we have enough tokens
        if tokens >= 1:
            # Consume one token
            tokens -= 1

            # Update storage
            self.rate_limit_storage[bucket_key] = [tokens]
            self.rate_limit_storage[f"refill_{bucket_key}"] = [current_time]

            return {
                "allowed": True,
                "limit_type": "token_bucket",
                "tokens_remaining": tokens,
                "burst_capacity": config.burst_capacity or config.requests_per_window,
                "refill_rate": config.requests_per_window / config.window_seconds
            }
        else:
            # Calculate retry after based on token refill rate
            refill_rate = config.requests_per_window / config.window_seconds
            retry_after = int((1 - tokens) / refill_rate) + 1

            return {
                "allowed": False,
                "limit_type": "token_bucket",
                "tokens_remaining": tokens,
                "retry_after": max(retry_after, 1),
                "refill_rate": refill_rate
            }

    def _apply_fixed_window_limit(self, identifier: str, config: RateLimitConfig) -> Dict[str, Any]:
        """Apply fixed window rate limiting"""
        current_time = time.time()
        window_start = int(current_time // config.window_seconds) * config.window_seconds

        window_key = f"fixed_{identifier}_{window_start}"
        request_count = self.rate_limit_storage.get(window_key, [0])[0]

        if request_count >= config.requests_per_window:
            # Calculate retry after (next window start)
            retry_after = int(window_start + config.window_seconds - current_time) + 1

            return {
                "allowed": False,
                "limit_type": "fixed_window",
                "current_count": request_count,
                "limit": config.requests_per_window,
                "window_seconds": config.window_seconds,
                "window_reset": window_start + config.window_seconds,
                "retry_after": max(retry_after, 1)
            }

        # Increment request count
        request_count += 1
        self.rate_limit_storage[window_key] = [request_count]

        return {
            "allowed": True,
            "limit_type": "fixed_window",
            "current_count": request_count,
            "limit": config.requests_per_window,
            "window_seconds": config.window_seconds,
            "remaining": config.requests_per_window - request_count
        }

    async def _audit_api_access(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Audit API access with comprehensive logging"""
        request_data = parameters.get("request_data", {})
        response_data = parameters.get("response_data", {})
        security_events = parameters.get("security_events", [])

        try:
            # Create audit entry
            audit_entry = APIRequest(
                request_id=request_data.get("request_id", str(uuid.uuid4())),
                credential_id=request_data.get("credential_id"),
                endpoint=request_data.get("endpoint", ""),
                method=request_data.get("method", "GET"),
                ip_address=request_data.get("ip_address", ""),
                user_agent=request_data.get("user_agent", ""),
                request_size=request_data.get("content_length", 0),
                response_status=response_data.get("status_code"),
                response_size=response_data.get("content_length", 0),
                processing_time_ms=response_data.get("processing_time_ms", 0),
                rate_limited=request_data.get("rate_limited", False),
                blocked=request_data.get("blocked", False),
                security_violations=security_events
            )

            # Generate request hash for integrity checking
            audit_entry.request_hash = self._generate_request_hash(audit_entry)

            # Add to audit log
            self.audit_log.append(audit_entry)

            # Publish audit event
            if self.event_manager:
                event = Event(
                    type="security.api.audit",
                    source="cfbd_api_security_manager",
                    data={
                        "request_id": audit_entry.request_id,
                        "credential_id": audit_entry.credential_id,
                        "endpoint": audit_entry.endpoint,
                        "ip_address": audit_entry.ip_address,
                        "status_code": audit_entry.response_status,
                        "processing_time_ms": audit_entry.processing_time_ms,
                        "security_events": audit_entry.security_violations,
                        "timestamp": audit_entry.timestamp.isoformat()
                    },
                    priority=EventPriority.NORMAL if audit_entry.response_status and audit_entry.response_status < 400 else EventPriority.HIGH
                )
                await self.event_manager.publish_event(event)

            # Check for suspicious patterns
            await self._analyze_suspicious_patterns(audit_entry)

            return {
                "status": "success",
                "audit_id": audit_entry.request_id,
                "logged": True,
                "request_hash": audit_entry.request_hash
            }

        except Exception as e:
            logger.error(f"Failed to audit API access: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _generate_request_hash(self, request: APIRequest) -> str:
        """Generate cryptographic hash for request integrity"""
        hash_data = {
            "request_id": request.request_id,
            "credential_id": request.credential_id,
            "endpoint": request.endpoint,
            "method": request.method,
            "ip_address": request.ip_address,
            "timestamp": request.timestamp.isoformat()
        }

        hash_string = json.dumps(hash_data, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(hash_string.encode()).hexdigest()

    async def _detect_threats(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Advanced threat detection using pattern analysis"""
        request_pattern = parameters.get("request_pattern", {})
        behavior_analysis = parameters.get("behavior_analysis", {})
        context = parameters.get("context", {})

        try:
            threats_detected = []
            threat_level = "low"
            recommendations = []
            should_block = False

            # Analyze request patterns for threats
            pattern_threats = await self._analyze_request_patterns(request_pattern, context)
            threats_detected.extend(pattern_threats)

            # Analyze behavioral patterns
            behavior_threats = await self._analyze_behavioral_patterns(behavior_analysis, context)
            threats_detected.extend(behavior_threats)

            # Analyze IP reputation
            ip_address = context.get("ip_address", "")
            if ip_address:
                ip_threats = await self._analyze_ip_reputation(ip_address)
                threats_detected.extend(ip_threats)

            # Determine overall threat level
            if threats_detected:
                high_severity_threats = [t for t in threats_detected if t.get("severity") == "high"]
                medium_severity_threats = [t for t in threats_detected if t.get("severity") == "medium"]

                if high_severity_threats:
                    threat_level = "high"
                    should_block = True
                    recommendations.extend([
                        "Block request immediately",
                        "Increase monitoring frequency",
                        "Review credential access patterns"
                    ])
                elif medium_severity_threats:
                    threat_level = "medium"
                    recommendations.extend([
                        "Apply additional validation",
                        "Monitor for escalation",
                        "Consider rate limiting"
                    ])
                else:
                    threat_level = "low"
                    recommendations.append("Continue monitoring")

            # Create security alert if threats detected
            if threats_detected:
                await self._create_security_alert(
                    alert_type="threat_detected",
                    severity=threat_level,
                    ip_address=context.get("ip_address", ""),
                    description=f"Threats detected: {len(threats_detected)}",
                    metadata={
                        "threats": threats_detected,
                        "recommendations": recommendations,
                        "context": context
                    }
                )

            return {
                "status": "success",
                "threat_level": threat_level,
                "threats_detected": len(threats_detected),
                "threats": threats_detected,
                "recommendations": recommendations,
                "blocked": should_block
            }

        except Exception as e:
            logger.error(f"Failed to detect threats: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _analyze_request_patterns(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze request patterns for threats"""
        threats = []

        # Check for SQL injection patterns
        suspicious_params = pattern.get("parameters", {})
        for param_name, param_value in suspicious_params.items():
            if isinstance(param_value, str):
                sql_patterns = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_"]
                if any(p in param_value.lower() for p in sql_patterns):
                    threats.append({
                        "type": "sql_injection",
                        "severity": "high",
                        "parameter": param_name,
                        "value": param_value[:100] + "..." if len(param_value) > 100 else param_value
                    })

        # Check for excessive parameter counts
        if len(suspicious_params) > 50:
            threats.append({
                "type": "excessive_parameters",
                "severity": "medium",
                "parameter_count": len(suspicious_params)
            })

        # Check for unusual endpoint combinations
        endpoint = pattern.get("endpoint", "")
        if "admin" in endpoint.lower() and pattern.get("method") != "GET":
            threats.append({
                "type": "admin_endpoint_access",
                "severity": "medium",
                "endpoint": endpoint,
                "method": pattern.get("method")
            })

        return threats

    async def _analyze_behavioral_patterns(self, behavior: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze behavioral patterns for anomalies"""
        threats = []

        # Check for rapid request patterns
        request_frequency = behavior.get("requests_per_minute", 0)
        if request_frequency > 100:
            threats.append({
                "type": "high_request_frequency",
                "severity": "medium",
                "frequency": request_frequency,
                "threshold": 100
            })

        # Check for unusual user agent patterns
        user_agent = behavior.get("user_agent", "")
        if not user_agent or len(user_agent) < 10:
            threats.append({
                "type": "suspicious_user_agent",
                "severity": "low",
                "user_agent": user_agent
            })

        # Check for endpoint enumeration
        unique_endpoints = behavior.get("unique_endpoints", [])
        if len(unique_endpoints) > 20:
            threats.append({
                "type": "endpoint_enumeration",
                "severity": "medium",
                "endpoint_count": len(unique_endpoints)
            })

        # Check for time-based anomalies
        request_times = behavior.get("request_times", [])
        if len(request_times) > 10:
            # Check if requests are evenly spaced (bot-like behavior)
            time_diffs = [request_times[i] - request_times[i-1] for i in range(1, len(request_times))]
            avg_diff = sum(time_diffs) / len(time_diffs)
            variance = sum((diff - avg_diff) ** 2 for diff in time_diffs) / len(time_diffs)

            if variance < 1.0:  # Very low variance suggests bot
                threats.append({
                    "type": "bot_like_behavior",
                    "severity": "medium",
                    "variance": variance,
                    "avg_interval": avg_diff
                })

        return threats

    async def _analyze_ip_reputation(self, ip_address: str) -> List[Dict[str, Any]]:
        """Analyze IP address reputation"""
        threats = []

        # Check if IP is in blocked list
        if self._is_ip_blocked(ip_address):
            threats.append({
                "type": "blocked_ip",
                "severity": "high",
                "ip_address": ip_address
            })

        # Check for known malicious patterns
        ip_int = int(ipaddress.ip_address(ip_address))

        # Simple heuristics for suspicious IP ranges
        # (In production, use threat intelligence feeds)
        suspicious_ranges = [
            # Example ranges - replace with actual threat intelligence
            "0.0.0.0/8",      # Reserved
            "127.0.0.0/8",    # Loopback (unless explicitly allowed)
            "224.0.0.0/4",    # Multicast
        ]

        for range_str in suspicious_ranges:
            network = ipaddress.ip_network(range_str)
            if ipaddress.ip_address(ip_address) in network:
                threats.append({
                    "type": "suspicious_ip_range",
                    "severity": "medium",
                    "ip_address": ip_address,
                    "range": str(network)
                })

        # Check IP reputation history
        ip_history = self.ip_reputation.get(ip_address, {})
        failed_attempts = ip_history.get("failed_attempts", 0)

        if failed_attempts > 10:
            threats.append({
                "type": "high_failure_rate",
                "severity": "medium",
                "ip_address": ip_address,
                "failed_attempts": failed_attempts
            })

        return threats

    def _is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP address is blocked"""
        return ip_address in self.blocked_ips

    async def _create_security_alert(
        self,
        alert_type: str,
        severity: str,
        ip_address: str,
        description: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Create a security alert"""
        alert_id = f"alert_{uuid.uuid4().hex[:12]}"

        alert = SecurityAlert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            ip_address=ip_address,
            description=description,
            metadata=metadata
        )

        self.security_alerts[alert_id] = alert
        self.security_metrics["security_alerts_generated"] += 1

        # Publish security alert event
        if self.event_manager:
            event = Event(
                type="security.alert.created",
                source="cfbd_api_security_manager",
                data={
                    "alert_id": alert_id,
                    "alert_type": alert_type,
                    "severity": severity,
                    "ip_address": ip_address,
                    "description": description,
                    "metadata": metadata,
                    "timestamp": alert.timestamp.isoformat()
                },
                priority=EventPriority.HIGH if severity in ["high", "critical"] else EventPriority.NORMAL
            )
            await self.event_manager.publish_event(event)

        logger.warning(f"Security alert created: {alert_type} - {description}")

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""
        while True:
            try:
                await self._cleanup_expired_data()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired_data(self) -> None:
        """Clean up expired data"""
        current_time = datetime.now(timezone.utc)

        # Clean up expired credentials
        expired_credentials = [
            cred_id for cred_id, cred in self.credentials.items()
            if cred.expires_at and cred.expires_at < current_time
        ]

        for cred_id in expired_credentials:
            del self.credentials[cred_id]
            logger.info(f"Removed expired credential: {cred_id}")

        # Clean up old audit logs (keep last 30 days)
        cutoff_time = current_time - timedelta(days=30)
        self.audit_log = deque(
            (entry for entry in self.audit_log if entry.timestamp >= cutoff_time),
            maxlen=100000
        )

        # Clean up old security alerts (keep resolved alerts for 7 days)
        alerts_to_remove = []
        for alert_id, alert in self.security_alerts.items():
            if alert.resolved and alert.resolved_at:
                if alert.resolved_at < current_time - timedelta(days=7):
                    alerts_to_remove.append(alert_id)

        for alert_id in alerts_to_remove:
            del self.security_alerts[alert_id]

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop"""
        while True:
            try:
                await self._generate_security_metrics()
                await asyncio.sleep(60)  # Monitor every minute
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(30)

    async def _generate_security_metrics(self) -> None:
        """Generate security metrics for monitoring"""
        current_time = time.time()

        # Calculate recent metrics (last hour)
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_requests = [
            entry for entry in self.audit_log
            if entry.timestamp >= one_hour_ago
        ]

        if recent_requests:
            processing_times = [entry.processing_time_ms for entry in recent_requests if entry.processing_time_ms > 0]
            self.security_metrics["average_processing_time_ms"] = (
                sum(processing_times) / len(processing_times) if processing_times else 0
            )

        # Publish metrics event
        if self.event_manager:
            metrics_event = Event(
                type="security.metrics.generated",
                source="cfbd_api_security_manager",
                data={
                    "metrics": self.security_metrics,
                    "active_credentials": len(self.credentials),
                    "blocked_ips": len(self.blocked_ips),
                    "active_alerts": len([a for a in self.security_alerts.values() if not a.resolved]),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                priority=EventPriority.NORMAL
            )
            await self.event_manager.publish_event(metrics_event)

    async def _analyze_suspicious_patterns(self, audit_entry: APIRequest) -> None:
        """Analyze audit entry for suspicious patterns"""
        ip_address = audit_entry.ip_address

        # Update IP history
        if ip_address not in self.ip_reputation:
            self.ip_reputation[ip_address] = {
                "failed_attempts": 0,
                "successful_requests": 0,
                "last_seen": audit_entry.timestamp
            }

        ip_history = self.ip_reputation[ip_address]

        if audit_entry.response_status and audit_entry.response_status >= 400:
            ip_history["failed_attempts"] += 1
        else:
            ip_history["successful_requests"] += 1

        ip_history["last_seen"] = audit_entry.timestamp

        # Check for patterns indicating attacks
        if ip_history["failed_attempts"] > 20:
            await self._block_ip_temporarily(ip_address, "High failure rate")

    async def _block_ip_temporarily(self, ip_address: str, reason: str) -> None:
        """Temporarily block an IP address"""
        self.blocked_ips.add(ip_address)

        # Create security alert
        await self._create_security_alert(
            alert_type="ip_blocked",
            severity="medium",
            ip_address=ip_address,
            description=f"IP blocked due to: {reason}",
            metadata={
                "reason": reason,
                "block_duration": self.security_config["lockout_duration_minutes"],
                "blocked_at": datetime.now(timezone.utc).isoformat()
            }
        )

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        return {
            "security_metrics": self.security_metrics.copy(),
            "credentials_count": len(self.credentials),
            "blocked_ips_count": len(self.blocked_ips),
            "active_alerts_count": len([a for a in self.security_alerts.values() if not a.resolved]),
            "audit_log_size": len(self.audit_log),
            "rate_limit_storage_size": len(self.rate_limit_storage),
            "ip_reputation_entries": len(self.ip_reputation)
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the security manager"""
        try:
            # Cancel background tasks
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            # Shutdown event manager
            if self.event_manager:
                await self.event_manager.shutdown()

            logger.info("CFBD API Security Manager shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")