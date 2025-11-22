#!/usr/bin/env python3
"""
Project File Organization Workflow

This script orchestrates the file organization process using our specialized agents.
It demonstrates a practical multi-agent workflow for organizing project files.
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add current directory to Python path
current_dir = Path.cwd()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FileOrganizationOrchestrator:
    """
    Simple orchestrator for the file organization workflow.
    Demonstrates practical multi-agent coordination.
    """

    def __init__(self):
        self.project_root = Path.cwd()
        self.organization_log = []
        self.validation_results = []

        # Initialize agents
        try:
            from agents.file_organization_agent import create_file_organization_agent
            from agents.validation_agent import create_validation_agent

            self.file_org_agent = create_file_organization_agent('orchestrator_file_org')
            self.validation_agent = create_validation_agent('orchestrator_validation')

            logger.info("✅ All agents initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize agents: {e}")
            raise

    def run_organization_workflow(self) -> Dict[str, Any]:
        """Run the complete file organization workflow."""

        logger.info("🚀 Starting File Organization Workflow")
        logger.info("=" * 60)

        workflow_start = time.time()
        workflow_results = {}

        try:
            # Phase 1: Create missing directories
            logger.info("📁 Phase 1: Creating missing directory structure...")
            workflow_results['directories'] = self._create_directories()

            # Phase 2: Organize files
            logger.info("📋 Phase 2: Organizing files into proper directories...")
            workflow_results['file_organization'] = self._organize_files()

            # Phase 3: Validate organization
            logger.info("✅ Phase 3: Validating organization integrity...")
            workflow_results['validation'] = self._validate_organization()

            # Phase 4: System maintenance
            logger.info("🔧 Phase 4: System maintenance and cleanup...")
            workflow_results['maintenance'] = self._system_maintenance()

            # Generate final report
            workflow_results['workflow_summary'] = self._generate_workflow_summary(
                time.time() - workflow_start
            )

            logger.info("=" * 60)
            logger.info("🎉 File Organization Workflow Completed Successfully!")
            self._log_completion_summary(workflow_results)

            return {
                'status': 'success',
                'results': workflow_results,
                'execution_time': time.time() - workflow_start
            }

        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': time.time() - workflow_start
            }

    def _create_directories(self) -> Dict[str, Any]:
        """Create missing directory structure using file organization agent."""

        try:
            result = self.file_org_agent._execute_action(
                action="create_missing_directories",
                parameters={},
                user_context={"workflow_phase": "directory_creation"}
            )

            self.organization_log.append({
                "phase": "directory_creation",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

            if result['status'] == 'success':
                created = result['result']['total_created']
                logger.info(f"✅ Created {created} missing directories")
                return {"success": True, "directories_created": created}
            else:
                logger.error(f"❌ Directory creation failed: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error')}

        except Exception as e:
            logger.error(f"❌ Directory creation error: {e}")
            return {"success": False, "error": str(e)}

    def _organize_files(self) -> Dict[str, Any]:
        """Organize files using file organization agent."""

        try:
            # First classify files
            classification_result = self.file_org_agent._execute_action(
                action="classify_root_files",
                parameters={},
                user_context={"workflow_phase": "file_classification"}
            )

            if classification_result['status'] != 'success':
                raise Exception(f"File classification failed: {classification_result.get('error')}")

            total_files = classification_result['result']['total_files']
            logger.info(f"📊 Found {total_files} files to organize")

            # Then organize them
            organization_result = self.file_org_agent._execute_action(
                action="organize_into_directories",
                parameters={},
                user_context={"workflow_phase": "file_organization"}
            )

            self.organization_log.extend(self.file_org_agent.organization_log)

            if organization_result['status'] == 'success':
                moved = organization_result['result']['total_moved']
                failed = organization_result['result']['total_failed']

                logger.info(f"✅ Moved {moved} files successfully")
                if failed > 0:
                    logger.warning(f"⚠️ {failed} files failed to move")

                return {
                    "success": True,
                    "files_moved": moved,
                    "files_failed": failed,
                    "total_found": total_files,
                    "moved_files": organization_result['result']['moved_files']
                }
            else:
                raise Exception(f"File organization failed: {organization_result.get('error')}")

        except Exception as e:
            logger.error(f"❌ File organization error: {e}")
            return {"success": False, "error": str(e)}

    def _validate_organization(self) -> Dict[str, Any]:
        """Validate organization using validation agent."""

        try:
            validation_results = {}

            # Validate file moves
            moved_files = (self.organization_log[-1] if self.organization_log
                          else {}).get('result', {}).get('moved_files', {})

            if moved_files:
                file_validation = self.validation_agent._execute_action(
                    action="validate_file_moves",
                    parameters={"moved_files": moved_files},
                    user_context={"workflow_phase": "validation"}
                )

                validation_results['file_moves'] = file_validation
                if file_validation['status'] == 'success':
                    success_rate = file_validation['result']['success_rate']
                    logger.info(f"✅ File validation: {success_rate:.1%} success rate")

            # Validate import integrity
            import_validation = self.validation_agent._execute_action(
                action="validate_import_integrity",
                parameters={},
                user_context={"workflow_phase": "validation"}
            )

            validation_results['import_integrity'] = import_validation
            if import_validation['status'] == 'success':
                success_rate = import_validation['result']['import_success_rate']
                logger.info(f"✅ Import validation: {success_rate:.1%} success rate")

            self.validation_results.extend(self.validation_agent.validation_results)

            return {
                "success": True,
                "file_validation": validation_results.get('file_moves', {}).get('result', {}),
                "import_validation": validation_results.get('import_integrity', {}).get('result', {}),
                "overall_success": all(
                    result.get('result', {}).get('success_rate', 0) >= 0.9
                    for result in validation_results.values()
                    if result.get('status') == 'success'
                )
            }

        except Exception as e:
            logger.error(f"❌ Validation error: {e}")
            return {"success": False, "error": str(e)}

    def _system_maintenance(self) -> Dict[str, Any]:
        """Perform system maintenance tasks."""

        try:
            maintenance_results = {}

            # Update .gitignore
            gitignore_result = self.validation_agent._execute_action(
                action="update_gitignore",
                parameters={},
                user_context={"workflow_phase": "maintenance"}
            )

            maintenance_results['gitignore'] = gitignore_result
            if gitignore_result['status'] == 'success':
                updated = gitignore_result['result']['gitignore_updated']
                logger.info(f"✅ .gitignore updated: {updated}")

            return {
                "success": True,
                "gitignore_updated": gitignore_result['result'].get('gitignore_updated', False),
                "maintenance_details": maintenance_results
            }

        except Exception as e:
            logger.error(f"❌ System maintenance error: {e}")
            return {"success": False, "error": str(e)}

    def _generate_workflow_summary(self, execution_time: float) -> Dict[str, Any]:
        """Generate comprehensive workflow summary."""

        return {
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "total_organization_actions": len(self.organization_log),
            "total_validation_results": len(self.validation_results),
            "workflow_phases_completed": [
                "directory_creation",
                "file_classification",
                "file_organization",
                "validation",
                "system_maintenance"
            ]
        }

    def _log_completion_summary(self, workflow_results: Dict[str, Any]):
        """Log final completion summary."""

        logger.info("📊 Workflow Summary:")
        logger.info(f"   Execution Time: {workflow_results['workflow_summary']['execution_time']:.2f}s")
        logger.info(f"   Organization Actions: {workflow_results['workflow_summary']['total_organization_actions']}")

        if workflow_results.get('file_organization', {}).get('success'):
            moved = workflow_results['file_organization']['files_moved']
            logger.info(f"   Files Organized: {moved}")

        if workflow_results.get('validation', {}).get('success'):
            logger.info(f"   Validation Status: ✅ PASSED")

        if workflow_results.get('maintenance', {}).get('success'):
            gitignore_updated = workflow_results['maintenance']['gitignore_updated']
            logger.info(f"   .gitignore Updated: {gitignore_updated}")


def main():
    """Main function to run the file organization workflow."""

    print("🗂️  Script Ohio 2.0 - File Organization Workflow")
    print("=" * 60)
    print("This workflow will organize project files using a multi-agent system.")
    print()

    # Confirm with user before proceeding
    response = input("Do you want to proceed with file organization? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("File organization cancelled.")
        return

    print()
    print("Starting file organization workflow...")
    print()

    try:
        orchestrator = FileOrganizationOrchestrator()
        result = orchestrator.run_organization_workflow()

        if result['status'] == 'success':
            print("\n🎉 File organization completed successfully!")
            print(f"Total execution time: {result['execution_time']:.2f}s")
        else:
            print(f"\n❌ File organization failed: {result.get('error', 'Unknown error')}")
            return 1

    except Exception as e:
        print(f"\n💥 Critical error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)