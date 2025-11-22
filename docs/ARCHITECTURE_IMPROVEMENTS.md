# Architecture Improvements Guide

**Last Updated**: November 2025  
**Status**: Active improvements in progress

## Overview

This document outlines prioritized architecture improvements for Script Ohio 2.0, focusing on scalability, maintainability, and technical debt reduction.

## Code Organization Improvements

### Duplicate Code Elimination

**Current State**: Multiple CFBD client implementations exist across the codebase.

**Problem Areas**:
- `src/cfbd_client/client.py` - Legacy client implementation
- `src/data_sources/cfbd_client.py` - Duplicate client wrapper
- `starter_pack/utils/cfbd_loader.py` - Notebook-specific loader
- `agents/core/enhanced_cfbd_integration.py` - Agent-specific wrapper

**Target Solution**: Complete migration to `UnifiedCFBDClient`

**Migration Plan**:
1. Identify all usages of duplicate clients
2. Update imports to use `src/cfbd_client/unified_client.py`
3. Test each migration point thoroughly
4. Deprecate old implementations with warnings
5. Remove deprecated code after full migration

**Benefits**:
- Single source of truth for CFBD integration
- Consistent error handling and rate limiting
- Reduced maintenance burden
- Improved testability

### File Size Management

**Current State**: Some files exceed 1000 lines, making them difficult to maintain.

**Problem Files**:
- `agents/analytics_orchestrator.py` (>1000 lines)

**Refactoring Strategy**:

**For `analytics_orchestrator.py`**:
Split into focused modules:
- `agents/core/orchestration/coordinator.py` - Main orchestration logic
- `agents/core/orchestration/router.py` - Agent routing and dispatch
- `agents/core/orchestration/synthesizer.py` - Response synthesis
- `agents/core/orchestration/middleware.py` - Request/response middleware

**General Guidelines**:
- Target file size: <500 lines for core logic
- Extract utility functions to separate modules
- Use composition over inheritance
- Create focused, single-responsibility modules

### Archive Management

**Current State**: Archive and backup directories exist in main repository.

**Problem**:
- Increases repository size
- Slows git operations
- Clutters file tree

**Solutions**:

**Option 1: Separate Branch**
```bash
git checkout --orphan archive
git add archive/ backup/
git commit -m "Archive historical files"
# Keep for reference but not in main branch
```

**Option 2: Git LFS**
- Move large backup files to Git LFS
- Reduces clone size for most users
- Maintains version history

**Option 3: External Storage**
- Move archives to external storage (S3, GCS)
- Update documentation with access instructions
- Remove from repository

**Recommended Approach**: Option 3 for large files, Option 1 for historical reference

## Scalability Roadmap

### Phase 1: Caching Migration (Current → 3 months)

**Current**: SQLite-based caching
**Target**: Redis-based distributed caching

**Migration Steps**:
1. Implement Redis adapter for cache manager
2. Maintain SQLite as fallback for local development
3. Migrate cache keys to Redis-compatible format
4. Update TTL strategies for distributed environment
5. Add cache cluster configuration

**Benefits**:
- Supports multi-instance deployment
- Better performance for high-traffic scenarios
- Centralized cache management
- Improved cache invalidation

### Phase 2: Message Queue Integration (3-6 months)

**Purpose**: Enable async task processing and improve system responsiveness

**Technology Options**:
- **Redis Queue (RQ)**: Simple, Redis-based
- **Celery**: Full-featured, multiple backends
- **RabbitMQ**: Enterprise-grade, robust

**Recommended**: Start with Redis Queue for simplicity, migrate to Celery if needed

**Use Cases**:
- Long-running model predictions
- Batch data processing
- Scheduled analysis tasks
- Webhook processing

### Phase 3: Database Migration (6-12 months)

**Current**: SQLite for caching and state
**Target**: PostgreSQL for production data

**Migration Strategy**:
1. Set up PostgreSQL instance
2. Implement database abstraction layer
3. Migrate cache metadata to PostgreSQL
4. Migrate state management to PostgreSQL
5. Keep SQLite for local development

**Benefits**:
- Better concurrency handling
- Advanced query capabilities
- Production-grade reliability
- Support for complex relationships

### Phase 4: Horizontal Scaling (12+ months)

**Goals**:
- Multi-instance deployment
- Load balancing
- Stateless service design
- Shared state via external services

**Requirements**:
- Stateless agent execution
- External session management
- Shared cache (Redis)
- Shared database (PostgreSQL)
- Message queue for coordination

## Performance Optimization Strategies

### Async I/O Operations

**Current**: Synchronous HTTP requests

**Optimization**: Refactor to async/await pattern

**Target Files**:
- `src/cfbd_client/unified_client.py`
- `agents/cfbd_integration_agent.py`

**Implementation**:
```python
import aiohttp

async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()
```

**Benefits**:
- Non-blocking I/O operations
- Better resource utilization
- Improved concurrency
- Reduced latency

### Connection Pooling

**Current**: New connections for each request

**Optimization**: Implement connection pooling

**For Redis**:
```python
from redis.connection import ConnectionPool

pool = ConnectionPool(host='localhost', port=6379, db=0)
redis_client = redis.Redis(connection_pool=pool)
```

**For PostgreSQL**:
```python
from psycopg2 import pool

connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    host='localhost',
    database='script_ohio',
    user='user',
    password='password'
)
```

**Benefits**:
- Reduced connection overhead
- Better resource management
- Improved performance under load

### Profiling Integration

**Tools**:
- `cProfile`: Built-in Python profiler
- `py-spy`: Sampling profiler with low overhead
- `line_profiler`: Line-by-line profiling

**Integration**:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # Top 20 functions
```

**Development Workflow**:
1. Profile critical paths regularly
2. Identify bottlenecks
3. Optimize hot paths
4. Verify improvements with benchmarks

## Code Consolidation Plan

### UnifiedCFBDClient Migration

**Status**: In Progress

**Remaining Work**:
1. Audit all CFBD client usages
2. Update deprecated imports
3. Test each integration point
4. Remove legacy implementations

**Timeline**: 2-4 weeks

### Large File Refactoring

**Status**: Planned

**Priority Files**:
1. `agents/analytics_orchestrator.py` (High priority)
2. Other files >1000 lines (Medium priority)

**Timeline**: 4-8 weeks

### Archive Cleanup

**Status**: Planned

**Action Items**:
1. Review archive/backup contents
2. Move large files to external storage
3. Update documentation with access info
4. Remove from repository

**Timeline**: 2-3 weeks

## Monitoring & Observability

### Current State

- Basic logging implemented
- Inconsistent log levels
- No centralized log collection
- Limited performance metrics

### Target State

**Structured Logging**:
- JSON format for log aggregation
- Consistent log levels across codebase
- Contextual information in all logs

**Metrics Collection**:
- Request/response times
- Error rates
- Cache hit rates
- Agent execution times
- Resource utilization

**Dashboard**:
- Grafana for visualization
- Real-time system health
- Performance trends
- Alert management

**Distributed Tracing**:
- OpenTelemetry integration
- Request flow visualization
- Performance bottleneck identification

## Implementation Priorities

### Immediate (0-1 month)
1. Complete UnifiedCFBDClient migration
2. Implement structured logging
3. Set up dependency scanning in CI/CD

### Short-term (1-3 months)
1. Refactor large files
2. Implement Redis caching adapter
3. Add code coverage reporting
4. Set up monitoring dashboard

### Medium-term (3-6 months)
1. Implement message queue system
2. Migrate to async I/O
3. Set up PostgreSQL
4. Implement distributed tracing

### Long-term (6-12 months)
1. Horizontal scaling preparation
2. Multi-instance deployment
3. Advanced monitoring and alerting
4. Performance optimization pass

## Success Metrics

**Code Quality**:
- No files >1000 lines (core logic)
- 80%+ test coverage
- Zero duplicate client implementations
- All public APIs have type hints

**Performance**:
- <100ms p95 response time for agent actions
- <50ms cache response time
- 99.9% uptime
- Support for 100+ concurrent requests

**Maintainability**:
- All dependencies documented
- Clear separation of concerns
- Comprehensive test suite
- Up-to-date architecture documentation

## References

- **Agent Framework**: `agents/core/agent_framework.py`
- **CFBD Client**: `src/cfbd_client/unified_client.py`
- **Main Documentation**: `AGENTS.md`
- **Security Guide**: `docs/SECURITY_BEST_PRACTICES.md`
- **Code Quality Guide**: `docs/CODE_QUALITY_GUIDELINES.md`

