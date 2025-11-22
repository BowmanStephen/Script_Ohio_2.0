#!/usr/bin/env python3
"""
Agent Documentation Validator

Validates consistency between agent code and documentation.
"""

import ast
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class DocValidator:
    """Validates agent documentation consistency"""
    
    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir)
        self.issues: List[str] = []
    
    def validate(self) -> List[str]:
        """Run all validation checks"""
        self.issues = []
        
        # Load agent metadata
        registry_path = self.root_dir / "docs" / "agents" / "capability_registry.json"
        if not registry_path.exists():
            self.issues.append("capability_registry.json not found. Run --update first.")
            return self.issues
        
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        # Validate capabilities have implementations
        self._validate_capability_implementations(registry)
        
        # Validate documentation completeness
        self._validate_doc_completeness(registry)
        
        # Validate tool references
        self._validate_tool_references(registry)
        
        return self.issues
    
    def _validate_capability_implementations(self, registry: Dict[str, Any]):
        """Check that all capabilities have implementations in _execute_action"""
        for agent_type, agent_info in registry.get("agent_types", {}).items():
            class_name = agent_info.get("class")
            if not class_name:
                continue
            
            # Find agent file
            agent_file = self._find_agent_file(class_name)
            if not agent_file:
                self.issues.append(f"Could not find file for {class_name}")
                continue
            
            # Parse file to find _execute_action
            try:
                with open(agent_file, 'r') as f:
                    content = f.read()
                    tree = ast.parse(content)
                
                # Find _execute_action method and all method definitions
                execute_actions = []
                method_names = []
                
                def extract_from_if(stmt):
                    """Recursively extract actions from if/elif chains"""
                    actions = []
                    if isinstance(stmt, ast.If):
                        # Check if this is checking action == "something"
                        if isinstance(stmt.test, ast.Compare):
                            if isinstance(stmt.test.left, ast.Name) and stmt.test.left.id == "action":
                                if len(stmt.test.comparators) > 0:
                                    comp = stmt.test.comparators[0]
                                    if isinstance(comp, ast.Constant):
                                        actions.append(comp.value)
                                    elif isinstance(comp, ast.Str):
                                        actions.append(comp.s)
                        # Check orelse (elif chains)
                        for orelse in stmt.orelse:
                            actions.extend(extract_from_if(orelse))
                    return actions
                
                # Collect all method names in the class
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        method_names.append(node.name)
                
                # Find _execute_action method using proper traversal
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name == "_execute_action":
                        # Walk the function body properly
                        for stmt in node.body:
                            # Handle try blocks
                            if isinstance(stmt, ast.Try):
                                for try_stmt in stmt.body:
                                    execute_actions.extend(extract_from_if(try_stmt))
                            else:
                                execute_actions.extend(extract_from_if(stmt))
                        break
                
                # Check capabilities
                capabilities = agent_info.get("capabilities", {})
                for cap_name in capabilities.keys():
                    # Direct match in execute_actions
                    if cap_name in execute_actions:
                        continue
                    
                    # Check if capability name appears in method names (indirect routing)
                    # e.g., "discover_system" might be in "_execute_discovery_phase"
                    found_in_method = False
                    for method_name in method_names:
                        # Check if capability name (with underscores) appears in method name
                        # Handle variations: "discover_system" -> "discovery", "discover", etc.
                        cap_parts = cap_name.split('_')
                        if len(cap_parts) > 1:
                            # Check if any significant part of capability is in method name
                            for part in cap_parts:
                                if len(part) > 3 and part.lower() in method_name.lower():
                                    found_in_method = True
                                    break
                        elif cap_name.lower() in method_name.lower():
                            found_in_method = True
                    
                    # Check if capability is called via method call (e.g., self._execute_discovery_phase)
                    if not found_in_method:
                        # Look for method calls that might route to the capability
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Call):
                                if isinstance(node.func, ast.Attribute):
                                    if hasattr(node.func, 'attr') and node.func.attr:
                                        method_attr = node.func.attr.lower()
                                        # Check if capability name components are in method call
                                        cap_parts = cap_name.split('_')
                                        for part in cap_parts:
                                            if len(part) > 3 and part.lower() in method_attr:
                                                found_in_method = True
                                                break
                                    if found_in_method:
                                        break
                            if found_in_method:
                                break
                    
                    if not found_in_method:
                        # Special case: orchestrator patterns where capabilities map to phases
                        # e.g., ValidationOrchestrator uses "execute_validation_workflow" which calls phases
                        if "orchestrator" in class_name.lower() or "orchestrator" in agent_type.lower():
                            # For orchestrators, check if capability name appears in phase method names
                            phase_methods = [m for m in method_names if 'phase' in m.lower() or 'execute' in m.lower()]
                            for phase_method in phase_methods:
                                cap_parts = cap_name.split('_')
                                for part in cap_parts:
                                    if len(part) > 3 and part.lower() in phase_method.lower():
                                        found_in_method = True
                                        break
                                if found_in_method:
                                    break
                    
                    if not found_in_method:
                        self.issues.append(
                            f"{class_name}: Capability '{cap_name}' defined but not implemented in _execute_action"
                        )
            except Exception as e:
                self.issues.append(f"Error validating {class_name}: {e}")
    
    def _validate_doc_completeness(self, registry: Dict[str, Any]):
        """Check that all agents have documentation"""
        docs_dir = self.root_dir / "docs" / "agents"
        
        for agent_type in registry.get("agent_types", {}).keys():
            doc_file = docs_dir / f"{agent_type}.md"
            if not doc_file.exists():
                self.issues.append(f"Missing documentation for {agent_type}")
            
            # Check capability descriptions
            agent_info = registry["agent_types"][agent_type]
            for cap_name, cap_info in agent_info.get("capabilities", {}).items():
                if not cap_info.get("description") or cap_info["description"].strip() == "":
                    self.issues.append(
                        f"{agent_type}.{cap_name}: Missing or empty description"
                    )
    
    def _validate_tool_references(self, registry: Dict[str, Any]):
        """Validate that referenced tools exist (basic check)"""
        # This is a placeholder - would need tool_loader to fully validate
        # For now, just check that tools_required is a list
        for agent_type, agent_info in registry.get("agent_types", {}).items():
            for cap_name, cap_info in agent_info.get("capabilities", {}).items():
                tools = cap_info.get("tools_required", [])
                if not isinstance(tools, list):
                    self.issues.append(
                        f"{agent_type}.{cap_name}: tools_required should be a list"
                    )
    
    def _find_agent_file(self, class_name: str) -> Path:
        """Find the file containing an agent class"""
        agents_dir = self.root_dir / "agents"
        
        for py_file in agents_dir.rglob("*.py"):
            if "archive" in str(py_file) or "test" in str(py_file):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    if f"class {class_name}" in content:
                        return py_file
            except Exception:
                continue
        
        return None
