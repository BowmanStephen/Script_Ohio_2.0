#!/usr/bin/env python3.13
"""
File Categorization Agent - Phase 1 of Project Management Reorganization

This agent analyzes all files in the project_management directory and categorizes them
by purpose, usage, and destination in the new structure.
"""

import os
import json
import ast
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class FileInfo:
    """Information about a file for categorization"""
    path: str
    name: str
    extension: str
    size_bytes: int
    modified_time: datetime
    category: str = ""
    subcategory: str = ""
    purpose: str = ""
    destination: str = ""
    dependencies: List[str] = None
    referenced_by_claude_md: bool = False
    priority: str = "medium"  # high, medium, low

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

class FileCategorizationAgent:
    """Analyzes and categorizes files for project management reorganization"""

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.pm_directory = self.project_root / "project_management"
        self.claude_md_path = self.project_root / "CLAUDE.md"
        self.categorized_files = []

    def scan_directory(self) -> List[FileInfo]:
        """Scan all files in project_management directory"""
        files = []

        for root, dirs, filenames in os.walk(self.pm_directory):
            for filename in filenames:
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(self.project_root)

                try:
                    stat_info = file_path.stat()
                    file_info = FileInfo(
                        path=str(relative_path),
                        name=filename,
                        extension=file_path.suffix,
                        size_bytes=stat_info.st_size,
                        modified_time=datetime.fromtimestamp(stat_info.st_mtime)
                    )
                    files.append(file_info)
                except Exception as e:
                    print(f"⚠️  Could not read {file_path}: {e}")

        return files

    def analyze_claude_md_references(self) -> List[str]:
        """Extract file references from CLAUDE.md"""
        referenced_files = []

        try:
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for file references in code blocks and text
            lines = content.split('\n')
            for line in lines:
                if 'project_management/' in line:
                    # Extract file path from various patterns
                    if 'python project_management/' in line:
                        file_ref = line.split('project_management/')[1].split()[0].strip()
                        referenced_files.append(file_ref)
                    elif 'project_management/' in line:
                        # Extract from other contexts
                        parts = line.split('project_management/')
                        if len(parts) > 1:
                            file_ref = parts[1].split()[0].strip('`"\'').split('/')[0]
                            if file_ref.endswith('.py'):
                                referenced_files.append(file_ref)

        except Exception as e:
            print(f"⚠️  Could not analyze CLAUDE.md: {e}")

        return referenced_files

    def categorize_by_location_and_name(self, file_info: FileInfo) -> Tuple[str, str]:
        """Categorize file based on its location and name patterns"""
        path_parts = Path(file_info.path).parts
        filename = file_info.name.lower()

        # Core tools (high priority)
        if filename == 'data_workflows.py':
            return "core_tools", "main_cli"
        elif filename == 'demo_agent_system.py':
            return "core_tools", "demo_system"
        elif filename == 'test_agents.py':
            return "core_tools", "validation"
        elif 'test' in filename and filename.endswith('.py'):
            return "quality_assurance", "testing"

        # Configuration files
        elif 'config' in filename or filename in ['model_features.py', 'environment_setup.py']:
            return "config", "configuration"

        # Model related
        elif 'model' in filename:
            return "config", "model_config"

        # Documentation
        elif file_info.extension in ['.md', '.txt']:
            if 'readme' in filename:
                return "docs", "readme"
            elif 'guide' in filename or 'tutorial' in filename:
                return "docs", "user_guide"
            elif 'roadmap' in filename or 'plan' in filename:
                return "docs", "planning"
            else:
                return "docs", "documentation"

        # Agent systems
        elif 'agent' in filename:
            return "agents", "management_agents"

        # Archive candidates
        elif any(keyword in filename for keyword in ['log', 'decision', 'weekly', 'status', 'implementation']):
            return "archive", "historical_docs"

        # By directory structure
        elif 'TOOLS_AND_CONFIG' in path_parts:
            return "core_tools", "utilities"
        elif 'QUALITY_ASSURANCE' in path_parts:
            return "quality_assurance", "validation"
        elif 'AGENTS' in path_parts or 'AGENT_SYSTEM' in path_parts:
            return "agents", "system_agents"
        elif 'ARCHIVE' in path_parts:
            return "archive", "archived"
        elif 'DOCUMENTATION' in path_parts:
            return "docs", "technical_docs"
        elif 'CFBD_INTEGRATION' in path_parts:
            return "docs", "api_docs"
        else:
            return "misc", "uncategorized"

    def analyze_python_dependencies(self, file_path: str) -> List[str]:
        """Analyze Python file for local dependencies"""
        dependencies = []

        if not file_path.endswith('.py'):
            return dependencies

        try:
            full_path = self.project_root / file_path
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('project_management'):
                            dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.startswith('project_management'):
                        dependencies.append(node.module)

        except Exception as e:
            print(f"⚠️  Could not analyze dependencies for {file_path}: {e}")

        return dependencies

    def determine_priority(self, file_info: FileInfo, category: str, referenced_by_claude: bool) -> str:
        """Determine file priority based on usage and references"""
        if referenced_by_claude:
            return "high"
        elif category == "core_tools":
            return "high"
        elif category in ["config", "quality_assurance"]:
            return "medium"
        elif category == "archive":
            return "low"
        else:
            return "medium"

    def categorize_files(self) -> List[FileInfo]:
        """Main categorization logic"""
        print("🔍 Starting file categorization...")

        # Scan all files
        files = self.scan_directory()
        print(f"📁 Found {len(files)} files")

        # Get CLAUDE.md references
        claude_references = self.analyze_claude_md_references()
        print(f"📖 CLAUDE.md references {len(claude_references)} files")

        # Categorize each file
        for file_info in files:
            # Category and subcategory
            category, subcategory = self.categorize_by_location_and_name(file_info)
            file_info.category = category
            file_info.subcategory = subcategory

            # Dependencies
            file_info.dependencies = self.analyze_python_dependencies(file_info.path)

            # CLAUDE.md reference check
            file_info.referenced_by_claude_md = file_info.name in claude_references

            # Priority
            file_info.priority = self.determine_priority(file_info, category, file_info.referenced_by_claude_md)

            # Purpose
            file_info.purpose = self._determine_purpose(file_info, category, subcategory)

            # Destination in new structure
            file_info.destination = self._determine_destination(file_info, category, subcategory)

        self.categorized_files = files
        return files

    def _determine_purpose(self, file_info: FileInfo, category: str, subcategory: str) -> str:
        """Determine the purpose of a file"""
        purposes = {
            ("core_tools", "main_cli"): "Main data workflow orchestration CLI",
            ("core_tools", "demo_system"): "Agent system demonstration and onboarding",
            ("core_tools", "validation"): "Quick system health validation",
            ("config", "configuration"): "System configuration and settings",
            ("config", "model_config"): "ML model configuration and features",
            ("quality_assurance", "testing"): "System testing and validation",
            ("quality_assurance", "validation"): "Quality assurance and verification",
            ("docs", "user_guide"): "User documentation and guides",
            ("docs", "technical_docs"): "Technical documentation",
            ("docs", "planning"): "Planning and roadmap documents",
            ("agents", "management_agents"): "Project management and coordination agents",
            ("archive", "historical_docs"): "Historical documentation and logs"
        }

        return purposes.get((category, subcategory), f"{category.replace('_', ' ')} file")

    def _determine_destination(self, file_info: FileInfo, category: str, subcategory: str) -> str:
        """Determine where file should go in new structure"""
        destinations = {
            ("core_tools", "main_cli"): "core_tools/data_workflows.py",
            ("core_tools", "demo_system"): "core_tools/demo_agent_system.py",
            ("core_tools", "validation"): "core_tools/test_agents.py",
            ("config", "configuration"): "config/",
            ("config", "model_config"): "config/",
            ("quality_assurance", "testing"): "quality_assurance/",
            ("quality_assurance", "validation"): "quality_assurance/",
            ("docs", "user_guide"): "docs/user_guides/",
            ("docs", "technical_docs"): "docs/technical_docs/",
            ("docs", "planning"): "docs/comprehensive_guides/",
            ("agents", "management_agents"): "agents/",
            ("archive", "historical_docs"): "archive/"
        }

        base_dest = destinations.get((category, subcategory), f"{category}/")

        # Keep original filename if not already specified
        if base_dest.endswith('/'):
            return f"{base_dest}{file_info.name}"
        else:
            return base_dest

    def generate_report(self) -> Dict:
        """Generate categorization report"""
        if not self.categorized_files:
            self.categorize_files()

        # Summary statistics
        total_files = len(self.categorized_files)
        by_category = {}
        by_priority = {"high": 0, "medium": 0, "low": 0}
        claude_referenced = 0
        total_size = 0

        for file_info in self.categorized_files:
            by_category[file_info.category] = by_category.get(file_info.category, 0) + 1
            by_priority[file_info.priority] += 1
            if file_info.referenced_by_claude_md:
                claude_referenced += 1
            total_size += file_info.size_bytes

        report = {
            "summary": {
                "total_files": total_files,
                "by_category": by_category,
                "by_priority": by_priority,
                "claude_referenced": claude_referenced,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "generated_at": datetime.now().isoformat()
            },
            "files": [asdict(f) for f in self.categorized_files]
        }

        return report

    def save_report(self, output_path: str = None):
        """Save categorization report to file"""
        if output_path is None:
            output_path = self.project_root / "project_management" / "categorization_report.json"

        report = self.generate_report()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"📄 Categorization report saved to: {output_path}")
        return output_path

def main():
    """Main execution function"""
    print("🚀 File Categorization Agent - Starting Analysis")
    print("=" * 60)

    agent = FileCategorizationAgent()

    # Run categorization
    files = agent.categorize_files()

    # Generate and save report
    report_path = agent.save_report()

    # Print summary
    report = agent.generate_report()
    summary = report["summary"]

    print(f"\n📊 CATEGORIZATION SUMMARY")
    print(f"   Total files: {summary['total_files']}")
    print(f"   Total size: {summary['total_size_mb']} MB")
    print(f"   CLAUDE.md references: {summary['claude_referenced']}")
    print(f"   High priority: {summary['by_priority']['high']}")
    print(f"   Medium priority: {summary['by_priority']['medium']}")
    print(f"   Low priority: {summary['by_priority']['low']}")

    print(f"\n📁 BY CATEGORY:")
    for category, count in summary['by_category'].items():
        print(f"   {category}: {count} files")

    print(f"\n📄 Full report saved to: {report_path}")
    print("✅ File Categorization Agent - Analysis Complete!")

if __name__ == "__main__":
    main()