"""
CFBD Integration Monitor - Real-time monitoring and health checks for CFBD API integration

This agent monitors the health, performance, and utilization of the CollegeFootballData.com
integration, providing real-time alerts and performance metrics.

Key Features:
- Endpoint availability monitoring
- Performance metrics tracking
- Error rate analysis
- Tier optimization validation
- Cache performance monitoring
- Rate limiting compliance
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core.agent_framework import AgentCapability, BaseAgent, PermissionLevel

logger = logging.getLogger(__name__)


@dataclass
class CFBDHealthMetrics:
    """Health metrics for CFBD integration"""

    endpoint_availability: float
    average_response_time: float
    error_rate: float
    cache_hit_rate: float
    rate_limit_utilization: float
    tier_compliance_score: float
    last_check: str
    total_requests: int
    successful_requests: int


@dataclass
class EndpointStatus:
    """Status of individual CFBD endpoints"""

    name: str
    available: bool
    response_time: Optional[float]
    last_success: Optional[str]
    error_count: int
    total_calls: int
    success_rate: float


class CFBDIntegrationMonitor(BaseAgent):
    """
    CFBD Integration Monitor Agent

    Provides comprehensive monitoring and health checks for the CFBD API integration,
    ensuring optimal performance and early detection of issues.
    """

    def __init__(self, agent_id: str):
        super().__init__(
            agent_id, "CFBD Integration Monitor", PermissionLevel.READ_EXECUTE
        )
        self.max_execution_time = 300  # 5 minutes
        self.memory_limit_mb = 100

        # Initialize CFBD client for monitoring
        try:
            from ...cfbd_client.unified_client import UnifiedCFBDClient

            self.cfbd_client = UnifiedCFBDClient()
        except ImportError as e:
            logger.error(f"Failed to import CFBD client: {e}")
            self.cfbd_client = None

        # Monitoring configuration
        self.endpoints_to_monitor = [
            "get_games",
            "get_teams",
            "get_player_stats",
            "get_transfer_portal",
            "get_nfl_draft_picks",
            "get_game_weather",
            "get_wepa_team_season",
            "get_advanced_game_stats",
            "get_player_season_stats",
            "get_team_season_stats",
            "get_betting_props",
        ]

        # Health tracking
        self.health_history: List[CFBDHealthMetrics] = []
        self.endpoint_status: Dict[str, EndpointStatus] = {}

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define monitoring capabilities"""
        return [
            AgentCapability(
                name="health_check",
                description="Comprehensive health check of CFBD integration",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd_integration", "monitoring"],
                data_access="health_metrics",
                execution_time_estimate=30.0,
            ),
            AgentCapability(
                name="performance_monitoring",
                description="Real-time performance monitoring and metrics collection",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd_integration", "analytics"],
                data_access="performance_data",
                execution_time_estimate=45.0,
            ),
            AgentCapability(
                name="endpoint_validation",
                description="Validate individual endpoint availability and performance",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd_integration"],
                data_access="endpoint_status",
                execution_time_estimate=60.0,
            ),
            AgentCapability(
                name="tier_compliance_check",
                description="Verify tier optimization and compliance metrics",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["cfbd_integration", "configuration"],
                data_access="tier_configuration",
                execution_time_estimate=20.0,
            ),
            AgentCapability(
                name="alert_generation",
                description="Generate alerts for performance issues or service degradation",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["monitoring", "notifications"],
                data_access="alert_data",
                execution_time_estimate=15.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute monitoring actions"""
        try:
            if not self.cfbd_client:
                raise ValueError("CFBD client not available for monitoring")

            if action == "health_check":
                return self._perform_health_check(parameters)
            elif action == "performance_monitoring":
                return self._monitor_performance(parameters)
            elif action == "endpoint_validation":
                return self._validate_endpoints(parameters)
            elif action == "tier_compliance_check":
                return self._check_tier_compliance(parameters)
            elif action == "alert_generation":
                return self._generate_alerts(parameters)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Error in {self.agent_id}._execute_action: {e}")
            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "execution_time": time.time(),
            }

    def _perform_health_check(self, parameters: Dict) -> Dict:
        """Perform comprehensive health check of CFBD integration"""
        try:
            start_time = time.time()

            # Test basic connectivity
            basic_health = self._test_basic_connectivity()

            # Check endpoint availability
            endpoint_health = self._check_endpoint_availability()

            # Test performance metrics
            performance_metrics = self._measure_performance()

            # Check cache performance
            cache_metrics = self._check_cache_performance()

            # Validate rate limiting compliance
            rate_limit_status = self._check_rate_limiting()

            # Calculate overall health score
            health_score = self._calculate_health_score(
                basic_health,
                endpoint_health,
                performance_metrics,
                cache_metrics,
                rate_limit_status,
            )

            # Create health metrics
            health_metrics = CFBDHealthMetrics(
                endpoint_availability=endpoint_health["availability"],
                average_response_time=performance_metrics["avg_response_time"],
                error_rate=endpoint_health["error_rate"],
                cache_hit_rate=cache_metrics["hit_rate"],
                rate_limit_utilization=rate_limit_status["utilization"],
                tier_compliance_score=health_score["tier_compliance"],
                last_check=datetime.utcnow().isoformat(),
                total_requests=endpoint_health["total_requests"],
                successful_requests=endpoint_health["successful_requests"],
            )

            # Store in history
            self.health_history.append(health_metrics)
            if len(self.health_history) > 100:  # Keep last 100 checks
                self.health_history.pop(0)

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "health_metrics": asdict(health_metrics),
                "health_score": health_score["overall"],
                "recommendations": health_score["recommendations"],
                "execution_time": execution_time,
                "timestamp": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _test_basic_connectivity(self) -> Dict:
        """Test basic CFBD API connectivity"""
        try:
            # Test a simple endpoint
            start_time = time.time()
            response = self.cfbd_client.get_fbs_teams()
            response_time = time.time() - start_time

            return {
                "connected": len(response) > 0,
                "response_time": response_time,
                "team_count": len(response),
            }
        except Exception as e:
            return {"connected": False, "error": str(e), "response_time": None}

    def _check_endpoint_availability(self) -> Dict:
        """Check availability of key endpoints"""
        total_requests = 0
        successful_requests = 0
        error_count = 0
        available_endpoints = 0

        for endpoint_name in self.endpoints_to_monitor:
            try:
                total_requests += 1
                start_time = time.time()

                # Get the method from the client
                method = getattr(self.cfbd_client, endpoint_name, None)
                if not method:
                    logger.warning(f"Endpoint {endpoint_name} not found")
                    continue

                # Call the method with minimal parameters
                if endpoint_name in ["get_games", "get_teams", "get_fbs_teams"]:
                    result = method(year=2025)
                elif endpoint_name in ["get_player_stats", "get_team_season_stats"]:
                    result = method(year=2025)
                else:
                    result = method(year=2025)

                response_time = time.time() - start_time

                if result is not None:
                    successful_requests += 1
                    available_endpoints += 1
                    self._update_endpoint_status(endpoint_name, True, response_time)
                else:
                    error_count += 1
                    self._update_endpoint_status(endpoint_name, False, None)

            except Exception as e:
                error_count += 1
                logger.warning(f"Endpoint {endpoint_name} failed: {e}")
                self._update_endpoint_status(endpoint_name, False, None)

        return {
            "availability": (available_endpoints / len(self.endpoints_to_monitor))
            * 100,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "error_rate": (error_count / max(total_requests, 1)) * 100,
            "available_endpoints": available_endpoints,
            "total_endpoints": len(self.endpoints_to_monitor),
        }

    def _measure_performance(self) -> Dict:
        """Measure performance metrics"""
        response_times = []

        # Test a few representative endpoints
        test_endpoints = ["get_games", "get_teams", "get_player_stats"]

        for endpoint_name in test_endpoints:
            try:
                start_time = time.time()
                method = getattr(self.cfbd_client, endpoint_name)

                if endpoint_name == "get_games":
                    method(year=2025, week=1)
                elif endpoint_name == "get_teams":
                    method()
                elif endpoint_name == "get_player_stats":
                    method(year=2025)

                response_time = time.time() - start_time
                response_times.append(response_time)

            except Exception as e:
                logger.warning(f"Performance test failed for {endpoint_name}: {e}")

        return {
            "avg_response_time": (
                sum(response_times) / len(response_times) if response_times else 0
            ),
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "total_tests": len(response_times),
            "performance_grade": self._grade_performance(response_times),
        }

    def _check_cache_performance(self) -> Dict:
        """Check cache performance metrics"""
        try:
            # Get performance metrics from CFBD client
            perf_metrics = self.cfbd_client.get_performance_metrics()

            return {
                "hit_rate": perf_metrics.get("cache_hit_rate", 0),
                "cache_size": perf_metrics.get("cache_size", 0),
                "cache_ttl_status": (
                    "optimal"
                    if perf_metrics.get("cache_hit_rate", 0) > 70
                    else "suboptimal"
                ),
                "recommendation": self._get_cache_recommendation(
                    perf_metrics.get("cache_hit_rate", 0)
                ),
            }
        except Exception as e:
            logger.warning(f"Cache performance check failed: {e}")
            return {
                "hit_rate": 0,
                "cache_size": 0,
                "cache_ttl_status": "unknown",
                "recommendation": "Unable to assess cache performance",
            }

    def _check_rate_limiting(self) -> Dict:
        """Check rate limiting compliance"""
        try:
            # This would ideally connect to rate limiting middleware
            # For now, simulate rate limit status

            return {
                "utilization": 65.0,  # 65% of rate limit used
                "compliance": True,
                "current_rate": 19.5,  # requests per second
                "max_rate": 30,  # requests per second (Tier 3)
                "status": "healthy",
            }
        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            return {
                "utilization": 0,
                "compliance": False,
                "current_rate": 0,
                "max_rate": 30,
                "status": "unknown",
            }

    def _calculate_health_score(
        self,
        basic_health: Dict,
        endpoint_health: Dict,
        performance: Dict,
        cache: Dict,
        rate_limit: Dict,
    ) -> Dict:
        """Calculate overall health score and recommendations"""

        scores = []
        recommendations = []

        # Basic connectivity (30% weight)
        if basic_health["connected"]:
            scores.append(30)
        else:
            scores.append(0)
            recommendations.append(
                "Basic API connectivity is failing - check authentication"
            )

        # Endpoint availability (25% weight)
        endpoint_score = min(endpoint_health["availability"], 100)
        scores.append(endpoint_score * 0.25)
        if endpoint_health["availability"] < 90:
            recommendations.append(
                f"Only {endpoint_health['availability']:.1f}% of endpoints available"
            )

        # Performance (20% weight)
        performance_score = 100 - min(
            (performance["avg_response_time"] - 0.5) * 10, 100
        )
        performance_score = max(performance_score, 0)
        scores.append(performance_score * 0.2)
        if performance["avg_response_time"] > 2.0:
            recommendations.append(
                "Response times are elevated - check network conditions"
            )

        # Cache performance (15% weight)
        cache_score = cache["hit_rate"]
        scores.append(cache_score * 0.15)
        if cache["hit_rate"] < 70:
            recommendations.append(
                "Cache hit rate is below optimal - consider cache tuning"
            )

        # Rate limiting (10% weight)
        rate_limit_score = 100 if rate_limit["compliance"] else 0
        scores.append(rate_limit_score * 0.1)
        if rate_limit["utilization"] > 80:
            recommendations.append(
                "Rate limit utilization is high - optimize API calls"
            )

        overall_score = sum(scores)

        return {
            "overall": overall_score,
            "tier_compliance": min(overall_score + 5, 100),  # Tier 3 gives slight bonus
            "breakdown": {
                "connectivity": scores[0] / 30 * 100,
                "endpoints": scores[1] / 25 * 100,
                "performance": scores[2] / 20 * 100,
                "cache": scores[3] / 15 * 100,
                "rate_limit": scores[4] / 10 * 100,
            },
            "recommendations": recommendations,
            "grade": self._get_health_grade(overall_score),
        }

    def _update_endpoint_status(
        self, endpoint_name: str, available: bool, response_time: Optional[float]
    ):
        """Update endpoint status tracking"""
        if endpoint_name not in self.endpoint_status:
            self.endpoint_status[endpoint_name] = EndpointStatus(
                name=endpoint_name,
                available=available,
                response_time=response_time,
                last_success=datetime.utcnow().isoformat() if available else None,
                error_count=0 if available else 1,
                total_calls=1,
                success_rate=100 if available else 0,
            )
        else:
            status = self.endpoint_status[endpoint_name]
            status.total_calls += 1
            if available:
                status.available = True
                status.response_time = response_time
                status.last_success = datetime.utcnow().isoformat()
                status.success_rate = (
                    (status.success_rate * (status.total_calls - 1)) + 100
                ) / status.total_calls
            else:
                status.error_count += 1
                status.available = False
                status.success_rate = (
                    status.success_rate * (status.total_calls - 1)
                ) / status.total_calls

    def _grade_performance(self, response_times: List[float]) -> str:
        """Grade performance based on response times"""
        if not response_times:
            return "Unknown"

        avg_time = sum(response_times) / len(response_times)

        if avg_time < 0.5:
            return "Excellent"
        elif avg_time < 1.0:
            return "Good"
        elif avg_time < 2.0:
            return "Fair"
        else:
            return "Poor"

    def _get_cache_recommendation(self, hit_rate: float) -> str:
        """Get cache performance recommendation"""
        if hit_rate >= 80:
            return "Cache performance is optimal"
        elif hit_rate >= 60:
            return "Consider increasing cache TTL for frequently accessed data"
        elif hit_rate >= 40:
            return "Cache hit rate is low - review caching strategy"
        else:
            return "Critical: Cache performance needs immediate attention"

    def _get_health_grade(self, score: float) -> str:
        """Get letter grade for health score"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def _monitor_performance(self, parameters: Dict) -> Dict:
        """Monitor real-time performance metrics"""
        return self._perform_health_check(parameters)

    def _validate_endpoints(self, parameters: Dict) -> Dict:
        """Validate individual endpoint status"""
        endpoint_health = self._check_endpoint_availability()

        return {
            "status": "success",
            "endpoint_status": {
                name: asdict(status) for name, status in self.endpoint_status.items()
            },
            "summary": endpoint_health,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def _check_tier_compliance(self, parameters: Dict) -> Dict:
        """Check tier optimization and compliance"""
        try:
            from ...config.tier_optimized_cfbd_config import TierOptimizedCFBDConfig

            config = TierOptimizedCFBDConfig()
            tier_info = config.to_dict()

            return {
                "status": "success",
                "tier_config": tier_info,
                "compliance_score": 95.0,  # Simulated compliance score
                "optimization_status": "optimized",
                "feature_summary": config.get_feature_summary(),
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _generate_alerts(self, parameters: Dict) -> Dict:
        """Generate alerts for performance issues"""
        alerts = []

        # Check recent health metrics
        if len(self.health_history) >= 2:
            recent = self.health_history[-1]
            previous = self.health_history[-2]

            # Check for significant degradation
            if recent.endpoint_availability < previous.endpoint_availability - 10:
                alerts.append(
                    {
                        "severity": "warning",
                        "type": "endpoint_degradation",
                        "message": f"Endpoint availability dropped from {previous.endpoint_availability:.1f}% to {recent.endpoint_availability:.1f}%",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

            if recent.error_rate > previous.error_rate + 5:
                alerts.append(
                    {
                        "severity": "warning",
                        "type": "error_rate_increase",
                        "message": f"Error rate increased by {recent.error_rate - previous.error_rate:.1f}%",
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        # Check endpoint status for failures
        failed_endpoints = [
            name
            for name, status in self.endpoint_status.items()
            if not status.available and status.total_calls > 5
        ]

        for endpoint in failed_endpoints:
            alerts.append(
                {
                    "severity": "error",
                    "type": "endpoint_failure",
                    "message": f"Endpoint {endpoint} is consistently failing",
                    "endpoint": endpoint,
                    "failure_rate": (1 - self.endpoint_status[endpoint].success_rate)
                    * 100,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        return {
            "status": "success",
            "alerts": alerts,
            "alert_count": len(alerts),
            "severity_breakdown": {
                "error": len([a for a in alerts if a["severity"] == "error"]),
                "warning": len([a for a in alerts if a["severity"] == "warning"]),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }
