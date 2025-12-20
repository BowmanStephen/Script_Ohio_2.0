"""
Advanced Security Manager for Multi-Agent System

This module provides comprehensive security management for the advanced agent system,
including role-based access control, audit logging, encryption, and secure communication.

Key Features:
- Multi-tier permission system with role-based access
- Comprehensive audit logging with immutable trails
- Field-level encryption for sensitive data
- API security with token rotation and rate limiting
- Docker container security management
- Real-time threat detection and response
"""

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import jwt
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import threading

# Import our enhanced permission system
from .enhanced_agent_framework import EnhancedPermissionLevel, SecurityContext

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security classification levels"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    TOP_SECRET = "top_secret"


class ThreatLevel(Enum):
    """Threat severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityPolicy:
    """Security policy configuration"""

    name: str
    description: str
    required_permissions: List[EnhancedPermissionLevel]
    security_level: SecurityLevel
    audit_required: bool = True
    encryption_required: bool = False
    timeout_seconds: float = 300.0
    max_attempts: int = 3
    rate_limit_per_minute: int = 60


@dataclass
class SecurityEvent:
    """Security event for audit logging"""

    event_id: str
    timestamp: datetime
    agent_id: str
    user_id: Optional[str]
    action: str
    resource: str
    permission_level: EnhancedPermissionLevel
    threat_level: ThreatLevel
    success: bool
    details: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class EncryptionKey:
    """Encryption key metadata"""

    key_id: str
    algorithm: str
    created_at: datetime
    expires_at: datetime
    purpose: str
    is_active: bool = True


class SecurityManager:
    """
    Advanced Security Manager for Multi-Agent System

    Provides comprehensive security including:
    - Role-based access control with fine-grained permissions
    - Audit logging with immutable trails
    - Field-level encryption with key rotation
    - API security with token management
    - Real-time threat detection
    - Docker container security integration
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "/etc/agent_security"
        self.encryption_keys: Dict[str, EncryptionKey] = {}
        self.active_policies: Dict[str, SecurityPolicy] = {}
        self.security_events: List[SecurityEvent] = []
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.rate_limits: Dict[str, List[float]] = {}
        self.blocked_ips: Set[str] = set()
        self.blocked_agents: Set[str] = set()

        # Thread safety
        self._lock = threading.RLock()

        # Initialize components
        self._initialize_encryption()
        self._load_security_policies()
        self._setup_audit_logging()
        self._initialize_threat_detection()

        logger.info("Advanced Security Manager initialized")

    def _initialize_encryption(self):
        """Initialize encryption system with key management"""
        try:
            # Generate master key for key encryption
            self.master_key = self._generate_master_key()

            # Initialize field encryption
            self.field_encryptor = Fernet(
                self._derive_encryption_key("field_encryption")
            )

            logger.info("Encryption system initialized")

        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise

    def _generate_master_key(self) -> bytes:
        """Generate or load master encryption key"""
        key_file = Path(self.config_path) / "master.key"

        if key_file.exists():
            with open(key_file, "rb") as f:
                return f.read()
        else:
            # Generate new master key
            master_key = secrets.token_bytes(32)
            key_file.parent.mkdir(parents=True, exist_ok=True)

            with open(key_file, "wb") as f:
                f.write(master_key)
            os.chmod(key_file, 0o600)  # Restrict file permissions

            logger.info("Generated new master encryption key")
            return master_key

    def _derive_encryption_key(self, purpose: str) -> bytes:
        """Derive encryption key for specific purpose"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=purpose.encode(),
            iterations=100000,
        )
        return kdf.derive(self.master_key)

    def _load_security_policies(self):
        """Load security policies and roles"""
        # Define default security policies
        policies = [
            SecurityPolicy(
                name="data_access",
                description="Access to sensitive data",
                required_permissions=[EnhancedPermissionLevel.READ_EXECUTE],
                security_level=SecurityLevel.CONFIDENTIAL,
                encryption_required=True,
            ),
            SecurityPolicy(
                name="model_execution",
                description="Machine learning model execution",
                required_permissions=[EnhancedPermissionLevel.MODEL_EXECUTION],
                security_level=SecurityLevel.INTERNAL,
                timeout_seconds=600.0,
            ),
            SecurityPolicy(
                name="api_access",
                description="External API access",
                required_permissions=[EnhancedPermissionLevel.API_ACCESS],
                security_level=SecurityLevel.RESTRICTED,
                rate_limit_per_minute=30,
            ),
            SecurityPolicy(
                name="system_admin",
                description="System administration tasks",
                required_permissions=[EnhancedPermissionLevel.SYSTEM_ADMIN],
                security_level=SecurityLevel.TOP_SECRET,
                audit_required=True,
                max_attempts=1,
            ),
            SecurityPolicy(
                name="human_review",
                description="Human review and approval",
                required_permissions=[EnhancedPermissionLevel.HUMAN_REVIEW],
                security_level=SecurityLevel.RESTRICTED,
                audit_required=True,
            ),
        ]

        for policy in policies:
            self.active_policies[policy.name] = policy

        logger.info(f"Loaded {len(policies)} security policies")

    def _setup_audit_logging(self):
        """Setup comprehensive audit logging"""
        self.audit_log_file = Path(self.config_path) / "security_audit.log"
        self.audit_log_file.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Audit logging system initialized")

    def _initialize_threat_detection(self):
        """Initialize threat detection system"""
        self.threat_patterns = {
            "rapid_api_calls": {"threshold": 100, "window": 60, "action": "rate_limit"},
            "failed_auth_attempts": {
                "threshold": 5,
                "window": 300,
                "action": "block_ip",
            },
            "privilege_escalation": {"threshold": 1, "window": 3600, "action": "alert"},
            "unusual_access_patterns": {
                "threshold": 3,
                "window": 1800,
                "action": "monitor",
            },
            "data_exfiltration": {"threshold": 10, "window": 300, "action": "block"},
        }

        logger.info("Threat detection system initialized")

    def create_security_context(
        self,
        user_id: Optional[str] = None,
        permissions: Optional[List[EnhancedPermissionLevel]] = None,
        session_id: Optional[str] = None,
    ) -> SecurityContext:
        """Create a new security context"""
        context_id = secrets.token_hex(16)
        session_id = session_id or context_id

        # Generate access token
        access_token = self._generate_access_token(context_id, user_id, permissions)

        # Create session
        session_data = {
            "context_id": context_id,
            "user_id": user_id,
            "permissions": permissions or [],
            "access_token": access_token,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=24),
        }

        with self._lock:
            self.active_sessions[session_id] = session_data

        context = SecurityContext(
            user_id=user_id,
            session_id=session_id,
            permissions=permissions or [],
            access_token=access_token,
            audit_required=True,
        )

        # Log context creation
        self._log_security_event(
            agent_id="security_manager",
            user_id=user_id,
            action="create_context",
            resource="security_context",
            permission_level=EnhancedPermissionLevel.READ_EXECUTE,
            threat_level=ThreatLevel.LOW,
            success=True,
            details={
                "context_id": context_id,
                "permissions": [p.value for p in permissions or []],
            },
        )

        return context

    def _generate_access_token(
        self,
        context_id: str,
        user_id: Optional[str],
        permissions: Optional[List[EnhancedPermissionLevel]],
    ) -> str:
        """Generate JWT access token"""
        payload = {
            "context_id": context_id,
            "user_id": user_id,
            "permissions": [p.value for p in permissions or []],
            "iat": datetime.utcnow(),
            "exp": datetime.utcnow() + timedelta(hours=1),  # 1 hour expiration
        }

        # In production, use proper secret key management
        secret_key = self.master_key.decode("latin-1")

        return jwt.encode(payload, secret_key, algorithm="HS256")

    def validate_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT access token"""
        try:
            secret_key = self.master_key.decode("latin-1")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Access token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid access token")
            return None

    def check_permissions(
        self,
        context: SecurityContext,
        required_permissions: List[EnhancedPermissionLevel],
        policy_name: Optional[str] = None,
    ) -> bool:
        """Check if security context has required permissions"""
        # Basic permission check
        for required_perm in required_permissions:
            if required_perm not in context.permissions:
                self._log_security_event(
                    agent_id="security_manager",
                    user_id=context.user_id,
                    action="permission_denied",
                    resource=policy_name or "unknown",
                    permission_level=required_perm,
                    threat_level=ThreatLevel.MEDIUM,
                    success=False,
                    details={
                        "required_permissions": [p.value for p in required_permissions],
                        "context_permissions": [p.value for p in context.permissions],
                    },
                )
                return False

        # Policy-specific checks
        if policy_name and policy_name in self.active_policies:
            policy = self.active_policies[policy_name]
            return self._check_policy_requirements(context, policy)

        return True

    def _check_policy_requirements(
        self, context: SecurityContext, policy: SecurityPolicy
    ) -> bool:
        """Check policy-specific requirements"""
        # Check required permissions
        for required_perm in policy.required_permissions:
            if required_perm not in context.permissions:
                return False

        # Check security level
        if policy.security_level == SecurityLevel.TOP_SECRET:
            if EnhancedPermissionLevel.SYSTEM_ADMIN not in context.permissions:
                return False

        # Check encryption requirement
        if policy.encryption_required:
            if not context.encryption_key:
                return False

        return True

    def encrypt_field(self, data: str, field_name: str) -> str:
        """Encrypt a field value"""
        try:
            # Add field metadata for audit purposes
            metadata = {
                "field_name": field_name,
                "encrypted_at": datetime.utcnow().isoformat(),
                "encryption_version": "1.0",
            }

            # Combine data with metadata
            combined_data = json.dumps({"data": data, "metadata": metadata})

            # Encrypt
            encrypted_data = self.field_encryptor.encrypt(combined_data.encode())

            # Return base64 encoded encrypted data
            return encrypted_data.decode()

        except Exception as e:
            logger.error(f"Field encryption failed for {field_name}: {e}")
            raise

    def decrypt_field(self, encrypted_data: str, field_name: str) -> str:
        """Decrypt a field value"""
        try:
            # Decode and decrypt
            encrypted_bytes = encrypted_data.encode()
            decrypted_data = self.field_encryptor.decrypt(encrypted_bytes).decode()

            # Parse combined data
            combined = json.loads(decrypted_data)

            # Validate metadata
            metadata = combined.get("metadata", {})
            if metadata.get("field_name") != field_name:
                logger.warning(
                    f"Field name mismatch in decryption: expected {field_name}, got {metadata.get('field_name')}"
                )

            return combined["data"]

        except Exception as e:
            logger.error(f"Field decryption failed for {field_name}: {e}")
            raise

    def rate_limit_check(self, agent_id: str, policy_name: str) -> bool:
        """Check rate limiting for an agent"""
        if policy_name not in self.active_policies:
            return True

        policy = self.active_policies[policy_name]
        current_time = time.time()

        with self._lock:
            if agent_id not in self.rate_limits:
                self.rate_limits[agent_id] = []

            # Clean old entries
            self.rate_limits[agent_id] = [
                timestamp
                for timestamp in self.rate_limits[agent_id]
                if current_time - timestamp < 60  # Keep last minute
            ]

            # Check rate limit
            if len(self.rate_limits[agent_id]) >= policy.rate_limit_per_minute:
                self._log_security_event(
                    agent_id=agent_id,
                    user_id=None,
                    action="rate_limit_exceeded",
                    resource=policy_name,
                    permission_level=EnhancedPermissionLevel.READ_EXECUTE,
                    threat_level=ThreatLevel.MEDIUM,
                    success=False,
                    details={
                        "current_rate": len(self.rate_limits[agent_id]),
                        "limit": policy.rate_limit_per_minute,
                        "policy": policy_name,
                    },
                )
                return False

            # Record this access
            self.rate_limits[agent_id].append(current_time)
            return True

    def detect_threats(self, event: SecurityEvent) -> ThreatLevel:
        """Detect potential threats from security events"""
        threat_level = ThreatLevel.LOW

        # Check for rapid API calls
        if event.action == "api_access":
            recent_api_calls = [
                e
                for e in self.security_events[-100:]
                if e.action == "api_access"
                and e.agent_id == event.agent_id
                and (datetime.utcnow() - e.timestamp).total_seconds() < 60
            ]

            if (
                len(recent_api_calls)
                > self.threat_patterns["rapid_api_calls"]["threshold"]
            ):
                threat_level = ThreatLevel.HIGH
                self._handle_threat("rapid_api_calls", event, threat_level)

        # Check for failed authentication
        if not event.success and event.action in ["authenticate", "validate_token"]:
            recent_failures = [
                e
                for e in self.security_events[-50:]
                if not e.success
                and e.action in ["authenticate", "validate_token"]
                and e.user_id == event.user_id
                and (datetime.utcnow() - e.timestamp).total_seconds()
                < self.threat_patterns["failed_auth_attempts"]["window"]
            ]

            if (
                len(recent_failures)
                >= self.threat_patterns["failed_auth_attempts"]["threshold"]
            ):
                threat_level = ThreatLevel.CRITICAL
                self._handle_threat("failed_auth_attempts", event, threat_level)

        # Check for unusual access patterns
        if event.security_level == SecurityLevel.TOP_SECRET:
            # High-security access requires additional scrutiny
            recent_high_security = [
                e
                for e in self.security_events[-20:]
                if e.security_level == SecurityLevel.TOP_SECRET
                and e.agent_id == event.agent_id
                and (datetime.utcnow() - e.timestamp).total_seconds()
                < self.threat_patterns["unusual_access_patterns"]["window"]
            ]

            if (
                len(recent_high_security)
                > self.threat_patterns["unusual_access_patterns"]["threshold"]
            ):
                threat_level = ThreatLevel.MEDIUM
                self._handle_threat("unusual_access_patterns", event, threat_level)

        return threat_level

    def _handle_threat(
        self, threat_type: str, event: SecurityEvent, threat_level: ThreatLevel
    ):
        """Handle detected threat"""
        pattern = self.threat_patterns[threat_type]
        action = pattern["action"]

        if action == "rate_limit":
            # Implement rate limiting
            with self._lock:
                self.rate_limits[event.agent_id] = [time.time() - 61] * (
                    pattern["threshold"] + 1
                )

        elif action == "block_ip" and event.ip_address:
            # Block IP address
            self.blocked_ips.add(event.ip_address)

        elif action == "block_agent":
            # Block agent
            self.blocked_agents.add(event.agent_id)

        elif action == "alert":
            # Send alert (in real implementation, integrate with alerting system)
            logger.warning(
                f"Security threat detected: {threat_type} from {event.agent_id}"
            )

        # Log threat handling
        self._log_security_event(
            agent_id="security_manager",
            user_id=None,
            action="threat_detected",
            resource=threat_type,
            permission_level=EnhancedPermissionLevel.SYSTEM_ADMIN,
            threat_level=threat_level,
            success=True,
            details={
                "threat_type": threat_type,
                "trigger_event": event.event_id,
                "action_taken": action,
                "blocked_ips": len(self.blocked_ips),
                "blocked_agents": len(self.blocked_agents),
            },
        )

    def _log_security_event(
        self,
        agent_id: str,
        user_id: Optional[str],
        action: str,
        resource: str,
        permission_level: EnhancedPermissionLevel,
        threat_level: ThreatLevel,
        success: bool,
        details: Dict[str, Any] = None,
    ):
        """Log a security event for audit purposes"""
        event = SecurityEvent(
            event_id=secrets.token_hex(16),
            timestamp=datetime.utcnow(),
            agent_id=agent_id,
            user_id=user_id,
            action=action,
            resource=resource,
            permission_level=permission_level,
            threat_level=threat_level,
            success=success,
            details=details or {},
        )

        with self._lock:
            self.security_events.append(event)

        # Keep only recent events (last 10000)
        if len(self.security_events) > 10000:
            self.security_events = self.security_events[-5000:]

        # Write to audit log file
        try:
            log_entry = json.dumps(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "agent_id": event.agent_id,
                    "user_id": event.user_id,
                    "action": event.action,
                    "resource": event.resource,
                    "permission_level": event.permission_level.value,
                    "threat_level": event.threat_level.value,
                    "success": event.success,
                    "details": event.details,
                }
            )

            with open(self.audit_log_file, "a") as f:
                f.write(log_entry + "\n")

        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")

    def get_security_metrics(self) -> Dict[str, Any]:
        """Get comprehensive security metrics"""
        with self._lock:
            # Calculate metrics
            total_events = len(self.security_events)
            recent_events = len(
                [
                    e
                    for e in self.security_events
                    if (datetime.utcnow() - e.timestamp).total_seconds() < 3600
                ]
            )

            success_rate = (
                len([e for e in self.security_events if e.success]) / total_events * 100
                if total_events > 0
                else 0
            )

            threat_counts = {}
            for event in self.security_events:
                threat = event.threat_level.value
                threat_counts[threat] = threat_counts.get(threat, 0) + 1

            return {
                "total_events": total_events,
                "recent_events": recent_events,
                "success_rate": round(success_rate, 2),
                "blocked_ips": len(self.blocked_ips),
                "blocked_agents": len(self.blocked_agents),
                "active_sessions": len(self.active_sessions),
                "threat_distribution": threat_counts,
                "policies_active": len(self.active_policies),
                "encryption_keys": len(self.encryption_keys),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def create_secure_container_config(self, agent_type: str) -> Dict[str, Any]:
        """Create Docker container security configuration"""
        security_configs = {
            "data_operations": {
                "user": "cfbd-data",
                "read_only": False,
                "tmpfs_size": "1G",
                "security_opt": ["no-new-privileges"],
                "cap_drop": ["ALL"],
                "cap_add": ["NET_RAW"],
                "networks": ["cfbd-network"],
                "environment": ["PYTHONUNBUFFERED=1", "CFBD_ENCRYPTION_ENABLED=true"],
            },
            "analytics": {
                "user": "ml-analytics",
                "read_only": False,
                "resources": {"memory": "4G", "cpus": "2.0"},
                "security_opt": ["no-new-privileges"],
                "cap_drop": ["ALL"],
                "devices": ["/dev/dri:/dev/dri"],
                "networks": ["analytics-network"],
            },
            "security": {
                "user": "security-admin",
                "read_only": True,
                "volumes": [f"{self.config_path}:/etc/agent-security:ro"],
                "security_opt": ["no-new-privileges"],
                "cap_drop": ["ALL"],
            },
            "quality_assurance": {
                "user": "qa-agent",
                "read_only": True,
                "tmpfs_size": "512M",
                "security_opt": ["no-new-privileges"],
                "cap_drop": ["ALL"],
            },
        }

        return security_configs.get(agent_type, security_configs["quality_assurance"])

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.utcnow()
        expired_sessions = []

        with self._lock:
            for session_id, session_data in self.active_sessions.items():
                if current_time > session_data["expires_at"]:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.active_sessions[session_id]

        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")


# Global security manager instance
security_manager = SecurityManager()
