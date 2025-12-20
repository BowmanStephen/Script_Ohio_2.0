#!/usr/bin/env python3
"""
Event Stream Manager - Core Event-Driven Streaming Architecture
Implements publish-subscribe patterns, event routing, and stream processing
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
from collections import defaultdict, deque
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import redis.asyncio as redis
from kafka import KafkaProducer, KafkaConsumer
import aio_pika
from .enhanced_agent_framework import EnhancedBaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """Event priority levels for routing"""
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"

class EventStatus(Enum):
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"

@dataclass
class Event:
    """Core event structure for streaming"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: str = ""
    source: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    priority: EventPriority = EventPriority.NORMAL
    status: EventStatus = EventStatus.PENDING
    metadata: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 30
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority.value,
            "status": self.status.value,
            "metadata": self.metadata,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary"""
        event = cls(
            id=data["id"],
            type=data["type"],
            source=data["source"],
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            priority=EventPriority(data["priority"]),
            status=EventStatus(data["status"]),
            metadata=data["metadata"],
            retry_count=data["retry_count"],
            max_retries=data["max_retries"],
            timeout_seconds=data["timeout_seconds"],
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id")
        )
        return event

@dataclass
class EventSubscription:
    """Event subscription configuration"""
    subscriber_id: str
    event_types: Set[str]
    filter_func: Optional[Callable[[Event], bool]] = None
    priority_filter: Optional[Set[EventPriority]] = None
    async_callback: bool = True
    timeout_seconds: int = 30

class EventStreamManager:
    """
    High-performance event stream manager with multiple backends
    Supports Redis, Kafka, RabbitMQ, and in-memory streaming
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_buffer: deque = deque(maxlen=config.get("buffer_size", 10000))
        self.processing_events: Dict[str, Event] = {}
        self.event_stats = defaultdict(int)

        # Backend configurations
        self.backend_type = config.get("backend", "memory")
        self.redis_client = None
        self.kafka_producer = None
        self.kafka_consumer = None
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None

        # Performance monitoring
        self.performance_metrics = {
            "events_published": 0,
            "events_processed": 0,
            "events_failed": 0,
            "average_processing_time": 0.0,
            "buffer_utilization": 0.0
        }

        # Thread pool for synchronous processing
        self.executor = ThreadPoolExecutor(max_workers=config.get("max_workers", 10))

        # Event processing state
        self.is_running = False
        self.background_tasks: List[asyncio.Task] = []

    async def initialize(self) -> None:
        """Initialize the event stream backend"""
        try:
            if self.backend_type == "redis":
                await self._initialize_redis()
            elif self.backend_type == "kafka":
                await self._initialize_kafka()
            elif self.backend_type == "rabbitmq":
                await self._initialize_rabbitmq()
            elif self.backend_type == "memory":
                logger.info("Using in-memory event streaming")
            else:
                raise ValueError(f"Unsupported backend: {self.backend_type}")

            self.is_running = True
            logger.info(f"Event stream manager initialized with {self.backend_type} backend")

        except Exception as e:
            logger.error(f"Failed to initialize event stream manager: {e}")
            raise

    async def _initialize_redis(self) -> None:
        """Initialize Redis backend"""
        try:
            self.redis_client = redis.Redis(
                host=self.config.get("redis_host", "localhost"),
                port=self.config.get("redis_port", 6379),
                db=self.config.get("redis_db", 0),
                password=self.config.get("redis_password"),
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Redis backend initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    async def _initialize_kafka(self) -> None:
        """Initialize Kafka backend"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=self.config.get("kafka_bootstrap_servers", ["localhost:9092"]),
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                acks='all',
                retries=3
            )
            logger.info("Kafka backend initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka: {e}")
            raise

    async def _initialize_rabbitmq(self) -> None:
        """Initialize RabbitMQ backend"""
        try:
            connection_string = self.config.get("rabbitmq_url", "amqp://guest:guest@localhost:5672/")
            self.rabbitmq_connection = await aio_pika.connect_robust(connection_string)
            self.rabbitmq_channel = await self.rabbitmq_connection.channel()
            await self.rabbitmq_channel.set_qos(prefetch_count=100)
            logger.info("RabbitMQ backend initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RabbitMQ: {e}")
            raise

    async def publish_event(self, event: Event) -> bool:
        """
        Publish an event to the stream

        Args:
            event: Event to publish

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Add to buffer for local processing
            self.event_buffer.append(event)
            self.event_stats[f"published_{event.type}"] += 1
            self.performance_metrics["events_published"] += 1

            # Publish to backend
            if self.backend_type == "redis":
                await self._publish_to_redis(event)
            elif self.backend_type == "kafka":
                await self._publish_to_kafka(event)
            elif self.backend_type == "rabbitmq":
                await self._publish_to_rabbitmq(event)

            # Trigger immediate processing for high-priority events
            if event.priority in [EventPriority.CRITICAL, EventPriority.HIGH]:
                await self._process_event_immediately(event)

            logger.debug(f"Published event {event.id} of type {event.type}")
            return True

        except Exception as e:
            logger.error(f"Failed to publish event {event.id}: {e}")
            self.performance_metrics["events_failed"] += 1
            return False

    async def _publish_to_redis(self, event: Event) -> None:
        """Publish event to Redis stream"""
        if not self.redis_client:
            return

        stream_key = f"events:{event.type}"
        await self.redis_client.xadd(
            stream_key,
            event.to_dict(),
            maxlen=10000
        )

    async def _publish_to_kafka(self, event: Event) -> None:
        """Publish event to Kafka topic"""
        if not self.kafka_producer:
            return

        topic = f"events.{event.type}"
        future = self.kafka_producer.send(topic, event.to_dict())
        # Ensure message is sent
        record_metadata = future.get(timeout=10)

    async def _publish_to_rabbitmq(self, event: Event) -> None:
        """Publish event to RabbitMQ exchange"""
        if not self.rabbitmq_channel:
            return

        exchange_name = "events"
        routing_key = event.type

        await self.rabbitmq_channel.default_exchange.publish(
            aio_pika.Message(
                json.dumps(event.to_dict(), default=str).encode(),
                content_type="application/json",
                priority=self._get_rabbitmq_priority(event.priority)
            ),
            routing_key=routing_key
        )

    def _get_rabbitmq_priority(self, priority: EventPriority) -> int:
        """Convert EventPriority to RabbitMQ priority (0-9)"""
        priority_map = {
            EventPriority.CRITICAL: 9,
            EventPriority.HIGH: 7,
            EventPriority.NORMAL: 5,
            EventPriority.LOW: 1
        }
        return priority_map.get(priority, 5)

    async def subscribe_to_events(
        self,
        subscription: EventSubscription
    ) -> bool:
        """
        Subscribe to specific event types

        Args:
            subscription: Event subscription configuration

        Returns:
            True if subscribed successfully, False otherwise
        """
        try:
            self.subscriptions[subscription.subscriber_id] = subscription

            # Start background consumer task
            if subscription.async_callback:
                task = asyncio.create_task(
                    self._event_consumer_loop(subscription)
                )
                self.background_tasks.append(task)

            logger.info(f"Subscriber {subscription.subscriber_id} subscribed to {subscription.event_types}")
            return True

        except Exception as e:
            logger.error(f"Failed to subscribe {subscription.subscriber_id}: {e}")
            return False

    async def _event_consumer_loop(self, subscription: EventSubscription) -> None:
        """Background loop for consuming events"""
        while self.is_running:
            try:
                event = await self._get_next_event(subscription)
                if event:
                    await self._process_event(event, subscription)
                else:
                    await asyncio.sleep(0.1)  # Small delay when no events

            except Exception as e:
                logger.error(f"Error in consumer loop for {subscription.subscriber_id}: {e}")
                await asyncio.sleep(1)

    async def _get_next_event(self, subscription: EventSubscription) -> Optional[Event]:
        """Get next event matching subscription criteria"""
        # Check buffer first
        for event in list(self.event_buffer):
            if self._event_matches_subscription(event, subscription):
                self.event_buffer.remove(event)
                return event

        # Check backend for more events
        if self.backend_type == "redis":
            return await self._get_from_redis(subscription)
        elif self.backend_type == "kafka":
            return await self._get_from_kafka(subscription)
        elif self.backend_type == "rabbitmq":
            return await self._get_from_rabbitmq(subscription)

        return None

    def _event_matches_subscription(self, event: Event, subscription: EventSubscription) -> bool:
        """Check if event matches subscription criteria"""
        # Check event type
        if event.type not in subscription.event_types:
            return False

        # Check priority filter
        if subscription.priority_filter and event.priority not in subscription.priority_filter:
            return False

        # Check custom filter function
        if subscription.filter_func and not subscription.filter_func(event):
            return False

        return True

    async def _process_event(self, event: Event, subscription: EventSubscription) -> None:
        """Process an event for a subscription"""
        try:
            event.status = EventStatus.PROCESSING
            self.processing_events[event.id] = event

            start_time = time.time()

            # Call the subscriber callback
            if hasattr(self, f"_callback_{subscription.subscriber_id}"):
                callback = getattr(self, f"_callback_{subscription.subscriber_id}")
                if subscription.async_callback:
                    await callback(event)
                else:
                    await asyncio.get_event_loop().run_in_executor(
                        self.executor, callback, event
                    )

            # Update metrics
            processing_time = time.time() - start_time
            self._update_processing_metrics(processing_time)

            event.status = EventStatus.COMPLETED
            self.event_stats[f"processed_{event.type}"] += 1
            self.performance_metrics["events_processed"] += 1

            logger.debug(f"Processed event {event.id} for {subscription.subscriber_id}")

        except Exception as e:
            logger.error(f"Failed to process event {event.id}: {e}")
            event.status = EventStatus.FAILED
            self.performance_metrics["events_failed"] += 1

            # Schedule retry if max retries not reached
            if event.retry_count < event.max_retries:
                event.retry_count += 1
                event.status = EventStatus.RETRY
                await asyncio.sleep(min(2 ** event.retry_count, 30))  # Exponential backoff
                await self.publish_event(event)  # Re-publish for retry

        finally:
            # Remove from processing events
            if event.id in self.processing_events:
                del self.processing_events[event.id]

    async def _process_event_immediately(self, event: Event) -> None:
        """Immediately process high-priority events"""
        for subscription in self.subscriptions.values():
            if self._event_matches_subscription(event, subscription):
                asyncio.create_task(self._process_event(event, subscription))

    def _update_processing_metrics(self, processing_time: float) -> None:
        """Update performance metrics"""
        total_events = self.performance_metrics["events_processed"]
        if total_events == 0:
            self.performance_metrics["average_processing_time"] = processing_time
        else:
            # Moving average
            current_avg = self.performance_metrics["average_processing_time"]
            self.performance_metrics["average_processing_time"] = (
                (current_avg * (total_events - 1) + processing_time) / total_events
            )

        # Update buffer utilization
        self.performance_metrics["buffer_utilization"] = (
            len(self.event_buffer) / self.event_buffer.maxlen
        )

    async def create_event_stream(
        self,
        stream_name: str,
        event_types: List[str],
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a named event stream for complex workflows

        Args:
            stream_name: Name of the stream
            event_types: Event types to include
            filters: Optional filtering criteria

        Returns:
            Stream ID for reference
        """
        stream_id = f"stream_{stream_name}_{uuid.uuid4().hex[:8]}"

        # Create stream-specific subscription
        subscription = EventSubscription(
            subscriber_id=stream_id,
            event_types=set(event_types),
            filter_func=self._create_stream_filter(filters) if filters else None
        )

        await self.subscribe_to_events(subscription)

        logger.info(f"Created event stream {stream_id} for types {event_types}")
        return stream_id

    def _create_stream_filter(self, filters: Dict[str, Any]) -> Callable[[Event], bool]:
        """Create filter function from filter criteria"""
        def filter_func(event: Event) -> bool:
            for key, value in filters.items():
                if key == "priority" and event.priority.value != value:
                    return False
                elif key == "source" and event.source != value:
                    return False
                elif key in event.metadata and event.metadata[key] != value:
                    return False
                elif key in event.data and event.data[key] != value:
                    return False
            return True
        return filter_func

    async def get_event_history(
        self,
        event_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Event]:
        """
        Get event history with filtering options

        Args:
            event_type: Filter by event type
            source: Filter by source
            limit: Maximum number of events to return
            start_time: Filter start time
            end_time: Filter end time

        Returns:
            List of matching events
        """
        events = []

        # Search buffer first
        for event in self.event_buffer:
            if self._event_matches_filter(event, event_type, source, start_time, end_time):
                events.append(event)

        # Search backend for more events
        if len(events) < limit:
            backend_events = await self._get_events_from_backend(
                event_type, source, limit - len(events), start_time, end_time
            )
            events.extend(backend_events)

        return events[:limit]

    def _event_matches_filter(
        self,
        event: Event,
        event_type: Optional[str],
        source: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> bool:
        """Check if event matches filter criteria"""
        if event_type and event.type != event_type:
            return False
        if source and event.source != source:
            return False
        if start_time and event.timestamp < start_time:
            return False
        if end_time and event.timestamp > end_time:
            return False
        return True

    async def _get_events_from_backend(
        self,
        event_type: Optional[str],
        source: Optional[str],
        limit: int,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[Event]:
        """Get events from backend storage"""
        # Implementation would depend on backend-specific queries
        # For now, return empty list
        return []

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        return {
            "performance_metrics": self.performance_metrics.copy(),
            "event_stats": dict(self.event_stats),
            "subscription_count": len(self.subscriptions),
            "processing_events": len(self.processing_events),
            "buffer_size": len(self.event_buffer),
            "buffer_capacity": self.event_buffer.maxlen,
            "is_running": self.is_running
        }

    async def shutdown(self) -> None:
        """Gracefully shutdown the event stream manager"""
        try:
            self.is_running = False

            # Cancel background tasks
            for task in self.background_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            # Close backend connections
            if self.redis_client:
                await self.redis_client.close()

            if self.kafka_producer:
                self.kafka_producer.close()

            if self.rabbitmq_connection:
                await self.rabbitmq_connection.close()

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

            logger.info("Event stream manager shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def __del__(self):
        """Cleanup on deletion"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)