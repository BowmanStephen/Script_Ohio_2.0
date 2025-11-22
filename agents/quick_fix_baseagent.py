#!/usr/bin/env python3
"""
Quick fix script for remaining BaseAgent files
"""

import os
import re

def fix_baseagent_file(file_path: str):
    """Fix a single BaseAgent file"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Fix import statements
        content = re.sub(
            r'from agents\.core\.agent_framework import BaseAgent',
            'from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel',
            content
        )

        content = re.sub(
            r'from agents\.core\.context_manager import ContextManager',
            '# from agents.core.context_manager import ContextManager  # Not needed for now',
            content
        )

        # Fix constructor pattern - simple replacement
        content = re.sub(
            r'def __init__\(self\):\s*super\(\).__init__\(\s*name="[^"]+",\s*description="[^"]+",\s*role="[^"]+",\s*permissions=\[[^\]]+\],\s*tools=\[[^\]]+\]\s*\)',
            '''def __init__(self, agent_id: str = "fixed_agent", name: str = "FixedAgent"):
        permission_level = PermissionLevel.READ_EXECUTE_WRITE
        super().__init__(agent_id, name, permission_level)''',
            content,
            flags=re.DOTALL
        )

        # Remove ContextManager initialization
        content = re.sub(
            r'self\.context_manager = ContextManager\(\)\s*\n',
            '',
            content
        )

        # Check if abstract methods exist, if not add them before the first regular method
        if '_define_capabilities' not in content:
            # Find the first regular method after __init__
            method_match = re.search(r'\n    (def [^_].*?\(.*?\):)', content)
            if method_match:
                insertion_point = method_match.start()

                abstract_methods = '''
    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities and permissions"""
        return [
            AgentCapability(
                name="base_capability",
                description="Base agent capability",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=[]
            )
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                      user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent action with proper routing"""
        if action == "validate_models":
            return self._validate_models(parameters, user_context)
        elif action == "check_compatibility":
            return self._check_data_compatibility(parameters, user_context)
        elif action == "performance_test":
            return self._run_performance_tests(parameters, user_context)
        else:
            raise ValueError(f"Unknown action: {action}")

'''
                content = content[:insertion_point] + abstract_methods + content[insertion_point:]

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"ℹ️  No changes needed: {file_path}")
            return False

    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all remaining BaseAgent files"""
    target_files = [
        'week12_matchup_analysis_agent.py',
        'week12_mock_enhancement_agent.py',
        'async_agent_framework.py',
        'grade_a_integration_engine.py'
    ]

    print("🔧 QUICK FIXER FOR BASEAGENT FILES")
    print("=" * 50)

    fixed_count = 0
    for file_path in target_files:
        if fix_baseagent_file(file_path):
            fixed_count += 1

    print(f"\n📊 SUMMARY: {fixed_count}/{len(target_files)} files fixed")

    # Test compilation
    print("\n🧪 TESTING COMPILATION...")
    for file_path in target_files:
        if os.path.exists(file_path):
            try:
                result = os.system(f'python3 -m py_compile {file_path}')
                if result == 0:
                    print(f"✅ {file_path}: Compiles successfully")
                else:
                    print(f"❌ {file_path}: Compilation failed")
            except Exception as e:
                print(f"❌ {file_path}: Compilation error - {e}")

if __name__ == "__main__":
    main()