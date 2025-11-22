#!/usr/bin/env python3
"""
MCP-Enhanced Analytics Orchestrator

This enhanced orchestrator integrates Model Context Protocol (MCP) servers
with the existing college football analytics agent system to provide
advanced database operations, data processing, and visualization capabilities.

Key Features:
- MCP server integration and management
- Enhanced data processing capabilities
- Advanced database operations
- Real-time visualization generation
- Improved context management
- Scalable architecture for multiple users
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import importlib.util
from contextlib import asynccontextmanager

# Import existing agent system components
sys.path.append(str(Path(__file__).parent.parent.parent / "agents"))
try:
    from analytics_orchestrator import AnalyticsOrchestrator, AnalyticsRequest
    from model_execution_engine import ModelExecutionEngine
    # ContextManager is deprecated - removed import
except ImportError as e:
    logging.warning(f"Could not import existing agent components: {e}")

class MCPServerType(Enum):
    """MCP server types used in the analytics platform"""
    DATABASE = "database"
    DATA_PROCESSING = "data_processing"
    VISUALIZATION = "visualization"
    WEB_DATA = "web_data"
    SYSTEM = "system"
    EXTERNAL_APIS = "external_apis"

class OperationType(Enum):
    """Analytics operation types"""
    DATA_QUERY = "data_query"
    DATA_PROCESSING = "data_processing"
    VISUALIZATION = "visualization"
    MODEL_EXECUTION = "model_execution"
    WEB_SCRAPING = "web_scraping"
    FILE_OPERATION = "file_operation"

@dataclass
class MCPOperation:
    """Represents an MCP server operation"""
    server_type: MCPServerType
    operation_type: OperationType
    parameters: Dict[str, Any]
    expected_result_type: str
    timeout: int = 30
    retries: int = 3

@dataclass
class MCPServerStatus:
    """Status of an MCP server"""
    name: str
    server_type: MCPServerType
    enabled: bool
    connected: bool
    last_check: str
    response_time: Optional[float] = None
    error_count: int = 0
    total_requests: int = 0

@dataclass
class EnhancedAnalyticsRequest:
    """Enhanced analytics request with MCP capabilities"""
    user_id: str
    request_text: str
    request_type: str
    context: Dict[str, Any]
    parameters: Dict[str, Any]

    # MCP-specific fields
    mcp_operations: List[MCPOperation] = None
    require_database: bool = False
    require_visualization: bool = False
    require_real_time_data: bool = False
    export_format: str = "json"  # json, csv, excel, png
    output_target: str = "response"  # response, file, dashboard

class MCPEnhancedOrchestrator:
    """
    Enhanced orchestrator that integrates MCP servers with the analytics platform

    This orchestrator provides seamless integration between traditional analytics
    operations and advanced MCP server capabilities, enabling:
    - Real-time database queries
    - Advanced data processing
    - Dynamic visualization generation
    - Enhanced model execution
    - Improved user experience
    """

    def __init__(self, config_path: str = None):
        """
        Initialize the MCP-enhanced orchestrator

        Args:
            config_path: Path to MCP configuration file
        """
        self.project_root = Path(__file__).parent.parent.parent
        self.mcp_dir = self.project_root / "mcp_servers"

        # Setup logging
        self.logger = self._setup_logging()

        # Load MCP configuration
        self.config = self._load_mcp_config(config_path)

        # Initialize server connections
        self.server_connections = {}
        self.server_status = {}

        # Initialize traditional components
        self._initialize_traditional_components()

        # Performance metrics
        self.performance_metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "mcp_operations": 0,
            "average_response_time": 0.0,
            "cache_hits": 0
        }

        # Cache for frequently accessed data
        self.cache = {}

        self.logger.info("MCP-Enhanced Orchestrator initialized successfully")

    def _setup_logging(self) -> logging.Logger:
        """Setup enhanced logging with MCP-specific tracking"""
        log_dir = self.mcp_dir / "logs"
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - MCP-Orchestrator - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "orchestrator.log"),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)

    def _load_mcp_config(self, config_path: str = None) -> Dict:
        """Load MCP server configuration"""
        if config_path is None:
            config_path = self.mcp_dir / "config" / "mcp_config.json"

        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Loaded MCP configuration from {config_path}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load MCP configuration: {e}")
            return {"mcpServers": {}, "global_settings": {}}

    def _initialize_traditional_components(self):
        """Initialize traditional analytics components"""
        try:
            # Initialize context manager
            context_config = {
                "token_reduction_target": 0.4,
                "cache_duration": 3600,
                "enable_mcp_optimization": True
            }
            # ContextManager is deprecated - removed initialization
            self.context_manager = None

            # Initialize model execution engine
            self.model_engine = ModelExecutionEngine()

            # Initialize traditional orchestrator if available
            self.traditional_orchestrator = AnalyticsOrchestrator()

            self.logger.info("Traditional components initialized successfully")

        except Exception as e:
            self.logger.warning(f"Could not initialize traditional components: {e}")
            self.context_manager = None
            self.model_engine = None
            self.traditional_orchestrator = None

    async def initialize_mcp_servers(self) -> bool:
        """Initialize connections to all enabled MCP servers"""
        self.logger.info("Initializing MCP server connections...")

        success_count = 0
        total_count = 0

        for category, servers in self.config["mcpServers"].items():
            if isinstance(servers, dict):
                for server_name, server_config in servers.items():
                    if isinstance(server_config, dict) and server_config.get("enabled", False):
                        total_count += 1
                        server_id = f"{category}_{server_name}"

                        if await self._connect_to_server(server_id, server_config):
                            success_count += 1

        self.logger.info(f"Connected to {success_count}/{total_count} MCP servers")
        return success_count > 0

    async def _connect_to_server(self, server_id: str, server_config: Dict) -> bool:
        """Connect to a specific MCP server"""
        try:
            # In a real implementation, this would establish actual MCP connections
            # For now, we simulate successful connections
            server_type = self._get_server_type(server_id)

            self.server_connections[server_id] = {
                "config": server_config,
                "connected": True,
                "last_heartbeat": asyncio.get_event_loop().time()
            }

            self.server_status[server_id] = MCPServerStatus(
                name=server_config.get("command", ""),
                server_type=server_type,
                enabled=server_config.get("enabled", False),
                connected=True,
                last_check=str(asyncio.get_event_loop().time())
            )

            self.logger.info(f"Connected to MCP server: {server_id}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to MCP server {server_id}: {e}")
            self.server_status[server_id] = MCPServerStatus(
                name=server_id,
                server_type=server_type,
                enabled=False,
                connected=False,
                last_check=str(asyncio.get_event_loop().time())
            )
            return False

    def _get_server_type(self, server_id: str) -> MCPServerType:
        """Determine server type from server ID"""
        for server_type in MCPServerType:
            if server_type.value in server_id:
                return server_type
        return MCPServerType.SYSTEM

    async def process_enhanced_analytics_request(
        self,
        request: EnhancedAnalyticsRequest
    ) -> Dict[str, Any]:
        """
        Process an enhanced analytics request using MCP servers

        Args:
            request: Enhanced analytics request with MCP operations

        Returns:
            Dictionary containing the response data and metadata
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info(f"Processing enhanced request for user {request.user_id}")
            self.performance_metrics["total_requests"] += 1

            # ContextManager is deprecated - use request context directly
            optimized_context = request.context

            # Process MCP operations
            mcp_results = {}
            if request.mcp_operations:
                mcp_results = await self._execute_mcp_operations(request.mcp_operations)

            # Execute traditional analytics
            traditional_results = {}
            if self.traditional_orchestrator:
                # Convert to traditional request format
                trad_request = AnalyticsRequest(
                    user_id=request.user_id,
                    request_text=request.request_text,
                    request_type=request.request_type,
                    context=optimized_context,
                    parameters=request.parameters
                )
                traditional_results = self.traditional_orchestrator.process_analytics_request(trad_request)

            # Generate visualizations if requested
            visualizations = {}
            if request.require_visualization:
                visualizations = await self._generate_visualizations(request, mcp_results)

            # Export results in requested format
            exported_data = await self._export_results(
                request, mcp_results, traditional_results, visualizations
            )

            # Calculate response time
            response_time = asyncio.get_event_loop().time() - start_time
            self._update_performance_metrics(response_time, True)

            return {
                "success": True,
                "data": {
                    "traditional_results": traditional_results,
                    "mcp_results": mcp_results,
                    "visualizations": visualizations,
                    "exported_data": exported_data
                },
                "metadata": {
                    "response_time": response_time,
                    "servers_used": list(mcp_results.keys()),
                    "cache_hit": self._check_cache_hit(request)
                }
            }

        except Exception as e:
            self.logger.error(f"Error processing enhanced request: {e}")
            self._update_performance_metrics(0, False)

            return {
                "success": False,
                "error": str(e),
                "metadata": {
                    "response_time": asyncio.get_event_loop().time() - start_time
                }
            }

    async def _optimize_context_with_mcp(
        self,
        request: EnhancedAnalyticsRequest
    ) -> Dict[str, Any]:
        """Optimize request context using MCP capabilities"""
        optimized_context = request.context.copy()

        try:
            # Use database MCP to add relevant data context
            if request.require_database:
                relevant_data = await self._get_relevant_database_context(request)
                optimized_context["database_context"] = relevant_data

            # Use data processing MCP to optimize parameters
            if request.parameters:
                optimized_params = await self._optimize_parameters_with_mcp(request.parameters)
                optimized_context["optimized_parameters"] = optimized_params

            return optimized_context

        except Exception as e:
            self.logger.warning(f"Context optimization failed: {e}")
            return optimized_context

    async def _execute_mcp_operations(
        self,
        operations: List[MCPOperation]
    ) -> Dict[str, Any]:
        """Execute a list of MCP operations"""
        results = {}

        for operation in operations:
            try:
                server_id = self._find_server_for_operation(operation)
                if server_id and server_id in self.server_connections:
                    result = await self._execute_mcp_operation(server_id, operation)
                    results[f"{operation.server_type.value}_{operation.operation_type.value}"] = result
                    self.performance_metrics["mcp_operations"] += 1

            except Exception as e:
                self.logger.error(f"MCP operation failed: {e}")
                results[f"{operation.server_type.value}_{operation.operation_type.value}"] = {
                    "error": str(e),
                    "success": False
                }

        return results

    async def _execute_mcp_operation(
        self,
        server_id: str,
        operation: MCPOperation
    ) -> Dict[str, Any]:
        """Execute a single MCP operation on a server"""
        try:
            # Simulate MCP operation execution
            # In a real implementation, this would use actual MCP protocol

            await asyncio.sleep(0.1)  # Simulate network latency

            # Update server status
            if server_id in self.server_status:
                self.server_status[server_id].total_requests += 1

            # Return mock result based on operation type
            if operation.operation_type == OperationType.DATA_QUERY:
                return {
                    "success": True,
                    "data": self._generate_mock_query_result(operation),
                    "row_count": 100,
                    "execution_time": 0.05
                }
            elif operation.operation_type == OperationType.DATA_PROCESSING:
                return {
                    "success": True,
                    "processed_rows": 1000,
                    "features_created": 5,
                    "execution_time": 0.15
                }
            elif operation.operation_type == OperationType.VISUALIZATION:
                return {
                    "success": True,
                    "chart_url": f"/charts/{operation.operation_type.value}_{id(operation)}.png",
                    "chart_type": "bar",
                    "execution_time": 0.08
                }
            else:
                return {"success": True, "message": "Operation completed successfully"}

        except Exception as e:
            if server_id in self.server_status:
                self.server_status[server_id].error_count += 1
            raise e

    def _generate_mock_query_result(self, operation: MCPOperation) -> List[Dict]:
        """Generate mock query results for demonstration"""
        # This would be replaced with actual database queries
        return [
            {"team": "Ohio State", "wins": 10, "losses": 2, "points_scored": 450},
            {"team": "Michigan", "wins": 9, "losses": 3, "points_scored": 380},
            {"team": "Penn State", "wins": 8, "losses": 4, "points_scored": 340}
        ]

    async def _generate_visualizations(
        self,
        request: EnhancedAnalyticsRequest,
        mcp_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate visualizations based on request and MCP results"""
        visualizations = {}

        try:
            # Generate team performance chart
            if "database_data_query" in mcp_results:
                visualizations["team_performance"] = await self._create_team_chart(
                    mcp_results["database_data_query"]["data"]
                )

            # Generate trend analysis
            if request.require_real_time_data:
                visualizations["trend_analysis"] = await self._create_trend_chart(
                    mcp_results
                )

        except Exception as e:
            self.logger.error(f"Visualization generation failed: {e}")

        return visualizations

    async def _export_results(
        self,
        request: EnhancedAnalyticsRequest,
        mcp_results: Dict[str, Any],
        traditional_results: Dict[str, Any],
        visualizations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Export results in the requested format"""
        try:
            all_data = {
                "mcp_results": mcp_results,
                "traditional_results": traditional_results,
                "visualizations": visualizations
            }

            if request.export_format == "json":
                return {"format": "json", "data": all_data}
            elif request.export_format == "csv":
                return await self._export_to_csv(all_data)
            elif request.export_format == "excel":
                return await self._export_to_excel(all_data)
            else:
                return {"format": "json", "data": all_data}

        except Exception as e:
            self.logger.error(f"Export failed: {e}")
            return {"format": "json", "data": all_data}

    def _find_server_for_operation(self, operation: MCPOperation) -> Optional[str]:
        """Find the appropriate MCP server for an operation"""
        for server_id, connection in self.server_connections.items():
            if operation.server_type.value in server_id:
                return server_id
        return None

    def _update_performance_metrics(self, response_time: float, success: bool):
        """Update performance tracking metrics"""
        if success:
            self.performance_metrics["successful_requests"] += 1

        # Update average response time
        total_requests = self.performance_metrics["total_requests"]
        current_avg = self.performance_metrics["average_response_time"]
        self.performance_metrics["average_response_time"] = (
            (current_avg * (total_requests - 1) + response_time) / total_requests
        )

    def _check_cache_hit(self, request: EnhancedAnalyticsRequest) -> bool:
        """Check if request was served from cache"""
        # Simple cache key based on request text and parameters
        cache_key = f"{request.request_text}_{hash(str(request.parameters))}"

        if cache_key in self.cache:
            self.performance_metrics["cache_hits"] += 1
            return True

        return False

    async def get_server_status(self) -> Dict[str, MCPServerStatus]:
        """Get status of all MCP servers"""
        # Update last check time for all servers
        current_time = str(asyncio.get_event_loop().time())
        for status in self.server_status.values():
            status.last_check = current_time

        return self.server_status

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get orchestrator performance metrics"""
        return {
            **self.performance_metrics,
            "success_rate": (
                self.performance_metrics["successful_requests"] /
                max(self.performance_metrics["total_requests"], 1)
            ),
            "cache_hit_rate": (
                self.performance_metrics["cache_hits"] /
                max(self.performance_metrics["total_requests"], 1)
            )
        }

    async def shutdown(self):
        """Gracefully shutdown the orchestrator and all MCP connections"""
        self.logger.info("Shutting down MCP-enhanced orchestrator...")

        # Close all server connections
        for server_id, connection in self.server_connections.items():
            try:
                connection["connected"] = False
                if server_id in self.server_status:
                    self.server_status[server_id].connected = False
            except Exception as e:
                self.logger.error(f"Error closing connection to {server_id}: {e}")

        self.logger.info("MCP-enhanced orchestrator shutdown complete")

# Utility functions for creating enhanced requests
def create_enhanced_request(
    user_id: str,
    request_text: str,
    request_type: str = "analysis",
    context: Dict[str, Any] = None,
    parameters: Dict[str, Any] = None,
    **kwargs
) -> EnhancedAnalyticsRequest:
    """Create an EnhancedAnalyticsRequest with sensible defaults"""
    return EnhancedAnalyticsRequest(
        user_id=user_id,
        request_text=request_text,
        request_type=request_type,
        context=context or {},
        parameters=parameters or {},
        **kwargs
    )

def add_mcp_database_operation(request: EnhancedAnalyticsRequest, query: str):
    """Add a database operation to an enhanced request"""
    if request.mcp_operations is None:
        request.mcp_operations = []

    request.mcp_operations.append(MCPOperation(
        server_type=MCPServerType.DATABASE,
        operation_type=OperationType.DATA_QUERY,
        parameters={"query": query},
        expected_result_type="dataframe"
    ))
    request.require_database = True

def add_mcp_visualization_operation(
    request: EnhancedAnalyticsRequest,
    chart_type: str,
    data_source: str
):
    """Add a visualization operation to an enhanced request"""
    if request.mcp_operations is None:
        request.mcp_operations = []

    request.mcp_operations.append(MCPOperation(
        server_type=MCPServerType.VISUALIZATION,
        operation_type=OperationType.VISUALIZATION,
        parameters={"chart_type": chart_type, "data_source": data_source},
        expected_result_type="chart"
    ))
    request.require_visualization = True

# Example usage and testing
if __name__ == "__main__":
    async def main():
        """Example usage of the MCP-enhanced orchestrator"""
        # Initialize orchestrator
        orchestrator = MCPEnhancedOrchestrator()

        try:
            # Initialize MCP servers
            await orchestrator.initialize_mcp_servers()

            # Create an enhanced request
            request = create_enhanced_request(
                user_id="demo_user",
                request_text="Show me the top 10 teams by points scored this season",
                request_type="team_analysis",
                require_visualization=True,
                export_format="json"
            )

            # Add database operation
            add_mcp_database_operation(
                request,
                "SELECT team_name, SUM(points_scored) as total_points FROM games WHERE season = 2025 GROUP BY team_name ORDER BY total_points DESC LIMIT 10"
            )

            # Add visualization operation
            add_mcp_visualization_operation(request, "bar", "team_points")

            # Process the request
            result = await orchestrator.process_enhanced_analytics_request(request)

            print("Request processed successfully!")
            print(f"Response time: {result['metadata']['response_time']:.2f}s")
            print(f"Used servers: {result['metadata']['servers_used']}")

            # Get performance metrics
            metrics = await orchestrator.get_performance_metrics()
            print(f"Success rate: {metrics['success_rate']:.2%}")

        finally:
            await orchestrator.shutdown()

    # Run example
    asyncio.run(main())