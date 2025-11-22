"""Tests for plan-to-workflow conversion functionality."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

# Add project root to path
import sys
import importlib.util
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    # Import plan_to_workflow as a module (scripts is not a package)
    plan_to_workflow_path = project_root / "scripts" / "plan_to_workflow.py"
    spec = importlib.util.spec_from_file_location("plan_to_workflow", plan_to_workflow_path)
    plan_to_workflow = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plan_to_workflow)
    
    parse_toon_plan = plan_to_workflow.parse_toon_plan
    parse_json_plan = plan_to_workflow.parse_json_plan
    parse_markdown_plan = plan_to_workflow.parse_markdown_plan
    validate_plan_structure = plan_to_workflow.validate_plan_structure
    convert_to_workflow_definition = plan_to_workflow.convert_to_workflow_definition
    
    from toon_format import encode, _check_toon_cli
except (ImportError, FileNotFoundError) as e:
    pytest.skip(f"Plan to workflow module not available: {e}", allow_module_level=True)


def check_toon_cli_available():
    """Check if TOON CLI is available via npx."""
    try:
        result = subprocess.run(
            ["npx", "@toon-format/cli", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


TOON_CLI_AVAILABLE = check_toon_cli_available()


@pytest.fixture
def sample_plan_data():
    """Sample plan data structure."""
    return {
        "metadata": {
            "title": "Test Plan",
            "objective": "Test objective",
            "version": "1.0"
        },
        "tasks": [
            {
                "id": "task_1",
                "name": "Task 1",
                "description": "First task",
                "steps": ["step_1"],
                "dependencies": [],
                "agent_type": "model_engine",
                "tools_required": [],
                "estimated_time": 5.0
            }
        ],
        "steps": [
            {
                "id": "step_1",
                "task_id": "task_1",
                "action": "run_prediction",
                "parameters": {},
                "step_type": "AGENT_EXECUTION",
                "timeout": 30,
                "dependencies": [],
                "retry_count": 3
            }
        ],
        "shared_inputs": {},
        "workflow_config": {
            "parallel_execution": False,
            "error_recovery": True,
            "max_retries": 3
        }
    }


@pytest.fixture
def sample_markdown_plan():
    """Sample markdown plan content."""
    return """# Test Plan

## Objective
Test objective

## Tasks

### Task 1: Task 1
- **ID**: task_1
- **Description**: First task
- **Agent**: model_engine
- **Steps**: step_1
- **Dependencies**: []
- **Estimated Time**: 5.0s

## Steps

### Step 1: Run Prediction
- **ID**: step_1
- **Task**: task_1
- **Action**: run_prediction
- **Type**: AGENT_EXECUTION
- **Parameters**: {}
- **Timeout**: 30s
- **Dependencies**: []

## Shared Inputs
{}

## Workflow Config
- Parallel Execution: false
- Error Recovery: true
- Max Retries: 3
"""


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for test files."""
    return tmp_path


class TestJSONPlanParsing:
    """Tests for JSON plan parsing."""
    
    def test_parse_valid_json_plan(self, sample_plan_data, temp_dir):
        """Test parsing valid JSON plan."""
        json_file = temp_dir / "plan.json"
        with open(json_file, 'w') as f:
            json.dump(sample_plan_data, f)
        
        parsed = parse_json_plan(json_file)
        assert parsed["metadata"]["title"] == "Test Plan"
        assert len(parsed["tasks"]) == 1
        assert len(parsed["steps"]) == 1
    
    def test_parse_json_plan_not_found(self, temp_dir):
        """Test parsing non-existent JSON plan raises error."""
        missing_file = temp_dir / "missing.json"
        with pytest.raises(FileNotFoundError):
            parse_json_plan(missing_file)
    
    def test_parse_invalid_json_plan(self, temp_dir):
        """Test parsing invalid JSON raises error."""
        invalid_file = temp_dir / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        with pytest.raises(RuntimeError, match="Failed to parse JSON"):
            parse_json_plan(invalid_file)


@pytest.mark.skipif(not TOON_CLI_AVAILABLE, reason="TOON CLI not available")
class TestTOONPlanParsing:
    """Tests for TOON plan parsing."""
    
    def test_parse_valid_toon_plan(self, sample_plan_data, temp_dir):
        """Test parsing valid TOON plan."""
        # Create TOON file
        toon_content = encode(sample_plan_data)
        toon_file = temp_dir / "plan.toon"
        toon_file.write_text(toon_content)
        
        parsed = parse_toon_plan(toon_file)
        assert parsed["metadata"]["title"] == "Test Plan"
        assert len(parsed["tasks"]) == 1
    
    def test_parse_toon_plan_not_found(self, temp_dir):
        """Test parsing non-existent TOON plan raises error."""
        missing_file = temp_dir / "missing.toon"
        with pytest.raises(FileNotFoundError):
            parse_toon_plan(missing_file)


class TestMarkdownPlanParsing:
    """Tests for markdown plan parsing."""
    
    def test_parse_valid_markdown_plan(self, sample_markdown_plan, temp_dir):
        """Test parsing valid markdown plan."""
        md_file = temp_dir / "plan.md"
        md_file.write_text(sample_markdown_plan)
        
        parsed = parse_markdown_plan(md_file)
        assert parsed["metadata"]["title"] == "Test Plan"
        assert parsed["metadata"]["objective"] == "Test objective"
        assert len(parsed["tasks"]) == 1
        assert len(parsed["steps"]) == 1
        assert parsed["tasks"][0]["id"] == "task_1"
        assert parsed["steps"][0]["id"] == "step_1"
    
    def test_parse_markdown_plan_not_found(self, temp_dir):
        """Test parsing non-existent markdown plan raises error."""
        missing_file = temp_dir / "missing.md"
        with pytest.raises(FileNotFoundError):
            parse_markdown_plan(missing_file)
    
    def test_parse_markdown_with_multiple_tasks(self, temp_dir):
        """Test parsing markdown with multiple tasks."""
        md_content = """# Multi-Task Plan

## Objective
Test multiple tasks

## Tasks

### Task 1: First Task
- **ID**: task_1
- **Description**: First task
- **Agent**: model_engine
- **Steps**: step_1
- **Dependencies**: []
- **Estimated Time**: 5.0s

### Task 2: Second Task
- **ID**: task_2
- **Description**: Second task
- **Agent**: insight_generator
- **Steps**: step_2
- **Dependencies**: [task_1]
- **Estimated Time**: 10.0s

## Steps

### Step 1: Action 1
- **ID**: step_1
- **Task**: task_1
- **Action**: run_prediction
- **Type**: AGENT_EXECUTION
- **Timeout**: 30s
- **Dependencies**: []

### Step 2: Action 2
- **ID**: step_2
- **Task**: task_2
- **Action**: generate_analysis
- **Type**: ANALYSIS
- **Timeout**: 60s
- **Dependencies**: [step_1]
"""
        md_file = temp_dir / "multi_task.md"
        md_file.write_text(md_content)
        
        parsed = parse_markdown_plan(md_file)
        assert len(parsed["tasks"]) == 2
        assert len(parsed["steps"]) == 2
        assert parsed["tasks"][1]["dependencies"] == ["task_1"]
        assert parsed["steps"][1]["dependencies"] == ["step_1"]


class TestPlanValidation:
    """Tests for plan structure validation."""
    
    def test_validate_valid_plan(self, sample_plan_data):
        """Test validation of valid plan."""
        result = validate_plan_structure(sample_plan_data)
        assert result is True
    
    def test_validate_missing_metadata(self):
        """Test validation fails with missing metadata."""
        invalid_plan = {
            "tasks": [],
            "steps": []
        }
        with pytest.raises(ValueError, match="Missing required key"):
            validate_plan_structure(invalid_plan)
    
    def test_validate_missing_title_objective(self):
        """Test validation fails with missing title/objective."""
        invalid_plan = {
            "metadata": {},
            "tasks": [],
            "steps": []
        }
        with pytest.raises(ValueError, match="must contain 'title' and 'objective'"):
            validate_plan_structure(invalid_plan)
    
    def test_validate_empty_tasks(self):
        """Test validation fails with empty tasks."""
        invalid_plan = {
            "metadata": {"title": "Test", "objective": "Test"},
            "tasks": [],
            "steps": []
        }
        with pytest.raises(ValueError, match="tasks array cannot be empty"):
            validate_plan_structure(invalid_plan)
    
    def test_validate_non_uniform_tasks(self):
        """Test validation fails with non-uniform task structure."""
        invalid_plan = {
            "metadata": {"title": "Test", "objective": "Test"},
            "tasks": [
                {"id": "task_1", "name": "Task 1", "agent": "model"},
                {"id": "task_2", "name": "Task 2"}  # Missing 'agent'
            ],
            "steps": []
        }
        with pytest.raises(ValueError, match="inconsistent structure"):
            validate_plan_structure(invalid_plan)
    
    def test_validate_invalid_step_reference(self):
        """Test validation fails with invalid step task_id reference."""
        invalid_plan = {
            "metadata": {"title": "Test", "objective": "Test"},
            "tasks": [
                {"id": "task_1", "name": "Task 1", "agent": "model"}
            ],
            "steps": [
                {"id": "step_1", "task_id": "invalid_task", "action": "test"}
            ]
        }
        with pytest.raises(ValueError, match="references invalid task_id"):
            validate_plan_structure(invalid_plan)
    
    def test_validate_duplicate_step_id(self):
        """Test validation fails with duplicate step IDs."""
        invalid_plan = {
            "metadata": {"title": "Test", "objective": "Test"},
            "tasks": [
                {"id": "task_1", "name": "Task 1", "agent": "model"}
            ],
            "steps": [
                {"id": "step_1", "task_id": "task_1", "action": "test"},
                {"id": "step_1", "task_id": "task_1", "action": "test2"}  # Duplicate
            ]
        }
        with pytest.raises(ValueError, match="Duplicate step ID"):
            validate_plan_structure(invalid_plan)


class TestWorkflowConversion:
    """Tests for workflow definition conversion."""
    
    def test_convert_to_workflow_definition(self, sample_plan_data):
        """Test conversion of plan to workflow definition."""
        workflow_def = convert_to_workflow_definition(sample_plan_data)
        
        assert "workflow_id" in workflow_def
        assert "name" in workflow_def
        assert "description" in workflow_def
        assert "steps" in workflow_def
        assert len(workflow_def["steps"]) == 1
        assert workflow_def["name"] == "Test Plan"
        assert workflow_def["description"] == "Test objective"
    
    def test_convert_workflow_step_types(self, sample_plan_data):
        """Test conversion with different step types."""
        sample_plan_data["steps"] = [
            {
                "id": "step_1",
                "task_id": "task_1",
                "action": "test",
                "step_type": "DATA_PROCESSING",
                "timeout": 60,
                "dependencies": [],
                "retry_count": 2
            }
        ]
        
        workflow_def = convert_to_workflow_definition(sample_plan_data)
        step = workflow_def["steps"][0]
        assert step.step_type.value == "data_processing"  # Enum values are lowercase
        assert step.timeout == 60
        assert step.retry_count == 2
    
    def test_convert_workflow_metadata(self, sample_plan_data):
        """Test conversion includes workflow metadata."""
        sample_plan_data["workflow_config"] = {
            "parallel_execution": True,
            "error_recovery": False,
            "max_retries": 5
        }
        
        workflow_def = convert_to_workflow_definition(sample_plan_data)
        metadata = workflow_def["metadata"]
        assert metadata["parallel_execution"] is True
        assert metadata["error_recovery"] is False
        assert metadata["max_retries"] == 5
    
    def test_convert_workflow_shared_inputs(self, sample_plan_data):
        """Test conversion includes shared inputs."""
        sample_plan_data["shared_inputs"] = {
            "season": 2025,
            "week": 8
        }
        
        workflow_def = convert_to_workflow_definition(sample_plan_data)
        assert workflow_def["shared_inputs"]["season"] == 2025
        assert workflow_def["shared_inputs"]["week"] == 8

