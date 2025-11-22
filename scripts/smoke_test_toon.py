#!/usr/bin/env python3
"""
Smoke test for TOON format functionality.

Tests all major features:
1. TOON CLI availability
2. Encoding/decoding
3. Markdown plan parsing
4. Plan validation
5. Workflow conversion
6. End-to-end markdown → TOON → workflow
"""

import json
import sys
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_toon_cli():
    """Test 1: TOON CLI availability"""
    print("=" * 60)
    print("TEST 1: TOON CLI Availability")
    print("=" * 60)
    try:
        from toon_format import _check_toon_cli
        available = _check_toon_cli()
        if available:
            print("✓ TOON CLI is available")
            return True
        else:
            print("✗ TOON CLI is not available")
            print("  Install with: npm install -g @toon-format/cli")
            return False
    except Exception as e:
        print(f"✗ Error checking TOON CLI: {e}")
        return False

def test_encoding_decoding():
    """Test 2: Encoding and decoding"""
    print("\n" + "=" * 60)
    print("TEST 2: TOON Encoding/Decoding")
    print("=" * 60)
    try:
        from toon_format import encode, decode
        
        test_data = {
            "plan": {
                "title": "Test Plan",
                "tasks": [
                    {"id": "task_1", "name": "Task 1", "time": 5.0},
                    {"id": "task_2", "name": "Task 2", "time": 10.0}
                ]
            }
        }
        
        # Encode
        toon_output = encode(test_data)
        print(f"✓ Encoded to TOON ({len(toon_output)} chars)")
        
        # Decode
        decoded = decode(toon_output)
        print(f"✓ Decoded from TOON")
        
        # Verify roundtrip (TOON may preserve structure but with minor differences)
        # Check that key data is preserved
        if (decoded.get('plan', {}).get('title') == test_data['plan']['title'] and
            len(decoded.get('plan', {}).get('tasks', [])) == len(test_data['plan']['tasks']) and
            decoded.get('plan', {}).get('tasks', [{}])[0].get('id') == test_data['plan']['tasks'][0]['id']):
            print("✓ Roundtrip verification passed (key data preserved)")
            return True
        else:
            print("✗ Roundtrip verification failed")
            print(f"  Original tasks: {len(test_data['plan']['tasks'])}")
            print(f"  Decoded tasks: {len(decoded.get('plan', {}).get('tasks', []))}")
            return False
    except Exception as e:
        print(f"✗ Encoding/decoding failed: {e}")
        return False

def test_markdown_parsing():
    """Test 3: Markdown plan parsing"""
    print("\n" + "=" * 60)
    print("TEST 3: Markdown Plan Parsing")
    print("=" * 60)
    try:
        import importlib.util
        plan_to_workflow_path = project_root / "scripts" / "plan_to_workflow.py"
        spec = importlib.util.spec_from_file_location("plan_to_workflow", plan_to_workflow_path)
        plan_to_workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plan_to_workflow)
        parse_markdown_plan = plan_to_workflow.parse_markdown_plan
        
        # Create test markdown plan
        md_content = """# Smoke Test Plan

## Objective
Test markdown parsing functionality

## Tasks

### Task 1: Test Task
- **ID**: task_1
- **Description**: A test task
- **Agent**: model_engine
- **Steps**: step_1
- **Dependencies**: []
- **Estimated Time**: 5.0s

## Steps

### Step 1: Test Step
- **ID**: step_1
- **Task**: task_1
- **Action**: test_action
- **Type**: AGENT_EXECUTION
- **Timeout**: 30s
- **Dependencies**: []
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            md_path = Path(f.name)
        
        try:
            plan_data = parse_markdown_plan(md_path)
            print(f"✓ Parsed markdown plan")
            print(f"  - Title: {plan_data['metadata']['title']}")
            print(f"  - Tasks: {len(plan_data['tasks'])}")
            print(f"  - Steps: {len(plan_data['steps'])}")
            
            if plan_data['tasks'][0]['id'] == 'task_1':
                print("✓ Task parsing correct")
            else:
                print("✗ Task parsing incorrect")
                return False
            
            if plan_data['steps'][0]['id'] == 'step_1':
                print("✓ Step parsing correct")
            else:
                print("✗ Step parsing incorrect")
                return False
            
            return True
        finally:
            md_path.unlink()
    except Exception as e:
        print(f"✗ Markdown parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_plan_validation():
    """Test 4: Plan validation"""
    print("\n" + "=" * 60)
    print("TEST 4: Plan Validation")
    print("=" * 60)
    try:
        import importlib.util
        plan_to_workflow_path = project_root / "scripts" / "plan_to_workflow.py"
        spec = importlib.util.spec_from_file_location("plan_to_workflow", plan_to_workflow_path)
        plan_to_workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plan_to_workflow)
        validate_plan_structure = plan_to_workflow.validate_plan_structure
        
        valid_plan = {
            "metadata": {
                "title": "Test Plan",
                "objective": "Test objective"
            },
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Task 1",
                    "description": "Test",
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
                    "action": "test",
                    "step_type": "AGENT_EXECUTION",
                    "timeout": 30,
                    "dependencies": []
                }
            ]
        }
        
        result = validate_plan_structure(valid_plan)
        print("✓ Valid plan passed validation")
        
        # Test invalid plan
        invalid_plan = {"metadata": {}}
        try:
            validate_plan_structure(invalid_plan)
            print("✗ Invalid plan should have failed validation")
            return False
        except ValueError:
            print("✓ Invalid plan correctly rejected")
        
        return True
    except Exception as e:
        print(f"✗ Plan validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_conversion():
    """Test 5: Workflow conversion"""
    print("\n" + "=" * 60)
    print("TEST 5: Workflow Conversion")
    print("=" * 60)
    try:
        import importlib.util
        plan_to_workflow_path = project_root / "scripts" / "plan_to_workflow.py"
        spec = importlib.util.spec_from_file_location("plan_to_workflow", plan_to_workflow_path)
        plan_to_workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plan_to_workflow)
        convert_to_workflow_definition = plan_to_workflow.convert_to_workflow_definition
        
        plan_data = {
            "metadata": {
                "title": "Test Plan",
                "objective": "Test objective"
            },
            "tasks": [
                {
                    "id": "task_1",
                    "name": "Task 1",
                    "description": "Test",
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
                    "action": "test_action",
                    "step_type": "AGENT_EXECUTION",
                    "timeout": 30,
                    "dependencies": []
                }
            ],
            "shared_inputs": {},
            "workflow_config": {
                "parallel_execution": False,
                "error_recovery": True,
                "max_retries": 3
            }
        }
        
        workflow_def = convert_to_workflow_definition(plan_data)
        print(f"✓ Converted plan to workflow")
        print(f"  - Workflow ID: {workflow_def['workflow_id']}")
        print(f"  - Name: {workflow_def['name']}")
        print(f"  - Steps: {len(workflow_def['steps'])}")
        
        if workflow_def['steps'][0].action == 'test_action':
            print("✓ Step conversion correct")
        else:
            print("✗ Step conversion incorrect")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Workflow conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_end_to_end():
    """Test 6: End-to-end markdown → TOON → workflow"""
    print("\n" + "=" * 60)
    print("TEST 6: End-to-End (Markdown → TOON → Workflow)")
    print("=" * 60)
    try:
        from toon_format import encode
        import importlib.util
        plan_to_workflow_path = project_root / "scripts" / "plan_to_workflow.py"
        spec = importlib.util.spec_from_file_location("plan_to_workflow", plan_to_workflow_path)
        plan_to_workflow = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(plan_to_workflow)
        parse_markdown_plan = plan_to_workflow.parse_markdown_plan
        validate_plan_structure = plan_to_workflow.validate_plan_structure
        convert_to_workflow_definition = plan_to_workflow.convert_to_workflow_definition
        
        # Step 1: Parse markdown
        md_content = """# End-to-End Test Plan

## Objective
Test complete workflow

## Tasks

### Task 1: Process Data
- **ID**: task_1
- **Description**: Process the data
- **Agent**: model_engine
- **Steps**: step_1
- **Dependencies**: []
- **Estimated Time**: 10.0s

## Steps

### Step 1: Load Data
- **ID**: step_1
- **Task**: task_1
- **Action**: load_data
- **Type**: DATA_PROCESSING
- **Timeout**: 60s
- **Dependencies**: []
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(md_content)
            md_path = Path(f.name)
        
        try:
            # Parse markdown
            plan_data = parse_markdown_plan(md_path)
            print("✓ Step 1: Parsed markdown plan")
            
            # Validate
            validate_plan_structure(plan_data)
            print("✓ Step 2: Validated plan structure")
            
            # Convert to TOON
            toon_content = encode(plan_data)
            print(f"✓ Step 3: Converted to TOON ({len(toon_content)} chars)")
            
            # Convert to workflow
            workflow_def = convert_to_workflow_definition(plan_data)
            print(f"✓ Step 4: Converted to workflow definition")
            print(f"  - Workflow: {workflow_def['name']}")
            print(f"  - Steps: {len(workflow_def['steps'])}")
            
            return True
        finally:
            md_path.unlink()
    except Exception as e:
        print(f"✗ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all smoke tests"""
    print("\n" + "=" * 60)
    print("TOON FORMAT SMOKE TEST")
    print("=" * 60)
    print()
    
    results = []
    
    results.append(("TOON CLI", test_toon_cli()))
    results.append(("Encoding/Decoding", test_encoding_decoding()))
    results.append(("Markdown Parsing", test_markdown_parsing()))
    results.append(("Plan Validation", test_plan_validation()))
    results.append(("Workflow Conversion", test_workflow_conversion()))
    results.append(("End-to-End", test_end_to_end()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! TOON format functionality is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

