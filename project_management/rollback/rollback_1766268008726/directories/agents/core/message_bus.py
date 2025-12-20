"""
Redis-based inter-agent communication system for containerized deployment
"""
import json
import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime, timezone
import redis.asyncio as redis
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessagePriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class MessageStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    ACKNOWLEDGED = "acknowledged"

@dataclass
class AgentMessage:
    sender: str
    receiver: str
    message_type: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    correlation_id: Optional[str] = None
    timestamp: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    status: MessageStatus = MessageStatus.PENDING
    reply_to: Optional[str] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.correlation_id is None:
            self.correlation_id = f"{self.sender}-{int(self.timestamp.timestamp())}"
        if self.expires_at is None:
            # Default expiration: 5 minutes
            self.expires_at = self.timestamp.replace(second=0, microsecond=0) + timedelta(minutes=5)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'message_type': self.message_type,
            'payload': self.payload,
            'priority': self.priority.value,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'reply_to': self.reply_to,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentMessage':
        return cls(
            sender=data['sender'],
            receiver=data['receiver'],
            message_type=data['message_type'],
            payload=data['payload'],
            priority=MessagePriority(data['priority']),
            correlation_id=data.get('correlation_id'),
            timestamp=datetime.fromisoformat(data['timestamp']),
            status=MessageStatus(data.get('status', 'pending')),
            reply_to=data.get('reply_to'),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )

    def is_expired(self) -> bool:
        """Check if message has expired"""
        if not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

class MessageBus:
    def __init__(self, redis_url: str, agent_id: str):
        self.redis_url = redis_url
        self.agent_id = agent_id
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self.message_history_key = "message_history"
        self.agent_status_key = "agent_status"
        self.message_queue_key = f"message_queue:{agent_id}"

    async def connect(self):
        """Connect to Redis and initialize pubsub"""
        try:
            self.redis = redis.from_url(self.redis_url)
            # Test connection
            await self.redis.ping()
            self.pubsub = self.redis.pubsub()
            await self.pubsub.subscribe(f"agent:{self.agent_id}")
            await self.pubsub.subscribe("broadcast")  # For system-wide messages
            self.running = True
            logger.info(f"Connected to Redis at {self.redis_url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect from Redis"""
        self.running = False
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
        if self.redis:
            await self.redis.close()
        logger.info("Disconnected from Redis")

    async def send_message(self, message: AgentMessage) -> bool:
        """Send a message to another agent"""
        try:
            # Check if message is expired
            if message.is_expired():
                logger.warning(f"Message {message.correlation_id} expired before sending")
                return False

            # Update status
            message.status = MessageStatus.SENT
            message_data = message.to_dict()

            # Publish to receiver's channel
            await self.redis.publish(
                f"agent:{message.receiver}",
                json.dumps(message_data)
            )

            # Store in message history for debugging
            await self.redis.lpush(
                self.message_history_key,
                json.dumps(message_data)
            )

            # Trim message history to last 1000 messages
            await self.redis.ltrim(self.message_history_key, 0, 999)

            # Store in receiver's queue if they're offline
            await self.redis.lpush(
                self.message_queue_key,
                json.dumps(message_data)
            )

            # Set expiration on queue (24 hours)
            await self.redis.expire(self.message_queue_key, 86400)

            logger.info(f"Sent message {message.correlation_id} to {message.receiver}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            message.status = MessageStatus.FAILED
            return False

    async def send_reply(self, original_message: AgentMessage, reply_payload: Dict[str, Any]) -> bool:
        """Send a reply to a message"""
        reply = AgentMessage(
            sender=self.agent_id,
            receiver=original_message.sender,
            message_type="reply",
            payload=reply_payload,
            priority=original_message.priority,
            correlation_id=original_message.correlation_id,
            reply_to=original_message.correlation_id
        )
        return await self.send_message(reply)

    async def broadcast_message(self, message_type: str, payload: Dict[str, Any],
                              priority: MessagePriority = MessagePriority.NORMAL) -> bool:
        """Broadcast a message to all agents"""
        message = AgentMessage(
            sender=self.agent_id,
            receiver="broadcast",
            message_type=message_type,
            payload=payload,
            priority=priority
        )

        try:
            message_data = message.to_dict()
            await self.redis.publish("broadcast", json.dumps(message_data))
            logger.info(f"Broadcasted {message_type} message")
            return True
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            return False

    async def register_handler(self, message_type: str, handler: Callable):
        """Register a handler for a specific message type"""
        self.handlers[message_type] = handler
        logger.info(f"Registered handler for message type: {message_type}")

    async def unregister_handler(self, message_type: str):
        """Unregister a handler for a specific message type"""
        if message_type in self.handlers:
            del self.handlers[message_type]
            logger.info(f"Unregistered handler for message type: {message_type}")

    async def start_listening(self):
        """Start listening for messages"""
        if not self.running:
            return

        logger.info(f"Starting to listen for messages for agent {self.agent_id}")

        # Process queued messages first
        await self._process_queued_messages()

        while self.running:
            try:
                message = await self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    await self._handle_message(message['data'])
            except Exception as e:
                logger.error(f"Error handling message: {e}")
                await asyncio.sleep(1)

    async def _process_queued_messages(self):
        """Process messages that arrived while agent was offline"""
        try:
            queued = await self.redis.lrange(self.message_queue_key, 0, -1)
            if queued:
                logger.info(f"Processing {len(queued)} queued messages")
                for message_data in queued:
                    await self._handle_message(message_data)
                # Clear queue
                await self.redis.delete(self.message_queue_key)
        except Exception as e:
            logger.error(f"Error processing queued messages: {e}")

    async def _handle_message(self, message_data: Union[bytes, str]):
        """Handle incoming message"""
        try:
            if isinstance(message_data, bytes):
                message_data = message_data.decode('utf-8')

            data = json.loads(message_data)
            message = AgentMessage.from_dict(data)

            # Check if message is expired
            if message.is_expired():
                logger.warning(f"Dropping expired message {message.correlation_id}")
                return

            # Update status
            message.status = MessageStatus.DELIVERED

            # Handle broadcast messages
            if message.receiver == "broadcast":
                await self._handle_broadcast_message(message)
                return

            # Handle direct messages
            if message.receiver == self.agent_id:
                await self._handle_direct_message(message)
            else:
                logger.warning(f"Received message for different agent: {message.receiver}")

        except Exception as e:
            logger.error(f"Error processing message: {e}")

    async def _handle_direct_message(self, message: AgentMessage):
        """Handle direct message to this agent"""
        try:
            # Send acknowledgment
            if message.priority != MessagePriority.LOW:
                await self.send_message(AgentMessage(
                    sender=self.agent_id,
                    receiver=message.sender,
                    message_type="acknowledgment",
                    payload={"correlation_id": message.correlation_id},
                    priority=MessagePriority.LOW,
                    correlation_id=message.correlation_id
                ))

            # Call registered handler
            if message.message_type in self.handlers:
                try:
                    await self.handlers[message.message_type](message)
                    message.status = MessageStatus.ACKNOWLEDGED
                except Exception as e:
                    logger.error(f"Handler error for {message.message_type}: {e}")
                    # Send error reply
                    await self.send_reply(message, {
                        "error": str(e),
                        "correlation_id": message.correlation_id
                    })
            else:
                logger.warning(f"No handler for message type: {message.message_type}")

        except Exception as e:
            logger.error(f"Error handling direct message: {e}")

    async def _handle_broadcast_message(self, message: AgentMessage):
        """Handle broadcast message"""
        try:
            # Only process if we have a handler
            if message.message_type in self.handlers:
                await self.handlers[message.message_type](message)
        except Exception as e:
            logger.error(f"Error handling broadcast message: {e}")

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of another agent"""
        try:
            status_data = await self.redis.hget(self.agent_status_key, agent_id)
            if status_data:
                return json.loads(status_data)
            return None
        except Exception:
            return None

    async def update_agent_status(self, status: Dict[str, Any]):
        """Update this agent's status"""
        try:
            await self.redis.hset(
                self.agent_status_key,
                self.agent_id,
                json.dumps({
                    **status,
                    'last_updated': datetime.now(timezone.utc).isoformat()
                })
            )
            # Set expiration (24 hours)
            await self.redis.expire(self.agent_status_key, 86400)
        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    async def get_message_history(self, limit: int = 100) -> List[AgentMessage]:
        """Get recent message history"""
        try:
            history_data = await self.redis.lrange(self.message_history_key, 0, limit - 1)
            messages = []
            for data in history_data:
                messages.append(AgentMessage.from_dict(json.loads(data)))
            return messages
        except Exception as e:
            logger.error(f"Failed to get message history: {e}")
            return []

    async def clear_message_history(self):
        """Clear message history"""
        try:
            await self.redis.delete(self.message_history_key)
            logger.info("Message history cleared")
        except Exception as e:
            logger.error(f"Failed to clear message history: {e}")

# Example usage in an agent
class ContainerizedAgent:
    def __init__(self, agent_id: str, redis_url: str):
        self.agent_id = agent_id
        self.message_bus = MessageBus(redis_url, agent_id)

    async def initialize(self):
        """Initialize agent with message bus"""
        await self.message_bus.connect()

        # Register message handlers
        await self.message_bus.register_handler("request", self._handle_request)
        await self.message_bus.register_handler("health_check", self._handle_health_check)
        await self.message_bus.register_handler("shutdown", self._handle_shutdown)

        # Update initial status
        await self.message_bus.update_agent_status({
            "status": "active",
            "capabilities": self._get_capabilities()
        })

        # Start listening in background
        asyncio.create_task(self.message_bus.start_listening())

    async def _handle_request(self, message: AgentMessage):
        """Handle incoming request"""
        try:
            # Process request based on payload
            action = message.payload.get("action", "unknown")
            result = await self._process_action(action, message.payload.get("parameters", {}))

            # Send response
            await self.message_bus.send_reply(message, {
                "result": result,
                "status": "success",
                "correlation_id": message.correlation_id
            })
        except Exception as e:
            await self.message_bus.send_reply(message, {
                "error": str(e),
                "status": "error",
                "correlation_id": message.correlation_id
            })

    async def _handle_health_check(self, message: AgentMessage):
        """Handle health check request"""
        await self.message_bus.send_reply(message, {
            "status": "healthy",
            "agent_id": self.agent_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def _handle_shutdown(self, message: AgentMessage):
        """Handle shutdown request"""
        logger.info("Received shutdown request")
        await self.message_bus.update_agent_status({"status": "shutting_down"})
        # Graceful shutdown logic here
        asyncio.create_task(self._shutdown())

    async def _process_action(self, action: str, parameters: Dict[str, Any]) -> Any:
        """Process an action - to be implemented by specific agent"""
        return {"action": action, "parameters": parameters, "processed": True}

    def _get_capabilities(self) -> List[str]:
        """Get agent capabilities - to be implemented by specific agent"""
        return ["process_request"]

    async def _shutdown(self):
        """Graceful shutdown"""
        await asyncio.sleep(1)  # Allow final messages to be sent
        await self.message_bus.disconnect()