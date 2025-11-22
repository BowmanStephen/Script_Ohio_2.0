# Learning Navigator

**Type**: `learning_navigator`
**Permission Level**: `READ_EXECUTE`
**Source**: [`agents/core/agent_framework.py`](../../agents/core/agent_framework.py)

## Description

Agent for educational guidance and learning path navigation

## Capabilities

| Capability | Description | Permissions | Tools | Est. Time |
| --- | --- | --- | --- | --- |
| `guide_learning_path` | Guide users through starter pack notebooks | READ_EXECUTE | `notebook_loader`, `progress_tracker` | 2.0s |
| `recommend_content` | Recommend content based on user skill level | READ_EXECUTE | `content_analyzer`, `user_profiler` | 1.5s |

## Usage Examples

### Example 1

```python
agent = LearningNavigatorAgent(agent_id="pytest_learning")
```

