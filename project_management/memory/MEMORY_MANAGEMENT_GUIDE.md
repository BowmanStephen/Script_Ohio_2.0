# Memory Management System - User Guide

## 🧠 Overview

Your Super AI Agent Architecture includes a sophisticated 4-level hierarchical memory management system that provides intelligent data storage, retrieval, and optimization capabilities. This system dramatically improves performance through smart caching, compression, and hierarchical organization.

## 🏛️ Memory Hierarchy

### Level 1: Meta Agent Memory (Persistent)
- **Purpose**: Critical system state and agent registry
- **Capacity**: 100 MB
- **Retention**: 365 days
- **Use Cases**:
  - Agent registration and configuration
  - System health metrics
  - Performance baselines
  - Audit trails

### Level 2: Orchestrator Memory (Session)
- **Purpose**: Active plans and coordination data
- **Capacity**: 50 MB
- **Retention**: 24 hours
- **Use Cases**:
  - Active workflow states
  - Task queues and assignments
  - Inter-agent coordination
  - Session-specific context

### Level 3: Agent Memory (Ephemeral)
- **Purpose**: Task-specific context and intermediate results
- **Capacity**: 20 MB
- **Retention**: 60 minutes
- **Use Cases**:
  - API call tracking
  - Task progress states
  - Intermediate computation results
  - Temporary agent context

### Level 4: Cache Memory (Temporary)
- **Purpose**: Fast access to frequently used data
- **Capacity**: 200 MB
- **Retention**: Variable (1-1440 minutes)
- **Use Cases**:
  - CFBD API responses (60 min TTL)
  - Model predictions (24 hr TTL)
  - TOON format outputs (30 min TTL)
  - Computed analytics

## 🚀 Quick Start Commands

### Basic Operations
```bash
/memory status              # Show complete system overview
/memory cleanup             # Clean all expired entries
/memory cache flush         # Clear entire cache
```

### Level-Specific Operations
```bash
/memory meta list          # List Meta Agent entries
/memory orchestrator list  # List active sessions
/memory agents list        # List agent memory contents
/memory cache list         # Show cache by type
```

### Advanced Operations
```bash
/memory meta compress      # Compress old Meta Agent entries
/memory agents cleanup     # Clean expired agent data
/memory cache optimize     # Optimize cache TTL settings
```

## 📊 Programming Interface

### Import and Initialization
```python
from agents.optimization.memory_manager import memory_manager, MemoryLevel
from datetime import datetime, timedelta
```

### Storing Data
```python
# Store CFBD API response in cache
cache_data = {
    'games': [{'id': 401752911, 'home': 'Oregon', 'away': 'USC'}],
    'timestamp': datetime.now().isoformat()
}

success = memory_manager.store(
    key='cfbd_week14_games',
    value=cache_data,
    level=MemoryLevel.CACHE,
    expires_in=timedelta(hours=1),  # 1 hour TTL
    tags=['cfbd', 'api_response', 'week14']
)
```

### Retrieving Data
```python
# Retrieve cached data
retrieved = memory_manager.retrieve('cfbd_week14_games')
if retrieved:
    games = retrieved['games']
    print(f"Found {len(games)} cached games")
```

### Searching by Tags
```python
# Find all model-related entries
model_entries = memory_manager.search_by_tags(['model', 'predictions'])

# Find specific agent data
agent_data = memory_manager.search_by_tags(['agent', 'cfbd'])
```

## 💡 Best Practices

### Memory Level Selection
- **Meta Agent**: Use only for data that must persist across sessions
- **Orchestrator**: Use for active workflows and coordination
- **Agent**: Use for task-specific context with short retention
- **Cache**: Use for frequently accessed temporary data

### Tagging Strategy
- Use descriptive, hierarchical tags: `['cfbd', 'api_response', 'week14']`
- Include data type: `['model', 'predictions']`, `['agent', 'context']`
- Add temporal tags: `['session_2025_01_18']`, `['backup_monthly']`

### Performance Optimization
- Monitor hit rates: Target >80% for frequently accessed data
- Set appropriate TTL values: Shorter for volatile data, longer for stable data
- Use compression for large entries (>1KB)
- Regular cleanup prevents memory bloat

### Error Handling
```python
try:
    data = memory_manager.retrieve('some_key')
    if data:
        # Process data
        pass
    else:
        # Handle cache miss
        pass
except Exception as e:
    # Handle retrieval errors
    logger.warning(f"Memory retrieval error: {e}")
```

## 📈 Performance Monitoring

### Key Metrics
- **Hit Rate**: Percentage of successful retrievals (>80% target)
- **Compression Ratio**: Space savings from compression (target: 0.5)
- **Memory Utilization**: Usage vs capacity at each level
- **Access Patterns**: Frequency and type of memory operations

### Monitoring Commands
```bash
# Check overall system health
/memory status --verbose

# Monitor specific level
/memory cache status
/memory agents status

# Performance optimization
/memory cache optimize
```

## 🔧 Configuration

### Memory Limits (configurable in `config/claude_code_optimization.json`)
```json
{
  "memory_hierarchy": {
    "level_1_meta_agent": {
      "max_size_mb": 100,
      "retention_days": 365
    },
    "level_4_cache": {
      "max_size_mb": 200,
      "ttl_minutes": {
        "cfbd_api_responses": 60,
        "model_predictions": 1440,
        "toon_outputs": 30
      }
    }
  }
}
```

### Custom TTL Values
- CFBD API responses: 60 minutes (matches data freshness)
- Model predictions: 24 hours (stable for session)
- TOON outputs: 30 minutes (temporary compression)
- Agent context: 60 minutes (task duration)
- System metrics: 24 hours (session-based)

## 🛠️ Advanced Features

### Memory Compression
- Automatic TOON format compression for structured data
- Generic compression for binary data
- Level-specific compression strategies
- Compression validation prevents data corruption

### Hierarchical Search
- Search across levels with priority ordering
- Tag-based filtering and Boolean logic
- Temporal search (by creation/expiration time)
- Agent-specific memory isolation

### Auto-Cleanup System
- Background cleanup every 60 seconds
- Expired entry removal
- Size-based eviction (LRU)
- Memory pressure monitoring

### Performance Optimization
- Intelligent load balancing across levels
- Access pattern analysis
- Cache warming for predictable access
- Memory defragmentation

## 🚨 Troubleshooting

### Common Issues

**Memory Pressure at Level 3 (Agents)**
```bash
# Check agent memory usage
/memory agents status

# Clean expired agent data
/memory agents cleanup --older=15m

# Balance memory across agents
/memory agents balance
```

**Low Cache Hit Rates**
```bash
# Check cache performance
/memory cache status

# Optimize TTL settings
/memory cache optimize

# Clear corrupted cache
/memory cache flush
```

**Performance Degradation**
```bash
# Run comprehensive cleanup
/memory cleanup

# Check system-wide metrics
/memory status --verbose

# Optimize all levels
/memory meta compress && /memory agents compress
```

### Recovery Procedures
```bash
# Emergency memory reset
rm -rf project_management/memory/cache/

# Restore from backups
/memory meta backup --restore

# Validate memory integrity
python3 -c "from agents.optimization.memory_manager import memory_manager; print(memory_manager.validate_integrity())"
```

## 📝 Examples and Use Cases

### CFBD API Caching
```python
# Cache API responses to avoid rate limits
def get_cfbd_games(week, season):
    cache_key = f'cfbd_games_{season}_week{week}'

    # Try cache first
    cached_data = memory_manager.retrieve(cache_key)
    if cached_data:
        return cached_data

    # Fetch from API
    games = cfbd_client.get_games(year=season, week=week)

    # Cache for 60 minutes
    memory_manager.store(
        key=cache_key,
        value=games,
        level=MemoryLevel.CACHE,
        expires_in=timedelta(hours=1),
        tags=['cfbd', 'games', f'week{week}', f'season{season}']
    )

    return games
```

### Agent Task Context
```python
# Track agent progress and context
def update_agent_context(agent_id, task_data):
    context_key = f'{agent_id}_context'

    # Get existing context
    existing_context = memory_manager.retrieve(context_key) or {}

    # Update with new data
    existing_context.update({
        'last_update': datetime.now().isoformat(),
        'current_task': task_data,
        'progress': task_data.get('progress', 0)
    })

    # Store with 45-minute TTL
    memory_manager.store(
        key=context_key,
        value=existing_context,
        level=MemoryLevel.AGENT,
        expires_in=timedelta(minutes=45),
        tags=['agent', agent_id, 'context']
    )
```

### System Performance Tracking
```python
# Store system metrics for monitoring
def track_system_performance():
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'cpu_usage': psutil.cpu_percent(),
        'memory_usage': psutil.virtual_memory().percent,
        'active_agents': len(get_active_agents()),
        'api_calls_today': get_api_call_count()
    }

    memory_manager.store(
        key=f'system_metrics_{int(time.time())}',
        value=metrics,
        level=MemoryLevel.META_AGENT,
        expires_in=timedelta(days=30),  # Keep for 30 days
        tags=['system', 'metrics', 'performance']
    )
```

## 🎯 Integration with Agent System

Your memory management system integrates seamlessly with your Super AI Agent Architecture:

### Meta Agent Integration
- Agent registry and lifecycle management
- System-wide performance monitoring
- Audit trail and compliance tracking

### Orchestrator Integration
- Active workflow state management
- Inter-agent coordination data
- Task queue and assignment tracking

### Agent Integration
- Individual agent context and state
- API usage tracking and rate limiting
- Intermediate result storage

### Cache Integration
- TOON format compressed outputs
- API response caching
- Model prediction storage

This memory management system provides the foundation for high-performance, scalable agent operations while maintaining data integrity and optimal resource utilization.