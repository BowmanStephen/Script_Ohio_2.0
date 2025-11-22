<!-- 7c971037-c0f1-4d44-81cf-bc545de30d4a de04067b-bb0a-4753-91b8-537701761071 -->
# Agent Documentation Generator - Implementation Plan

## Objective

Create an automated documentation system that extracts agent capabilities from Python code, generates comprehensive documentation, validates consistency, and maintains a capability registry for the orchestrator.

## Metadata

- **Title**: Agent Documentation Generator
- **Objective**: Automate agent capability documentation extraction, generation, and validation
- **Created**: 2025-11-19
- **Version**: 1.0

## Tasks

### Task 1: Build Agent Scanner

- **ID**: task_1
- **Name**: Build Agent Scanner
- **Description**: Create AST-based scanner to find BaseAgent subclasses and extract capability metadata from Python agent files
- **Agent**: workflow_automator
- **Steps**: step_1, step_2, step_3
- **Dependencies**: []
- **Tools Required**: []
- **Estimated Time**: 8.0

### Task 2: Generate Documentation

- **ID**: task_2
- **Name**: Generate Documentation
- **Description**: Generate markdown documentation from scanned agent metadata, update AGENTS.md cheat sheet, create individual agent docs
- **Agent**: workflow_automator
- **Steps**: step_4, step_5, step_6
- **Dependencies**: [task_1]
- **Tools Required**: []
- **Estimated Time**: 6.0

### Task 3: Create Capability Registry

- **ID**: task_3
- **Name**: Create Capability Registry
- **Description**: Generate machine-readable JSON registry and routing matrix for orchestrator use
- **Agent**: workflow_automator
- **Steps**: step_7, step_8
- **Dependencies**: [task_1]
- **Tools Required**: []
- **Estimated Time**: 4.0

### Task 4: Implement Validator

- **ID**: task_4
- **Name**: Implement Validator
- **Description**: Build consistency validator to check code-doc sync, capability implementations, and tool references
- **Agent**: workflow_automator
- **Steps**: step_9, step_10
- **Dependencies**: [task_1, task_2]
- **Tools Required**: []
- **Estimated Time**: 5.0

### Task 5: Extract Usage Examples

- **ID**: task_5
- **Name**: Extract Usage Examples
- **Description**: Parse test files to extract usage examples and integrate into individual agent documentation
- **Agent**: workflow_automator
- **Steps**: step_11
- **Dependencies**: [task_2]
- **Tools Required**: []
- **Estimated Time**: 3.0

### Task 6: Create CLI Interface

- **ID**: task_6
- **Name**: Create CLI Interface
- **Description**: Build CLI with --update, --validate, --output flags and proper error handling
- **Agent**: workflow_automator
- **Steps**: step_12
- **Dependencies**: [task_2, task_4]
- **Tools Required**: []
- **Estimated Time**: 2.0

## Steps

### Step 1: Build AST Parser

- **ID**: step_1
- **Task**: task_1
- **Action**: build_ast_parser
- **Type**: CODE_ANALYSIS
- **Parameters**: {"target_dir": "agents/", "base_class": "BaseAgent"}
- **Timeout**: 60
- **Dependencies**: []

### Step 2: Implement Dynamic Import

- **ID**: step_2
- **Task**: task_1
- **Action**: implement_dynamic_import
- **Type**: CODE_ANALYSIS
- **Parameters**: {"method": "_define_capabilities", "handle_edge_cases": true}
- **Timeout**: 120
- **Dependencies**: [step_1]

### Step 3: Extract Agent Metadata

- **ID**: step_3
- **Task**: task_1
- **Action**: extract_agent_metadata
- **Type**: DATA_PROCESSING
- **Parameters**: {"output_format": "dict", "include_registration": true}
- **Timeout**: 90
- **Dependencies**: [step_2]

### Step 4: Update AGENTS.md Cheat Sheet

- **ID**: step_4
- **Task**: task_2
- **Action**: update_agents_md
- **Type**: DOCUMENTATION
- **Parameters**: {"target_file": "AGENTS.md", "preserve_content": true, "lines": "30-41"}
- **Timeout**: 60
- **Dependencies**: [step_3]

### Step 5: Generate Individual Agent Docs

- **ID**: step_5
- **Task**: task_2
- **Action**: generate_agent_docs
- **Type**: DOCUMENTATION
- **Parameters**: {"output_dir": "docs/agents/", "template": "agent_doc_template.md"}
- **Timeout**: 120
- **Dependencies**: [step_3]

### Step 6: Create Capability Index

- **ID**: step_6
- **Task**: task_2
- **Action**: create_capability_index
- **Type**: DOCUMENTATION
- **Parameters**: {"output_file": "docs/agents/CAPABILITY_INDEX.md"}
- **Timeout**: 60
- **Dependencies**: [step_3]

### Step 7: Generate Capability Registry JSON

- **ID**: step_7
- **Task**: task_3
- **Action**: generate_capability_registry
- **Type**: DATA_PROCESSING
- **Parameters**: {"output_file": "docs/agents/capability_registry.json", "format": "json"}
- **Timeout**: 60
- **Dependencies**: [step_3]

### Step 8: Create Routing Matrix

- **ID**: step_8
- **Task**: task_3
- **Action**: create_routing_matrix
- **Type**: DATA_PROCESSING
- **Parameters**: {"output_file": "docs/agents/routing_matrix.json", "map_query_to_agent": true}
- **Timeout**: 60
- **Dependencies**: [step_3]

### Step 9: Implement Code Validation

- **ID**: step_9
- **Task**: task_4
- **Action**: implement_code_validation
- **Type**: CODE_ANALYSIS
- **Parameters**: {"check_implementations": true, "check_permissions": true, "check_tools": true}
- **Timeout**: 120
- **Dependencies**: [step_3]

### Step 10: Implement Documentation Validation

- **ID**: step_10
- **Task**: task_4
- **Action**: implement_doc_validation
- **Type**: CODE_ANALYSIS
- **Parameters**: {"check_agents_md": true, "check_individual_docs": true, "check_descriptions": true}
- **Timeout**: 90
- **Dependencies**: [step_4, step_5]

### Step 11: Extract Test Examples

- **ID**: step_11
- **Task**: task_5
- **Action**: extract_test_examples
- **Type**: CODE_ANALYSIS
- **Parameters**: {"test_dir": "agents/tests/", "integrate_into_docs": true}
- **Timeout**: 120
- **Dependencies**: [step_5]

### Step 12: Build CLI Interface

- **ID**: step_12
- **Task**: task_6
- **Action**: build_cli_interface
- **Type**: CODE_ANALYSIS
- **Parameters**: {"flags": ["--update", "--validate", "--output"], "error_handling": true}
- **Timeout**: 90
- **Dependencies**: [step_4, step_9, step_10]

## Shared Inputs

- **agent_files_dir**: "agents/"
- **output_docs_dir**: "docs/agents/"
- **agents_md_path**: "AGENTS.md"
- **orchestrator_path**: "agents/analytics_orchestrator.py"

## Workflow Config

- **Parallel Execution**: false
- **Error Recovery**: true
- **Max Retries**: 3

## Current State Analysis

### Existing Structure

- **Agent Classes**: 19+ agent files in `agents/` directory, all inherit from `BaseAgent`
- **Capability Definition**: Each agent implements `_define_capabilities()` returning `List[AgentCapability]`
- **Registration**: Agents registered in `analytics_orchestrator.py` via `AgentFactory.register_agent_class()`
- **Documentation**: Manual `AGENTS.md` with cheat sheet table (lines 30-41)
- **Tests**: Capability validation in `agents/tests/` (e.g., `test_learning_navigator_agent.py`)
- **Tools**: Tool loader system in `agents/core/tool_loader.py` with tool metadata

### Key Components to Leverage

- `AgentCapability` dataclass (name, description, permission_required, tools_required, data_access, execution_time_estimate)
- `BaseAgent` framework with `_define_capabilities()` abstract method
- `AgentFactory` registration system
- `RequestRouter` that uses capabilities for routing

## Implementation Details

### Component 1: Agent Scanner (`scripts/generate_agent_docs.py`)

**Purpose**: Parse Python agent files and extract capability metadata

**Implementation**:

- Use AST parsing to find all classes inheriting from `BaseAgent`
- Import agent modules dynamically to access `_define_capabilities()`
- Extract metadata:
  - Class name, docstring, file path
  - Permission level from `__init__`
  - All capabilities from `_define_capabilities()`
  - Agent type mapping (from `analytics_orchestrator.py` registration)
- Handle edge cases:
  - Agents with constructor parameters (weekly agents, CFBD agents)
  - Conditional capabilities (GraphQL capabilities in CFBD agent)
  - Deprecated agents in `archive/`

**Output**: `Dict[str, AgentMetadata]` where key is agent_type

**Files to create**:

- `scripts/generate_agent_docs.py` - Main scanner script
- `scripts/agent_doc_utils.py` - Utility functions for parsing

### Component 2: Documentation Generator

**Purpose**: Generate markdown documentation from scanned agent metadata

**Implementation**:

- **Update AGENTS.md cheat sheet** (lines 30-41):
  - Auto-generate table rows from capability data
  - Preserve existing structure and formatting
  - Sort agents alphabetically
  - Include all capabilities in "Key Actions" column
- **Generate individual agent docs**:
  - Create `docs/agents/[agent_name].md` for each agent
  - Include: purpose, capabilities table, permission level, usage examples
  - Link to source code
- **Create capability index**:
  - `docs/agents/CAPABILITY_INDEX.md` - All capabilities across all agents
  - Grouped by capability name with agent references

**Files to modify**:

- `AGENTS.md` - Update cheat sheet section (preserve other content)
- `docs/agents/` - New directory for individual agent docs

**Files to create**:

- `docs/agents/README.md` - Index of all agent documentation
- `docs/agents/CAPABILITY_INDEX.md` - Cross-reference of capabilities

### Component 3: Capability Registry Generator

**Purpose**: Create machine-readable JSON registry for orchestrator use

**Implementation**:

- Generate `docs/agents/capability_registry.json`:
  ```json
  {
    "agent_types": {
      "insight_generator": {
        "class": "InsightGeneratorAgent",
        "permission_level": "READ_EXECUTE_WRITE",
        "capabilities": {
          "generate_analysis": {
            "description": "...",
            "tools_required": [...],
            "data_access": [...],
            "execution_time_estimate": 3.0
          }
        }
      }
    },
    "capability_index": {
      "generate_analysis": ["insight_generator"],
      "run_prediction": ["model_engine"]
    }
  }
  ```

- Generate `docs/agents/routing_matrix.json`:
  - Maps query_type + action → agent_type
  - Used by orchestrator for intelligent routing

**Files to create**:

- `docs/agents/capability_registry.json`
- `docs/agents/routing_matrix.json`

### Component 4: Consistency Validator

**Purpose**: Validate code and documentation stay in sync

**Implementation**:

- **Code validation**:
  - Verify all capabilities in `_define_capabilities()` have implementations in `_execute_action()`
  - Check capability names match between definition and execution
  - Validate permission levels are consistent
- **Documentation validation**:
  - Verify AGENTS.md cheat sheet matches scanned capabilities
  - Check all registered agents have documentation
  - Validate capability descriptions are non-empty
- **Tool validation**:
  - Verify `tools_required` in capabilities exist in tool_loader
  - Check data_access paths are valid
- **Registration validation**:
  - Verify all agents in `analytics_orchestrator.py` are scanned
  - Check agent_type mappings are consistent

**Output**: Validation report with warnings and errors

**Files to create**:

- `scripts/validate_agent_docs.py` - Validation script
- `docs/agents/validation_report.json` - Latest validation results

### Component 5: Usage Example Extractor

**Purpose**: Extract usage examples from test files

**Implementation**:

- Parse test files in `agents/tests/`
- Extract test functions that demonstrate agent usage
- Generate code examples for each capability:
  - From `test_learning_navigator_agent.py` → learning navigator examples
  - From orchestrator demos → full workflow examples
- Include in individual agent docs

**Files to modify**:

- Individual agent docs in `docs/agents/` - Add usage examples section

## Integration Points

### With Orchestrator

- **Capability Registry**: Load `capability_registry.json` for routing decisions
- **Validation**: Run validator before orchestrator startup (optional)
- **Auto-update**: Hook into agent registration to trigger doc generation

### With CI/CD

- **Pre-commit hook**: Validate docs before commit
- **CI check**: Fail build if docs are out of sync
- **Auto-generation**: Generate docs on agent changes

### With Development Workflow

- **CLI command**: `python scripts/generate_agent_docs.py --update`
- **Watch mode**: Auto-regenerate on agent file changes (optional)
- **Validation**: `python scripts/validate_agent_docs.py` before PR

## File Structure

```
scripts/
  generate_agent_docs.py      # Main documentation generator
  agent_doc_utils.py          # Parsing utilities
  validate_agent_docs.py      # Consistency validator

docs/
  agents/
    README.md                 # Index of agent documentation
    CAPABILITY_INDEX.md        # Cross-reference of all capabilities
    capability_registry.json # Machine-readable capability data
    routing_matrix.json       # Query type → agent mapping
    validation_report.json    # Latest validation results
    learning_navigator.md     # Individual agent docs
    model_engine.md
    insight_generator.md
    # ... one per agent

AGENTS.md                     # Updated cheat sheet (preserve other content)
```

## Implementation Phases

### Phase 1: Core Scanner (Week 1)

1. Build AST parser to find BaseAgent subclasses
2. Implement dynamic import and capability extraction
3. Handle edge cases (weekly agents, conditional capabilities)
4. Generate basic agent metadata structure
5. Test with all 19+ agent files

### Phase 2: Documentation Generation (Week 1)

1. Implement AGENTS.md cheat sheet updater
2. Create individual agent doc templates
3. Generate capability index
4. Preserve existing AGENTS.md content (non-cheat-sheet sections)

### Phase 3: Registry & Validation (Week 2)

1. Generate JSON capability registry
2. Create routing matrix
3. Implement consistency validator
4. Add validation report generation

### Phase 4: Integration & Polish (Week 2)

1. Extract usage examples from tests
2. Add CLI interface with flags
3. Create pre-commit hook
4. Update project documentation

## Technical Considerations

### Parsing Strategy

- **AST for structure**: Find class definitions, inheritance
- **Dynamic import for capabilities**: Actually instantiate agents to get `_define_capabilities()`
- **Fallback for complex constructors**: Use mock parameters for weekly/CFBD agents

### Error Handling

- **Graceful degradation**: Continue if one agent fails to parse
- **Clear error messages**: Report which agent/file failed
- **Validation warnings**: Non-blocking warnings for minor issues

### Performance

- **Caching**: Cache parsed agent metadata
- **Incremental updates**: Only regenerate changed agents
- **Parallel parsing**: Parse multiple agents concurrently

### Backward Compatibility

- **Preserve AGENTS.md structure**: Only update cheat sheet section
- **Support deprecated agents**: Mark but don't fail on archive/ agents
- **Version metadata**: Track doc generation version

## Success Criteria

1. **Automated Updates**: AGENTS.md cheat sheet auto-updates from code
2. **Complete Coverage**: All registered agents have documentation
3. **Validation**: Consistency checks catch code-doc drift
4. **Usability**: Generated docs are clear and useful
5. **Maintainability**: System is easy to extend for new agents

## Testing Strategy

1. **Unit tests**: Test scanner on individual agent files
2. **Integration tests**: Test full doc generation pipeline
3. **Validation tests**: Verify validator catches known issues
4. **Regression tests**: Ensure existing docs aren't broken

## Dependencies

- **Python AST module**: Built-in, no external deps
- **Existing agent framework**: Leverage BaseAgent, AgentCapability
- **Markdown generation**: Use string templates (no external lib needed)
- **JSON output**: Built-in json module

## Future Enhancements (Out of Scope)

- Interactive capability explorer (HTML)
- TOON format capability registry
- Agent dependency graph visualization
- Performance metrics integration
- Auto-generated API docs from capabilities

### To-dos

- [ ] Build core agent scanner using AST to find BaseAgent subclasses and extract class metadata (name, docstring, file path)
- [ ] Implement dynamic import and capability extraction from _define_capabilities() method, handling edge cases (weekly agents, conditional capabilities)
- [ ] Parse analytics_orchestrator.py to extract agent_type mappings from register_agent_class() calls
- [ ] Implement AGENTS.md cheat sheet updater that preserves existing content and auto-generates table rows from capability data
- [ ] Create individual agent doc generator with templates for purpose, capabilities table, permission level, and usage examples
- [ ] Generate capability index (CAPABILITY_INDEX.md) cross-referencing all capabilities across agents
- [ ] Generate machine-readable capability_registry.json and routing_matrix.json for orchestrator use
- [ ] Implement code validation: verify capabilities have implementations, check permission consistency, validate tool/data_access references
- [ ] Implement documentation validation: verify AGENTS.md matches scanned data, check all agents have docs, validate descriptions
- [ ] Extract usage examples from test files and integrate into individual agent documentation
- [ ] Create CLI interface with --update, --validate, --output flags and proper error handling
- [ ] Test full pipeline on all 19+ agent files, verify output quality, and ensure backward compatibility with existing AGENTS.md