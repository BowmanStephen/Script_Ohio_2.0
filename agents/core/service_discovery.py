"""
Service discovery for containerized agents
"""
import json
import asyncio
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
import redis.asyncio as redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ServiceInfo:
    agent_id: str
    agent_type: str
    host: str
    port: int
    capabilities: List[str]
    status: str = "active"
    last_heartbeat: Optional[datetime] = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "host": self.host,
            "port": self.port,
            "capabilities": self.capabilities,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "metadata": self.metadata,
            "version": self.version
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ServiceInfo':
        return cls(
            agent_id=data["agent_id"],
            agent_type=data["agent_type"],
            host=data["host"],
            port=data["port"],
            capabilities=data["capabilities"],
            status=data.get("status", "active"),
            last_heartbeat=datetime.fromisoformat(data["last_heartbeat"]),
            metadata=data.get("metadata", {}),
            version=data.get("version", "1.0.0")
        )

    def is_healthy(self, timeout_seconds: int = 60) -> bool:
        """Check if service is healthy based on last heartbeat"""
        if self.status != "active":
            return False
        if not self.last_heartbeat:
            return False
        return (datetime.now(timezone.utc) - self.last_heartbeat).total_seconds() < timeout_seconds

class ServiceDiscovery:
    def __init__(self, redis_url: str, heartbeat_interval: int = 30):
        self.redis_url = redis_url
        self.heartbeat_interval = heartbeat_interval
        self.redis: Optional[redis.Redis] = None
        self.services_key = "services"
        self.agent_capabilities_key = "agent_capabilities"
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.registered_services: Dict[str, ServiceInfo] = {}

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info("Connected to Redis for service discovery")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Disconnect and cleanup"""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass

        # Deregister all services
        for agent_id in list(self.registered_services.keys()):
            await self.deregister_service(agent_id)

        if self.redis:
            await self.redis.close()
        logger.info("Disconnected from service discovery")

    async def register_service(self, service: ServiceInfo) -> bool:
        """Register a service with the discovery system"""
        try:
            # Store service information
            await self.redis.hset(
                self.services_key,
                service.agent_id,
                json.dumps(service.to_dict())
            )

            # Update capabilities index
            for capability in service.capabilities:
                await self.redis.sadd(
                    f"{self.agent_capabilities_key}:{capability}",
                    service.agent_id
                )

            # Store locally for heartbeat
            self.registered_services[service.agent_id] = service

            # Set expiration for service (2x heartbeat interval)
            await self.redis.expire(
                self.services_key,
                self.heartbeat_interval * 2
            )

            # Start heartbeat task if not running
            if not self.heartbeat_task or self.heartbeat_task.done():
                self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())

            logger.info(f"Registered service: {service.agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to register service {service.agent_id}: {e}")
            return False

    async def update_service(self, service: ServiceInfo) -> bool:
        """Update an existing service"""
        try:
            # Get old service to update capabilities
            old_service = await self.get_service(service.agent_id)
            if old_service:
                # Remove old capabilities
                for capability in old_service.capabilities:
                    await self.redis.srem(
                        f"{self.agent_capabilities_key}:{capability}",
                        service.agent_id
                    )

            # Update service
            await self.register_service(service)
            return True
        except Exception as e:
            logger.error(f"Failed to update service {service.agent_id}: {e}")
            return False

    async def deregister_service(self, agent_id: str) -> bool:
        """Deregister a service"""
        try:
            # Get service info before removing
            service = await self.get_service(agent_id)
            if service:
                # Remove from capabilities
                for capability in service.capabilities:
                    await self.redis.srem(
                        f"{self.agent_capabilities_key}:{capability}",
                        agent_id
                    )

            # Remove from services
            await self.redis.hdel(self.services_key, agent_id)

            # Remove from local registry
            if agent_id in self.registered_services:
                del self.registered_services[agent_id]

            logger.info(f"Deregistered service: {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to deregister service {agent_id}: {e}")
            return False

    async def get_service(self, agent_id: str) -> Optional[ServiceInfo]:
        """Get a specific service by ID"""
        try:
            service_data = await self.redis.hget(self.services_key, agent_id)
            if service_data:
                return ServiceInfo.from_dict(json.loads(service_data))
            return None
        except Exception as e:
            logger.error(f"Failed to get service {agent_id}: {e}")
            return None

    async def discover_services(self, agent_type: Optional[str] = None,
                               status: str = "active") -> List[ServiceInfo]:
        """Discover services, optionally filtered by type and status"""
        try:
            services = await self.redis.hgetall(self.services_key)
            result = []

            for service_data in services.values():
                service = ServiceInfo.from_dict(json.loads(service_data))
                if agent_type is None or service.agent_type == agent_type:
                    if status is None or service.status == status:
                        if service.is_healthy():
                            result.append(service)

            return result
        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            return []

    async def find_agents_by_capability(self, capability: str,
                                      status: str = "active") -> List[ServiceInfo]:
        """Find agents with a specific capability"""
        try:
            agent_ids = await self.redis.smembers(f"{self.agent_capabilities_key}:{capability}")
            services = []

            for agent_id in agent_ids:
                service = await self.get_service(agent_id)
                if service and (status is None or service.status == status):
                    if service.is_healthy():
                        services.append(service)

            return services
        except Exception as e:
            logger.error(f"Failed to find agents by capability {capability}: {e}")
            return []

    async def get_all_capabilities(self) -> Set[str]:
        """Get all available capabilities"""
        try:
            keys = await self.redis.keys(f"{self.agent_capabilities_key}:*")
            capabilities = set()
            for key in keys:
                capability = key.decode('utf-8').split(':')[-1]
                capabilities.add(capability)
            return capabilities
        except Exception as e:
            logger.error(f"Failed to get all capabilities: {e}")
            return set()

    async def get_service_count(self) -> Dict[str, int]:
        """Get count of services by type"""
        try:
            services = await self.redis.hgetall(self.services_key)
            counts = {}

            for service_data in services.values():
                service = ServiceInfo.from_dict(json.loads(service_data))
                if service.is_healthy():
                    counts[service.agent_type] = counts.get(service.agent_type, 0) + 1

            return counts
        except Exception as e:
            logger.error(f"Failed to get service count: {e}")
            return {}

    async def _heartbeat_loop(self):
        """Periodic heartbeat for registered services"""
        while self.registered_services:
            try:
                for agent_id, service in list(self.registered_services.items()):
                    # Update heartbeat
                    service.last_heartbeat = datetime.now(timezone.utc)
                    await self.redis.hset(
                        self.services_key,
                        agent_id,
                        json.dumps(service.to_dict())
                    )

                    # Set expiration
                    await self.redis.expire(
                        self.services_key,
                        self.heartbeat_interval * 2
                    )

                await asyncio.sleep(self.heartbeat_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")
                await asyncio.sleep(5)

    async def cleanup_stale_services(self, timeout_seconds: int = 120):
        """Clean up services that haven't sent heartbeat"""
        try:
            services = await self.redis.hgetall(self.services_key)
            now = datetime.now(timezone.utc)

            for agent_id, service_data in services.items():
                agent_id = agent_id.decode('utf-8')
                service = ServiceInfo.from_dict(json.loads(service_data))

                if not service.is_healthy(timeout_seconds):
                    logger.info(f"Cleaning up stale service: {agent_id}")
                    await self.deregister_service(agent_id)

        except Exception as e:
            logger.error(f"Failed to cleanup stale services: {e}")

    async def get_service_health(self) -> Dict[str, any]:
        """Get overall health of services"""
        try:
            all_services = await self.redis.hgetall(self.services_key)
            total = len(all_services)
            active = 0
            by_type = {}

            for service_data in all_services.values():
                service = ServiceInfo.from_dict(json.loads(service_data))
                agent_type = service.agent_type
                by_type[agent_type] = by_type.get(agent_type, {"total": 0, "active": 0})
                by_type[agent_type]["total"] += 1

                if service.is_healthy():
                    active += 1
                    by_type[agent_type]["active"] += 1

            return {
                "total_services": total,
                "active_services": active,
                "health_percentage": (active / total * 100) if total > 0 else 0,
                "by_type": by_type,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get service health: {e}")
            return {}

# Example usage in an agent
class ServiceAwareAgent:
    def __init__(self, agent_id: str, redis_url: str):
        self.agent_id = agent_id
        self.service_discovery = ServiceDiscovery(redis_url)

    async def initialize(self, host: str, port: int, capabilities: List[str]):
        """Initialize agent with service discovery"""
        await self.service_discovery.connect()

        # Register this service
        service_info = ServiceInfo(
            agent_id=self.agent_id,
            agent_type=self.__class__.__name__.replace("Agent", "").lower(),
            host=host,
            port=port,
            capabilities=capabilities,
            metadata={"container": "docker", "version": "2.0"}
        )
        await self.service_discovery.register_service(service_info)

    async def find_agent_for_task(self, required_capability: str) -> Optional[ServiceInfo]:
        """Find an agent that can handle a specific task"""
        agents = await self.service_discovery.find_agents_by_capability(required_capability)
        if agents:
            # Return the first healthy agent (could implement load balancing here)
            return agents[0]
        return None

    async def list_all_agents(self) -> List[ServiceInfo]:
        """List all active agents"""
        return await self.service_discovery.discover_services()

    async def get_agents_by_type(self, agent_type: str) -> List[ServiceInfo]:
        """Get agents of a specific type"""
        return await self.service_discovery.discover_services(agent_type=agent_type)

    async def shutdown(self):
        """Cleanup and disconnect"""
        await self.service_discovery.disconnect()