#!/usr/bin/env python3
"""
Streaming Integration Configuration - Central Configuration for Event-Driven Architecture
Connects all data pipeline components with proper configuration and orchestration
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .event_stream_manager import EventStreamManager, EventPriority
from .enhanced_agent_framework import EnhancedBaseAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamingIntegrationConfig:
    """
    Central configuration for event-driven streaming architecture
    Manages initialization, connections, and coordination between components
    """

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config = self._load_configuration()
        self.components = {}
        self.event_manager: Optional[EventStreamManager] = None

    def _load_configuration(self) -> Dict[str, Any]:
        """Load streaming configuration from file or use defaults"""
        default_config = {
            "event_stream": {
                "backend": "memory",  # memory, redis, kafka, rabbitmq
                "buffer_size": 10000,
                "max_workers": 10,
                "redis": {
                    "host": "localhost",
                    "port": 6379,
                    "db": 0,
                    "password": None
                },
                "kafka": {
                    "bootstrap_servers": ["localhost:9092"],
                    "topics": {
                        "events": "cfbd_pipeline_events",
                        "alerts": "cfbd_pipeline_alerts",
                        "metrics": "cfbd_pipeline_metrics"
                    }
                },
                "rabbitmq": {
                    "url": "amqp://guest:guest@localhost:5672/",
                    "exchange": "cfbd_pipeline",
                    "queues": {
                        "events": "cfbd_events",
                        "alerts": "cfbd_alerts",
                        "metrics": "cfbd_metrics"
                    }
                }
            },
            "data_pipeline": {
                "pipeline_configs": {
                    "cfbd_data_processing": {
                        "stages": ["ingestion", "validation", "transformation", "enrichment", "distribution", "archival"],
                        "source_systems": ["cfbd_api", "cache_system"],
                        "target_consumers": ["model_execution", "bowl_analysis", "quality_assurance"],
                        "batch_size": 100,
                        "retry_policy": {
                            "max_retries": 3,
                            "backoff_factor": 2,
                            "timeout_seconds": 300
                        }
                    },
                    "realtime_game_updates": {
                        "stages": ["ingestion", "validation", "distribution"],
                        "source_systems": ["cfbd_websocket", "scoreboard_api"],
                        "target_consumers": ["dashboard", "alert_system", "prediction_updates"],
                        "batch_size": 10,
                        "retry_policy": {
                            "max_retries": 2,
                            "backoff_factor": 1.5,
                            "timeout_seconds": 60
                        }
                    }
                }
            },
            "monitoring": {
                "metrics_collection_interval": 30,
                "alert_evaluation_interval": 60,
                "health_assessment_interval": 300,
                "performance_windows": {
                    "1m": 60,
                    "5m": 300,
                    "15m": 900,
                    "1h": 3600,
                    "24h": 86400
                },
                "alert_thresholds": {
                    "pipeline_throughput": {"warning": 50, "critical": 20},
                    "error_rate": {"warning": 5, "critical": 15},
                    "data_quality_score": {"warning": 0.7, "critical": 0.5},
                    "agent_response_time": {"warning": 5000, "critical": 10000},
                    "end_to_end_latency": {"warning": 60, "critical": 120}
                }
            },
            "agents": {
                "data_pipeline_orchestrator": {
                    "class": "DataPipelineOrchestrator",
                    "permissions": "READ_EXECUTE_WRITE",
                    "capabilities": [
                        "coordinate_pipeline_execution",
                        "manage_data_flow",
                        "monitor_pipeline_health",
                        "handle_pipeline_events"
                    ]
                },
                "data_flow_monitor": {
                    "class": "DataFlowMonitor",
                    "permissions": "READ_ONLY",
                    "capabilities": [
                        "monitor_pipeline_performance",
                        "track_data_quality",
                        "manage_alerts",
                        "generate_health_report"
                    ]
                },
                "cfbd_integration_agent": {
                    "class": "CFBDIntegrationAgent",
                    "permissions": "READ_EXECUTE",
                    "capabilities": [
                        "fetch_cfbd_data",
                        "manage_api_ratelimits",
                        "handle_data_caching"
                    ]
                },
                "data_validation_agent": {
                    "class": "DataValidationAgent",
                    "permissions": "READ_EXECUTE",
                    "capabilities": [
                        "validate_data_schema",
                        "assess_data_quality",
                        "detect_anomalies"
                    ]
                }
            },
            "security": {
                "encryption_enabled": True,
                "audit_logging": True,
                "rate_limiting": {
                    "enabled": True,
                    "default_limit": 1000,  # requests per hour
                    "burst_limit": 100
                },
                "permissions": {
                    "hierarchy": ["READ_ONLY", "READ_EXECUTE", "READ_EXECUTE_WRITE", "ADMIN"],
                    "default": "READ_ONLY"
                }
            }
        }

        if self.config_path and Path(self.config_path).exists():
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                # Merge with defaults
                default_config.update(file_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}, using defaults")

        return default_config

    async def initialize_components(self) -> Dict[str, Any]:
        """Initialize all streaming components"""
        try:
            # Initialize event stream manager
            event_config = self.config["event_stream"]
            self.event_manager = EventStreamManager(event_config)
            await self.event_manager.initialize()
            self.components["event_manager"] = self.event_manager

            # Initialize data pipeline orchestrator
            from ..data.data_pipeline_orchestrator import DataPipelineOrchestrator
            pipeline_orchestrator = DataPipelineOrchestrator()
            pipeline_config = {
                "event_stream": event_config,
                "pipeline_configs": self.config["data_pipeline"]["pipeline_configs"]
            }
            pipeline_result = await pipeline_orchestrator.initialize(pipeline_config)
            if pipeline_result["status"] == "success":
                self.components["data_pipeline_orchestrator"] = pipeline_orchestrator

            # Initialize data flow monitor
            from ..monitoring.data_flow_monitor import DataFlowMonitor
            data_monitor = DataFlowMonitor()
            monitor_config = {
                "event_stream": event_config,
                "monitoring": self.config["monitoring"]
            }
            monitor_result = await data_monitor.initialize(monitor_config)
            if monitor_result["status"] == "success":
                self.components["data_flow_monitor"] = data_monitor

            logger.info("All streaming components initialized successfully")

            return {
                "status": "success",
                "components_initialized": list(self.components.keys()),
                "event_backend": event_config["backend"],
                "pipeline_configs": len(self.config["data_pipeline"]["pipeline_configs"]),
                "monitoring_enabled": True
            }

        except Exception as e:
            logger.error(f"Failed to initialize streaming components: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__
            }

    def get_agent_config(self, agent_id: str) -> Dict[str, Any]:
        """Get configuration for a specific agent"""
        agents_config = self.config.get("agents", {})
        agent_config = agents_config.get(agent_id, {})

        # Add common configuration
        agent_config.update({
            "event_stream": self.config["event_stream"],
            "security": self.config["security"],
            "monitoring": self.config["monitoring"]
        })

        return agent_config

    def get_pipeline_config(self, pipeline_name: str) -> Dict[str, Any]:
        """Get configuration for a specific pipeline"""
        pipeline_configs = self.config["data_pipeline"]["pipeline_configs"]
        return pipeline_configs.get(pipeline_name, {})

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration"""
        def deep_update(base_dict: Dict, update_dict: Dict) -> None:
            for key, value in update_dict.items():
                if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                    deep_update(base_dict[key], value)
                else:
                    base_dict[key] = value

        deep_update(self.config, updates)

    def save_config(self, path: Optional[str] = None) -> None:
        """Save current configuration to file"""
        save_path = path or self.config_path or "streaming_config.json"
        try:
            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
            logger.info(f"Configuration saved to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    async def shutdown(self) -> None:
        """Gracefully shutdown all components"""
        try:
            # Shutdown event manager
            if self.event_manager:
                await self.event_manager.shutdown()

            # Shutdown other components
            for component_name, component in self.components.items():
                if component_name != "event_manager" and hasattr(component, 'shutdown'):
                    try:
                        if asyncio.iscoroutinefunction(component.shutdown):
                            await component.shutdown()
                        else:
                            component.shutdown()
                    except Exception as e:
                        logger.error(f"Error shutting down {component_name}: {e}")

            logger.info("All streaming components shutdown complete")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status"""
        status = {
            "event_manager_initialized": self.event_manager is not None,
            "components_active": list(self.components.keys()),
            "event_backend": self.config["event_stream"]["backend"],
            "config_timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Add component-specific status
        for component_name, component in self.components.items():
            if hasattr(component, 'get_metrics'):
                try:
                    if asyncio.iscoroutinefunction(component.get_metrics):
                        # For async methods, we'll just note they're available
                        status[f"{component_name}_metrics_available"] = True
                    else:
                        status[f"{component_name}_metrics"] = component.get_metrics()
                except Exception as e:
                    status[f"{component_name}_status"] = f"Error getting metrics: {e}"

        return status

# Global configuration instance
streaming_config = StreamingIntegrationConfig()

async def initialize_streaming_system(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Initialize the complete streaming system"""
    global streaming_config

    if config_path:
        streaming_config = StreamingIntegrationConfig(config_path)

    return await streaming_config.initialize_components()

def get_streaming_config() -> StreamingIntegrationConfig:
    """Get the global streaming configuration instance"""
    return streaming_config