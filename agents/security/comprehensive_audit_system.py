#!/usr/bin/env python3
"""
Comprehensive Audit System - Enterprise-Grade Audit Logging and Forensics
Provides detailed audit trails, compliance reporting, and forensic analysis capabilities
"""

import asyncio
import hashlib
import json
import logging
import gzip
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
import threading
from collections import defaultdict, deque
from pathlib import Path
import aiofiles
import aiofiles.os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from ..core.event_stream_manager import (
    EventStreamManager, Event, EventPriority, EventSubscription
)
from ..core.enhanced_agent_framework import EnhancedBaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AuditCategory(Enum):
    """Audit log categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    API_ACCESS = "api_access"
    SYSTEM_EVENTS = "system_events"
    SECURITY_EVENTS = "security_events"
    CONFIGURATION = "configuration"
    PERFORMANCE = "performance"
    ERRORS = "errors"
    USER_ACTIVITY = "user_activity"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ComplianceFramework(Enum):
    """Compliance frameworks"""
    GDPR = "gdpr"
    SOX = "sox"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"
    NIST = "nist"

@dataclass
class AuditEvent:
    """Comprehensive audit event structure"""
    event_id: str
    category: AuditCategory
    severity: AuditSeverity
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source_system: str = ""
    actor_id: Optional[str] = None
    actor_type: Optional[str] = None  # user, system, api_key, service
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    action: str = ""
    outcome: str = ""  # success, failure, partial
    description: str = ""
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    request_id: Optional[str] = None

    # Detailed event data
    request_data: Dict[str, Any] = field(default_factory=dict)
    response_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Security and compliance
    compliance_tags: Set[ComplianceFramework] = field(default_factory=set)
    retention_days: int = 2555  # 7 years default
    requires_encryption: bool = False
    sensitive_data: bool = False

    # Integrity and verification
    event_hash: Optional[str] = None
    previous_event_hash: Optional[str] = None
    chain_position: int = 0

    # Performance metrics
    processing_time_ms: int = 0
    database_queries: int = 0
    external_api_calls: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary"""
        result = asdict(self)
        # Convert sets to lists for JSON serialization
        result['compliance_tags'] = [tag.value for tag in self.compliance_tags]
        # Convert datetime to ISO string
        result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Create audit event from dictionary"""
        # Handle compliance tags
        compliance_tags = {ComplianceFramework(tag) for tag in data.get('compliance_tags', [])}

        # Handle timestamp
        timestamp = datetime.fromisoformat(data['timestamp']) if isinstance(data.get('timestamp'), str) else data.get('timestamp')

        event = cls(
            event_id=data['event_id'],
            category=AuditCategory(data['category']),
            severity=AuditSeverity(data['severity']),
            timestamp=timestamp,
            source_system=data.get('source_system', ''),
            actor_id=data.get('actor_id'),
            actor_type=data.get('actor_type'),
            resource_id=data.get('resource_id'),
            resource_type=data.get('resource_type'),
            action=data.get('action', ''),
            outcome=data.get('outcome', ''),
            description=data.get('description', ''),
            ip_address=data.get('ip_address'),
            user_agent=data.get('user_agent'),
            session_id=data.get('session_id'),
            correlation_id=data.get('correlation_id'),
            request_id=data.get('request_id'),
            request_data=data.get('request_data', {}),
            response_data=data.get('response_data', {}),
            metadata=data.get('metadata', {}),
            compliance_tags=compliance_tags,
            retention_days=data.get('retention_days', 2555),
            requires_encryption=data.get('requires_encryption', False),
            sensitive_data=data.get('sensitive_data', False),
            event_hash=data.get('event_hash'),
            previous_event_hash=data.get('previous_event_hash'),
            chain_position=data.get('chain_position', 0),
            processing_time_ms=data.get('processing_time_ms', 0),
            database_queries=data.get('database_queries', 0),
            external_api_calls=data.get('external_api_calls', 0)
        )
        return event

@dataclass
class AuditConfiguration:
    """Configuration for audit system"""
    storage_directory: str = "audit_logs"
    encryption_enabled: bool = True
    encryption_key: Optional[bytes] = None
    compression_enabled: bool = True
    file_rotation_mb: int = 100
    retention_policies: Dict[ComplianceFramework, int] = field(default_factory=lambda: {
        ComplianceFramework.GDPR: 2555,      # 7 years
        ComplianceFramework.SOX: 2555,       # 7 years
        ComplianceFramework.HIPAA: 2190,     # 6 years
        ComplianceFramework.PCI_DSS: 365,    # 1 year
        ComplianceFramework.ISO_27001: 2555, # 7 years
        ComplianceFramework.NIST: 2555       # 7 years
    })
    batch_size: int = 100
    flush_interval_seconds: int = 60
    event_buffer_size: int = 10000
    forensic_mode: bool = False

class ComprehensiveAuditSystem(EnhancedBaseAgent):
    """
    Enterprise-grade comprehensive audit system with encryption,
    compression, compliance reporting, and forensic analysis capabilities
    """

    def __init__(self, agent_id: str = "comprehensive_audit_system"):
        super().__init__(
            agent_id=agent_id,
            agent_name="Comprehensive Audit System",
            permission_level=self.PermissionLevel.READ_ONLY
        )

        # Configuration
        self.config = AuditConfiguration()

        # Event storage and processing
        self.event_buffer: deque = deque(maxlen=self.config.event_buffer_size)
        self.event_chains: Dict[str, List[AuditEvent]] = defaultdict(list)
        self.processed_events: deque = deque(maxlen=100000)  # Recent events for quick access

        # Encryption
        self.encryption_key: Optional[Fernet] = None
        if self.config.encryption_enabled:
            self.encryption_key = self._generate_encryption_key()

        # File management
        self.current_file_handle = None
        self.current_file_path: Optional[Path] = None
        self.current_file_size = 0
        self.file_rotation_lock = threading.Lock()

        # Event stream integration
        self.event_manager: Optional[EventStreamManager] = None

        # Compliance and reporting
        self.compliance_reports: Dict[str, Dict[str, Any]] = {}
        self.forensic_markers: Dict[str, Dict[str, Any]] = {}

        # Performance metrics
        self.audit_metrics = {
            "events_processed": 0,
            "events_encrypted": 0,
            "files_created": 0,
            "storage_used_mb": 0,
            "average_processing_time_ms": 0.0,
            "compliance_reports_generated": 0,
            "forensic_queries_handled": 0
        }

        # Background processing
        self.flush_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.compliance_task: Optional[asyncio.Task] = None

        # Audit statistics
        self.category_counts = defaultdict(int)
        self.severity_counts = defaultdict(int)
        self.hourly_counts = defaultdict(int)

    def _define_capabilities(self) -> List['AgentCapability']:
        """Define audit system capabilities"""
        return [
            self.AgentCapability(
                name="log_audit_event",
                description="Log comprehensive audit events with encryption and integrity verification",
                execution_time_estimate=2.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["audit_event_data", "compliance_tags", "encryption_required"],
                returns={"event_id": "string", "logged": "bool", "chain_position": "int"}
            ),
            self.AgentCapability(
                name="generate_compliance_report",
                description="Generate compliance reports for various frameworks (GDPR, SOX, HIPAA, etc.)",
                execution_time_estimate=10.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["framework", "date_range", "report_format"],
                returns={"report_id": "string", "report_data": "dict", "download_url": "string"}
            ),
            self.AgentCapability(
                name="perform_forensic_analysis",
                description="Perform detailed forensic analysis on audit trails and event chains",
                execution_time_estimate=15.0,
                required_permissions=[self.PermissionLevel.READ_ONLY],
                parameters=["analysis_type", "time_range", "filters", "correlation_id"],
                returns={"analysis_results": "dict", "evidence_chains": "list", "recommendations": "list"}
            ),
            self.AgentCapability(
                name="manage_retention_policies",
                description="Manage data retention policies and automated cleanup procedures",
                execution_time_estimate=5.0,
                required_permissions=[self.PermissionLevel.READ_EXECUTE],
                parameters=["policy_updates", "compliance_frameworks", "cleanup_actions"],
                returns={"policies_updated": "list", "cleanup_results": "dict"}
            )
        ]

    async def initialize(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize the comprehensive audit system

        Args:
            config: Configuration dictionary

        Returns:
            Initialization status
        """
        try:
            # Update configuration
            if "audit" in config:
                audit_config = config["audit"]
                self.config = AuditConfiguration(**audit_config)

            # Create storage directory
            storage_path = Path(self.config.storage_directory)
            storage_path.mkdir(parents=True, exist_ok=True)

            # Initialize encryption
            if self.config.encryption_enabled and not self.encryption_key:
                self.encryption_key = self._load_or_create_encryption_key()

            # Initialize event stream manager
            if "event_stream" in config:
                event_config = config["event_stream"]
                self.event_manager = EventStreamManager(event_config)
                await self.event_manager.initialize()
                await self._setup_audit_subscriptions()

            # Initialize current file
            await self._initialize_current_file()

            # Start background tasks
            self.flush_task = asyncio.create_task(self._flush_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.compliance_task = asyncio.create_task(self._compliance_loop())

            # Load existing forensic markers
            await self._load_forensic_markers()

            logger.info("Comprehensive Audit System initialized successfully")
            return {
                "status": "success",
                "storage_directory": self.config.storage_directory,
                "encryption_enabled": self.config.encryption_enabled,
                "compression_enabled": self.config.compression_enabled,
                "forensic_mode": self.config.forensic_mode,
                "compliance_frameworks": [fw.value for fw in self.config.retention_policies.keys()]
            }

        except Exception as e:
            logger.error(f"Failed to initialize Comprehensive Audit System: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _generate_encryption_key(self) -> Fernet:
        """Generate encryption key for audit log encryption"""
        password = b"audit_system_encryption_password"  # In production, use secure key management
        salt = b"audit_system_salt"  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return Fernet(key)

    def _load_or_create_encryption_key(self) -> Fernet:
        """Load existing encryption key or create new one"""
        key_file = Path(self.config.storage_directory) / "audit_encryption.key"

        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    key_data = f.read()
                return Fernet(key_data)
            except Exception as e:
                logger.warning(f"Failed to load encryption key, creating new one: {e}")

        # Generate new key
        key = self._generate_encryption_key()
        try:
            with open(key_file, 'wb') as f:
                f.write(key.encryption_key)
            logger.info("Created new encryption key")
        except Exception as e:
            logger.error(f"Failed to save encryption key: {e}")

        return key

    async def _setup_audit_subscriptions(self) -> None:
        """Setup event subscriptions for comprehensive audit logging"""
        # All security events
        security_subscription = EventSubscription(
            subscriber_id="comprehensive_audit_security",
            event_types={
                "security.*",  # All security events
                "api.*",       # All API events
                "auth.*",      # All authentication events
                "credential.*" # All credential events
            },
            priority_filter={EventPriority.HIGH, EventPriority.CRITICAL, EventPriority.NORMAL}
        )
        await self.event_manager.subscribe_to_events(security_subscription)

        # System events
        system_subscription = EventSubscription(
            subscriber_id="comprehensive_audit_system",
            event_types={
                "pipeline.*",
                "agent.*",
                "system.*"
            }
        )
        await self.event_manager.subscribe_to_events(system_subscription)

    async def _initialize_current_file(self) -> None:
        """Initialize current audit log file"""
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        file_name = f"audit_{current_date}_{uuid.uuid4().hex[:8]}.jsonl"

        if self.config.compression_enabled:
            file_name += ".gz"

        self.current_file_path = Path(self.config.storage_directory) / file_name
        self.current_file_size = 0

        # Create file with header
        if self.current_file_path.exists():
            # Append to existing file
            self.current_file_size = self.current_file_path.stat().st_size
        else:
            # Create new file
            async with aiofiles.open(self.current_file_path, 'w') as f:
                header = {
                    "file_created": datetime.now(timezone.utc).isoformat(),
                    "version": "1.0",
                    "encryption_enabled": self.config.encryption_enabled,
                    "compression_enabled": self.config.compression_enabled
                }
                await f.write(json.dumps(header) + '\n')

    async def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Execute audit system actions"""
        try:
            if action == "log_audit_event":
                return await self._log_audit_event(parameters, user_context)
            elif action == "generate_compliance_report":
                return await self._generate_compliance_report(parameters, user_context)
            elif action == "perform_forensic_analysis":
                return await self._perform_forensic_analysis(parameters, user_context)
            elif action == "manage_retention_policies":
                return await self._manage_retention_policies(parameters, user_context)
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

    async def _log_audit_event(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Log a comprehensive audit event"""
        try:
            event_data = parameters.get("audit_event_data", {})
            compliance_tags = parameters.get("compliance_tags", [])
            encryption_required = parameters.get("encryption_required", False)

            # Create audit event
            audit_event = AuditEvent(
                event_id=str(uuid.uuid4()),
                category=AuditCategory(event_data.get("category", "system_events")),
                severity=AuditSeverity(event_data.get("severity", "info")),
                source_system=event_data.get("source_system", "unknown"),
                actor_id=event_data.get("actor_id"),
                actor_type=event_data.get("actor_type"),
                resource_id=event_data.get("resource_id"),
                resource_type=event_data.get("resource_type"),
                action=event_data.get("action", ""),
                outcome=event_data.get("outcome", "success"),
                description=event_data.get("description", ""),
                ip_address=event_data.get("ip_address"),
                user_agent=event_data.get("user_agent"),
                session_id=event_data.get("session_id"),
                correlation_id=event_data.get("correlation_id"),
                request_id=event_data.get("request_id"),
                request_data=event_data.get("request_data", {}),
                response_data=event_data.get("response_data", {}),
                metadata=event_data.get("metadata", {}),
                compliance_tags={ComplianceFramework(tag) for tag in compliance_tags},
                requires_encryption=encryption_required or event_data.get("sensitive_data", False),
                sensitive_data=event_data.get("sensitive_data", False),
                processing_time_ms=event_data.get("processing_time_ms", 0)
            )

            # Set retention based on compliance tags
            if audit_event.compliance_tags:
                max_retention = max(
                    self.config.retention_policies.get(tag, 2555)
                    for tag in audit_event.compliance_tags
                )
                audit_event.retention_days = max_retention

            # Generate event hash for integrity
            audit_event.event_hash = self._generate_event_hash(audit_event)

            # Add to event chain if correlation exists
            if audit_event.correlation_id:
                chain = self.event_chains[audit_event.correlation_id]
                if chain:
                    audit_event.previous_event_hash = chain[-1].event_hash
                    audit_event.chain_position = len(chain)
                chain.append(audit_event)

            # Add to buffer
            self.event_buffer.append(audit_event)
            self.processed_events.append(audit_event)

            # Update metrics
            self.audit_metrics["events_processed"] += 1
            self.category_counts[audit_event.category.value] += 1
            self.severity_counts[audit_event.severity.value] += 1

            # Hourly count for monitoring
            hour_key = audit_event.timestamp.strftime("%Y-%m-%d %H:00")
            self.hourly_counts[hour_key] += 1

            # Create forensic marker for significant events
            if audit_event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                await self._create_forensic_marker(audit_event)

            logger.debug(f"Audit event logged: {audit_event.event_id} ({audit_event.category.value})")

            return {
                "status": "success",
                "event_id": audit_event.event_id,
                "logged": True,
                "chain_position": audit_event.chain_position,
                "event_hash": audit_event.event_hash,
                "correlation_id": audit_event.correlation_id
            }

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _generate_event_hash(self, event: AuditEvent) -> str:
        """Generate cryptographic hash for event integrity"""
        # Create canonical representation
        event_data = {
            "event_id": event.event_id,
            "category": event.category.value,
            "severity": event.severity.value,
            "timestamp": event.timestamp.isoformat(),
            "source_system": event.source_system,
            "actor_id": event.actor_id,
            "action": event.action,
            "outcome": event.outcome,
            "resource_id": event.resource_id,
            "previous_event_hash": event.previous_event_hash,
            "chain_position": event.chain_position
        }

        # Sort and serialize
        event_string = json.dumps(event_data, sort_keys=True, separators=(',', ':'))

        # Generate hash
        return hashlib.sha256(event_string.encode()).hexdigest()

    async def _create_forensic_marker(self, event: AuditEvent) -> None:
        """Create forensic marker for significant events"""
        marker = {
            "event_id": event.event_id,
            "timestamp": event.timestamp.isoformat(),
            "severity": event.severity.value,
            "category": event.category.value,
            "actor_id": event.actor_id,
            "correlation_id": event.correlation_id,
            "description": event.description,
            "file_location": str(self.current_file_path) if self.current_file_path else None,
            "requires_investigation": event.severity == AuditSeverity.CRITICAL
        }

        self.forensic_markers[event.event_id] = marker

        # Publish forensic marker event
        if self.event_manager:
            forensic_event = Event(
                type="audit.forensic_marker.created",
                source="comprehensive_audit_system",
                data=marker,
                priority=EventPriority.HIGH
            )
            await self.event_manager.publish_event(forensic_event)

    async def _generate_compliance_report(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Generate compliance reports for various frameworks"""
        framework = parameters.get("framework")
        date_range = parameters.get("date_range", {})
        report_format = parameters.get("report_format", "json")

        try:
            if not framework:
                raise ValueError("Framework is required for compliance reporting")

            compliance_framework = ComplianceFramework(framework)

            # Parse date range
            start_date = datetime.fromisoformat(date_range.get("start", (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()))
            end_date = datetime.fromisoformat(date_range.get("end", datetime.now(timezone.utc).isoformat()))

            # Generate report ID
            report_id = f"compliance_{framework}_{int(time.time())}_{uuid.uuid4().hex[:8]}"

            # Collect events for the period
            events = await self._get_events_by_date_range(start_date, end_date)

            # Filter by compliance framework
            relevant_events = [
                event for event in events
                if compliance_framework in event.compliance_tags
            ]

            # Generate framework-specific report
            if compliance_framework == ComplianceFramework.GDPR:
                report_data = await self._generate_gdpr_report(relevant_events, start_date, end_date)
            elif compliance_framework == ComplianceFramework.SOX:
                report_data = await self._generate_sox_report(relevant_events, start_date, end_date)
            elif compliance_framework == ComplianceFramework.HIPAA:
                report_data = await self._generate_hipaa_report(relevant_events, start_date, end_date)
            else:
                report_data = await self._generate_generic_compliance_report(relevant_events, compliance_framework, start_date, end_date)

            # Save report
            report_path = await self._save_compliance_report(report_id, report_data, report_format)

            # Store report metadata
            self.compliance_reports[report_id] = {
                "framework": framework,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "event_count": len(relevant_events),
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "file_path": str(report_path),
                "format": report_format
            }

            self.audit_metrics["compliance_reports_generated"] += 1

            logger.info(f"Generated {framework} compliance report: {report_id}")

            return {
                "status": "success",
                "report_id": report_id,
                "report_data": report_data if report_format == "json" else None,
                "download_url": f"file://{report_path}",
                "event_count": len(relevant_events),
                "framework": framework,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()}
            }

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {
                "status": "error",
                "error": str(e),
                "framework": framework
            }

    async def _generate_gdpr_report(self, events: List[AuditEvent], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate GDPR compliance report"""
        report = {
            "framework": "GDPR",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": {
                "total_events": len(events),
                "data_access_events": 0,
                "data_processing_events": 0,
                "consent_related_events": 0,
                "data_subject_requests": 0,
                "breach_events": 0
            },
            "categories": defaultdict(int),
            "data_subjects": set(),
            "data_types": set(),
            "processing_purposes": set(),
            "recommendations": []
        }

        for event in events:
            # Categorize events
            if "data_access" in event.description.lower() or "data_access" in event.action:
                report["summary"]["data_access_events"] += 1
                report["categories"]["data_access"] += 1

            if "data_processing" in event.description.lower() or "process" in event.action:
                report["summary"]["data_processing_events"] += 1
                report["categories"]["data_processing"] += 1

            if "consent" in event.description.lower():
                report["summary"]["consent_related_events"] += 1
                report["categories"]["consent"] += 1

            if "data_subject_request" in event.action or "dsar" in event.action:
                report["summary"]["data_subject_requests"] += 1
                report["categories"]["data_subject_request"] += 1

            if "breach" in event.description.lower() or event.severity == AuditSeverity.CRITICAL:
                report["summary"]["breach_events"] += 1
                report["categories"]["data_breach"] += 1

            # Collect GDPR-specific information
            if event.actor_id:
                report["data_subjects"].add(event.actor_id)

            # Extract data types from metadata
            data_types = event.metadata.get("data_types", [])
            if data_types:
                report["data_types"].update(data_types)

            # Extract processing purposes
            purposes = event.metadata.get("processing_purposes", [])
            if purposes:
                report["processing_purposes"].update(purposes)

        # Convert sets to counts for serialization
        report["summary"]["unique_data_subjects"] = len(report["data_subjects"])
        report["summary"]["unique_data_types"] = len(report["data_types"])
        report["summary"]["unique_purposes"] = len(report["processing_purposes"])
        report["data_subjects"] = list(report["data_subjects"])
        report["data_types"] = list(report["data_types"])
        report["processing_purposes"] = list(report["processing_purposes"])

        # Generate recommendations
        if report["summary"]["breach_events"] > 0:
            report["recommendations"].append("Review breach response procedures and notify supervisory authority if required")

        if report["summary"]["data_subject_requests"] > 0:
            report["recommendations"].append("Ensure timely response to data subject requests within GDPR timelines")

        if len(report["data_types"]) > 10:
            report["recommendations"].append("Consider data minimization principles and review data inventory")

        return report

    async def _generate_sox_report(self, events: List[AuditEvent], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate SOX compliance report"""
        report = {
            "framework": "SOX",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": {
                "total_events": len(events),
                "financial_system_access": 0,
                "configuration_changes": 0,
                "privileged_access": 0,
                "audit_events": 0,
                "control_failures": 0
            },
            "control_objectives": defaultdict(int),
            "system_access": defaultdict(int),
            "user_activities": defaultdict(list),
            "recommendations": []
        }

        for event in events:
            # SOX-specific categorization
            if "financial" in event.description.lower() or "financial" in event.resource_type:
                report["summary"]["financial_system_access"] += 1
                report["control_objectives"]["financial_reporting"] += 1

            if "config" in event.action or "configure" in event.action or "change" in event.action:
                report["summary"]["configuration_changes"] += 1
                report["control_objectives"]["change_management"] += 1

            if event.actor_type in ["admin", "privileged", "root"]:
                report["summary"]["privileged_access"] += 1
                report["control_objectives"]["access_control"] += 1

            if "audit" in event.category.value:
                report["summary"]["audit_events"] += 1
                report["control_objectives"]["audit_logging"] += 1

            if event.outcome == "failure" or event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                report["summary"]["control_failures"] += 1

            # Track user activities
            if event.actor_id:
                report["user_activities"][event.actor_id].append({
                    "timestamp": event.timestamp.isoformat(),
                    "action": event.action,
                    "resource": event.resource_id,
                    "outcome": event.outcome
                })

        # Generate SOX recommendations
        if report["summary"]["configuration_changes"] > 50:
            report["recommendations"].append("High number of configuration changes detected - review change management controls")

        if report["summary"]["privileged_access"] > 100:
            report["recommendations"].append("High privileged access usage - review access controls and segregation of duties")

        if report["summary"]["control_failures"] > 10:
            report["recommendations"].append("Multiple control failures detected - immediate investigation required")

        return report

    async def _generate_hipaa_report(self, events: List[AuditEvent], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate HIPAA compliance report"""
        report = {
            "framework": "HIPAA",
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": {
                "total_events": len(events),
                "phi_access": 0,
                "authentication_events": 0,
                "authorization_failures": 0,
                "audit_events": 0,
                "security_incidents": 0
            },
            "phi_categories": defaultdict(int),
            "user_activities": defaultdict(list),
            "security_measures": defaultdict(int),
            "recommendations": []
        }

        for event in events:
            # HIPAA-specific categorization
            if "phi" in event.description.lower() or "protected_health_info" in event.description.lower():
                report["summary"]["phi_access"] += 1
                phi_category = event.metadata.get("phi_category", "unknown")
                report["phi_categories"][phi_category] += 1

            if event.category == AuditCategory.AUTHENTICATION:
                report["summary"]["authentication_events"] += 1
                report["security_measures"]["authentication"] += 1

            if event.category == AuditCategory.AUTHORIZATION:
                report["summary"]["authorization_failures"] += 1 if event.outcome == "failure" else 0
                report["security_measures"]["authorization"] += 1

            if event.category == AuditCategory.SECURITY_EVENTS:
                report["summary"]["security_incidents"] += 1

            # Track user access to PHI
            if "phi" in event.description.lower() and event.actor_id:
                report["user_activities"][event.actor_id].append({
                    "timestamp": event.timestamp.isoformat(),
                    "action": event.action,
                    "phi_category": event.metadata.get("phi_category"),
                    "access_reason": event.metadata.get("access_reason"),
                    "outcome": event.outcome
                })

        # Generate HIPAA recommendations
        if report["summary"]["authorization_failures"] > 5:
            report["recommendations"].append("Multiple authorization failures detected - review access controls")

        if len(report["user_activities"]) > 20:
            report["recommendations"].append("High number of users accessing PHI - review minimum necessary principle")

        if report["summary"]["security_incidents"] > 0:
            report["recommendations"].append("Security incidents detected - ensure proper incident response procedures")

        return report

    async def _generate_generic_compliance_report(self, events: List[AuditEvent], framework: ComplianceFramework, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate generic compliance report for other frameworks"""
        report = {
            "framework": framework.value,
            "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "summary": {
                "total_events": len(events),
                "by_category": defaultdict(int),
                "by_severity": defaultdict(int),
                "success_rate": 0,
                "failure_count": 0
            },
            "events": []
        }

        # Analyze events
        for event in events:
            report["summary"]["by_category"][event.category.value] += 1
            report["summary"]["by_severity"][event.severity.value] += 1

            if event.outcome == "failure":
                report["summary"]["failure_count"] += 1

            # Include key events in report
            if event.severity in [AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
                report["events"].append({
                    "event_id": event.event_id,
                    "timestamp": event.timestamp.isoformat(),
                    "category": event.category.value,
                    "severity": event.severity.value,
                    "description": event.description,
                    "actor_id": event.actor_id
                })

        # Calculate success rate
        if len(events) > 0:
            report["summary"]["success_rate"] = ((len(events) - report["summary"]["failure_count"]) / len(events)) * 100

        return report

    async def _perform_forensic_analysis(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Perform detailed forensic analysis on audit trails"""
        analysis_type = parameters.get("analysis_type", "timeline")
        time_range = parameters.get("time_range", {})
        filters = parameters.get("filters", {})
        correlation_id = parameters.get("correlation_id")

        try:
            # Parse time range
            start_date = datetime.fromisoformat(time_range.get("start", (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()))
            end_date = datetime.fromisoformat(time_range.get("end", datetime.now(timezone.utc).isoformat()))

            # Get events for analysis
            if correlation_id:
                # Analyze specific event chain
                events = self.event_chains.get(correlation_id, [])
            else:
                # Get events by time range and filters
                events = await self._get_events_by_date_range(start_date, end_date)

                # Apply filters
                if filters:
                    events = await self._apply_event_filters(events, filters)

            # Perform analysis
            if analysis_type == "timeline":
                analysis_results = await self._analyze_timeline(events, start_date, end_date)
            elif analysis_type == "anomaly":
                analysis_results = await self._detect_anomalies(events)
            elif analysis_type == "user_behavior":
                analysis_results = await self._analyze_user_behavior(events)
            elif analysis_type == "security":
                analysis_results = await self._analyze_security_patterns(events)
            else:
                analysis_results = await self._analyze_timeline(events, start_date, end_date)

            # Generate evidence chains
            evidence_chains = await self._build_evidence_chains(events)

            # Generate recommendations
            recommendations = await self._generate_forensic_recommendations(analysis_results, events)

            self.audit_metrics["forensic_queries_handled"] += 1

            logger.info(f"Forensic analysis completed: {analysis_type} ({len(events)} events)")

            return {
                "status": "success",
                "analysis_type": analysis_type,
                "analysis_results": analysis_results,
                "evidence_chains": evidence_chains,
                "recommendations": recommendations,
                "events_analyzed": len(events),
                "time_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "correlation_id": correlation_id
            }

        except Exception as e:
            logger.error(f"Failed to perform forensic analysis: {e}")
            return {
                "status": "error",
                "error": str(e),
                "analysis_type": analysis_type
            }

    async def _analyze_timeline(self, events: List[AuditEvent], start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Analyze events in timeline order"""
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        timeline = []
        for event in sorted_events:
            timeline.append({
                "timestamp": event.timestamp.isoformat(),
                "event_id": event.event_id,
                "category": event.category.value,
                "severity": event.severity.value,
                "actor": event.actor_id,
                "action": event.action,
                "outcome": event.outcome,
                "description": event.description,
                "processing_time_ms": event.processing_time_ms
            })

        # Identify patterns and gaps
        patterns = []
        if len(sorted_events) > 1:
            # Calculate time gaps
            time_gaps = []
            for i in range(1, len(sorted_events)):
                gap = (sorted_events[i].timestamp - sorted_events[i-1].timestamp).total_seconds()
                time_gaps.append(gap)

            if time_gaps:
                avg_gap = sum(time_gaps) / len(time_gaps)
                max_gap = max(time_gaps)
                min_gap = min(time_gaps)

                patterns.append({
                    "type": "time_gaps",
                    "average_gap_seconds": avg_gap,
                    "maximum_gap_seconds": max_gap,
                    "minimum_gap_seconds": min_gap,
                    "unusual_gaps": [gap for gap in time_gaps if gap > avg_gap * 3]
                })

        return {
            "timeline": timeline,
            "patterns": patterns,
            "summary": {
                "total_events": len(events),
                "time_span_hours": (end_date - start_date).total_seconds() / 3600,
                "events_per_hour": len(events) / max(1, (end_date - start_date).total_seconds() / 3600)
            }
        }

    async def _detect_anomalies(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Detect anomalies in event patterns"""
        anomalies = []

        # Group events by actor
        actor_events = defaultdict(list)
        for event in events:
            if event.actor_id:
                actor_events[event.actor_id].append(event)

        # Detect anomalies per actor
        for actor_id, actor_event_list in actor_events.items():
            # Check for rapid succession events
            if len(actor_event_list) > 10:
                time_diffs = []
                for i in range(1, len(actor_event_list)):
                    diff = (actor_event_list[i].timestamp - actor_event_list[i-1].timestamp).total_seconds()
                    time_diffs.append(diff)

                if time_diffs:
                    avg_diff = sum(time_diffs) / len(time_diffs)
                    if avg_diff < 1:  # Less than 1 second between actions
                        anomalies.append({
                            "type": "rapid_actions",
                            "actor_id": actor_id,
                            "description": f"Rapid succession actions (avg {avg_diff:.2f}s between actions)",
                            "severity": "medium",
                            "event_count": len(actor_event_list)
                        })

        # Detect failed authentication patterns
        auth_failures = [
            event for event in events
            if event.category == AuditCategory.AUTHENTICATION and event.outcome == "failure"
        ]

        if len(auth_failures) > 5:
            anomalies.append({
                "type": "authentication_failures",
                "description": f"Multiple authentication failures detected",
                "severity": "high",
                "failure_count": len(auth_failures)
            })

        return {
            "anomalies": anomalies,
            "summary": {
                "total_anomalies": len(anomalies),
                "high_severity": len([a for a in anomalies if a.get("severity") == "high"]),
                "medium_severity": len([a for a in anomalies if a.get("severity") == "medium"]),
                "low_severity": len([a for a in anomalies if a.get("severity") == "low"])
            }
        }

    async def _analyze_user_behavior(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Analyze user behavior patterns"""
        user_analysis = {}

        # Group by user
        user_events = defaultdict(list)
        for event in events:
            if event.actor_id:
                user_events[event.actor_id].append(event)

        # Analyze each user
        for user_id, user_event_list in user_events.items():
            user_data = {
                "total_events": len(user_event_list),
                "categories": defaultdict(int),
                "actions": defaultdict(int),
                "outcomes": defaultdict(int),
                "time_distribution": defaultdict(int),
                "risk_score": 0
            }

            # Analyze event patterns
            for event in user_event_list:
                user_data["categories"][event.category.value] += 1
                user_data["actions"][event.action] += 1
                user_data["outcomes"][event.outcome] += 1

                # Time distribution
                hour = event.timestamp.hour
                user_data["time_distribution"][hour] += 1

            # Calculate risk score
            failure_rate = user_data["outcomes"].get("failure", 0) / max(1, len(user_event_list))
            if failure_rate > 0.2:  # More than 20% failure rate
                user_data["risk_score"] += 30

            # Check for unusual activity patterns
            if user_event_list:
                time_span = (max(event.timestamp for event in user_event_list) -
                            min(event.timestamp for event in user_event_list)).total_seconds()
                if time_span > 0:
                    frequency = len(user_event_list) / (time_span / 3600)  # events per hour
                    if frequency > 100:  # Very high frequency
                        user_data["risk_score"] += 20

            user_analysis[user_id] = user_data

        return {
            "user_analysis": user_analysis,
            "summary": {
                "total_users": len(user_analysis),
                "high_risk_users": len([u for u in user_analysis.values() if u["risk_score"] > 50]),
                "average_events_per_user": sum(u["total_events"] for u in user_analysis.values()) / max(1, len(user_analysis))
            }
        }

    async def _analyze_security_patterns(self, events: List[AuditEvent]) -> Dict[str, Any]:
        """Analyze security-related patterns"""
        security_events = [
            event for event in events
            if event.category in [AuditCategory.SECURITY_EVENTS, AuditCategory.AUTHENTICATION, AuditCategory.AUTHORIZATION]
        ]

        analysis = {
            "security_events": len(security_events),
            "attack_patterns": [],
            "vulnerabilities": [],
            "compliance_gaps": []
        }

        # Look for potential attack patterns
        auth_failures = [e for e in security_events if e.category == AuditCategory.AUTHENTICATION and e.outcome == "failure"]
        if len(auth_failures) > 10:
            analysis["attack_patterns"].append({
                "type": "brute_force_attempt",
                "description": f"Multiple authentication failures from various sources",
                "severity": "high",
                "failure_count": len(auth_failures)
            })

        # Check for privilege escalation attempts
        unauthorized_access = [e for e in security_events if e.category == AuditCategory.AUTHORIZATION and e.outcome == "failure"]
        if len(unauthorized_access) > 5:
            analysis["attack_patterns"].append({
                "type": "privilege_escalation",
                "description": "Multiple unauthorized access attempts",
                "severity": "high",
                "attempt_count": len(unauthorized_access)
            })

        return analysis

    async def _build_evidence_chains(self, events: List[AuditEvent]) -> List[Dict[str, Any]]:
        """Build evidence chains from related events"""
        chains = []

        # Group by correlation ID
        correlation_groups = defaultdict(list)
        for event in events:
            if event.correlation_id:
                correlation_groups[event.correlation_id].append(event)

        # Build chains for each correlation group
        for correlation_id, group_events in correlation_groups.items():
            if len(group_events) > 1:  # Only chains with multiple events
                chain = {
                    "correlation_id": correlation_id,
                    "event_count": len(group_events),
                    "time_span": "",
                    "actors": set(),
                    "actions": [],
                    "summary": ""
                }

                # Sort events by timestamp
                sorted_events = sorted(group_events, key=lambda e: e.timestamp)

                # Calculate time span
                if len(sorted_events) > 1:
                    time_span = sorted_events[-1].timestamp - sorted_events[0].timestamp
                    chain["time_span"] = str(time_span)

                # Extract actors and actions
                for event in sorted_events:
                    if event.actor_id:
                        chain["actors"].add(event.actor_id)
                    chain["actions"].append(event.action)

                # Convert actors set to list
                chain["actors"] = list(chain["actors"])

                # Generate summary
                if chain["actors"]:
                    chain["summary"] = f"Activity involving {', '.join(chain['actors'])} with {len(chain['actions'])} actions over {chain['time_span']}"
                else:
                    chain["summary"] = f"System activity with {len(chain['actions'])} actions over {chain['time_span']}"

                chains.append(chain)

        return chains

    async def _generate_forensic_recommendations(self, analysis_results: Dict[str, Any], events: List[AuditEvent]) -> List[str]:
        """Generate recommendations based on forensic analysis"""
        recommendations = []

        # Analyze anomalies
        if "anomalies" in analysis_results:
            anomalies = analysis_results["anomalies"]
            if anomalies.get("high_severity", 0) > 0:
                recommendations.append("Immediate investigation required for high-severity anomalies")

            if anomalies.get("medium_severity", 0) > 5:
                recommendations.append("Review security controls due to multiple medium-severity anomalies")

        # Analyze user behavior
        if "user_analysis" in analysis_results:
            user_analysis = analysis_results["user_analysis"]
            high_risk_users = [uid for uid, data in user_analysis.items() if data.get("risk_score", 0) > 50]
            if high_risk_users:
                recommendations.append(f"Review activity for high-risk users: {', '.join(high_risk_users)}")

        # Analyze security patterns
        if "security_patterns" in analysis_results:
            security_patterns = analysis_results["security_patterns"]
            if security_patterns.get("attack_patterns"):
                recommendations.append("Implement additional security measures to address detected attack patterns")

        # General recommendations
        if len(events) > 1000:
            recommendations.append("Consider implementing automated monitoring for high-volume periods")

        critical_events = [e for e in events if e.severity == AuditSeverity.CRITICAL]
        if critical_events:
            recommendations.append(f"Review {len(critical_events)} critical events for immediate action")

        return recommendations

    async def _manage_retention_policies(self, parameters: Dict, user_context: Dict) -> Dict[str, Any]:
        """Manage data retention policies and cleanup"""
        policy_updates = parameters.get("policy_updates", {})
        compliance_frameworks = parameters.get("compliance_frameworks", [])
        cleanup_actions = parameters.get("cleanup_actions", [])

        try:
            updated_policies = []
            cleanup_results = {}

            # Update retention policies
            for framework_name, retention_days in policy_updates.items():
                try:
                    framework = ComplianceFramework(framework_name)
                    self.config.retention_policies[framework] = retention_days
                    updated_policies.append(framework_name)
                except ValueError:
                    logger.warning(f"Unknown compliance framework: {framework_name}")

            # Perform cleanup actions
            if "expired_events" in cleanup_actions:
                cleanup_results["expired_events"] = await self._cleanup_expired_events()

            if "old_files" in cleanup_actions:
                cleanup_results["old_files"] = await self._cleanup_old_files()

            if "orphaned_markers" in cleanup_actions:
                cleanup_results["orphaned_markers"] = await self._cleanup_orphaned_markers()

            logger.info(f"Retention policies updated: {updated_policies}")

            return {
                "status": "success",
                "policies_updated": updated_policies,
                "cleanup_results": cleanup_results,
                "current_retention_policies": {
                    fw.value: days for fw, days in self.config.retention_policies.items()
                }
            }

        except Exception as e:
            logger.error(f"Failed to manage retention policies: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _cleanup_expired_events(self) -> Dict[str, Any]:
        """Clean up expired audit events"""
        current_time = datetime.now(timezone.utc)
        events_removed = 0
        storage_freed_mb = 0

        # Check processed events
        cutoff_times = {}
        for framework, retention_days in self.config.retention_policies.items():
            cutoff_times[framework] = current_time - timedelta(days=retention_days)

        # Filter events for removal
        events_to_keep = []
        for event in self.processed_events:
            should_keep = True
            earliest_cutoff = min(cutoff_times.values()) if cutoff_times else current_time - timedelta(days=365)

            if event.timestamp < earliest_cutoff:
                should_keep = False
                events_removed += 1
                # Estimate storage freed (rough calculation)
                storage_freed_mb += 0.001  # ~1KB per event estimate

            if should_keep:
                events_to_keep.append(event)

        # Update processed events
        self.processed_events = deque(events_to_keep, maxlen=100000)

        return {
            "events_removed": events_removed,
            "storage_freed_mb": storage_freed_mb
        }

    async def _cleanup_old_files(self) -> Dict[str, Any]:
        """Clean up old audit log files"""
        files_removed = 0
        storage_freed_mb = 0

        try:
            storage_path = Path(self.config.storage_directory)
            if storage_path.exists():
                current_time = datetime.now(timezone.utc)
                cutoff_time = current_time - timedelta(days=365)  # Default 1 year retention for files

                for file_path in storage_path.glob("audit_*.jsonl*"):
                    if file_path.stat().st_mtime < cutoff_time.timestamp():
                        file_size_mb = file_path.stat().st_size / (1024 * 1024)
                        await aiofiles.os.remove(file_path)
                        files_removed += 1
                        storage_freed_mb += file_size_mb

        except Exception as e:
            logger.error(f"Error cleaning up old files: {e}")

        return {
            "files_removed": files_removed,
            "storage_freed_mb": storage_freed_mb
        }

    async def _cleanup_orphaned_markers(self) -> Dict[str, Any]:
        """Clean up orphaned forensic markers"""
        markers_removed = 0

        # Find markers for events that no longer exist
        orphaned_markers = []
        for event_id, marker in self.forensic_markers.items():
            event_exists = any(event.event_id == event_id for event in self.processed_events)
            if not event_exists:
                orphaned_markers.append(event_id)

        # Remove orphaned markers
        for event_id in orphaned_markers:
            del self.forensic_markers[event_id]
            markers_removed += 1

        return {
            "markers_removed": markers_removed
        }

    async def _get_events_by_date_range(self, start_date: datetime, end_date: datetime) -> List[AuditEvent]:
        """Get events within specified date range"""
        # For this implementation, we'll search the processed events
        # In production, this would query the audit log files
        events = [
            event for event in self.processed_events
            if start_date <= event.timestamp <= end_date
        ]
        return events

    async def _apply_event_filters(self, events: List[AuditEvent], filters: Dict[str, Any]) -> List[AuditEvent]:
        """Apply filters to event list"""
        filtered_events = events

        if "category" in filters:
            category = AuditCategory(filters["category"])
            filtered_events = [e for e in filtered_events if e.category == category]

        if "severity" in filters:
            severity = AuditSeverity(filters["severity"])
            filtered_events = [e for e in filtered_events if e.severity == severity]

        if "actor_id" in filters:
            actor_id = filters["actor_id"]
            filtered_events = [e for e in filtered_events if e.actor_id == actor_id]

        if "outcome" in filters:
            outcome = filters["outcome"]
            filtered_events = [e for e in filtered_events if e.outcome == outcome]

        return filtered_events

    async def _save_compliance_report(self, report_id: str, report_data: Dict[str, Any], format: str) -> Path:
        """Save compliance report to file"""
        reports_dir = Path(self.config.storage_directory) / "compliance_reports"
        reports_dir.mkdir(exist_ok=True)

        file_extension = "json" if format == "json" else "txt"
        file_path = reports_dir / f"{report_id}.{file_extension}"

        async with aiofiles.open(file_path, 'w') as f:
            if format == "json":
                await f.write(json.dumps(report_data, indent=2, default=str))
            else:
                # Format as text report
                text_content = self._format_report_as_text(report_data)
                await f.write(text_content)

        return file_path

    def _format_report_as_text(self, report_data: Dict[str, Any]) -> str:
        """Format report data as readable text"""
        lines = []
        lines.append(f"Compliance Report: {report_data.get('framework', 'Unknown')}")
        lines.append("=" * 50)
        lines.append(f"Period: {report_data.get('period', {}).get('start', 'Unknown')} to {report_data.get('period', {}).get('end', 'Unknown')}")
        lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        lines.append("")

        summary = report_data.get('summary', {})
        if summary:
            lines.append("Summary:")
            for key, value in summary.items():
                lines.append(f"  {key}: {value}")
            lines.append("")

        return '\n'.join(lines)

    async def _flush_loop(self) -> None:
        """Background loop to flush events to storage"""
        while True:
            try:
                await self._flush_events()
                await asyncio.sleep(self.config.flush_interval_seconds)
            except Exception as e:
                logger.error(f"Error in flush loop: {e}")
                await asyncio.sleep(30)

    async def _flush_events(self) -> None:
        """Flush buffered events to storage"""
        if not self.event_buffer:
            return

        events_to_flush = list(self.event_buffer)
        self.event_buffer.clear()

        try:
            for event in events_to_flush:
                await self._write_event_to_file(event)

        except Exception as e:
            logger.error(f"Failed to flush events: {e}")
            # Re-add events to buffer for retry
            self.event_buffer.extendleft(reversed(events_to_flush))

    async def _write_event_to_file(self, event: AuditEvent) -> None:
        """Write event to current audit file"""
        if not self.current_file_path:
            await self._initialize_current_file()

        try:
            # Check if file rotation is needed
            event_size = len(json.dumps(event.to_dict()).encode())
            if self.current_file_size + event_size > (self.config.file_rotation_mb * 1024 * 1024):
                await self._rotate_file()

            # Prepare event data
            event_data = event.to_dict()

            # Encrypt if required
            if self.config.encryption_enabled and (event.requires_encryption or self.config.forensic_mode):
                event_json = json.dumps(event_data)
                if self.encryption_key:
                    encrypted_data = self.encryption_key.encrypt(event_json.encode())
                    event_data = {"encrypted": True, "data": base64.b64encode(encrypted_data).decode()}
                else:
                    logger.warning("Encryption required but no encryption key available")

            # Write to file
            write_mode = 'a'  # Append mode
            open_func = aiofiles.open

            if self.config.compression_enabled:
                # For compressed files, we need special handling
                write_mode = 'ab'  # Binary append for gzipped files

            async with open_func(self.current_file_path, write_mode) as f:
                if self.config.compression_enabled:
                    # Write compressed event
                    event_json = json.dumps(event_data) + '\n'
                    compressed_data = gzip.compress(event_json.encode())
                    await f.write(compressed_data)
                else:
                    # Write uncompressed event
                    await f.write(json.dumps(event_data) + '\n')

            self.current_file_size += event_size

            if self.config.encryption_enabled and event.requires_encryption:
                self.audit_metrics["events_encrypted"] += 1

        except Exception as e:
            logger.error(f"Failed to write event to file: {e}")
            raise

    async def _rotate_file(self) -> None:
        """Rotate audit log file"""
        with self.file_rotation_lock:
            if self.current_file_handle:
                await self.current_file_handle.close()
                self.current_file_handle = None

            await self._initialize_current_file()
            self.audit_metrics["files_created"] += 1

    async def _cleanup_loop(self) -> None:
        """Background cleanup loop"""
        while True:
            try:
                await self._cleanup_expired_events()
                await asyncio.sleep(3600)  # Cleanup every hour
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(300)

    async def _compliance_loop(self) -> None:
        """Background compliance monitoring loop"""
        while True:
            try:
                await self._monitor_compliance()
                await asyncio.sleep(1800)  # Check every 30 minutes
            except Exception as e:
                logger.error(f"Error in compliance loop: {e}")
                await asyncio.sleep(300)

    async def _monitor_compliance(self) -> None:
        """Monitor compliance metrics"""
        current_time = datetime.now(timezone.utc)
        recent_events = [
            event for event in self.processed_events
            if event.timestamp >= current_time - timedelta(hours=24)
        ]

        # Check for compliance issues
        critical_events = [e for e in recent_events if e.severity == AuditSeverity.CRITICAL]
        if critical_events:
            # Publish compliance alert
            if self.event_manager:
                event = Event(
                    type="compliance.alert",
                    source="comprehensive_audit_system",
                    data={
                        "alert_type": "critical_events",
                        "event_count": len(critical_events),
                        "time_window": "24h",
                        "frameworks": list(set.union(*(e.compliance_tags for e in critical_events)))
                    },
                    priority=EventPriority.HIGH
                )
                await self.event_manager.publish_event(event)

    async def _load_forensic_markers(self) -> None:
        """Load existing forensic markers"""
        markers_file = Path(self.config.storage_directory) / "forensic_markers.json"
        if markers_file.exists():
            try:
                async with aiofiles.open(markers_file, 'r') as f:
                    content = await f.read()
                    markers_data = json.loads(content)
                    self.forensic_markers = markers_data
            except Exception as e:
                logger.warning(f"Failed to load forensic markers: {e}")

    async def save_forensic_markers(self) -> None:
        """Save forensic markers to file"""
        markers_file = Path(self.config.storage_directory) / "forensic_markers.json"
        try:
            async with aiofiles.open(markers_file, 'w') as f:
                await f.write(json.dumps(self.forensic_markers, indent=2, default=str))
        except Exception as e:
            logger.error(f"Failed to save forensic markers: {e}")

    def get_audit_metrics(self) -> Dict[str, Any]:
        """Get comprehensive audit system metrics"""
        return {
            "audit_metrics": self.audit_metrics.copy(),
            "event_buffer_size": len(self.event_buffer),
            "processed_events_count": len(self.processed_events),
            "event_chains_count": len(self.event_chains),
            "forensic_markers_count": len(self.forensic_markers),
            "compliance_reports_count": len(self.compliance_reports),
            "category_distribution": dict(self.category_counts),
            "severity_distribution": dict(self.severity_counts),
            "current_file_size_mb": self.current_file_size / (1024 * 1024) if self.current_file_size > 0 else 0,
            "storage_directory": self.config.storage_directory
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the audit system"""
        try:
            # Flush remaining events
            await self._flush_events()

            # Cancel background tasks
            if self.flush_task:
                self.flush_task.cancel()
                try:
                    await self.flush_task
                except asyncio.CancelledError:
                    pass

            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass

            if self.compliance_task:
                self.compliance_task.cancel()
                try:
                    await self.compliance_task
                except asyncio.CancelledError:
                    pass

            # Close current file
            if self.current_file_handle:
                await self.current_file_handle.close()

            # Save forensic markers
            await self.save_forensic_markers()

            # Shutdown event manager
            if self.event_manager:
                await self.event_manager.shutdown()

            logger.info("Comprehensive Audit System shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")