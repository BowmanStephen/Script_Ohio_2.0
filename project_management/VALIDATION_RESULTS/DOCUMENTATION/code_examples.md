# Activation Fix System Code Examples

## Example 1: Basic Usage
```python
#!/usr/bin/env python3
from agents.activation_fix.activation_fix_orchestrator import ActivationFixOrchestrator

def main():
    orchestrator = ActivationFixOrchestrator()
    result = orchestrator.execute_workflow({
        "role": "admin",
        "user_id": "example_user"
    })

    if result["status"] == "success":
        print("✅ Activation fix completed!")
        print(f"Phases completed: {result['phases_completed']}")
    else:
        print("❌ Activation fix failed")

if __name__ == "__main__":
    main()
```

## Example 2: Custom Configuration
```python
#!/usr/bin/env python3
from agents.activation_fix.activation_fix_orchestrator import ActivationFixOrchestrator

def advanced_example():
    config = {
        "role": "admin",
        "user_id": "advanced_user",
        "shell_targets": ["bash", "zsh", "fish"],
        "rollback_on_failure": True,
        "create_backup": True,
        "monitoring_enabled": True
    }

    orchestrator = ActivationFixOrchestrator()
    result = orchestrator.execute_workflow(config)

    return result

if __name__ == "__main__":
    advanced_example()
```

*Generated: 2025-11-14 00:53:09*
