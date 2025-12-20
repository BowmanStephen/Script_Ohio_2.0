"""
Parallel Processing System for CFBD Data
Provides high-performance parallel API calls with intelligent rate limiting and batching
"""

import asyncio
import json
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from .enhanced_unified_client import EnhancedUnifiedCFBDClient

logger = logging.getLogger(__name__)


@dataclass
class ParallelTask:
    """Represents a parallel processing task"""

    task_id: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: int  # Lower numbers = higher priority
    created_at: datetime
    dependencies: List[str]  # Task IDs this task depends on


@dataclass
class TaskResult:
    """Represents the result of a parallel task"""

    task_id: str
    success: bool
    result: Any
    error: Optional[str]
    execution_time: float
    completed_at: datetime


@dataclass
class PerformanceMetrics:
    """Performance metrics for parallel processing"""

    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    average_execution_time: float
    total_time_saved: float  # Time saved compared to sequential execution
    peak_workers_used: int
    cache_hit_rate: float


class ParallelCFBDProcessor:
    """
    High-performance parallel processor for CFBD API calls

    Features:
    - Parallel API calls with configurable worker threads
    - Intelligent rate limiting and burst protection
    - Task prioritization and dependency management
    - Performance monitoring and optimization
    - Batching for similar API calls
    """

    def __init__(self, config=None, max_workers: int = 6):
        """
        Initialize parallel processor

        Args:
            config: CFBD configuration
            max_workers: Maximum number of parallel workers (default 6, respecting CFBD rate limits)
        """
        self.client = EnhancedUnifiedCFBDClient(config)
        self.max_workers = max_workers

        # Task management
        self.pending_tasks: List[ParallelTask] = []
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.running_tasks: Dict[str, threading.Thread] = {}

        # Performance tracking
        self.start_time = datetime.now(timezone.utc)
        self.sequential_baseline_time = 0.0
        self.parallel_execution_time = 0.0

        # Rate limiting
        self.rate_limit_semaphore = threading.Semaphore(max_workers)
        self.last_request_time = 0.0
        self.min_request_interval = 0.17  # 170ms for 6 req/sec rate limit

        # Caching
        self.cache_enabled = True
        self.cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0

        logger.info(
            f"🚀 Parallel CFBD Processor initialized with {max_workers} workers"
        )

    def add_task(
        self,
        task_id: str,
        function: Callable,
        *args,
        priority: int = 5,
        dependencies: List[str] = None,
        **kwargs,
    ) -> str:
        """
        Add a task to the processing queue

        Args:
            task_id: Unique identifier for the task
            function: Function to execute
            *args: Positional arguments for the function
            priority: Task priority (lower numbers = higher priority)
            dependencies: List of task IDs this task depends on
            **kwargs: Keyword arguments for the function

        Returns:
            Task ID
        """
        task = ParallelTask(
            task_id=task_id,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            created_at=datetime.now(timezone.utc),
            dependencies=dependencies or [],
        )

        self.pending_tasks.append(task)
        self.pending_tasks.sort(key=lambda t: t.priority)

        logger.debug(f"📝 Added task {task_id} with priority {priority}")
        return task_id

    def add_batch_tasks(
        self, tasks: List[Tuple[str, Callable, tuple, dict]], priority: int = 5
    ):
        """
        Add multiple tasks as a batch

        Args:
            tasks: List of (task_id, function, args, kwargs) tuples
            priority: Priority for all tasks in the batch
        """
        for task_id, function, args, kwargs in tasks:
            self.add_task(task_id, function, *args, priority=priority, **kwargs)

        logger.info(f"📦 Added batch of {len(tasks)} tasks with priority {priority}")

    def _get_cache_key(self, function: Callable, args: tuple, kwargs: dict) -> str:
        """Generate cache key for function call"""
        import hashlib

        key_data = f"{function.__name__}_{str(args)}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def _check_cache(
        self, function: Callable, args: tuple, kwargs: dict
    ) -> Optional[Any]:
        """Check if result is cached"""
        if not self.cache_enabled:
            return None

        cache_key = self._get_cache_key(function, args, kwargs)
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.debug(f"🎯 Cache hit for {function.__name__}")
            return self.cache[cache_key]

        self.cache_misses += 1
        return None

    def _cache_result(self, function: Callable, args: tuple, kwargs: dict, result: Any):
        """Cache function result"""
        if not self.cache_enabled:
            return

        cache_key = self._get_cache_key(function, args, kwargs)
        self.cache[cache_key] = result

    def _execute_task(self, task: ParallelTask) -> TaskResult:
        """
        Execute a single task with rate limiting and caching

        Args:
            task: Task to execute

        Returns:
            TaskResult with execution outcome
        """
        start_time = time.time()

        try:
            # Check cache first
            cached_result = self._check_cache(task.function, task.args, task.kwargs)
            if cached_result is not None:
                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    result=cached_result,
                    error=None,
                    execution_time=time.time() - start_time,
                    completed_at=datetime.now(timezone.utc),
                )

            # Acquire semaphore for rate limiting
            with self.rate_limit_semaphore:
                # Respect rate limits
                current_time = time.time()
                time_since_last = current_time - self.last_request_time
                if time_since_last < self.min_request_interval:
                    time.sleep(self.min_request_interval - time_since_last)

                self.last_request_time = time.time()

                # Execute the function
                logger.debug(f"🔄 Executing task {task.task_id}")
                result = task.function(*task.args, **task.kwargs)

                # Cache the result
                self._cache_result(task.function, task.args, task.kwargs, result)

                execution_time = time.time() - start_time

                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    result=result,
                    error=None,
                    execution_time=execution_time,
                    completed_at=datetime.now(timezone.utc),
                )

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"❌ Task {task.task_id} failed: {error_msg}")

            return TaskResult(
                task_id=task.task_id,
                success=False,
                result=None,
                error=error_msg,
                execution_time=execution_time,
                completed_at=datetime.now(timezone.utc),
            )

    def _check_dependencies(self, task: ParallelTask) -> bool:
        """Check if all task dependencies are completed"""
        for dep_id in task.dependencies:
            if dep_id not in self.completed_tasks:
                return False
            if not self.completed_tasks[dep_id].success:
                return False
        return True

    def process_tasks(self) -> Dict[str, TaskResult]:
        """
        Process all pending tasks in parallel

        Returns:
            Dictionary mapping task IDs to their results
        """
        if not self.pending_tasks:
            logger.info("📋 No pending tasks to process")
            return {}

        logger.info(
            f"🚀 Processing {len(self.pending_tasks)} tasks with {self.max_workers} workers"
        )
        start_time = time.time()

        # Filter tasks with satisfied dependencies
        ready_tasks = [
            task for task in self.pending_tasks if self._check_dependencies(task)
        ]

        if not ready_tasks:
            logger.warning("⚠️ No tasks with satisfied dependencies")
            return {}

        results = {}

        # Use ThreadPoolExecutor for parallel execution
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all ready tasks
            future_to_task = {}
            for task in ready_tasks:
                future = executor.submit(self._execute_task, task)
                future_to_task[future] = task

            # Process completed tasks
            completed_count = 0
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results[task.task_id] = result
                    self.completed_tasks[task.task_id] = result
                    completed_count += 1

                    if result.success:
                        logger.debug(
                            f"✅ Completed task {task.task_id} in {result.execution_time:.2f}s"
                        )
                    else:
                        logger.error(f"❌ Failed task {task.task_id}: {result.error}")

                except Exception as e:
                    logger.error(f"❌ Exception in task {task.task_id}: {e}")
                    error_result = TaskResult(
                        task_id=task.task_id,
                        success=False,
                        result=None,
                        error=str(e),
                        execution_time=0,
                        completed_at=datetime.now(timezone.utc),
                    )
                    results[task.task_id] = error_result
                    self.completed_tasks[task.task_id] = error_result

        # Remove completed tasks from pending
        self.pending_tasks = [
            task for task in self.pending_tasks if task.task_id not in results
        ]

        execution_time = time.time() - start_time
        self.parallel_execution_time += execution_time

        logger.info(
            f"🎉 Completed {completed_count}/{len(ready_tasks)} tasks in {execution_time:.2f}s"
        )

        return results

    def process_sequential_baseline(self, tasks: List[ParallelTask]) -> float:
        """
        Process tasks sequentially to establish performance baseline

        Args:
            tasks: List of tasks to process

        Returns:
            Time taken for sequential execution
        """
        logger.info(f"📏 Running sequential baseline with {len(tasks)} tasks")
        start_time = time.time()

        for task in tasks:
            result = self._execute_task(task)
            self.completed_tasks[f"baseline_{task.task_id}"] = result

        sequential_time = time.time() - start_time
        self.sequential_baseline_time += sequential_time

        logger.info(f"⏱️ Sequential baseline completed in {sequential_time:.2f}s")
        return sequential_time

    def parallel_get_games_batch(
        self, year: int, weeks: List[int]
    ) -> Dict[str, List[Dict]]:
        """
        Parallel batch processing for games data

        Args:
            year: Season year
            weeks: List of weeks to fetch

        Returns:
            Dictionary mapping weeks to game data
        """
        logger.info(f"🏈 Parallel batch games fetch: {year}, weeks {weeks}")

        # Create tasks for each week
        tasks = []
        for week in weeks:
            task_id = f"games_{year}_week_{week}"
            self.add_task(
                task_id=task_id,
                function=self.client.get_games,
                year=year,
                week=week,
                priority=1,  # High priority for games data
            )
            tasks.append(task_id)

        # Process tasks
        results = self.process_tasks()

        # Compile results
        games_by_week = {}
        for task_id in tasks:
            if task_id in results and results[task_id].success:
                week = int(task_id.split("_")[-1])
                games_by_week[f"week_{week}"] = results[task_id].result

        return games_by_week

    def parallel_get_team_stats_batch(
        self, teams: List[str], year: int
    ) -> Dict[str, Any]:
        """
        Parallel batch processing for team statistics

        Args:
            teams: List of team names
            year: Season year

        Returns:
            Dictionary of team statistics
        """
        logger.info(f"📊 Parallel batch team stats: {len(teams)} teams")

        # Create tasks for each team
        tasks = []
        for team in teams:
            task_id = f"team_stats_{team.replace(' ', '_')}"
            self.add_task(
                task_id=task_id,
                function=self.client.get_advanced_team_stats,
                year=year,
                team=team,
                priority=2,  # Medium priority
            )
            tasks.append(task_id)

        # Process tasks
        results = self.process_tasks()

        # Compile results
        team_stats = {}
        for task_id in tasks:
            if task_id in results and results[task_id].success:
                team_name = task_id.replace("team_stats_", "").replace("_", " ")
                team_stats[team_name] = results[task_id].result

        return team_stats

    def parallel_get_multiple_box_scores(self, game_ids: List[int]) -> Dict[int, Any]:
        """
        Parallel batch processing for multiple box scores

        Args:
            game_ids: List of game IDs

        Returns:
            Dictionary of box scores
        """
        logger.info(f"📋 Parallel batch box scores: {len(game_ids)} games")

        # Import here to avoid circular imports
        from .enhanced_box_scores import EnhancedBoxScoreClient

        box_score_client = EnhancedBoxScoreClient()

        # Create tasks for each game
        tasks = []
        for game_id in game_ids:
            task_id = f"box_score_{game_id}"
            self.add_task(
                task_id=task_id,
                function=box_score_client.get_enhanced_box_score,
                game_id=game_id,
                priority=3,  # Lower priority
            )
            tasks.append(task_id)

        # Process tasks
        results = self.process_tasks()

        # Compile results
        box_scores = {}
        for task_id in tasks:
            if task_id in results and results[task_id].success:
                game_id = int(task_id.split("_")[-1])
                box_scores[game_id] = results[task_id].result

        return box_scores

    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get comprehensive performance metrics"""
        total_tasks = len(self.completed_tasks)
        completed_tasks = len([r for r in self.completed_tasks.values() if r.success])
        failed_tasks = total_tasks - completed_tasks

        if completed_tasks > 0:
            avg_execution_time = (
                sum(
                    r.execution_time for r in self.completed_tasks.values() if r.success
                )
                / completed_tasks
            )
        else:
            avg_execution_time = 0.0

        # Calculate time saved
        if self.sequential_baseline_time > 0:
            time_saved = self.sequential_baseline_time - self.parallel_execution_time
            time_saved_pct = (time_saved / self.sequential_baseline_time) * 100
        else:
            time_saved = 0.0
            time_saved_pct = 0.0

        # Cache metrics
        total_cache_requests = self.cache_hits + self.cache_misses
        cache_hit_rate = (
            (self.cache_hits / total_cache_requests * 100)
            if total_cache_requests > 0
            else 0.0
        )

        return PerformanceMetrics(
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            average_execution_time=avg_execution_time,
            total_time_saved=time_saved,
            peak_workers_used=self.max_workers,
            cache_hit_rate=cache_hit_rate,
        )

    def optimize_performance(self):
        """Optimize processor settings based on performance metrics"""
        metrics = self.get_performance_metrics()

        logger.info("🔧 Performance Optimization Analysis:")
        logger.info(f"   Total tasks: {metrics.total_tasks}")
        logger.info(
            f"   Success rate: {(metrics.completed_tasks/max(metrics.total_tasks, 1)*100):.1f}%"
        )
        logger.info(f"   Average execution time: {metrics.average_execution_time:.2f}s")
        logger.info(f"   Time saved: {metrics.total_time_saved:.2f}s")
        logger.info(f"   Cache hit rate: {metrics.cache_hit_rate:.1f}%")

        # Recommendations
        if metrics.cache_hit_rate < 30:
            logger.info(
                "💡 Recommendation: Consider increasing cache TTL for better hit rates"
            )

        if metrics.average_execution_time > 2.0:
            logger.info(
                "💡 Recommendation: Some tasks are slow - consider batching or optimization"
            )

        if metrics.total_time_saved > 0:
            speedup = self.sequential_baseline_time / max(
                self.parallel_execution_time, 0.1
            )
            logger.info(f"🚀 Performance improvement: {speedup:.1f}x speedup achieved")

    def clear_cache(self):
        """Clear the internal cache"""
        self.cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info("🗑️ Cache cleared")

    def get_task_summary(self) -> Dict[str, Any]:
        """Get summary of all tasks"""
        return {
            "pending_tasks": len(self.pending_tasks),
            "completed_tasks": len(self.completed_tasks),
            "successful_tasks": len(
                [r for r in self.completed_tasks.values() if r.success]
            ),
            "failed_tasks": len(
                [r for r in self.completed_tasks.values() if not r.success]
            ),
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "hit_rate": (
                    self.cache_hits / max(self.cache_hits + self.cache_misses, 1)
                )
                * 100,
            },
            "uptime": (datetime.now(timezone.utc) - self.start_time).total_seconds(),
        }


# Example usage and demonstration
def demo_parallel_processor():
    """Demonstration of parallel processor capabilities"""
    print("🚀 Parallel CFBD Processor Demo")
    print("=" * 40)

    processor = ParallelCFBDProcessor(max_workers=6)

    # Example 1: Parallel games fetching
    print("\n📅 Example 1: Parallel games fetching")
    weeks = [12, 13, 14, 15]  # Championship season
    start_time = time.time()

    games_data = processor.parallel_get_games_batch(year=2025, weeks=weeks)

    end_time = time.time()
    total_games = sum(len(games) for games in games_data.values())

    print(
        f"   ✅ Fetched {total_games} games from {len(games_data)} weeks in {end_time - start_time:.2f}s"
    )

    # Example 2: Parallel team statistics
    print("\n📊 Example 2: Parallel team statistics")
    teams = ["Alabama", "Georgia", "Ohio State", "Michigan", "Texas", "Oklahoma"]
    start_time = time.time()

    team_stats = processor.parallel_get_team_stats_batch(teams, year=2025)

    end_time = time.time()
    print(
        f"   ✅ Fetched stats for {len(team_stats)} teams in {end_time - start_time:.2f}s"
    )

    # Example 3: Performance metrics
    print("\n📈 Performance Metrics:")
    metrics = processor.get_performance_metrics()
    print(f"   Total tasks: {metrics.total_tasks}")
    print(
        f"   Success rate: {(metrics.completed_tasks/max(metrics.total_tasks, 1)*100):.1f}%"
    )
    print(f"   Average time: {metrics.average_execution_time:.2f}s")
    print(f"   Cache hit rate: {metrics.cache_hit_rate:.1f}%")

    if metrics.total_time_saved > 0:
        print(f"   Time saved: {metrics.total_time_saved:.2f}s")
        speedup = metrics.total_time_saved / max(metrics.parallel_execution_time, 0.1)
        print(f"   Speedup: {speedup:.1f}x")

    # Show optimization recommendations
    processor.optimize_performance()


if __name__ == "__main__":
    demo_parallel_processor()
