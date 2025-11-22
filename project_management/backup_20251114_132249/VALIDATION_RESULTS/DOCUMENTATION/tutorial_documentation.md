# Activation Fix System Tutorial

## Getting Started

### Basic Usage
```python
from agents.activation_fix.activation_fix_orchestrator import ActivationFixOrchestrator

# Initialize orchestrator
orchestrator = ActivationFixOrchestrator()

# Execute workflow
result = orchestrator.execute_workflow({
    "role": "admin",
    "user_id": "your_user_id"
})
```

### Advanced Configuration
```python
# Advanced configuration
config = {
    "role": "admin",
    "user_id": "advanced_user",
    "shell_targets": ["bash", "zsh", "fish"],
    "rollback_on_failure": True,
    "create_backup": True
}

result = orchestrator.execute_workflow(config)
```

## Troubleshooting

### Common Issues
1. **Permission Errors**: Ensure adequate file permissions
2. **Shell Compatibility**: Verify target shell is installed
3. **Virtual Environment**: Check venv exists and is accessible

### Debug Mode
```python
# Enable debug logging
orchestrator = ActivationFixOrchestrator(debug=True)
```

*Generated: 2025-11-14 00:53:09*
