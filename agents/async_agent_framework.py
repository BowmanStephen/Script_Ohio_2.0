#!/usr/bin/env python3
"""
DEPRECATED: Asynchronous Agent Framework - High-Performance Async Processing

⚠️  DEPRECATION WARNING (2025-11-19):
This module is DEPRECATED and will be removed in a future version.
It was identified as unused in production code analysis.

AsyncAgentOrchestrator is defined but NEVER used in:
- scripts/generate_comprehensive_week13_analysis.py
- scripts/run_weekly_analysis.py
- Any production code

Weekly scripts are synchronous and work fine without async complexity.

Migration path:
- Use synchronous agent execution (see WeeklyAnalysisOrchestrator)
- If you need async, implement it directly where needed
- See agents/weekly_analysis_orchestrator.py for the pattern actually used

This module will be removed after 2025-12-19 (30-day deprecation period).

Original description:
This module implements asynchronous processing patterns, connection pooling,
and concurrent execution for the Script Ohio 2.0 agent system to achieve
sub-second response times and handle 1000+ concurrent users.
"""
import warnings

warnings.warn(
    "AsyncAgentOrchestrator is deprecated and will be removed after 2025-12-19. "
    "Use synchronous execution pattern from WeeklyAnalysisOrchestrator instead. "
    "See agents/weekly_analysis_orchestrator.py for the recommended pattern.",
    DeprecationWarning,
    stacklevel=2
)

Author: Claude Code Assistant (Performance Tuning Agent)
Created: 2025-11-10
Version: 1.0
"""

import os
import time
import asyncio
import logging
import threading
import queue
import json
import weakref
from typing import Dict, List, Optional, Any, Callable, Union, Awaitable
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
import inspect
import multiprocessing as mp
from contextlib import asynccontextmanager

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel, AgentRequest, AgentResponse, AgentStatus, PermissionLevel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AsyncAgentRequest:
    """Asynchronous agent request with enhanced metadata"""
    request_id: str
    agent_type: str
    action: str
    parameters: Dict[str, Any]
    user_context: Dict[str, Any]
    timestamp: float
    priority: int = 1
    timeout_seconds: float = 30.0
    callback: Optional[Callable] = None
    correlation_id: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

@dataclass
class AsyncAgentResponse:
    """Asynchronous agent response"""
    request_id: str
    agent_type: str
    status: AgentStatus
    result: Optional[Any]
    error_message: Optional[str]
    execution_time: float
    metadata: Dict[str, Any]
    completed_at: float
    worker_id: Optional[str] = None

class WorkerPool:
    """High-performance worker pool with dynamic scaling"""

    def __init__(self, min_workers: int = 2, max_workers: int = 20,
                 worker_type: str = 'thread', scale_up_threshold: float = 0.8,
                 scale_down_threshold: float = 0.3, idle_timeout: int = 300):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.worker_type = worker_type
        self.scale_up_threshold = scale_up_threshold
        self.scale_down_threshold = scale_down_threshold
        self.idle_timeout = idle_timeout

        self.workers = []
        self.available_workers = queue.Queue()
        self.busy_workers = set()
        self.pending_tasks = queue.Queue()
        self.completed_tasks = queue.Queue()

        self.scaling_active = False
        self.monitoring_active = False
        self.executor = None

        # Performance metrics
        self.task_history = deque(maxlen=1000)
        self.scale_events = deque(maxlen=100)

        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize worker pool"""
        if self.worker_type == 'thread':
            self.executor = ThreadPoolExecutor(
                max_workers=self.max_workers,
                thread_name_prefix="async_agent"
            )
        else:
            self.executor = ProcessPoolExecutor(
                max_workers=self.max_workers
            )

        # Create initial workers
        for i in range(self.min_workers):
            self._add_worker()

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()

        logger.info(f"Worker pool initialized: {self.min_workers} {self.worker_type} workers")

    def _add_worker(self):
        """Add a new worker to the pool"""
        if len(self.workers) >= self.max_workers:
            return False

        worker_id = f"worker_{len(self.workers)}_{int(time.time())}"
        worker_info = {
            'id': worker_id,
            'created_at': time.time(),
            'tasks_completed': 0,
            'last_activity': time.time(),
            'busy': False
        }

        self.workers.append(worker_info)
        self.available_workers.put(worker_id)

        logger.debug(f"Added worker {worker_id} to pool")
        return True

    def _remove_worker(self):
        """Remove an idle worker from the pool"""
        if len(self.workers) <= self.min_workers:
            return False

        try:
            worker_id = self.available_workers.get_nowait()
            self.workers = [w for w in self.workers if w['id'] != worker_id]
            logger.debug(f"Removed worker {worker_id} from pool")
            return True
        except queue.Empty:
            return False

    def submit_task(self, func: Callable, *args, **kwargs) -> str:
        """Submit task to worker pool"""
        task_id = f"task_{int(time.time() * 1000000)}"

        task_info = {
            'id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'submitted_at': time.time(),
            'status': 'pending'
        }

        self.pending_tasks.put(task_info)
        self._process_pending_tasks()
        return task_id

    def _process_pending_tasks(self):
        """Process pending tasks with available workers"""
        while not self.pending_tasks.empty():
            try:
                worker_id = self.available_workers.get_nowait()
                task_info = self.pending_tasks.get_nowait()

                # Execute task asynchronously
                future = self.executor.submit(task_info['func'], *task_info['args'], **task_info['kwargs'])

                # Mark worker as busy
                worker = next(w for w in self.workers if w['id'] == worker_id)
                worker['busy'] = True
                worker['last_activity'] = time.time()
                self.busy_workers.add(worker_id)

                # Setup completion callback
                future.add_done_callback(lambda f, w=worker_id, t=task_info: self._task_completed(f, w, t))

                logger.debug(f"Assigned task {task_info['id']} to worker {worker_id}")

            except queue.Empty:
                break  # No available workers

    def _task_completed(self, future: 'Future', worker_id: str, task_info: Dict[str, Any]):
        """Handle task completion"""
        try:
            result = future.result()
            task_info['result'] = result
            task_info['status'] = 'completed'
            task_info['completed_at'] = time.time()

            # Update worker info
            worker = next(w for w in self.workers if w['id'] == worker_id)
            worker['busy'] = False
            worker['tasks_completed'] += 1
            worker['last_activity'] = time.time()

            # Move worker back to available pool
            if worker_id in self.busy_workers:
                self.busy_workers.remove(worker_id)
            self.available_workers.put(worker_id)

            # Record task completion
            execution_time = task_info['completed_at'] - task_info['submitted_at']
            self.task_history.append({
                'task_id': task_info['id'],
                'worker_id': worker_id,
                'execution_time': execution_time,
                'completed_at': task_info['completed_at']
            })

            self.completed_tasks.put(task_info)

        except Exception as e:
            logger.error(f"Task {task_info['id']} failed: {str(e)}")
            task_info['error'] = str(e)
            task_info['status'] = 'failed'
            task_info['completed_at'] = time.time()

            # Return worker to available pool even on error
            if worker_id in self.busy_workers:
                self.busy_workers.remove(worker_id)
            self.available_workers.put(worker_id)

    def _monitoring_loop(self):
        """Monitor worker pool and adjust size"""
        while self.monitoring_active:
            try:
                # Calculate utilization
                busy_count = len(self.busy_workers)
                total_count = len(self.workers)
                utilization = busy_count / total_count if total_count > 0 else 0

                # Check for scaling
                if utilization > self.scale_up_threshold and total_count < self.max_workers:
                    if self._add_worker():
                        self.scale_events.append({
                            'action': 'scale_up',
                            'worker_count': total_count + 1,
                            'utilization': utilization,
                            'timestamp': time.time()
                        })

                elif utilization < self.scale_down_threshold and total_count > self.min_workers:
                    # Check for idle workers
                    idle_workers = [
                        w for w in self.workers
                        if not w['busy'] and (time.time() - w['last_activity']) > self.idle_timeout
                    ]

                    if idle_workers and self._remove_worker():
                        self.scale_events.append({
                            'action': 'scale_down',
                            'worker_count': total_count - 1,
                            'utilization': utilization,
                            'timestamp': time.time()
                        })

                time.sleep(10)  # Check every 10 seconds

            except Exception as e:
                logger.error(f"Error in worker pool monitoring: {str(e)}")
                time.sleep(30)

    def get_stats(self) -> Dict[str, Any]:
        """Get worker pool statistics"""
        total_workers = len(self.workers)
        busy_workers = len(self.busy_workers)
        pending_tasks = self.pending_tasks.qsize()

        # Calculate average execution time
        if self.task_history:
            avg_execution_time = sum(t['execution_time'] for t in self.task_history) / len(self.task_history)
        else:
            avg_execution_time = 0

        return {
            'total_workers': total_workers,
            'busy_workers': busy_workers,
            'available_workers': total_workers - busy_workers,
            'pending_tasks': pending_tasks,
            'utilization': busy_workers / total_workers if total_workers > 0 else 0,
            'avg_execution_time': avg_execution_time,
            'tasks_completed': sum(w['tasks_completed'] for w in self.workers),
            'scale_events_count': len(self.scale_events),
            'worker_details': [
                {
                    'id': w['id'],
                    'tasks_completed': w['tasks_completed'],
                    'busy': w['busy'],
                    'last_activity': w['last_activity']
                }
                for w in self.workers
            ]
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities and permissions"""
        return [
            AgentCapability(
                name="base_capability",
                description="Base agent capability",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=[]
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent action with proper routing"""
        if action == "validate_models":
            return self._validate_models(parameters, user_context)
        elif action == "check_compatibility":
            return self._check_data_compatibility(parameters, user_context)
        elif action == "performance_test":
            return self._run_performance_tests(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")


    def shutdown(self):
        """Shutdown worker pool"""
        self.monitoring_active = False
        if hasattr(self, 'monitoring_thread'):
            self.monitoring_thread.join(timeout=5)

        if self.executor:
            self.executor.shutdown(wait=True)

        logger.info("Worker pool shutdown completed")


class AsyncAgentOrchestrator:
    """
    Asynchronous agent orchestrator with high-performance concurrent processing,
    intelligent request routing, and dynamic resource management.

    .. deprecated:: 2025-11-19
        AsyncAgentOrchestrator is deprecated and will be removed in 30 days.
        Production code uses synchronous execution.
        Migration: Use synchronous agent execution (see WeeklyAnalysisOrchestrator pattern).
    """

    def __init__(self, base_path: str = None, max_concurrent_requests: int = 1000):
        import warnings
        warnings.warn(
            "AsyncAgentOrchestrator is deprecated and will be removed on 2025-12-19. "
            "Use synchronous agent execution instead (see WeeklyAnalysisOrchestrator pattern).",
            DeprecationWarning,
            stacklevel=2
        )
        self.base_path = base_path or os.getcwd()
        self.max_concurrent_requests = max_concurrent_requests

        # Worker pools for different agent types
        self.worker_pools = {
            'learning_navigator': WorkerPool(min_workers=2, max_workers=10),
            'model_engine': WorkerPool(min_workers=2, max_workers=8, worker_type='process'),
            'default': WorkerPool(min_workers=4, max_workers=20)
        }

        # Request management
        self.active_requests = {}  # request_id -> AsyncAgentRequest
        self.completed_responses = {}  # request_id -> AsyncAgentResponse
        self.request_queue = asyncio.Queue(maxsize=max_concurrent_requests)

        # Rate limiting and throttling
        self.rate_limiters = defaultdict(lambda: defaultdict(int))
        self.throttling_enabled = True

        # Circuit breaker for fault tolerance
        self.circuit_breakers = {}

        # Performance monitoring
        self.request_metrics = deque(maxlen=10000)
        self.response_time_history = deque(maxlen=1000)

        # Agent registry
        self.agent_registry = {}
        self.agent_factories = {}

        self.running = False
        self.processing_loop = None

        logger.info(f"Async Agent Orchestrator initialized: max_concurrent={max_concurrent_requests}")

    async def start(self):
        """Start the async orchestrator"""
        if self.running:
            return

        self.running = True
        self.processing_loop = asyncio.create_task(self._processing_loop())
        logger.info("Async Agent Orchestrator started")

    async def stop(self):
        """Stop the async orchestrator"""
        self.running = False

        if self.processing_loop:
            self.processing_loop.cancel()
            try:
                await self.processing_loop
            except asyncio.CancelledError:
                pass

        # Shutdown worker pools
        for pool in self.worker_pools.values():
            pool.shutdown()

        logger.info("Async Agent Orchestrator stopped")

    async def submit_request(self, request: AsyncAgentRequest) -> str:
        """Submit request for asynchronous processing"""
        try:
            # Check rate limits
            user_id = request.user_context.get('user_id', 'anonymous')
            if not await self._check_rate_limit(user_id, request.agent_type):
                raise Exception(f"Rate limit exceeded for user {user_id}")

            # Check circuit breaker
            if not self._is_circuit_breaker_open(request.agent_type):
                # Add to active requests
                self.active_requests[request.request_id] = request

                # Add to processing queue
                await self.request_queue.put(request)

                logger.debug(f"Submitted request {request.request_id} for async processing")
                return request.request_id
            else:
                raise Exception(f"Circuit breaker open for agent type {request.agent_type}")

        except Exception as e:
            logger.error(f"Failed to submit request {request.request_id}: {str(e)}")
            raise

    async def get_response(self, request_id: str, timeout_seconds: float = 30.0) -> Optional[AsyncAgentResponse]:
        """Get response for completed request"""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            if request_id in self.completed_responses:
                response = self.completed_responses.pop(request_id)
                if request_id in self.active_requests:
                    del self.active_requests[request_id]
                return response

            await asyncio.sleep(0.1)  # Check every 100ms

        # Timeout occurred
        if request_id in self.active_requests:
            request = self.active_requests[request_id]
            request.retry_count += 1

            if request.retry_count <= request.max_retries:
                # Retry the request
                await self.request_queue.put(request)
                logger.warning(f"Retrying request {request_id} (attempt {request.retry_count})")
            else:
                # Max retries exceeded
                del self.active_requests[request_id]
                logger.error(f"Request {request_id} failed after {request.max_retries} retries")

        return None

    async def _processing_loop(self):
        """Main processing loop for handling requests"""
        logger.info("Async processing loop started")

        while self.running:
            try:
                # Get request from queue with timeout
                request = await asyncio.wait_for(self.request_queue.get(), timeout=1.0)

                # Process request asynchronously
                asyncio.create_task(self._process_request_async(request))

            except asyncio.TimeoutError:
                # No requests available, continue loop
                continue
            except Exception as e:
                logger.error(f"Error in processing loop: {str(e)}")
                await asyncio.sleep(1)

    async def _process_request_async(self, request: AsyncAgentRequest):
        """Process single request asynchronously"""
        start_time = time.time()

        try:
            # Get appropriate worker pool
            pool = self.worker_pools.get(request.agent_type, self.worker_pools['default'])

            # Submit task to worker pool
            task_id = pool.submit_task(
                self._execute_agent_task,
                request
            )

            # Wait for completion (with timeout)
            while True:
                # Check completed tasks
                try:
                    task_info = pool.completed_tasks.get_nowait()
                    if task_info['id'] == task_id:
                        # Task completed
                        execution_time = time.time() - start_time

                        if 'result' in task_info:
                            response = AsyncAgentResponse(
                                request_id=request.request_id,
                                agent_type=request.agent_type,
                                status=AgentStatus.COMPLETED,
                                result=task_info['result'],
                                error_message=None,
                                execution_time=execution_time,
                                metadata={
                                    'worker_id': task_info.get('worker_id'),
                                    'processed_async': True
                                },
                                completed_at=time.time(),
                                worker_id=task_info.get('worker_id')
                            )

                            # Record metrics
                            self._record_request_metrics(request, response, True)

                            # Store response
                            self.completed_responses[request.request_id] = response

                            # Update circuit breaker
                            self._update_circuit_breaker(request.agent_type, success=True)

                            # Call callback if provided
                            if request.callback:
                                try:
                                    if inspect.iscoroutinefunction(request.callback):
                                        await request.callback(response)
                                    else:
                                        request.callback(response)
                                except Exception as e:
                                    logger.error(f"Error in callback for request {request.request_id}: {str(e)}")

                            logger.debug(f"Completed async request {request.request_id} in {execution_time:.3f}s")
                            break

                        elif 'error' in task_info:
                            # Task failed
                            execution_time = time.time() - start_time
                            response = AsyncAgentResponse(
                                request_id=request.request_id,
                                agent_type=request.agent_type,
                                status=AgentStatus.ERROR,
                                result=None,
                                error_message=task_info['error'],
                                execution_time=execution_time,
                                metadata={'worker_id': task_info.get('worker_id')},
                                completed_at=time.time(),
                                worker_id=task_info.get('worker_id')
                            )

                            self._record_request_metrics(request, response, False)
                            self.completed_responses[request.request_id] = response
                            self._update_circuit_breaker(request.agent_type, success=False)

                            logger.error(f"Request {request.request_id} failed: {task_info['error']}")
                            break

                except queue.Empty:
                    # Task not completed yet
                    await asyncio.sleep(0.1)

                    # Check timeout
                    if time.time() - start_time > request.timeout_seconds:
                        logger.error(f"Request {request.request_id} timed out")
                        response = AsyncAgentResponse(
                            request_id=request.request_id,
                            agent_type=request.agent_type,
                            status=AgentStatus.ERROR,
                            result=None,
                            error_message="Request timed out",
                            execution_time=request.timeout_seconds,
                            metadata={'timeout': True},
                            completed_at=time.time()
                        )

                        self.completed_responses[request.request_id] = response
                        self._update_circuit_breaker(request.agent_type, success=False)
                        break

        except Exception as e:
            logger.error(f"Error processing request {request.request_id}: {str(e)}")

            # Create error response
            response = AsyncAgentResponse(
                request_id=request.request_id,
                agent_type=request.agent_type,
                status=AgentStatus.ERROR,
                result=None,
                error_message=str(e),
                execution_time=time.time() - start_time,
                metadata={'processing_error': True},
                completed_at=time.time()
            )

            self.completed_responses[request.request_id] = response
            self._update_circuit_breaker(request.agent_type, success=False)

    def _execute_agent_task(self, request: AsyncAgentRequest) -> Dict[str, Any]:
        """Execute agent task (runs in worker thread/process)"""
        try:
            # This would integrate with the existing agent framework
            # For now, simulate agent execution

            # Simulate work based on agent type
            if request.agent_type == 'model_engine':
                time.sleep(0.1)  # Model predictions are fast
                result = {
                    'prediction': 0.75,
                    'confidence': 0.85,
                    'model_used': 'ridge_model_2025',
                    'agent_type': request.agent_type
                }
            elif request.agent_type == 'learning_navigator':
                time.sleep(0.2)  # Learning navigation takes moderate time
                result = {
                    'recommended_path': ['01_intro_to_data.ipynb', '02_build_simple_rankings.ipynb'],
                    'next_steps': ['Explore data structure', 'Build rankings'],
                    'agent_type': request.agent_type
                }
            else:
                time.sleep(0.15)  # Default processing time
                result = {
                    'message': f"Processed {request.action} for {request.agent_type}",
                    'agent_type': request.agent_type
                }

            return {
                'success': True,
                'result': result,
                'processing_time': time.time()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time()
            }

    async def _check_rate_limit(self, user_id: str, agent_type: str) -> bool:
        """Check if user is within rate limits"""
        if not self.throttling_enabled:
            return True

        current_minute = int(time.time() // 60)
        user_requests = self.rate_limiters[user_id][current_minute]

        # Simple rate limit: 100 requests per minute per user
        max_requests_per_minute = 100

        if user_requests >= max_requests_per_minute:
            return False

        self.rate_limiters[user_id][current_minute] += 1

        # Clean old rate limit data
        cutoff_time = current_minute - 5  # Keep last 5 minutes
        self.rate_limiters[user_id] = {
            minute: count for minute, count in self.rate_limiters[user_id].items()
            if minute >= cutoff_time
        }

        return True

    def _is_circuit_breaker_open(self, agent_type: str) -> bool:
        """Check if circuit breaker is open for agent type"""
        if agent_type not in self.circuit_breakers:
            self.circuit_breakers[agent_type] = {
                'failure_count': 0,
                'last_failure': 0,
                'state': 'closed',  # closed, open, half_open
                'success_count': 0
            }

        breaker = self.circuit_breakers[agent_type]

        if breaker['state'] == 'open':
            # Check if we should try half-open
            if time.time() - breaker['last_failure'] > 60:  # 1 minute timeout
                breaker['state'] = 'half_open'
                breaker['success_count'] = 0
                return False
            else:
                return True

        return False

    def _update_circuit_breaker(self, agent_type: str, success: bool):
        """Update circuit breaker state"""
        if agent_type not in self.circuit_breakers:
            return

        breaker = self.circuit_breakers[agent_type]

        if success:
            breaker['failure_count'] = max(0, breaker['failure_count'] - 1)
            breaker['success_count'] += 1

            if breaker['state'] == 'half_open' and breaker['success_count'] >= 3:
                breaker['state'] = 'closed'
        else:
            breaker['failure_count'] += 1
            breaker['last_failure'] = time.time()

            if breaker['failure_count'] >= 5:  # Open after 5 failures
                breaker['state'] = 'open'

    def _record_request_metrics(self, request: AsyncAgentRequest, response: AsyncAgentResponse, success: bool):
        """Record request metrics for performance monitoring"""
        self.request_metrics.append({
            'request_id': request.request_id,
            'agent_type': request.agent_type,
            'action': request.action,
            'priority': request.priority,
            'success': success,
            'execution_time': response.execution_time,
            'timestamp': time.time(),
            'user_id': request.user_context.get('user_id', 'anonymous')
        })

        self.response_time_history.append(response.execution_time)

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        # Calculate request metrics
        if self.request_metrics:
            total_requests = len(self.request_metrics)
            successful_requests = sum(1 for m in self.request_metrics if m['success'])
            success_rate = (successful_requests / total_requests) * 100

            avg_execution_time = sum(m['execution_time'] for m in self.request_metrics) / total_requests

            # Calculate percentiles for response times
            sorted_times = sorted(self.response_time_history)
            n = len(sorted_times)
            p50 = sorted_times[n // 2] if n > 0 else 0
            p95 = sorted_times[int(n * 0.95)] if n > 0 else 0
            p99 = sorted_times[int(n * 0.99)] if n > 0 else 0

            # Requests per second (last minute)
            one_minute_ago = time.time() - 60
            recent_requests = [m for m in self.request_metrics if m['timestamp'] > one_minute_ago]
            requests_per_second = len(recent_requests) / 60

        else:
            total_requests = 0
            success_rate = 0
            avg_execution_time = 0
            p50 = p95 = p99 = 0
            requests_per_second = 0

        # Worker pool stats
        worker_stats = {}
        for pool_name, pool in self.worker_pools.items():
            worker_stats[pool_name] = pool.get_stats()

        return {
            'async_orchestrator': {
                'active_requests': len(self.active_requests),
                'completed_responses': len(self.completed_responses),
                'queue_size': self.request_queue.qsize(),
                'max_concurrent': self.max_concurrent_requests
            },
            'request_metrics': {
                'total_requests': total_requests,
                'success_rate': success_rate,
                'avg_execution_time': avg_execution_time,
                'requests_per_second': requests_per_second,
                'response_time_percentiles': {
                    'p50': p50,
                    'p95': p95,
                    'p99': p99
                }
            },
            'worker_pools': worker_stats,
            'circuit_breakers': {
                agent_type: {
                    'state': breaker['state'],
                    'failure_count': breaker['failure_count']
                }
                for agent_type, breaker in self.circuit_breakers.items()
            },
            'rate_limiters': {
                user_id: dict(requests)
                for user_id, requests in list(self.rate_limiters.items())[:10]  # Top 10 users
            }
        }

    async def wait_for_completion(self, request_ids: List[str], timeout_seconds: float = 30.0) -> Dict[str, AsyncAgentResponse]:
        """Wait for multiple requests to complete"""
        responses = {}
        start_time = time.time()

        remaining_requests = set(request_ids)

        while remaining_requests and (time.time() - start_time) < timeout_seconds:
            completed = []

            for request_id in remaining_requests:
                if request_id in self.completed_responses:
                    responses[request_id] = self.completed_responses.pop(request_id)
                    if request_id in self.active_requests:
                        del self.active_requests[request_id]
                    completed.append(request_id)

            for request_id in completed:
                remaining_requests.remove(request_id)

            if remaining_requests:
                await asyncio.sleep(0.1)

        return responses


# Example usage and testing
async def test_async_orchestrator():
    """Test the async orchestrator"""
    orchestrator = AsyncAgentOrchestrator(max_concurrent_requests=100)
    await orchestrator.start()

    try:
        print("=== Async Agent Orchestrator Test ===")

        # Create test requests
        requests = []
        for i in range(10):
            request = AsyncAgentRequest(
                request_id=f"test_req_{i}",
                agent_type="learning_navigator" if i % 2 == 0 else "model_engine",
                action="test_action",
                parameters={"test_param": i},
                user_context={"user_id": f"test_user_{i % 3}"},
                timestamp=time.time(),
                priority=1
            )
            requests.append(request)

        # Submit requests asynchronously
        submitted_ids = []
        for request in requests:
            request_id = await orchestrator.submit_request(request)
            submitted_ids.append(request_id)

        print(f"Submitted {len(submitted_ids)} requests")

        # Wait for responses
        responses = await orchestrator.wait_for_completion(submitted_ids, timeout_seconds=10)

        print(f"Received {len(responses)} responses")

        # Get performance stats
        stats = orchestrator.get_performance_stats()
        print(f"\n=== Performance Statistics ===")
        print(f"Success rate: {stats['request_metrics']['success_rate']:.1f}%")
        print(f"Avg execution time: {stats['request_metrics']['avg_execution_time']:.3f}s")
        print(f"Requests per second: {stats['request_metrics']['requests_per_second']:.1f}")
        print(f"Response time p95: {stats['request_metrics']['response_time_percentiles']['p95']:.3f}s")

    finally:
        await orchestrator.stop()


if __name__ == "__main__":
    # Run async test
    asyncio.run(test_async_orchestrator())