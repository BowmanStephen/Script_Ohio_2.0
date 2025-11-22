"""
Secure Inter-Agent Communication Framework
Provides encrypted messaging, authentication, and routing for agent communication
"""

import json
import time
import uuid
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class MessagePriority(Enum):
    CRITICAL = 1      # System alerts, emergency shutdown
    HIGH = 2         # User requests, important tasks
    MEDIUM = 3       # Routine operations, analytics
    LOW = 4          # Background processing, maintenance

class MessageType(Enum):
    TASK_ASSIGNMENT = "task_assignment"
    STATUS_UPDATE = "status_update"
    RESULT = "result"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    DISCOVERY = "discovery"
    COORDINATION = "coordination"
    DATA_TRANSFER = "data_transfer"

@dataclass
class AgentMessage:
    """Secure message structure for inter-agent communication"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    receiver_id: str = ""
    message_type: MessageType = MessageType.STATUS_UPDATE
    priority: MessagePriority = MessagePriority.MEDIUM
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    ttl: Optional[int] = None  # Time to live in seconds
    signature: Optional[str] = None
    encryption_key_id: Optional[str] = None
    routing_path: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization"""
        data = asdict(self)
        # Handle datetime serialization
        data['timestamp'] = self.timestamp.isoformat()
        data['message_type'] = self.message_type.value
        data['priority'] = self.priority.value
        if isinstance(self.message_type, MessageType):
            data['message_type'] = self.message_type.value
        if isinstance(self.priority, MessagePriority):
            data['priority'] = self.priority.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        """Create message from dictionary"""
        # Handle datetime deserialization
        if 'timestamp' in data and isinstance(data['timestamp'], str):
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])

        # Handle enum deserialization
        if 'message_type' in data and isinstance(data['message_type'], str):
            data['message_type'] = MessageType(data['message_type'])
        if 'priority' in data and isinstance(data['priority'], str):
            data['priority'] = MessagePriority(data['priority'])
        elif 'priority' in data and isinstance(data['priority'], int):
            # Map int to enum
            priority_map = {1: MessagePriority.CRITICAL, 2: MessagePriority.HIGH,
                          3: MessagePriority.MEDIUM, 4: MessagePriority.LOW}
            data['priority'] = priority_map.get(data['priority'], MessagePriority.MEDIUM)

        return cls(**data)

class SecureMessageHandler:
    """Handles secure message encryption, signing, and validation"""

    def __init__(self, master_password: str = None):
        if master_password is None:
            master_password = os.environ.get('AGENT_MESSAGE_KEY', 'default_secure_key_2025')

        # Generate encryption key from master password
        self.master_password = master_password.encode()
        self.encryption_key = self._derive_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

        # Message store for tracking
        self.message_store: Dict[str, AgentMessage] = {}
        self.agent_keys: Dict[str, str] = {}  # Individual agent keys

        # Message handlers by type
        self.message_handlers: Dict[MessageType, List[Callable]] = {
            MessageType.TASK_ASSIGNMENT: [],
            MessageType.STATUS_UPDATE: [],
            MessageType.RESULT: [],
            MessageType.ERROR: [],
            MessageType.HEARTBEAT: [],
            MessageType.DISCOVERY: [],
            MessageType.COORDINATION: [],
            MessageType.DATA_TRANSFER: []
        }

        self.logger = logging.getLogger("secure_messaging")

    def _derive_encryption_key(self) -> bytes:
        """Derive encryption key from master password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'script_ohio_2025_salt',  # Fixed salt for consistency
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_password))
        return key

    def encrypt_message(self, message: AgentMessage) -> AgentMessage:
        """Encrypt message payload"""
        try:
            # Convert payload to JSON and encrypt
            payload_json = json.dumps(message.payload, default=str)
            encrypted_payload = self.cipher_suite.encrypt(payload_json.encode())

            # Update message with encrypted payload
            message.payload = {"encrypted_data": encrypted_payload.decode()}
            message.encryption_key_id = "default"

            return message
        except Exception as e:
            self.logger.error(f"Error encrypting message: {e}")
            raise

    def decrypt_message(self, message: AgentMessage) -> AgentMessage:
        """Decrypt message payload"""
        try:
            if "encrypted_data" not in message.payload:
                return message  # Not encrypted

            # Decrypt the payload
            encrypted_data = message.payload["encrypted_data"].encode()
            decrypted_json = self.cipher_suite.decrypt(encrypted_data).decode()
            message.payload = json.loads(decrypted_json)

            return message
        except Exception as e:
            self.logger.error(f"Error decrypting message: {e}")
            raise

    def sign_message(self, message: AgentMessage, sender_key: str = None) -> AgentMessage:
        """Sign message with HMAC"""
        try:
            if sender_key is None:
                sender_key = self.agent_keys.get(message.sender_id, self.master_password)

            # Create message signature
            message_data = json.dumps({
                "message_id": message.message_id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "message_type": message.message_type.value,
                "timestamp": message.timestamp.isoformat(),
                "payload_hash": hashlib.sha256(json.dumps(message.payload, default=str).encode()).hexdigest()
            })

            signature = hmac.new(
                sender_key.encode() if isinstance(sender_key, str) else sender_key,
                message_data.encode(),
                hashlib.sha256
            ).hexdigest()

            message.signature = signature
            return message

        except Exception as e:
            self.logger.error(f"Error signing message: {e}")
            raise

    def verify_signature(self, message: AgentMessage) -> bool:
        """Verify message signature"""
        try:
            if message.signature is None:
                return False

            sender_key = self.agent_keys.get(message.sender_id, self.master_password)

            # Recreate signature data
            message_data = json.dumps({
                "message_id": message.message_id,
                "sender_id": message.sender_id,
                "receiver_id": message.receiver_id,
                "message_type": message.message_type.value,
                "timestamp": message.timestamp.isoformat(),
                "payload_hash": hashlib.sha256(json.dumps(message.payload, default=str).encode()).hexdigest()
            })

            expected_signature = hmac.new(
                sender_key.encode() if isinstance(sender_key, str) else sender_key,
                message_data.encode(),
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(message.signature, expected_signature)

        except Exception as e:
            self.logger.error(f"Error verifying signature: {e}")
            return False

    def is_message_expired(self, message: AgentMessage) -> bool:
        """Check if message has expired"""
        if message.ttl is None:
            return False

        expiration_time = message.timestamp + timedelta(seconds=message.ttl)
        return datetime.now() > expiration_time

    def register_agent_key(self, agent_id: str, key: str):
        """Register encryption key for an agent"""
        self.agent_keys[agent_id] = key
        self.logger.info(f"Registered key for agent: {agent_id}")

    def register_handler(self, message_type: MessageType, handler: Callable):
        """Register a handler for specific message type"""
        self.message_handlers[message_type].append(handler)
        self.logger.info(f"Registered handler for message type: {message_type.value}")

class MessageRouter:
    """Routes messages between agents with load balancing and failover"""

    def __init__(self, secure_handler: SecureMessageHandler):
        self.secure_handler = secure_handler
        self.routing_table: Dict[str, List[str]] = {}  # agent_id -> [possible_routes]
        self.active_connections: Dict[str, Dict] = {}  # agent_id -> connection_info
        self.message_queue: Dict[str, List[AgentMessage]] = {}  # agent_id -> queued_messages
        self.delivery_stats: Dict[str, Dict] = {}  # agent_id -> delivery_statistics

        self.logger = logging.getLogger("message_router")

    def register_agent(self, agent_id: str, connection_info: Dict[str, Any]):
        """Register an agent for routing"""
        self.active_connections[agent_id] = {
            **connection_info,
            "registered_at": datetime.now(),
            "last_heartbeat": datetime.now(),
            "status": "active"
        }

        # Initialize message queue for agent
        if agent_id not in self.message_queue:
            self.message_queue[agent_id] = []

        # Initialize delivery stats
        if agent_id not in self.delivery_stats:
            self.delivery_stats[agent_id] = {
                "messages_sent": 0,
                "messages_delivered": 0,
                "messages_failed": 0,
                "average_delivery_time": 0.0
            }

        self.logger.info(f"Registered agent for routing: {agent_id}")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent from routing"""
        if agent_id in self.active_connections:
            self.active_connections[agent_id]["status"] = "inactive"
            self.logger.info(f"Unregistered agent: {agent_id}")

    def send_message(self, message: AgentMessage) -> bool:
        """Send a message to the target agent"""
        try:
            # Verify message is valid
            if not self.secure_handler.verify_signature(message):
                self.logger.warning(f"Message signature verification failed: {message.message_id}")
                return False

            if self.secure_handler.is_message_expired(message):
                self.logger.warning(f"Message expired: {message.message_id}")
                return False

            # Check if receiver is active
            if message.receiver_id not in self.active_connections:
                self.logger.warning(f"Receiver not found: {message.receiver_id}")
                # Queue message for later delivery
                if message.receiver_id not in self.message_queue:
                    self.message_queue[message.receiver_id] = []
                self.message_queue[message.receiver_id].append(message)
                return False

            # Decrypt message for delivery
            decrypted_message = self.secure_handler.decrypt_message(message)

            # Deliver message
            start_time = time.time()
            success = self._deliver_to_agent(decrypted_message)
            delivery_time = time.time() - start_time

            # Update stats
            self._update_delivery_stats(message.sender_id, success, delivery_time)

            if success:
                self.logger.info(f"Message delivered: {message.message_id} to {message.receiver_id}")
            else:
                self.logger.error(f"Message delivery failed: {message.message_id} to {message.receiver_id}")

            return success

        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
            return False

    def _deliver_to_agent(self, message: AgentMessage) -> bool:
        """Deliver message to specific agent (implementation depends on transport)"""
        # This would be implemented based on actual transport mechanism
        # For now, simulate successful delivery
        try:
            # Store message in agent's message store
            self.secure_handler.message_store[message.message_id] = message

            # Route to appropriate handlers
            handlers = self.secure_handler.message_handlers.get(message.message_type, [])
            for handler in handlers:
                try:
                    handler(message)
                except Exception as e:
                    self.logger.error(f"Handler error for message {message.message_id}: {e}")

            return True

        except Exception as e:
            self.logger.error(f"Error delivering message to agent: {e}")
            return False

    def _update_delivery_stats(self, sender_id: str, success: bool, delivery_time: float):
        """Update delivery statistics"""
        if sender_id not in self.delivery_stats:
            self.delivery_stats[sender_id] = {
                "messages_sent": 0,
                "messages_delivered": 0,
                "messages_failed": 0,
                "average_delivery_time": 0.0
            }

        stats = self.delivery_stats[sender_id]
        stats["messages_sent"] += 1

        if success:
            stats["messages_delivered"] += 1
        else:
            stats["messages_failed"] += 1

        # Update average delivery time
        total_delivered = stats["messages_delivered"]
        if total_delivered > 0:
            stats["average_delivery_time"] = (
                (stats["average_delivery_time"] * (total_delivered - 1) + delivery_time) / total_delivered
            )

    def get_queued_messages(self, agent_id: str) -> List[AgentMessage]:
        """Get queued messages for an agent"""
        messages = self.message_queue.get(agent_id, [])
        self.message_queue[agent_id] = []  # Clear queue
        return messages

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an agent"""
        if agent_id not in self.active_connections:
            return None

        connection_info = self.active_connections[agent_id]
        delivery_stats = self.delivery_stats.get(agent_id, {})
        queued_count = len(self.message_queue.get(agent_id, []))

        return {
            "agent_id": agent_id,
            "status": connection_info["status"],
            "registered_at": connection_info["registered_at"].isoformat(),
            "last_heartbeat": connection_info["last_heartbeat"].isoformat(),
            "delivery_stats": delivery_stats,
            "queued_messages": queued_count
        }

    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        active_agents = len([
            agent for agent, info in self.active_connections.items()
            if info["status"] == "active"
        ])

        total_queued = sum(len(queue) for queue in self.message_queue.values())
        total_messages = len(self.secure_handler.message_store)

        return {
            "active_agents": active_agents,
            "total_registered_agents": len(self.active_connections),
            "total_queued_messages": total_queued,
            "total_processed_messages": total_messages,
            "system_uptime": datetime.now().isoformat(),
            "message_handlers": {
                msg_type.value: len(handlers)
                for msg_type, handlers in self.secure_handler.message_handlers.items()
            }
        }

# Global instances
secure_messaging = SecureMessageHandler()
message_router = MessageRouter(secure_messaging)

# Utility functions
def create_message(sender_id: str, receiver_id: str, message_type: MessageType,
                  payload: Dict[str, Any], priority: MessagePriority = MessagePriority.MEDIUM,
                  ttl: int = None) -> AgentMessage:
    """Create and prepare a message for sending"""
    message = AgentMessage(
        sender_id=sender_id,
        receiver_id=receiver_id,
        message_type=message_type,
        priority=priority,
        payload=payload,
        ttl=ttl
    )

    # Sign and encrypt message
    message = secure_messaging.sign_message(message)
    message = secure_messaging.encrypt_message(message)

    return message

def send_message(message: AgentMessage) -> bool:
    """Send a message using the global router"""
    return message_router.send_message(message)

def register_agent(agent_id: str, connection_info: Dict[str, Any] = None):
    """Register an agent with the global router"""
    if connection_info is None:
        connection_info = {
            "endpoint": f"agent://{agent_id}",
            "protocol": "internal",
            "capabilities": []
        }

    message_router.register_agent(agent_id, connection_info)