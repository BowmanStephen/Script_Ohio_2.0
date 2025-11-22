# API Reference

## ActivationFixOrchestrator

### Constructor
```python
ActivationFixOrchestrator(agent_id: str)
```

### Methods

#### execute_workflow()
Execute the complete activation fix workflow.

**Parameters:**
- `parameters`: Dictionary containing workflow configuration

**Returns:**
Dictionary containing workflow results

## Agent Classes

### SyntaxCorrectorAgent
Fixes PATH quoting issues in activation scripts.

**Capabilities:**
- `fix_bash_activate`: Fix bash/zsh activation script
- `fix_csh_activate`: Fix csh/tcsh activation script
- `fix_fish_activate`: Fix fish activation script

### ShellTesterAgent
Validates activation across different shell environments.

**Capabilities:**
- `test_bash_activation`: Test bash/zsh activation
- `test_csh_activation`: Test csh/tcsh activation
- `test_fish_activation`: Test fish activation

*Generated: 2025-11-14 00:56:38*
