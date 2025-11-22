#!/usr/bin/env python3.13
"""
File Reorganization Agent - Phase 3 of Project Management Reorganization

This agent executes the file reorganization plan by moving files to their new locations
and updating import statements where necessary.
"""

import os
import json
import shutil
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ReorganizationAction:
    """Represents a file reorganization action"""
    action_type: str  # move, copy, archive, consolidate
    source_path: str
    destination_path: str
    reason: str
    confidence: float
    status: str = "pending"  # pending, completed, failed
    error_message: str = ""

class FileReorganizationAgent:
    """Executes file reorganization based on categorization and consolidation plans"""

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.pm_directory = self.project_root / "project_management"
        self.backup_directory = self.pm_directory / "backup_before_reorganization"
        self.actions = []
        self.completed_actions = []
        self.failed_actions = []

    def create_backup(self) -> str:
        """Create a complete backup before reorganization"""
        print("💾 Creating backup before reorganization...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.pm_directory / f"backup_{timestamp}"

        # Avoid backing up the backup directory itself
        exclude_patterns = [
            "backup_*",
            "categorization_report.json",
            "content_analysis_report.json",
            "consolidation_plan.json",
            "*_agent.py"
        ]

        try:
            # Create backup directory
            backup_path.mkdir(exist_ok=True)

            # Copy all files except our analysis files and existing backups
            copied_items = 0
            for item in self.pm_directory.iterdir():
                if item.name.startswith("backup_") or item.name.endswith("_agent.py"):
                    continue
                if item.name in ["categorization_report.json", "content_analysis_report.json", "consolidation_plan.json"]:
                    continue

                dest = backup_path / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                    copied_items += 1
                elif item.is_dir():
                    shutil.copytree(item, dest, ignore=shutil.ignore_patterns(*exclude_patterns))
                    copied_items += 1

            print(f"✅ Backup created at: {backup_path}")
            print(f"   Backed up {copied_items} items")
            return str(backup_path)

        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return ""

    def load_reorganization_plan(self) -> Dict:
        """Load the categorization and consolidation plans"""
        try:
            # Load categorization report
            cat_path = self.pm_directory / "categorization_report.json"
            with open(cat_path, 'r', encoding='utf-8') as f:
                categorization = json.load(f)

            # Load consolidation plan
            con_path = self.pm_directory / "consolidation_plan.json"
            with open(con_path, 'r', encoding='utf-8') as f:
                consolidation = json.load(f)

            return {
                "categorization": categorization,
                "consolidation": consolidation
            }

        except Exception as e:
            print(f"❌ Failed to load reorganization plans: {e}")
            return {}

    def create_new_directory_structure(self) -> bool:
        """Create the new directory structure"""
        print("📁 Creating new directory structure...")

        new_directories = [
            "core_tools",
            "config",
            "quality_assurance",
            "agents",
            "docs/user_guides",
            "docs/technical_docs",
            "docs/comprehensive_guides",
            "archive"
        ]

        try:
            for dir_path in new_directories:
                full_path = self.pm_directory / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"   Created: {dir_path}")

            return True

        except Exception as e:
            print(f"❌ Failed to create directory structure: {e}")
            return False

    def plan_file_moves(self, categorization: Dict) -> List[ReorganizationAction]:
        """Plan file moves based on categorization"""
        actions = []

        files_info = categorization.get("files", [])

        for file_info in files_info:
            source_path = file_info.get("path", "")
            category = file_info.get("category", "")
            priority = file_info.get("priority", "medium")
            destination = file_info.get("destination", "")

            # Skip if no clear destination
            if not destination:
                continue

            # Determine action based on category and priority
            if category == "archive" or priority == "low":
                action = ReorganizationAction(
                    action_type="archive",
                    source_path=source_path,
                    destination_path=f"archive/{Path(source_path).name}",
                    reason="Archive historical content",
                    confidence=0.9
                )
            elif category in ["core_tools", "config", "quality_assurance"]:
                # High priority core files
                final_dest = self._adjust_core_destination(destination, category)
                action = ReorganizationAction(
                    action_type="move",
                    source_path=source_path,
                    destination_path=final_dest,
                    reason=f"Move {category} file to new structure",
                    confidence=0.95
                )
            elif category == "docs":
                # Documentation files - most will be consolidated
                if priority == "high":
                    action = ReorganizationAction(
                        action_type="move",
                        source_path=source_path,
                        destination_path=f"docs/{Path(source_path).name}",
                        reason="Keep important documentation",
                        confidence=0.8
                    )
                else:
                    # Will be handled by consolidation agent
                    continue
            elif category == "agents":
                # Agent files - keep a subset, archive others
                if priority == "high":
                    action = ReorganizationAction(
                        action_type="move",
                        source_path=source_path,
                        destination_path=f"agents/{Path(source_path).name}",
                        reason="Keep essential agent files",
                        confidence=0.8
                    )
                else:
                    action = ReorganizationAction(
                        action_type="archive",
                        source_path=source_path,
                        destination_path=f"archive/agents/{Path(source_path).name}",
                        reason="Archive non-essential agent files",
                        confidence=0.9
                    )
            else:
                # Default: move to appropriate location
                action = ReorganizationAction(
                    action_type="move",
                    source_path=source_path,
                    destination_path=destination,
                    reason="General file reorganization",
                    confidence=0.7
                )

            actions.append(action)

        return actions

    def _adjust_core_destination(self, destination: str, category: str) -> str:
        """Adjust destination for core files based on new structure"""
        source_name = Path(destination).name

        if category == "core_tools":
            # Core tools go directly to core_tools/
            return f"core_tools/{source_name}"
        elif category == "config":
            # Config files go to config/
            return f"config/{source_name}"
        elif category == "quality_assurance":
            # QA files go to quality_assurance/
            return f"quality_assurance/{source_name}"
        else:
            return destination

    def execute_action(self, action: ReorganizationAction) -> bool:
        """Execute a single reorganization action"""
        source_full = self.project_root / action.source_path
        dest_full = self.project_root / action.destination_path

        try:
            # Ensure destination directory exists
            dest_full.parent.mkdir(parents=True, exist_ok=True)

            if action.action_type == "move":
                # Move file
                shutil.move(str(source_full), str(dest_full))
                print(f"   MOVED: {action.source_path} → {action.destination_path}")

            elif action.action_type == "archive":
                # Move to archive
                shutil.move(str(source_full), str(dest_full))
                print(f"   ARCHIVED: {action.source_path} → {action.destination_path}")

            elif action.action_type == "copy":
                # Copy file (for important files we want to preserve)
                shutil.copy2(str(source_full), str(dest_full))
                print(f"   COPIED: {action.source_path} → {action.destination_path}")

            action.status = "completed"
            return True

        except Exception as e:
            action.status = "failed"
            action.error_message = str(e)
            print(f"   FAILED: {action.source_path} → {action.destination_path} ({e})")
            return False

    def update_python_imports(self) -> None:
        """Update Python import statements after reorganization"""
        print("🔄 Updating Python import statements...")

        import_updates = {
            "project_management/core_tools/": "project_management/core_tools/",
            "project_management/quality_assurance/": "project_management/quality_assurance/",
            "project_management/config/": "project_management/config/",
        }

        # Find all Python files in the project
        python_files = list(self.project_root.rglob("*.py"))

        updated_files = 0
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                original_content = content

                # Update import statements
                for old_path, new_path in import_updates.items():
                    content = content.replace(old_path, new_path)

                # Write back if changed
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    updated_files += 1
                    print(f"   Updated imports in: {py_file.relative_to(self.project_root)}")

            except Exception as e:
                print(f"   ⚠️  Could not update {py_file}: {e}")

        print(f"   Updated {updated_files} Python files")

    def create_readme_files(self) -> None:
        """Create README files for new directory structure"""
        print("📝 Creating README files...")

        readmes = {
            "core_tools/README.md": """# Core Tools

Essential working scripts for Script Ohio 2.0 operations.

## Files

- `data_workflows.py` - Main CLI for data operations
- `demo_agent_system.py` - Complete agent system demonstration
- `test_agents.py` - Quick system validation

## Usage

See main project CLAUDE.md for usage examples.
""",

            "config/README.md": """# Configuration

System configuration and model settings.

## Files

- Model configuration files
- Feature definitions
- Environment setup

## Usage

Configuration files are loaded automatically by the system.
""",

            "quality_assurance/README.md": """# Quality Assurance

Testing and validation tools.

## Files

- `test_fixed_system.py` - Comprehensive system validation
- Other testing utilities

## Usage

Run validation with: `python project_management/quality_assurance/test_fixed_system.py`
""",

            "agents/README.md": """# Management Agents

Project management and coordination agents.

## Purpose

Essential agent systems for project management and automation.
""",

            "docs/README.md": """# Documentation

Consolidated documentation and guides.

## Structure

- `user_guides/` - User-facing documentation
- `technical_docs/` - Technical documentation
- `comprehensive_guides/` - Consolidated historical content

## Usage

See the comprehensive guides for complete project history and insights.
""",

            "archive/README.md": """# Archive

Historical content and development artifacts.

## Purpose

Preserved for reference but not actively used in day-to-day operations.

## Contents

- Historical reports and logs
- Development artifacts
- Non-essential documentation

## Note

Content here has been consolidated into comprehensive guides in the main docs/ directory.
"""
        }

        for file_path, content in readmes.items():
            full_path = self.pm_directory / file_path
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"   Created: {file_path}")
            except Exception as e:
                print(f"   ⚠️  Could not create {file_path}: {e}")

    def generate_reorganization_report(self) -> Dict:
        """Generate a report of the reorganization actions"""
        return {
            "summary": {
                "total_actions": len(self.actions),
                "completed": len(self.completed_actions),
                "failed": len(self.failed_actions),
                "success_rate": len(self.completed_actions) / len(self.actions) if self.actions else 0,
                "timestamp": datetime.now().isoformat()
            },
            "completed_actions": [
                {
                    "action": a.action_type,
                    "source": a.source_path,
                    "destination": a.destination_path,
                    "reason": a.reason
                }
                for a in self.completed_actions
            ],
            "failed_actions": [
                {
                    "action": a.action_type,
                    "source": a.source_path,
                    "destination": a.destination_path,
                    "error": a.error_message
                }
                for a in self.failed_actions
            ]
        }

    def execute_reorganization(self, dry_run: bool = False) -> bool:
        """Execute the complete reorganization"""
        print("🚀 Starting File Reorganization")
        print("=" * 60)

        if dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made")

        # Load plans
        plans = self.load_reorganization_plan()
        if not plans:
            print("❌ Could not load reorganization plans")
            return False

        # Create backup (unless dry run)
        if not dry_run:
            backup_path = self.create_backup()
            if not backup_path:
                print("❌ Backup failed - aborting reorganization")
                return False

        # Create new directory structure
        if not self.create_new_directory_structure():
            return False

        # Plan file moves
        categorization = plans.get("categorization", {})
        self.actions = self.plan_file_moves(categorization)

        print(f"\n📋 Planned {len(self.actions)} reorganization actions")

        # Execute actions
        if dry_run:
            print("\n🔍 DRY RUN - Actions that would be executed:")
            for action in self.actions:
                print(f"   {action.action_type.upper()}: {action.source_path} → {action.destination_path}")
            return True

        print(f"\n⚡ Executing reorganization actions...")
        for i, action in enumerate(self.actions, 1):
            print(f"[{i:3d}/{len(self.actions)}]", end=" ")

            if self.execute_action(action):
                self.completed_actions.append(action)
            else:
                self.failed_actions.append(action)

            # Small delay to avoid filesystem issues
            time.sleep(0.01)

        # Update Python imports
        self.update_python_imports()

        # Create README files
        self.create_readme_files()

        # Generate report
        report = self.generate_reorganization_report()
        report_path = self.pm_directory / "reorganization_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        # Print summary
        print(f"\n📊 REORGANIZATION SUMMARY")
        print(f"   Total actions: {report['summary']['total_actions']}")
        print(f"   Completed: {report['summary']['completed']}")
        print(f"   Failed: {report['summary']['failed']}")
        print(f"   Success rate: {report['summary']['success_rate']:.1%}")
        print(f"   Report saved: {report_path}")

        return len(self.failed_actions) == 0

def main():
    """Main execution function"""
    import argparse

    parser = argparse.ArgumentParser(description="File Reorganization Agent")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    print("🚀 File Reorganization Agent - Starting")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual changes will be made")
    print("=" * 60)

    agent = FileReorganizationAgent()

    success = agent.execute_reorganization(dry_run=args.dry_run)

    if args.dry_run:
        print("\n🔍 DRY RUN COMPLETE - Use without --dry-run to execute reorganization")
    elif success:
        print("\n✅ File Reorganization Agent - Reorganization Complete!")
    else:
        print("\n❌ File Reorganization Agent - Some operations failed")

if __name__ == "__main__":
    main()