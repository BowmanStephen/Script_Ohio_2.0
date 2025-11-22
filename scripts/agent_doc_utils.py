import ast
import importlib
import inspect
import os
import re
import sys
import logging
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass, asdict
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel

logger = logging.getLogger(__name__)

# Exclude templates and other non-agent BaseAgent subclasses
EXCLUDED_AGENTS = [
    "OrchestratorTemplate",
    "BaseAgent",  # Just in case
]

# Manual mappings for agents not in analytics_orchestrator.py
MANUAL_AGENT_MAPPINGS = {
    "ValidationOrchestrator": "validation_orchestrator",
    "ReportGeneratorAgent": "report_generator",
    "FileOrganizationAgent": "file_organization",
    "ValidationAgent": "validation_agent", 
}

@dataclass
class AgentMetadata:
    name: str
    class_name: str
    file_path: str
    description: str
    permission_level: str
    capabilities: List[Dict[str, Any]]
    agent_type: str
    
class AgentScanner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.agents_dir = self.root_dir / "agents"
        
    def scan_directory(self) -> Dict[str, AgentMetadata]:
        """Scan agents directory for BaseAgent subclasses"""
        agent_metadata = {}
        
        for file_path in self.agents_dir.rglob("*.py"):
            if "archive" in str(file_path) or "test" in str(file_path.name):
                continue
                
            try:
                classes = self._find_agent_classes(file_path)
                for class_name in classes:
                    if class_name in EXCLUDED_AGENTS:
                        logger.info(f"Skipping excluded agent: {class_name}")
                        continue
                        
                    metadata = self._extract_metadata(file_path, class_name)
                    if metadata:
                        # Use class name as key initially, will map to agent_type later
                        agent_metadata[metadata.class_name] = metadata
            except Exception as e:
                logger.warning(f"Failed to process {file_path}: {e}")
                
        return agent_metadata
    
    def _find_agent_classes(self, file_path: Path) -> List[str]:
        """Parse file with AST to find BaseAgent subclasses"""
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read())
            except SyntaxError:
                return []
                
        agent_classes = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    if isinstance(base, ast.Name) and base.id == "BaseAgent":
                        agent_classes.append(node.name)
                    elif isinstance(base, ast.Attribute) and base.attr == "BaseAgent":
                        agent_classes.append(node.name)
        return agent_classes

    def _extract_metadata(self, file_path: Path, class_name: str) -> Optional[AgentMetadata]:
        """Dynamically import and extract metadata from agent class"""
        try:
            # Construct module path from file path
            rel_path = file_path.relative_to(self.root_dir)
            module_path = str(rel_path).replace("/", ".").replace(".py", "")
            
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Skip abstract classes or BaseAgent itself if caught
            if agent_class is BaseAgent or inspect.isabstract(agent_class):
                return None

            # Instantiate to get capabilities
            # We need to handle __init__ args. Most take agent_id. 
            # Some might take more. We'll inspect signature.
            
            sig = inspect.signature(agent_class.__init__)
            init_args = {}
            
            # Standard args
            if 'agent_id' in sig.parameters:
                init_args['agent_id'] = 'doc_gen_temp_id'
            
            # Weekly agent args
            if 'week' in sig.parameters:
                init_args['week'] = 13
                
            # Template args
            if 'param1' in sig.parameters:
                init_args['param1'] = 'dummy'
                
            # Tool loader
            if 'tool_loader' in sig.parameters:
                init_args['tool_loader'] = None
            
            # Handle CFBD API Key requirement
            original_api_key = os.environ.get("CFBD_API_KEY")
            if not original_api_key:
                os.environ["CFBD_API_KEY"] = "dummy_key_for_docs"

            # Special handling for Week12 agents that create _weekly_agent before super().__init__()
            is_week12_agent = class_name.startswith("Week12")
            
            # For Week12 agents, don't pass tool_loader as it causes issues with weekly agent instantiation
            if is_week12_agent and 'tool_loader' in init_args:
                week12_args = {k: v for k, v in init_args.items() if k != 'tool_loader'}
            else:
                week12_args = init_args
            
            # Try to instantiate
            agent_instance = None
            try:
                agent_instance = agent_class(**week12_args)
            except TypeError as type_err:
                # Fallback: try with just agent_id if inspection failed or complex args
                if is_week12_agent:
                    # For Week12 agents, go directly to weekly agent extraction
                    logger.warning(f"Could not instantiate {class_name} directly, trying to extract from weekly agent: {type_err}")
                    # Extract from weekly agent (code below)
                    agent_instance = self._extract_from_weekly_agent(file_path, class_name, agent_class)
                    if agent_instance is None:
                        return None
                else:
                    try:
                        agent_instance = agent_class(agent_id='doc_gen_temp_id')
                    except Exception as e:
                        logger.warning(f"Could not instantiate {class_name} with fallback: {e}")
                        return None
            except Exception as e:
                if is_week12_agent:
                    # For Week12 agents, try to extract capabilities from the weekly agent class
                    logger.warning(f"Error instantiating {class_name}, attempting to extract from weekly agent: {e}")
                    agent_instance = self._extract_from_weekly_agent(file_path, class_name, agent_class)
                    if agent_instance is None:
                        return None
                else:
                    logger.warning(f"Error instantiating {class_name}: {e}")
                    return None
            finally:
                # Restore API Key
                if original_api_key is None:
                    del os.environ["CFBD_API_KEY"]
                else:
                    os.environ["CFBD_API_KEY"] = original_api_key
            
            if agent_instance is None:
                return None

            capabilities = []
            if hasattr(agent_instance, 'capabilities'):
                # Deduplicate capabilities by name (preserve first occurrence)
                seen_capabilities = {}
                for cap in agent_instance.capabilities:
                    cap_dict = asdict(cap)
                    # Convert enum to value for JSON serialization
                    if hasattr(cap.permission_required, 'name'):
                        cap_dict['permission_required'] = cap.permission_required.name
                    cap_name = cap_dict.get('name', '')
                    # Only add if we haven't seen this capability name before
                    if cap_name and cap_name not in seen_capabilities:
                        seen_capabilities[cap_name] = cap_dict
                        capabilities.append(cap_dict)
                    elif cap_name in seen_capabilities:
                        logger.warning(f"Duplicate capability '{cap_name}' found in {class_name}, skipping duplicate.")
            
            # Get permission level name
            perm_level = agent_instance.permission_level.name if hasattr(agent_instance.permission_level, 'name') else str(agent_instance.permission_level)
            
            # Get docstring
            description = inspect.getdoc(agent_class) or ""
            
            return AgentMetadata(
                name=agent_instance.name,
                class_name=class_name,
                file_path=str(rel_path),
                description=description,
                permission_level=perm_level,
                capabilities=capabilities,
                agent_type="" # To be filled by registry mapping
            )
            
        except Exception as e:
            logger.error(f"Error extracting metadata for {class_name} in {file_path}: {e}")
            return None
    
    def _extract_from_weekly_agent(self, file_path: Path, class_name: str, agent_class: Type) -> Optional[Any]:
        """Extract capabilities from weekly agent for Week12 wrapper agents"""
        try:
            # Week12 agents delegate to weekly agents, try to find and instantiate the weekly agent
            # Check the source code to find which weekly agent class is used
            with open(file_path, 'r') as f:
                source = f.read()
                # Look for imports like "from agents.weekly_X_agent import WeeklyXAgent"
                weekly_import_match = re.search(r'from agents\.weekly_(\w+)_agent import (\w+)', source)
                if weekly_import_match:
                    weekly_module_name = f"agents.weekly_{weekly_import_match.group(1)}_agent"
                    weekly_class_name = weekly_import_match.group(2)
                    try:
                        weekly_module = importlib.import_module(weekly_module_name)
                        weekly_class = getattr(weekly_module, weekly_class_name)
                        # Check weekly agent signature and only pass accepted parameters
                        weekly_sig = inspect.signature(weekly_class.__init__)
                        weekly_args = {}
                        if 'week' in weekly_sig.parameters:
                            weekly_args['week'] = 12
                        if 'season' in weekly_sig.parameters:
                            weekly_args['season'] = 2025
                        if 'agent_id' in weekly_sig.parameters:
                            weekly_args['agent_id'] = 'doc_gen_temp_id'
                        # Don't pass tool_loader to weekly agents
                        # Try to instantiate weekly agent
                        weekly_agent = weekly_class(**weekly_args)
                        # Create a mock agent instance with capabilities from weekly agent
                        class MockAgentInstance:
                            def __init__(self, weekly_agent, agent_class):
                                self.capabilities = weekly_agent.capabilities
                                self.permission_level = weekly_agent.permission_level
                                self.name = agent_class.__name__.replace("Agent", " Agent")
                        agent_instance = MockAgentInstance(weekly_agent, agent_class)
                        logger.info(f"Successfully extracted capabilities from weekly agent for {class_name}")
                        return agent_instance
                    except Exception as weekly_e:
                        logger.warning(f"Could not extract from weekly agent for {class_name}: {weekly_e}")
                        return None
                else:
                    logger.warning(f"Could not find weekly agent import for {class_name}")
                    return None
        except Exception as extract_e:
            logger.warning(f"Error extracting capabilities from weekly agent for {class_name}: {extract_e}")
            return None

class ExampleExtractor:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.tests_dir = self.root_dir / "agents" / "tests"
        
    def extract_examples(self, agent_type: str) -> List[str]:
        """Extract code examples from test files for a given agent type"""
        examples = []
        
        # Convert agent_type to class name patterns (e.g., "learning_navigator" -> "LearningNavigator", "LearningNavigatorAgent")
        class_name_variants = []
        parts = agent_type.split('_')
        # Generate variants: LearningNavigatorAgent, LearningNavigator, learning_navigator
        if len(parts) > 1:
            class_name_variants.append(''.join(p.capitalize() for p in parts) + 'Agent')
            class_name_variants.append(''.join(p.capitalize() for p in parts))
        class_name_variants.append(agent_type)
        
        # Look for files matching various patterns
        patterns = [
            f"test_{agent_type}_agent.py",
            f"test_{agent_type}.py",
            f"test_{agent_type.replace('_', '')}.py",
        ]
        
        # Search in multiple locations
        search_paths = [
            self.tests_dir,
            self.root_dir / "agents",
            self.root_dir / "tests",
            self.root_dir / "agents" / "tests"
        ]
        
        found_files = []
        for path in search_paths:
            if not path.exists():
                continue
            for pattern in patterns:
                # Check exact match
                candidate = path / pattern
                if candidate.exists() and candidate not in found_files:
                    found_files.append(candidate)
            # Also search recursively for files containing agent type
            for py_file in path.rglob("*.py"):
                if "test" in py_file.name.lower() and agent_type in py_file.name.lower():
                    if py_file not in found_files:
                        found_files.append(py_file)
        
        if not found_files:
            return []
        
        # Parse all found files
        for found_file in found_files:
            try:
                with open(found_file, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Check if file mentions the agent class
                mentions_agent = False
                for variant in class_name_variants:
                    if variant in content:
                        mentions_agent = True
                        break
                
                if not mentions_agent:
                    continue
                
                tree = ast.parse(content)
                lines = content.splitlines()
                
                # Extract examples from test functions
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        # Extract meaningful code snippets
                        example_code = self._extract_agent_usage_from_function(node, lines, class_name_variants)
                        if example_code and example_code not in examples:
                            examples.append(example_code)
                    
                    # Also look for agent instantiation outside test functions
                    elif isinstance(node, ast.Assign):
                        # Check if assignment creates agent instance
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                # Check if value is a call to agent class
                                if isinstance(node.value, ast.Call):
                                    if isinstance(node.value.func, ast.Name):
                                        if node.value.func.id in class_name_variants:
                                            # Extract this assignment
                                            start_line = node.lineno - 1
                                            end_line = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
                                            example_lines = lines[start_line:end_line]
                                            if example_lines:
                                                example_code = "\n".join(example_lines).strip()
                                                if example_code and example_code not in examples:
                                                    examples.append(example_code)
                                    
            except Exception as e:
                logger.warning(f"Failed to extract examples from {found_file}: {e}")
        
        return examples[:3]  # Limit to 3 examples
    
    def _extract_agent_usage_from_function(self, func_node: ast.FunctionDef, lines: List[str], class_name_variants: List[str]) -> str:
        """Extract agent usage code from a function"""
        # Find agent-related code in function body
        relevant_lines = []
        start_line = func_node.lineno - 1
        
        # Walk function body to find agent usage
        for stmt in func_node.body:
            # Look for assignments, calls, or expressions involving agent
            if isinstance(stmt, (ast.Assign, ast.Expr, ast.Call)):
                stmt_start = stmt.lineno - 1
                stmt_end = stmt.end_lineno if hasattr(stmt, 'end_lineno') else stmt.lineno
                
                # Check if statement mentions agent
                stmt_text = "\n".join(lines[stmt_start:stmt_end])
                for variant in class_name_variants:
                    if variant in stmt_text:
                        relevant_lines.append((stmt_start, stmt_end))
                        break
        
        if not relevant_lines:
            # Fallback: extract first few meaningful lines
            func_start = func_node.lineno - 1
            func_end = min(func_node.end_lineno if hasattr(func_node, 'end_lineno') else func_node.lineno + 10, len(lines))
            example_lines = lines[func_start:func_end]
            
            # Dedent
            if example_lines:
                first_line = example_lines[0]
                indent = len(first_line) - len(first_line.lstrip())
                dedented = [line[indent:] if len(line) > indent else line for line in example_lines[:15]]
                return "\n".join(dedented).strip()
            return ""
        
        # Extract relevant lines
        all_lines = set()
        for start, end in relevant_lines[:3]:  # Limit to first 3 relevant statements
            for i in range(start, min(end, len(lines))):
                all_lines.add(i)
        
        if all_lines:
            sorted_lines = sorted(all_lines)
            example_lines = [lines[i] for i in sorted_lines]
            # Dedent
            if example_lines:
                first_line = example_lines[0]
                indent = len(first_line) - len(first_line.lstrip())
                dedented = [line[indent:] if len(line) > indent else line for line in example_lines]
                return "\n".join(dedented).strip()
        
        return ""

def get_agent_type_mapping(orchestrator_path: str) -> Dict[str, str]:
    """Extract agent_type mapping from orchestrator registration"""
    mapping = {} # class_name -> agent_type
    
    with open(orchestrator_path, 'r') as f:
        tree = ast.parse(f.read())
        
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute) and node.func.attr == 'register_agent_class':
                # Look for factory.register_agent_class(Class, "type")
                if len(node.args) >= 2:
                    class_arg = node.args[0]
                    type_arg = node.args[1]
                    
                    class_name = None
                    if isinstance(class_arg, ast.Name):
                        class_name = class_arg.id
                        
                    type_name = None
                    if isinstance(type_arg, ast.Constant): # Python 3.8+
                        type_name = type_arg.value
                    elif isinstance(type_arg, ast.Str): # Older Python
                        type_name = type_arg.s
                        
                    if class_name and type_name:
                        mapping[class_name] = type_name
    
    # Add manual mappings
    mapping.update(MANUAL_AGENT_MAPPINGS)
    
    return mapping
