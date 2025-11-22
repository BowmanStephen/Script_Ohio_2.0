#!/usr/bin/env python3
"""
AbstractMethodFixerAgent - Specialized agent for fixing BaseAgent inheritance issues
Following Claude's best practices for focused, modular agents
"""

import ast
import re
import tempfile
import os
import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from base_agent import BaseAgent, AgentCapability, PermissionLevel

class ConstructorFixer:
    """Specialized class for fixing BaseAgent constructor signatures"""

    @staticmethod
    def find_constructor_issues(file_path: str) -> List[Dict[str, Any]]:
        """Find constructor issues in Python file with detailed analysis"""
        issues = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it inherits from BaseAgent
                    base_names = []
                    for base in node.bases:
                        if hasattr(base, 'id'):
                            base_names.append(base.id)
                        elif hasattr(base, 'attr'):
                            base_names.append(base.attr)

                    if 'BaseAgent' in base_names:
                        class_name = node.name
                        class_line = node.lineno

                        # Check constructor presence
                        constructor_found = False
                        constructor_node = None

                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                                constructor_found = True
                                constructor_node = item
                                break

                        if not constructor_found:
                            issues.append({
                                'type': 'missing_constructor',
                                'class_name': class_name,
                                'file_path': file_path,
                                'line_number': class_line,
                                'severity': 'critical',
                                'message': f'Missing __init__ method in {class_name} class'
                            })
                        else:
                            # Analyze existing constructor
                            issues.extend(ConstructorFixer._analyze_constructor(
                                constructor_node, file_path, class_name
                            ))

                        # Check for missing abstract methods
                        issues.extend(ConstructorFixer._check_abstract_methods(
                            node, file_path, class_name
                        ))

        except Exception as e:
            issues.append({
                'type': 'parse_error',
                'file_path': file_path,
                'line_number': 0,
                'severity': 'critical',
                'message': f'Error parsing file: {str(e)}'
            })

        return issues

    @staticmethod
    def _analyze_constructor(constructor_node: ast.FunctionDef,
                           file_path: str, class_name: str) -> List[Dict[str, Any]]:
        """Analyze constructor for BaseAgent compatibility issues"""
        issues = []

        # Check constructor signature
        args = constructor_node.args
        arg_names = [arg.arg for arg in args.args]

        # Should only have 'self' parameter for new BaseAgent signature
        if len(arg_names) > 1:
            issues.append({
                'type': 'old_constructor_signature',
                'class_name': class_name,
                'file_path': file_path,
                'line_number': constructor_node.lineno,
                'severity': 'critical',
                'message': f'Constructor has old signature with {len(arg_names)} parameters: {arg_names}'
            })

        # Check super().__init__ calls
        for node in ast.walk(constructor_node):
            if isinstance(node, ast.Call):
                if (hasattr(node.func, 'attr') and
                    node.func.attr == '__init__' and
                    hasattr(node.func, 'value') and
                    hasattr(node.func.value, 'id') and
                    node.func.value.id == 'super'):

                    # Check if old super().__init__ signature is used
                    if len(node.args) > 1 or len(node.keywords) > 0:
                        issues.append({
                            'type': 'old_super_call',
                            'class_name': class_name,
                            'file_path': file_path,
                            'line_number': node.lineno,
                            'severity': 'critical',
                            'message': 'Using old super().__init__() signature with multiple parameters'
                        })

        return issues

    @staticmethod
    def _check_abstract_methods(class_node: ast.ClassDef,
                              file_path: str, class_name: str) -> List[Dict[str, Any]]:
        """Check for missing abstract methods"""
        issues = []

        # Get all method names in the class
        method_names = []
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                method_names.append(item.name)

        # Check for required abstract methods
        if '_define_capabilities' not in method_names:
            issues.append({
                'type': 'missing_abstract_method',
                'method_name': '_define_capabilities',
                'class_name': class_name,
                'file_path': file_path,
                'line_number': class_node.lineno,
                'severity': 'critical',
                'message': f'Missing abstract method: _define_capabilities'
            })

        if '_execute_action' not in method_names:
            # Check if old method name exists
            if 'execute_task' in method_names:
                issues.append({
                    'type': 'old_method_name',
                    'method_name': 'execute_task',
                    'class_name': class_name,
                    'file_path': file_path,
                    'line_number': class_node.lineno,
                    'severity': 'critical',
                    'message': f'Using old method name: execute_task (should be _execute_action)'
                })
            else:
                issues.append({
                    'type': 'missing_abstract_method',
                    'method_name': '_execute_action',
                    'class_name': class_name,
                    'file_path': file_path,
                    'line_number': class_node.lineno,
                    'severity': 'critical',
                    'message': f'Missing abstract method: _execute_action'
                })

        return issues

    @staticmethod
    def fix_constructor_and_methods(file_path: str, issues: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """Fix constructor issues and missing abstract methods"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()

            content = original_content
            changes_made = []

            # Extract class names from issues
            class_names = list(set(issue['class_name'] for issue in issues
                                if 'class_name' in issue))

            for class_name in class_names:
                # Fix constructor
                constructor_pattern = rf'(class {class_name}\(BaseAgent\):.*?def __init__\(self.*?\):)(.*?)(?=\n    def |\nclass |\Z)'
                constructor_match = re.search(constructor_pattern, content, re.DOTALL)

                if constructor_match:
                    old_constructor = constructor_match.group(1) + constructor_match.group(2)

                    # Create new constructor
                    new_constructor = f'''class {class_name}(BaseAgent):
    def __init__(self, agent_id: str = "{class_name.lower()}",
                 name: str = "{class_name}"):
        permission_level = PermissionLevel.READ_EXECUTE_WRITE
        super().__init__(agent_id, name, permission_level)'''

                    content = content.replace(old_constructor, new_constructor)
                    changes_made.append(f"Fixed constructor for {class_name}")

                # Fix execute_task method name
                execute_task_pattern = rf'(    def execute_task\(self, task_data: Dict\[str, Any\]\) -> Dict\[str, Any\]:)'
                if re.search(execute_task_pattern, content):
                    content = re.sub(
                        execute_task_pattern,
                        '''    def _execute_action(self, action: str, parameters: Dict[str, Any],\\n                      user_context: Dict[str, Any]) -> Dict[str, Any]:''',
                        content
                    )
                    changes_made.append(f"Fixed method name for {class_name}")

                # Add missing abstract methods if needed
                missing_capabilities = any(issue['method_name'] == '_define_capabilities' for issue in issues
                                           if issue['class_name'] == class_name)
                missing_execute_action = any(issue['method_name'] == '_execute_action' for issue in issues
                                               if issue['class_name'] == class_name)

                if missing_capabilities:
                    # Find the end of the class to add methods
                    class_pattern = rf'(class {class_name}\(BaseAgent\):.*?)(?=\nclass |\Z)'
                    class_match = re.search(class_pattern, content, re.DOTALL)

                    if class_match:
                        class_content = class_match.group(1)
                        capabilities_method = '''
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities and permissions"""
        return [
            AgentCapability(
                name="analysis_capability",
                description="Capability description",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["tool1", "tool2"]
            )
        ]

'''
                        content = content.replace(class_content, class_content + capabilities_method)
                        changes_made.append(f"Added _define_capabilities for {class_name}")

                if missing_execute_action and not any('execute_task' in issue.get('message', '') for issue in issues):
                    # Add _execute_action method
                    class_pattern = rf'(class {class_name}\(BaseAgent\):.*?)(?=\nclass |\Z)'
                    class_match = re.search(class_pattern, content, re.DOTALL)

                    if class_match:
                        class_content = class_match.group(1)
                        execute_action_method = '''
    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent action with proper routing"""
        if action == "specific_action":
            return self._handle_specific_action(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")

'''
                        content = content.replace(class_content, class_content + execute_action_method)
                        changes_made.append(f"Added _execute_action for {class_name}")

            # Write back to file if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                return True, f"Changes applied: {', '.join(changes_made)}"
            else:
                return False, "No changes needed - file already compliant"

        except Exception as e:
            return False, f"Error fixing file: {str(e)}"

    @staticmethod
    def validate_fixes(file_path: str) -> Dict[str, Any]:
        """Validate that BaseAgent fixes were applied correctly"""
        validation_result = {
            'file_path': file_path,
            'valid_syntax': False,
            'has_baseagent': False,
            'has_define_capabilities': False,
            'has_execute_action': False,
            'no_old_constructor': False,
            'issues_found': []
        }

        try:
            # Check syntax
            result = subprocess.run(['python3', '-m', 'py_compile', file_path],
                                 capture_output=True, text=True, timeout=10)
            validation_result['valid_syntax'] = result.returncode == 0

            if not validation_result['valid_syntax']:
                validation_result['issues_found'].append(f"Syntax error: {result.stderr}")
                return validation_result

            # Read file and check content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            validation_result['has_baseagent'] = 'BaseAgent' in content
            validation_result['has_define_capabilities'] = '_define_capabilities' in content
            validation_result['has_execute_action'] = '_execute_action' in content

            # Check for old constructor patterns
            old_patterns = [
                r'super\(\).__init__\(',
                r'def execute_task\('
            ]

            validation_result['no_old_constructor'] = not any(re.search(pattern, content) for pattern in old_patterns)

            # Determine overall validity
            validation_result['is_valid'] = all([
                validation_result['valid_syntax'],
                validation_result['has_baseagent'],
                validation_result['has_define_capabilities'],
                validation_result['has_execute_action'],
                validation_result['no_old_constructor']
            ])

            if not validation_result['is_valid']:
                for key, value in validation_result.items():
                    if key.endswith('_') and isinstance(value, bool) and not value and key != 'is_valid' and key != 'valid_syntax':
                        validation_result['issues_found'].append(f"Missing: {key.replace('_', ' ').title()}")

        except Exception as e:
            validation_result['issues_found'].append(f"Validation error: {str(e)}")

        return validation_result

class AbstractMethodFixerAgent(BaseAgent):
    """
    Specialized agent for fixing BaseAgent inheritance issues
    Following Claude's best practices:
    - Focused capability (BaseAgent fixes)
    - Clear boundaries (only fixes inheritance issues)
    - Modular design (separate constructor and method fixers)
    - Comprehensive monitoring (detailed fix tracking)
    """

    def __init__(self, agent_id: str = "abstract_method_fixer"):
        super().__init__(agent_id, "Abstract Method Fixer Agent", PermissionLevel.READ_EXECUTE_WRITE)

        # Specialized components
        self.constructor_fixer = ConstructorFixer()
        self.method_templates = self._load_method_templates()
        self.fix_history = []

        self.logger.info("AbstractMethodFixerAgent initialized with BaseAgent inheritance focus")

    def _load_method_templates(self) -> Dict[str, str]:
        """Load templates for missing abstract methods"""
        return {
            "define_capabilities": '''    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities and permissions"""
        return [
            AgentCapability(
                name="capability_name",
                description="Description of what this capability does",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["tool1", "tool2"]
            )
        ]''',
            "execute_action": '''    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent action with proper routing"""
        if action == "specific_action":
            return self._handle_specific_action(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")'''
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities and permissions"""
        return [
            AgentCapability(
                name="constructor_standardization",
                description="Fix BaseAgent constructor signatures",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["ast_parser", "code_generator", "file_writer"],
                estimated_duration=10,
                resource_requirements={"memory": "256MB", "cpu": "0.3"}
            ),
            AgentCapability(
                name="abstract_method_implementation",
                description="Implement required abstract methods",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["method_generator", "template_engine", "code_validator"],
                estimated_duration=15,
                resource_requirements={"memory": "512MB", "cpu": "0.5"}
            ),
            AgentCapability(
                name="baseagent_validation",
                description="Validate BaseAgent inheritance compliance",
                permission_required=PermissionLevel.READ_EXECUTE,
                tools_required=["syntax_checker", "import_validator", "inheritance_validator"],
                estimated_duration=5,
                resource_requirements={"memory": "128MB", "cpu": "0.2"}
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent action with proper routing"""
        try:
            if action == "fix_baseagent_issues":
                return self._fix_all_baseagent_issues(parameters, user_context)
            elif action == "validate_inheritance":
                return self._validate_baseagent_inheritance(parameters, user_context)
            elif action == "analyze_issues":
                return self._analyze_baseagent_issues(parameters, user_context)
            elif action == "apply_fixes":
                return self._apply_baseagent_fixes(parameters, user_context)
            else:
                raise ValueError(f"Unknown action: {action}")

        except Exception as e:
            self.logger.error(f"Error executing action {action}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "action": action,
                "timestamp": datetime.now().isoformat()
            }

    def _fix_all_baseagent_issues(self, parameters: Dict[str, Any],
                                user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Fix all BaseAgent inheritance issues in target files"""
        try:
            target_files = parameters.get('target_files', [])
            results = []

            self.logger.info(f"Starting BaseAgent fixes for {len(target_files)} files")

            for file_path in target_files:
                if not os.path.exists(file_path):
                    results.append({
                        'file_path': file_path,
                        'status': 'error',
                        'message': 'File not found'
                    })
                    continue

                self.logger.info(f"Processing file: {file_path}")

                # Analyze issues in the file
                issues = self.constructor_fixer.find_constructor_issues(file_path)
                baseagent_issues = [issue for issue in issues
                                   if issue.get('type') in [
                                       'old_constructor_signature', 'old_super_call',
                                       'missing_constructor', 'missing_abstract_method',
                                       'old_method_name'
                                   ]]

                if baseagent_issues:
                    # Apply fixes
                    success, message = self.constructor_fixer.fix_constructor_and_methods(
                        file_path, baseagent_issues
                    )

                    # Record fix in history
                    fix_record = {
                        'file_path': file_path,
                        'issues_count': len(baseagent_issues),
                        'success': success,
                        'message': message,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.fix_history.append(fix_record)

                    results.append({
                        'file_path': file_path,
                        'status': 'success' if success else 'error',
                        'issues_fixed': len(baseagent_issues) if success else 0,
                        'message': message
                    })

                    self.logger.info(f"Fixed {file_path}: {message}")
                else:
                    results.append({
                        'file_path': file_path,
                        'status': 'no_action_needed',
                        'message': 'No BaseAgent issues found'
                    })

                    self.logger.info(f"No BaseAgent issues found in {file_path}")

            # Summary
            successful_fixes = sum(1 for r in results if r['status'] == 'success')
            total_issues_fixed = sum(r.get('issues_fixed', 0) for r in results)

            self.logger.info(f"BaseAgent fixes completed: {successful_fixes}/{len(target_files)} files, {total_issues_fixed} issues fixed")

            return {
                'status': 'completed',
                'results': results,
                'summary': {
                    'total_files_processed': len(target_files),
                    'files_fixed': successful_fixes,
                    'total_issues_fixed': total_issues_fixed,
                    'fix_history_length': len(self.fix_history)
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in _fix_all_baseagent_issues: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _validate_baseagent_inheritance(self, parameters: Dict[str, Any],
                                     user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate BaseAgent inheritance fixes"""
        try:
            target_files = parameters.get('target_files', [])
            validation_results = []

            self.logger.info(f"Validating BaseAgent inheritance for {len(target_files)} files")

            for file_path in target_files:
                if not os.path.exists(file_path):
                    validation_results.append({
                        'file_path': file_path,
                        'status': 'error',
                        'message': 'File not found'
                    })
                    continue

                validation = self.constructor_fixer.validate_fixes(file_path)
                validation_results.append(validation)

                status = '✅' if validation.get('is_valid', False) else '❌'
                self.logger.info(f"{status} {file_path}: {validation.get('issues_found', [])}")

            # Summary
            valid_files = sum(1 for v in validation_results if v.get('is_valid', False))
            total_files = len(target_files)

            self.logger.info(f"Validation complete: {valid_files}/{total_files} files valid")

            return {
                'status': 'completed',
                'validation_results': validation_results,
                'summary': {
                    'total_files_validated': total_files,
                    'valid_files': valid_files,
                    'invalid_files': total_files - valid_files,
                    'validation_rate': (valid_files / total_files * 100) if total_files > 0 else 0
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in _validate_baseagent_inheritance: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _analyze_baseagent_issues(self, parameters: Dict[str, Any],
                                user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze BaseAgent issues in target files"""
        try:
            target_files = parameters.get('target_files', [])
            analysis_results = []

            total_issues = 0

            for file_path in target_files:
                if not os.path.exists(file_path):
                    continue

                issues = self.constructor_fixer.find_constructor_issues(file_path)
                baseagent_issues = [issue for issue in issues
                                   if issue.get('type') in [
                                       'old_constructor_signature', 'old_super_call',
                                       'missing_constructor', 'missing_abstract_method',
                                       'old_method_name'
                                   ]]

                analysis_results.append({
                    'file_path': file_path,
                    'baseagent_issues': baseagent_issues,
                    'issues_count': len(baseagent_issues)
                })

                total_issues += len(baseagent_issues)

            return {
                'status': 'completed',
                'analysis_results': analysis_results,
                'summary': {
                    'total_files_analyzed': len(target_files),
                    'total_baseagent_issues': total_issues,
                    'files_with_issues': len([r for r in analysis_results if r['issues_count'] > 0])
                },
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in _analyze_baseagent_issues: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _apply_baseagent_fixes(self, parameters: Dict[str, Any],
                              user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply specific BaseAgent fixes"""
        try:
            file_path = parameters.get('file_path')
            issues = parameters.get('issues', [])

            if not file_path or not os.path.exists(file_path):
                return {
                    'status': 'error',
                    'error': 'Invalid or missing file path'
                }

            if not issues:
                return {
                    'status': 'no_action_needed',
                    'message': 'No issues to fix'
                }

            success, message = self.constructor_fixer.fix_constructor_and_methods(file_path, issues)

            return {
                'status': 'success' if success else 'error',
                'message': message,
                'issues_count': len(issues),
                'file_path': file_path,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in _apply_baseagent_fixes: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def get_fix_history(self) -> Dict[str, Any]:
        """Get detailed fix history"""
        return {
            'total_fixes': len(self.fix_history),
            'successful_fixes': sum(1 for fix in self.fix_history if fix['success']),
            'fix_history': self.fix_history,
            'timestamp': datetime.now().isoformat()
        }