"""
Prometheus metrics collection for containerized agents
"""
import time
import psutil
import asyncio
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentMetrics:
    def __init__(self, agent_id: str, agent_type: str, metrics_port: int = 8090):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.metrics_port = metrics_port

        # Metrics definitions
        self.request_total = Counter(
            'agent_requests_total',
            'Total number of requests processed',
            ['agent_id', 'agent_type', 'method', 'status']
        )

        self.request_duration = Histogram(
            'agent_request_duration_seconds',
            'Request processing duration in seconds',
            ['agent_id', 'agent_type', 'method'],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        )

        self.active_connections = Gauge(
            'agent_active_connections',
            'Number of active connections',
            ['agent_id', 'agent_type']
        )

        self.memory_usage_bytes = Gauge(
            'agent_memory_usage_bytes',
            'Memory usage in bytes',
            ['agent_id', 'agent_type']
        )

        self.memory_usage_percent = Gauge(
            'agent_memory_usage_percent',
            'Memory usage percentage',
            ['agent_id', 'agent_type']
        )

        self.cpu_usage_percent = Gauge(
            'agent_cpu_usage_percent',
            'CPU usage percentage',
            ['agent_id', 'agent_type']
        )

        self.agent_health = Gauge(
            'agent_health_status',
            'Agent health status (1=healthy, 0=unhealthy)',
            ['agent_id', 'agent_type']
        )

        self.message_count = Counter(
            'agent_messages_total',
            'Total number of messages sent/received',
            ['agent_id', 'agent_type', 'direction', 'message_type']
        )

        self.error_count = Counter(
            'agent_errors_total',
            'Total number of errors',
            ['agent_id', 'agent_type', 'error_type']
        )

        self.task_duration = Histogram(
            'agent_task_duration_seconds',
            'Task execution duration in seconds',
            ['agent_id', 'agent_type', 'task_type'],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0]
        )

        self.last_activity = Gauge(
            'agent_last_activity_timestamp',
            'Timestamp of last activity',
            ['agent_id', 'agent_type']
        )

        # Initialize metrics
        self._initialize_metrics()

    def _initialize_metrics(self):
        """Initialize metric values"""
        self.agent_health.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type
        ).set(1)  # Assume healthy at start

        self.active_connections.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type
        ).set(0)

        self.last_activity.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type
        ).set(time.time())

    def start_metrics_server(self) -> bool:
        """Start Prometheus metrics HTTP server"""
        try:
            start_http_server(self.metrics_port)
            logger.info(f"Metrics server started on port {self.metrics_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            return False

    def record_request(self, method: str, status: str, duration: float):
        """Record a request metric"""
        self.request_total.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            method=method,
            status=status
        ).inc()

        self.request_duration.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            method=method
        ).observe(duration)

        # Update last activity
        self.update_activity()

    def record_message(self, direction: str, message_type: str, count: int = 1):
        """Record message metrics"""
        self.message_count.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            direction=direction,  # 'sent' or 'received'
            message_type=message_type
        ).inc(count)

        # Update last activity
        self.update_activity()

    def record_error(self, error_type: str, count: int = 1):
        """Record error metrics"""
        self.error_count.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            error_type=error_type
        ).inc(count)

    def record_task(self, task_type: str, duration: float):
        """Record task execution metric"""
        self.task_duration.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            task_type=task_type
        ).observe(duration)

        # Update last activity
        self.update_activity()

    def update_system_metrics(self):
        """Update system metrics (CPU, memory, connections)"""
        try:
            process = psutil.Process()

            # Memory usage in bytes
            memory_info = process.memory_info()
            self.memory_usage_bytes.labels(
                agent_id=self.agent_id,
                agent_type=self.agent_type
            ).set(memory_info.rss)

            # Memory usage percentage
            memory_percent = process.memory_percent()
            self.memory_usage_percent.labels(
                agent_id=self.agent_id,
                agent_type=self.agent_type
            ).set(memory_percent)

            # CPU usage percentage
            cpu_percent = process.cpu_percent()
            self.cpu_usage_percent.labels(
                agent_id=self.agent_id,
                agent_type=self.agent_type
            ).set(cpu_percent)

        except Exception as e:
            logger.error(f"Failed to update system metrics: {e}")
            self.record_error("metrics_collection_error")

    def update_health_status(self, healthy: bool):
        """Update health status"""
        value = 1 if healthy else 0
        self.agent_health.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type
        ).set(value)

        # Log health status change
        status_str = "healthy" if healthy else "unhealthy"
        logger.info(f"Agent {self.agent_id} health status: {status_str}")

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type
        ).set(time.time())

    def increment_active_connections(self):
        """Increment active connections count"""
        label = self.active_connections.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type
        )
        label.set(label._value.get() + 1)

    def decrement_active_connections(self):
        """Decrement active connections count"""
        label = self.active_connections.labels(
            agent_id=self.agent_id,
            agent_type=self.agent_type
        )
        current_value = label._value.get()
        if current_value > 0:
            label.set(current_value - 1)

    async def start_metrics_collection(self, interval: int = 15):
        """Start periodic metrics collection"""
        logger.info(f"Starting metrics collection with {interval}s interval")

        while True:
            try:
                self.update_system_metrics()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics collection: {e}")
                await asyncio.sleep(5)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of current metrics"""
        try:
            return {
                "agent_id": self.agent_id,
                "agent_type": self.agent_type,
                "health": 1 if self.agent_health._value.get() == 1 else 0,
                "active_connections": self.active_connections._value.get(),
                "memory_bytes": self.memory_usage_bytes._value.get(),
                "memory_percent": self.memory_usage_percent._value.get(),
                "cpu_percent": self.cpu_usage_percent._value.get(),
                "last_activity": datetime.fromtimestamp(self.last_activity._value.get()).isoformat(),
                "requests_total": self.request_total._value.get(),
                "messages_total": self.message_count._value.get(),
                "errors_total": self.error_count._value.get()
            }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}

# Metrics decorator for functions
def track_execution_time(metrics: AgentMetrics, task_type: str):
    """Decorator to track function execution time"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_task(task_type, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_task(task_type, duration)
                metrics.record_error(f"{task_type}_error")
                raise

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_task(task_type, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_task(task_type, duration)
                metrics.record_error(f"{task_type}_error")
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

# Example integration in an agent
class MetricsEnabledAgent:
    def __init__(self, agent_id: str, agent_type: str, metrics_port: int = 8090):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.metrics = AgentMetrics(agent_id, agent_type, metrics_port)

    async def initialize(self):
        """Initialize agent with metrics collection"""
        # Start metrics server
        if not self.metrics.start_metrics_server():
            logger.error("Failed to start metrics server")

        # Start periodic metrics collection
        asyncio.create_task(self.metrics.start_metrics_collection())

        # Update initial health status
        self.metrics.update_health_status(True)

        # Log initialization
        logger.info(f"Agent {self.agent_id} initialized with metrics on port {self.metrics.metrics_port}")

    @track_execution_time(None, "process_request")
    async def handle_request(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle request with metrics tracking"""
        start_time = time.time()

        try:
            # Process request
            result = await self._process_request(method, payload)

            # Record successful request
            duration = time.time() - start_time
            self.metrics.record_request(method, "success", duration)

            return result

        except Exception as e:
            # Record failed request
            duration = time.time() - start_time
            self.metrics.record_request(method, "error", duration)
            self.metrics.record_error("request_error")

            # Update health status if too many errors
            if self.metrics.error_count._value.get() > 10:
                self.metrics.update_health_status(False)

            raise

    async def send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]):
        """Send message with metrics tracking"""
        try:
            # Send message logic here
            await self._send_message(recipient, message_type, payload)

            # Record sent message
            self.metrics.record_message("sent", message_type)

        except Exception as e:
            self.metrics.record_error("message_send_error")
            raise

    def receive_message(self, sender: str, message_type: str, payload: Dict[str, Any]):
        """Receive message with metrics tracking"""
        # Record received message
        self.metrics.record_message("received", message_type)

        # Process message logic here
        self._process_message(sender, message_type, payload)

    async def _process_request(self, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Override in subclass"""
        return {"method": method, "payload": payload}

    async def _send_message(self, recipient: str, message_type: str, payload: Dict[str, Any]):
        """Override in subclass"""
        pass

    def _process_message(self, sender: str, message_type: str, payload: Dict[str, Any]):
        """Override in subclass"""
        pass

    def shutdown(self):
        """Shutdown agent and update metrics"""
        self.metrics.update_health_status(False)
        logger.info(f"Agent {self.agent_id} shutdown")