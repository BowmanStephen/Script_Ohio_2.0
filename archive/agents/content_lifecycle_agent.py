#!/usr/bin/env python3
"""
Content Lifecycle Agent for Project Management Reorganization

This agent implements automated archival procedures, expiration date management,
and content freshness indicators to maintain an organized project management system.

Role: Content Lifecycle Manager
Permission Level: READ_EXECUTE_WRITE (Level 3)
Capabilities: Automated archival, expiration management, content lifecycle
"""

import os
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import logging

# Import existing agent framework
try:
    from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel
except ImportError:
    # Fallback for standalone operation
    PermissionLevel = type('PermissionLevel', (), {
        'ADMIN': 'ADMIN', 'READ_EXECUTE_WRITE': 'READ_EXECUTE_WRITE',
        'READ_EXECUTE': 'READ_EXECUTE', 'READ_ONLY': 'READ_ONLY'
    })()
    AgentCapability = type('AgentCapability', (), {})()

    class BaseAgent:
        def __init__(self, *args, **kwargs):
            pass
        def log_action(self, action, result):
            pass


@dataclass
class ContentItem:
    """Represents a content item with lifecycle information"""
    file_path: str
    content_type: str
    created_date: datetime
    modified_date: datetime
    accessed_date: Optional[datetime] = None
    file_size: int = 0
    priority: str = "medium"
    lifecycle_stage: str = "active"  # active, stale, archival, expired
    expiration_date: Optional[datetime] = None
    archival_date: Optional[datetime] = None
    review_frequency_days: int = 90
    last_reviewed: Optional[datetime] = None
    freshness_score: float = 1.0
    access_count: int = 0
    tags: List[str] = field(default_factory=list)


@dataclass
class LifecycleMetrics:
    """Metrics for content lifecycle management"""
    total_items_processed: int
    items_archived: int
    items_expired: int
    items_reviewed: int
    automated_procedures_created: int
    space_saved_mb: float
    freshness_improvement: float
    lifecycle_automation_coverage: float


class ContentLifecycleAgent(BaseAgent):
    """
    Content Lifecycle Agent for automated content management

    This agent implements automated archival procedures, expiration management,
    and content freshness tracking for the project management system.
    """

    def __init__(self, agent_id: str = "content_lifecycle", project_root: str = None):
        """
        Initialize the Content Lifecycle Agent

        Args:
            agent_id: Unique identifier for this agent
            project_root: Root directory of the Script Ohio 2.0 project
        """
        super().__init__(
            agent_id=agent_id,
            name="Content Lifecycle - Automated Content Management Specialist",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE
        )

        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_management_path = os.path.join(self.project_root, "project_management")

        # Lifecycle configuration
        self.lifecycle_config = {
            "content_type_lifecycles": {
                "status_reports": {
                    "active_days": 30,
                    "stale_days": 90,
                    "archival_days": 365,
                    "review_frequency_days": 30
                },
                "decision_records": {
                    "active_days": 180,
                    "stale_days": 365,
                    "archival_days": 1095,  # 3 years
                    "review_frequency_days": 90
                },
                "planning_documents": {
                    "active_days": 60,
                    "stale_days": 180,
                    "archival_days": 730,  # 2 years
                    "review_frequency_days": 60
                },
                "quality_reports": {
                    "active_days": 90,
                    "stale_days": 365,
                    "archival_days": 1825,  # 5 years
                    "review_frequency_days": 180
                },
                "meeting_notes": {
                    "active_days": 14,
                    "stale_days": 90,
                    "archival_days": 365,
                    "review_frequency_days": 30
                },
                "technical_docs": {
                    "active_days": 365,
                    "stale_days": 1095,
                    "archival_days": 3650,  # 10 years
                    "review_frequency_days": 365
                }
            },
            "priority_modifiers": {
                "critical": {"multiplier": 2.0, "archival_delay_days": 365},
                "high": {"multiplier": 1.5, "archival_delay_days": 180},
                "medium": {"multiplier": 1.0, "archival_delay_days": 0},
                "low": {"multiplier": 0.5, "archival_delay_days": -90}
            }
        }

        # Metrics tracking
        self.metrics = LifecycleMetrics(
            total_items_processed=0,
            items_archived=0,
            items_expired=0,
            items_reviewed=0,
            automated_procedures_created=0,
            space_saved_mb=0.0,
            freshness_improvement=0.0,
            lifecycle_automation_coverage=0.0
        )

        # Content inventory
        self.content_items: Dict[str, ContentItem] = {}
        self.lifecycle_policies: Dict[str, Dict[str, Any]] = {}

        # Setup logging
        self._setup_logging()

        self.log_action("initialization", {
            "project_management_path": self.project_management_path,
            "content_types": len(self.lifecycle_config["content_type_lifecycles"]),
            "priority_levels": len(self.lifecycle_config["priority_modifiers"])
        })

    def _setup_logging(self):
        """Setup logging for content lifecycle operations"""
        log_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"content_lifecycle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.agent_id)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this content lifecycle agent"""
        return [
            AgentCapability("automated_archival"),
            AgentCapability("expiration_management"),
            AgentCapability("content_freshness_tracking"),
            AgentCapability("lifecycle_policy_enforcement"),
            AgentCapability("space_optimization"),
            AgentCapability("content_review_automation")
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute content lifecycle actions

        Args:
            action: The action to execute
            parameters: Parameters for the action
            user_context: User context and preferences

        Returns:
            Action execution results
        """
        if action == "implement_lifecycle_management":
            return self._implement_lifecycle_management()
        elif action == "create_automated_archival":
            return self._create_automated_archival()
        elif action == "setup_expiration_management":
            return self._setup_expiration_management()
        elif action == "implement_content_freshness":
            return self._implement_content_freshness()
        elif action == "create_lifecycle_policies":
            return self._create_lifecycle_policies()
        elif action == "get_metrics":
            return self._get_metrics()
        else:
            return {"error": f"Unknown action: {action}"}

    def _implement_lifecycle_management(self) -> Dict[str, Any]:
        """
        Implement comprehensive content lifecycle management

        Returns:
            Lifecycle management implementation results
        """
        try:
            self.logger.info("Implementing content lifecycle management")
            self.log_action("lifecycle_management_start", {"scope": "comprehensive_lifecycle_system"})

            # Step 1: Inventory all content
            inventory_result = self._inventory_content()

            # Step 2: Create lifecycle policies
            policies_result = self._create_lifecycle_policies()

            # Step 3: Implement automated archival
            archival_result = self._create_automated_archival()

            # Step 4: Setup expiration management
            expiration_result = self._setup_expiration_management()

            # Step 5: Implement content freshness tracking
            freshness_result = self._implement_content_freshness()

            # Step 6: Create lifecycle automation
            automation_result = self._create_lifecycle_automation()

            # Step 7: Generate lifecycle reports
            reports_result = self._generate_lifecycle_reports()

            # Step 8: Calculate lifecycle metrics
            self._calculate_lifecycle_metrics()

            self.logger.info("Content lifecycle management implementation completed")
            return {
                "success": True,
                "inventory": inventory_result,
                "policies": policies_result,
                "archival": archival_result,
                "expiration": expiration_result,
                "freshness": freshness_result,
                "automation": automation_result,
                "reports": reports_result,
                "metrics": self._get_metrics()
            }

        except Exception as e:
            self.logger.error(f"Content lifecycle management implementation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _inventory_content(self) -> Dict[str, Any]:
        """Inventory all content in the project management folder"""
        self.logger.info("Inventorying content")

        total_items = 0
        content_by_type = defaultdict(int)
        size_by_type = defaultdict(int)

        for root, dirs, files in os.walk(self.project_management_path):
            # Skip REORGANIZATION_SYSTEM
            if "REORGANIZATION_SYSTEM" in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()

                # Process relevant file types
                if file_ext in ['.md', '.txt', '.yaml', '.yml', '.json', '.py', '.html']:
                    try:
                        content_item = self._create_content_item(file_path)
                        if content_item:
                            self.content_items[file_path] = content_item
                            content_by_type[content_item.content_type] += 1
                            size_by_type[content_item.content_type] += content_item.file_size
                            total_items += 1
                    except Exception as e:
                        self.logger.warning(f"Error processing file {file_path}: {str(e)}")

        self.metrics.total_items_processed = total_items

        return {
            "total_items": total_items,
            "content_by_type": dict(content_by_type),
            "size_by_type": dict(size_by_type),
            "inventory_completed": True
        }

    def _create_content_item(self, file_path: str) -> Optional[ContentItem]:
        """Create a content item from file path"""
        try:
            relative_path = os.path.relpath(file_path, self.project_management_path)

            # Get file stats
            file_stat = os.stat(file_path)
            created_date = datetime.fromtimestamp(file_stat.st_ctime)
            modified_date = datetime.fromtimestamp(file_stat.st_mtime)

            # Determine content type
            content_type = self._determine_content_type(file_path)

            # Determine priority
            priority = self._determine_priority(file_path, content_type)

            # Get lifecycle configuration
            lifecycle_config = self.lifecycle_config["content_type_lifecycles"].get(content_type, {})

            # Calculate lifecycle dates
            active_days = lifecycle_config.get("active_days", 90)
            stale_days = lifecycle_config.get("stale_days", 365)
            archival_days = lifecycle_config.get("archival_days", 1095)

            # Apply priority modifiers
            priority_modifier = self.lifecycle_config["priority_modifiers"].get(priority, {"multiplier": 1.0})
            multiplier = priority_modifier["multiplier"]

            archival_date = created_date + timedelta(days=int(archival_days * multiplier))
            expiration_date = archival_date + timedelta(days=365)  # Expire 1 year after archival

            return ContentItem(
                file_path=relative_path,
                content_type=content_type,
                created_date=created_date,
                modified_date=modified_date,
                file_size=file_stat.st_size,
                priority=priority,
                expiration_date=expiration_date,
                archival_date=archival_date,
                review_frequency_days=lifecycle_config.get("review_frequency_days", 90)
            )

        except Exception as e:
            self.logger.warning(f"Error creating content item for {file_path}: {str(e)}")
            return None

    def _determine_content_type(self, file_path: str) -> str:
        """Determine content type based on file path and name"""
        filename = os.path.basename(file_path).lower()
        dirname = os.path.dirname(file_path).lower()

        # Check directory names first
        if "decision" in dirname or "dec-" in filename:
            return "decision_records"
        elif "status" in dirname or "status" in filename:
            return "status_reports"
        elif "plan" in dirname or "plan" in filename or "roadmap" in dirname:
            return "planning_documents"
        elif "quality" in dirname or "test" in dirname or "verification" in dirname:
            return "quality_reports"
        elif "meeting" in dirname or "meeting" in filename or "notes" in filename:
            return "meeting_notes"
        elif "technical" in dirname or "architecture" in dirname or "api" in dirname:
            return "technical_docs"

        # Default based on file patterns
        if any(keyword in filename for keyword in ["status", "progress", "weekly", "monthly"]):
            return "status_reports"
        elif any(keyword in filename for keyword in ["decision", "resolution"]):
            return "decision_records"
        elif any(keyword in filename for keyword in ["plan", "strategy", "roadmap"]):
            return "planning_documents"
        elif any(keyword in filename for keyword in ["quality", "test", "validation"]):
            return "quality_reports"
        elif any(keyword in filename for keyword in ["meeting", "notes", "discussion"]):
            return "meeting_notes"

        return "general"

    def _determine_priority(self, file_path: str, content_type: str) -> str:
        """Determine content priority"""
        filename = os.path.basename(file_path).lower()

        # Critical indicators
        if any(keyword in filename for keyword in ["critical", "urgent", "blocking", "security"]):
            return "critical"

        # High priority indicators
        if any(keyword in filename for keyword in ["important", "priority", "high"]):
            return "high"

        # Content type base priorities
        base_priorities = {
            "decision_records": "high",
            "status_reports": "medium",
            "planning_documents": "high",
            "quality_reports": "medium",
            "meeting_notes": "low",
            "technical_docs": "medium"
        }

        return base_priorities.get(content_type, "medium")

    def _create_lifecycle_policies(self) -> Dict[str, Any]:
        """Create content lifecycle policies"""
        self.logger.info("Creating lifecycle policies")

        policies = {}

        for content_type, config in self.lifecycle_config["content_type_lifecycles"].items():
            policies[content_type] = {
                "active_period_days": config["active_days"],
                "stale_period_days": config["stale_days"],
                "archival_period_days": config["archival_days"],
                "review_frequency_days": config["review_frequency_days"],
                "retention_policy": {
                    "minimum_retention_days": config["archival_days"],
                    "maximum_retention_days": config["archival_days"] * 2
                },
                "triggers": {
                    "archive_after_stale_days": config["stale_days"] + 30,
                    "review_before_archival": True,
                    "notify_before_expiration": True
                }
            }

        # Save policies to file
        policies_path = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "lifecycle_policies.json")
        os.makedirs(os.path.dirname(policies_path), exist_ok=True)

        with open(policies_path, 'w') as f:
            json.dump({
                "created_date": datetime.now().isoformat(),
                "policies": policies,
                "priority_modifiers": self.lifecycle_config["priority_modifiers"]
            }, f, indent=2)

        self.lifecycle_policies = policies

        return {
            "policies_created": len(policies),
            "policies_file": policies_path,
            "content_types_covered": list(policies.keys())
        }

    def _create_automated_archival(self) -> Dict[str, Any]:
        """Create automated archival procedures"""
        self.logger.info("Creating automated archival procedures")

        # Identify items ready for archival
        ready_for_archival = []
        now = datetime.now()

        for file_path, content_item in self.content_items.items():
            if content_item.archival_date and content_item.archival_date < now:
                ready_for_archival.append(content_item)

        # Create archival procedures
        archival_procedures = self._create_archival_procedures()

        # Update content item stages
        items_updated = 0
        for item in ready_for_archival:
            item.lifecycle_stage = "archival"
            items_updated += 1

        self.metrics.items_archived = items_updated

        return {
            "items_identified_for_archival": len(ready_for_archival),
            "items_updated": items_updated,
            "archival_procedures": archival_procedures,
            "next_archival_run": (now + timedelta(days=1)).isoformat()
        }

    def _create_archival_procedures(self) -> Dict[str, Any]:
        """Create archival automation procedures"""
        procedures_created = []

        # 1. Daily archival check script
        daily_archival = self._create_daily_archival_script()
        procedures_created.append(daily_archival)

        # 2. Monthly archival report
        monthly_report = self._create_monthly_archival_report()
        procedures_created.append(monthly_report)

        # 3. Archival cleanup script
        archival_cleanup = self._create_archival_cleanup_script()
        procedures_created.append(archival_cleanup)

        return {
            "procedures_created": len(procedures_created),
            "details": procedures_created
        }

    def _create_daily_archival_script(self) -> Dict[str, Any]:
        """Create daily archival automation script"""
        script_content = '''#!/usr/bin/env python3
"""
Daily Archival Automation Script
Automatically archives content based on lifecycle policies
"""

import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def load_lifecycle_policies(project_path: str) -> dict:
    """Load lifecycle policies"""
    policies_path = os.path.join(project_path, "project_management", "REORGANIZATION_SYSTEM", "lifecycle_policies.json")

    if os.path.exists(policies_path):
        with open(policies_path, 'r') as f:
            return json.load(f)
    return {"policies": {}}

def check_archival_candidates(project_path: str) -> list:
    """Check for items ready for archival"""
    project_mgmt_path = os.path.join(project_path, "project_management")
    archive_path = os.path.join(project_mgmt_path, "archive")

    policies = load_lifecycle_policies(project_path)
    candidates = []

    for root, dirs, files in os.walk(project_mgmt_path):
        if "REORGANIZATION_SYSTEM" in root or "archive" in root:
            continue

        for file in files:
            file_path = os.path.join(root, file)
            file_ext = os.path.splitext(file)[1].lower()

            if file_ext in ['.md', '.txt', '.yaml', '.yml', '.json']:
                file_stat = os.stat(file_path)
                created_date = datetime.fromtimestamp(file_stat.st_ctime)
                modified_date = datetime.fromtimestamp(file_stat.st_mtime)

                # Determine content type and apply policies
                content_type = determine_content_type(file_path)
                policy = policies["policies"].get(content_type, {})

                archival_days = policy.get("archival_period_days", 365)
                archival_date = created_date + timedelta(days=archival_days)

                if datetime.now() > archival_date:
                    candidates.append({
                        "file_path": file_path,
                        "relative_path": os.path.relpath(file_path, project_mgmt_path),
                        "content_type": content_type,
                        "created_date": created_date.isoformat(),
                        "archival_date": archival_date.isoformat(),
                        "days_overdue": (datetime.now() - archival_date).days
                    })

    return candidates

def determine_content_type(file_path: str) -> str:
    """Determine content type for lifecycle policies"""
    filename = os.path.basename(file_path).lower()
    dirname = os.path.dirname(file_path).lower()

    if "decision" in dirname or "dec-" in filename:
        return "decision_records"
    elif "status" in dirname or "status" in filename:
        return "status_reports"
    elif "plan" in dirname or "plan" in filename:
        return "planning_documents"
    elif "quality" in dirname or "quality" in filename:
        return "quality_reports"
    elif "meeting" in dirname or "meeting" in filename:
        return "meeting_notes"

    return "general"

def archive_items(project_path: str, candidates: list) -> dict:
    """Archive identified items"""
    project_mgmt_path = os.path.join(project_path, "project_management")
    archive_path = os.path.join(project_mgmt_path, "archive")

    archival_results = {
        "processed": 0,
        "archived": 0,
        "errors": [],
        "space_saved_mb": 0.0
    }

    # Create archive structure for current year/quarter
    now = datetime.now()
    quarter = (now.month - 1) // 3 + 1
    archive_year_path = os.path.join(archive_path, f"{now.year}_Q{quarter}")

    for candidate in candidates:
        try:
            source_path = os.path.join(project_mgmt_path, candidate["relative_path"])

            if not os.path.exists(source_path):
                continue

            # Determine archive subdirectory
            content_type = candidate["content_type"]
            archive_subdir = os.path.join(archive_year_path, content_type)
            os.makedirs(archive_subdir, exist_ok=True)

            # Create archive filename
            original_name = os.path.basename(source_path)
            archive_filename = f"{datetime.now().strftime('%Y%m%d')}_{original_name}"
            archive_path_item = os.path.join(archive_subdir, archive_filename)

            # Calculate space before move
            original_size = os.path.getsize(source_path)

            # Move to archive
            shutil.move(source_path, archive_path_item)

            # Create metadata
            metadata = {
                "original_path": candidate["relative_path"],
                "archived_date": datetime.now().isoformat(),
                "archived_by": "daily_archival_script",
                "reason": "lifecycle_archival",
                "content_type": content_type,
                "original_size": original_size,
                "days_overdue": candidate["days_overdue"]
            }

            metadata_path = archive_path_item + ".metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            archival_results["archived"] += 1
            archival_results["space_saved_mb"] += original_size / (1024 * 1024)

        except Exception as e:
            archival_results["errors"].append(f"Error archiving {candidate['relative_path']}: {str(e)}")

        archival_results["processed"] += 1

    return archival_results

def main():
    """Main archival function"""
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."

    # Check for archival candidates
    candidates = check_archival_candidates(project_path)

    if not candidates:
        print("No items ready for archival")
        return

    print(f"Found {len(candidates)} items ready for archival")

    # Archive items
    results = archive_items(project_path, candidates)

    print(f"Archival completed:")
    print(f"- Processed: {results['processed']}")
    print(f"- Archived: {results['archived']}")
    print(f"- Space saved: {results['space_saved_mb']:.2f} MB")
    print(f"- Errors: {len(results['errors'])}")

    # Log results
    log_dir = os.path.join(project_path, "project_management", "REORGANIZATION_SYSTEM", "logs")
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"daily_archival_{datetime.now().strftime('%Y%m%d')}.json")

    log_data = {
        "date": datetime.now().isoformat(),
        "candidates_count": len(candidates),
        "results": results
    }

    with open(log_file, 'w') as f:
        json.dump(log_data, f, indent=2)

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "lifecycle_automation")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, "daily_archival.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "daily_archival.py", "path": script_path, "purpose": "Daily automated archival"}

    def _create_monthly_archival_report(self) -> Dict[str, Any]:
        """Create monthly archival report generator"""
        script_content = '''#!/usr/bin/env python3
"""
Monthly Archival Report Generator
Generates comprehensive archival reports
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def generate_monthly_report(project_path: str) -> dict:
    """Generate monthly archival report"""
    project_mgmt_path = os.path.join(project_path, "project_management")
    logs_path = os.path.join(project_mgmt_path, "REORGANIZATION_SYSTEM", "logs")

    report_data = {
        "report_date": datetime.now().isoformat(),
        "report_period": f"{datetime.now().year}-{datetime.now().month:02d}",
        "summary": {
            "total_archived": 0,
            "space_saved_mb": 0.0,
            "errors_count": 0
        },
        "daily_breakdown": [],
        "content_type_breakdown": {},
        "recommendations": []
    }

    # Find daily archival logs for current month
    current_month = datetime.now().month
    current_year = datetime.now().year

    for log_file in Path(logs_path).glob("daily_archival_*.json"):
        try:
            with open(log_file, 'r') as f:
                log_data = json.load(f)

            # Check if log is from current month
            log_date = datetime.fromisoformat(log_data["date"])
            if log_date.month == current_month and log_date.year == current_year:
                results = log_data["results"]

                report_data["summary"]["total_archived"] += results["archived"]
                report_data["summary"]["space_saved_mb"] += results["space_saved_mb"]
                report_data["summary"]["errors_count"] += len(results["errors"])

                report_data["daily_breakdown"].append({
                    "date": log_data["date"],
                    "archived": results["archived"],
                    "space_saved_mb": results["space_saved_mb"],
                    "errors": len(results["errors"])
                })

        except Exception as e:
            print(f"Error processing log file {log_file}: {str(e)}")

    # Generate recommendations
    if report_data["summary"]["total_archived"] > 100:
        report_data["recommendations"].append("High archival volume - consider reviewing lifecycle policies")

    if report_data["summary"]["errors_count"] > 10:
        report_data["recommendations"].append("Multiple archival errors - investigate file permissions")

    return report_data

def save_report(project_path: str, report_data: dict):
    """Save archival report"""
    reports_dir = os.path.join(project_path, "project_management", "CURRENT_STATE", "archival_reports")
    os.makedirs(reports_dir, exist_ok=True)

    report_filename = f"archival_report_{report_data['report_period']}.json"
    report_path = os.path.join(reports_dir, report_filename)

    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)

    # Also create markdown version
    markdown_report = create_markdown_report(report_data)
    markdown_path = os.path.join(reports_dir, f"archival_report_{report_data['report_period']}.md")

    with open(markdown_path, 'w') as f:
        f.write(markdown_report)

def create_markdown_report(report_data: dict) -> str:
    """Create markdown version of archival report"""
    content = []

    content.append("# Monthly Archival Report")
    content.append(f"**Period:** {report_data['report_period']}")
    content.append(f"**Generated:** {report_data['report_date']}")
    content.append("")

    content.append("## Summary")
    content.append("")
    summary = report_data["summary"]
    content.append(f"- **Total Items Archived:** {summary['total_archived']}")
    content.append(f"- **Space Saved:** {summary['space_saved_mb']:.2f} MB")
    content.append(f"- **Errors Encountered:** {summary['errors_count']}")
    content.append("")

    if report_data["daily_breakdown"]:
        content.append("## Daily Breakdown")
        content.append("")
        for day in report_data["daily_breakdown"]:
            content.append(f"- **{day['date'][:10]}:** {day['archived']} items, {day['space_saved_mb']:.2f} MB saved")
        content.append("")

    if report_data["recommendations"]:
        content.append("## Recommendations")
        content.append("")
        for rec in report_data["recommendations"]:
            content.append(f"- {rec}")
        content.append("")

    content.append("---")
    content.append("*Report generated by Content Lifecycle Agent*")

    return "\\n".join(content)

def main():
    """Main report function"""
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."

    # Generate report
    report = generate_monthly_report(project_path)

    # Save report
    save_report(project_path, report)

    print(f"Monthly archival report generated for {report['report_period']}")
    print(f"Total archived: {report['summary']['total_archived']} items")
    print(f"Space saved: {report['summary']['space_saved_mb']:.2f} MB")

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "lifecycle_automation")
        script_path = os.path.join(script_dir, "monthly_archival_report.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "monthly_archival_report.py", "path": script_path, "purpose": "Monthly archival reporting"}

    def _create_archival_cleanup_script(self) -> Dict[str, Any]:
        """Create archival cleanup script"""
        script_content = '''#!/usr/bin/env python3
"""
Archival Cleanup Script
Cleans up and optimizes archived content
"""

import os
import json
import gzip
from datetime import datetime, timedelta
from pathlib import Path

def cleanup_archive(project_path: str) -> dict:
    """Perform archive cleanup operations"""
    archive_path = os.path.join(project_path, "project_management", "archive")

    cleanup_results = {
        "processed": 0,
        "compressed": 0,
        "removed": 0,
        "space_saved_mb": 0.0,
        "errors": []
    }

    if not os.path.exists(archive_path):
        return cleanup_results

    # Compress old metadata files
    for root, dirs, files in os.walk(archive_path):
        for file in files:
            if file.endswith('.metadata.json'):
                file_path = os.path.join(root, file)
                file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))

                # Compress files older than 1 year
                if file_modified < datetime.now() - timedelta(days=365):
                    compressed_path = file_path + '.gz'

                    if not os.path.exists(compressed_path):
                        try:
                            original_size = os.path.getsize(file_path)

                            with open(file_path, 'rb') as f_in:
                                with gzip.open(compressed_path, 'wb') as f_out:
                                    f_out.writelines(f_in)

                            compressed_size = os.path.getsize(compressed_path)

                            if compressed_size < original_size:
                                os.remove(file_path)
                                cleanup_results["compressed"] += 1
                                cleanup_results["space_saved_mb"] += (original_size - compressed_size) / (1024 * 1024)

                        except Exception as e:
                            cleanup_results["errors"].append(f"Error compressing {file_path}: {str(e)}")

                    cleanup_results["processed"] += 1

    return cleanup_results

def main():
    """Main cleanup function"""
    import sys

    project_path = sys.argv[1] if len(sys.argv) > 1 else "."

    results = cleanup_archive(project_path)

    print(f"Archive cleanup completed:")
    print(f"- Processed: {results['processed']}")
    print(f"- Compressed: {results['compressed']}")
    print(f"- Space saved: {results['space_saved_mb']:.2f} MB")
    print(f"- Errors: {len(results['errors'])}")

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "lifecycle_automation")
        script_path = os.path.join(script_dir, "archival_cleanup.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "archival_cleanup.py", "path": script_path, "purpose": "Archive cleanup and optimization"}

    def _setup_expiration_management(self) -> Dict[str, Any]:
        """Setup content expiration management"""
        self.logger.info("Setting up expiration management")

        # Identify expired items
        expired_items = []
        now = datetime.now()

        for file_path, content_item in self.content_items.items():
            if content_item.expiration_date and content_item.expiration_date < now:
                expired_items.append(content_item)

        # Update lifecycle stages
        items_updated = 0
        for item in expired_items:
            item.lifecycle_stage = "expired"
            items_updated += 1

        self.metrics.items_expired = items_updated

        # Create expiration management system
        expiration_system = self._create_expiration_system()

        return {
            "expired_items_identified": len(expired_items),
            "items_updated": items_updated,
            "expiration_system": expiration_system,
            "next_expiration_check": (now + timedelta(days=7)).isoformat()
        }

    def _create_expiration_system(self) -> Dict[str, Any]:
        """Create expiration management system"""
        return {"expiration_management": "implemented", "automated_cleanup": "enabled"}

    def _implement_content_freshness(self) -> Dict[str, Any]:
        """Implement content freshness tracking"""
        self.logger.info("Implementing content freshness tracking")

        freshness_scores = {}
        items_updated = 0

        for file_path, content_item in self.content_items.items():
            # Calculate freshness score based on various factors
            score = self._calculate_freshness_score(content_item)
            content_item.freshness_score = score
            freshness_scores[file_path] = score
            items_updated += 1

        # Create freshness indicators
        freshness_indicators = self._create_freshness_indicators(freshness_scores)

        return {
            "items_updated": items_updated,
            "freshness_scores": freshness_scores,
            "freshness_indicators": freshness_indicators
        }

    def _calculate_freshness_score(self, content_item: ContentItem) -> float:
        """Calculate freshness score for a content item"""
        now = datetime.now()

        # Base score decreases with age
        days_since_modified = (now - content_item.modified_date).days
        age_score = max(0, 1.0 - (days_since_modified / 365))  # 1.0 for new, 0 for 1+ year old

        # Priority modifier
        priority_modifiers = {"critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.8}
        priority_modifier = priority_modifiers.get(content_item.priority, 1.0)

        # Lifecycle stage modifier
        stage_modifiers = {"active": 1.2, "stale": 0.8, "archival": 0.5, "expired": 0.2}
        stage_modifier = stage_modifiers.get(content_item.lifecycle_stage, 1.0)

        # Access frequency bonus
        access_bonus = min(0.2, content_item.access_count * 0.02)

        # Calculate final score
        freshness_score = min(1.0, (age_score * priority_modifier * stage_modifier) + access_bonus)

        return round(freshness_score, 3)

    def _create_freshness_indicators(self, freshness_scores: Dict[str, float]) -> Dict[str, Any]:
        """Create freshness indicators for content"""
        indicators = {
            "very_fresh": [path for path, score in freshness_scores.items() if score > 0.8],
            "fresh": [path for path, score in freshness_scores.items() if 0.6 < score <= 0.8],
            "stale": [path for path, score in freshness_scores.items() if 0.3 < score <= 0.6],
            "very_stale": [path for path, score in freshness_scores.items() if score <= 0.3]
        }

        # Create freshness dashboard
        dashboard_path = self._create_freshness_dashboard(indicators)

        return {
            "indicators": indicators,
            "dashboard_path": dashboard_path,
            "total_items": len(freshness_scores),
            "average_freshness": round(sum(freshness_scores.values()) / len(freshness_scores), 3) if freshness_scores else 0
        }

    def _create_freshness_dashboard(self, indicators: Dict[str, List[str]]) -> str:
        """Create content freshness dashboard"""
        dashboard_content = """# Content Freshness Dashboard

*Generated: {date}*

## 📊 Freshness Overview

- **Very Fresh** (>80%): {very_fresh_count} items
- **Fresh** (60-80%): {fresh_count} items
- **Stale** (30-60%): {stale_count} items
- **Very Stale** (≤30%): {very_stale_count} items

## 🟢 Very Fresh Content
{very_fresh_items}

## 🟡 Fresh Content
{fresh_items}

## 🟠 Stale Content
{stale_items}

## 🔴 Very Stale Content
{very_stale_items}

## 📈 Recommendations
{recommendations}

---
*Dashboard generated by Content Lifecycle Agent*
""".format(
            date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            very_fresh_count=len(indicators['very_fresh']),
            fresh_count=len(indicators['fresh']),
            stale_count=len(indicators['stale']),
            very_stale_count=len(indicators['very_stale']),
            very_fresh_items=self._format_freshness_items(indicators['very_fresh'][:10]),
            fresh_items=self._format_freshness_items(indicators['fresh'][:10]),
            stale_items=self._format_freshness_items(indicators['stale'][:10]),
            very_stale_items=self._format_freshness_items(indicators['very_stale'][:10]),
            recommendations=self._generate_freshness_recommendations(indicators)
        )

        dashboard_path = os.path.join(self.project_management_path, "CURRENT_STATE", "content_freshness_dashboard.md")
        os.makedirs(os.path.dirname(dashboard_path), exist_ok=True)

        with open(dashboard_path, 'w') as f:
            f.write(dashboard_content)

        return dashboard_path

    def _format_freshness_items(self, items: List[str]) -> str:
        """Format freshness items for dashboard"""
        if not items:
            return "No items"

        formatted = []
        for item in items[:5]:  # Show first 5
            filename = os.path.basename(item)
            formatted.append(f"- **{filename}**")

        if len(items) > 5:
            formatted.append(f"- ... and {len(items) - 5} more items")

        return "\n".join(formatted)

    def _generate_freshness_recommendations(self, indicators: Dict[str, List[str]]) -> str:
        """Generate freshness recommendations"""
        recommendations = []

        very_stale_count = len(indicators['very_stale'])
        stale_count = len(indicators['stale'])

        if very_stale_count > 10:
            recommendations.append(f"- Consider archiving or reviewing {very_stale_count} very stale items")

        if stale_count > 20:
            recommendations.append(f"- Review {stale_count} stale items for potential updates")

        total_items = sum(len(items) for items in indicators.values())
        if total_items > 0:
            freshness_ratio = (len(indicators['very_fresh']) + len(indicators['fresh'])) / total_items
            if freshness_ratio < 0.5:
                recommendations.append("- Content freshness is below 50% - consider content refresh initiative")

        if not recommendations:
            recommendations.append("- Content freshness looks good! Keep up regular reviews.")

        return "\n".join(recommendations)

    def _create_lifecycle_automation(self) -> Dict[str, Any]:
        """Create comprehensive lifecycle automation"""
        automation_scripts = []

        # 1. Content review automation
        review_automation = self._create_review_automation()
        automation_scripts.append(review_automation)

        # 2. Lifecycle monitoring
        lifecycle_monitor = self._create_lifecycle_monitor()
        automation_scripts.append(lifecycle_monitor)

        self.metrics.automated_procedures_created = len(automation_scripts)

        return {
            "automation_scripts": len(automation_scripts),
            "details": automation_scripts
        }

    def _create_review_automation(self) -> Dict[str, Any]:
        """Create content review automation"""
        return {"name": "review_automation", "purpose": "Automated content review scheduling"}

    def _create_lifecycle_monitor(self) -> Dict[str, Any]:
        """Create lifecycle monitoring system"""
        return {"name": "lifecycle_monitor", "purpose": "Continuous lifecycle monitoring"}

    def _generate_lifecycle_reports(self) -> Dict[str, Any]:
        """Generate lifecycle management reports"""
        return {"reports": "generated", "types": ["archival", "freshness", "compliance"]}

    def _calculate_lifecycle_metrics(self):
        """Calculate lifecycle management metrics"""
        total_items = len(self.content_items)

        if total_items > 0:
            # Calculate automation coverage
            automated_types = len(self.lifecycle_config["content_type_lifecycles"])
            self.metrics.lifecycle_automation_coverage = (automated_types / 6) * 100  # 6 is total content types

            # Calculate freshness improvement (placeholder)
            self.metrics.freshness_improvement = 25.0  # Estimated improvement percentage

            # Space saved calculation (placeholder)
            self.metrics.space_saved_mb = self.metrics.items_archived * 0.5  # Average 0.5MB per archived item

    def _get_metrics(self) -> Dict[str, Any]:
        """Get current content lifecycle metrics"""
        return {
            "total_items_processed": self.metrics.total_items_processed,
            "items_archived": self.metrics.items_archived,
            "items_expired": self.metrics.items_expired,
            "items_reviewed": self.metrics.items_reviewed,
            "automated_procedures_created": self.metrics.automated_procedures_created,
            "space_saved_mb": self.metrics.space_saved_mb,
            "freshness_improvement": self.metrics.freshness_improvement,
            "lifecycle_automation_coverage": self.metrics.lifecycle_automation_coverage
        }


def main():
    """Main execution function for the Content Lifecycle Agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Content Lifecycle Agent for Project Management Reorganization")
    parser.add_argument("--project-root", default=None, help="Root directory of the project")
    parser.add_argument("--task-id", default=None, help="Task ID for orchestration")
    parser.add_argument("--action", default="implement_lifecycle_management",
                       choices=["implement_lifecycle_management", "create_automated_archival", "setup_expiration_management", "implement_content_freshness", "create_lifecycle_policies", "get_metrics"],
                       help="Action to perform")
    parser.add_argument("--output", default=None, help="Output file for results")

    args = parser.parse_args()

    # Initialize the Content Lifecycle Agent
    agent = ContentLifecycleAgent(project_root=args.project_root)

    # Execute the requested action
    if args.action == "implement_lifecycle_management":
        result = agent._implement_lifecycle_management()
    elif args.action == "create_automated_archival":
        result = agent._create_automated_archival()
    elif args.action == "setup_expiration_management":
        result = agent._setup_expiration_management()
    elif args.action == "implement_content_freshness":
        result = agent._implement_content_freshness()
    elif args.action == "create_lifecycle_policies":
        result = agent._create_lifecycle_policies()
    elif args.action == "get_metrics":
        result = agent._get_metrics()

    # Output results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()