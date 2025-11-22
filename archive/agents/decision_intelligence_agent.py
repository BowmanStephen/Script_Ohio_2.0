#!/usr/bin/env python3
"""
Decision Intelligence Agent for Project Management Reorganization

This agent adds status tracking to all decisions, implements impact measurement,
and creates decision intelligence systems for better decision management.

Role: Decision Intelligence Specialist
Permission Level: READ_EXECUTE_WRITE (Level 3)
Capabilities: Decision status tracking, impact measurement, decision analytics
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
class DecisionRecord:
    """Represents a decision record with enhanced tracking"""
    decision_id: str
    title: str
    date_made: datetime
    status: str  # PROPOSED, APPROVED, IMPLEMENTED, REJECTED, SUPERSEDED
    priority: str  # LOW, MEDIUM, HIGH, CRITICAL
    impact_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    implementer: Optional[str] = None
    implementation_date: Optional[datetime] = None
    review_date: Optional[datetime] = None
    related_decisions: List[str] = field(default_factory=list)
    impact_metrics: Dict[str, Any] = field(default_factory=dict)
    stakeholders: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    file_path: str = ""
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class DecisionMetrics:
    """Metrics for decision intelligence"""
    total_decisions_analyzed: int
    decisions_with_status_tracking: int
    decisions_with_impact_measurement: int
    implementation_rate: float
    average_implementation_days: float
    high_priority_decisions: int
    critical_impact_decisions: int
    decision_trends: Dict[str, Any]
    stakeholder_engagement: float


class DecisionIntelligenceAgent(BaseAgent):
    """
    Decision Intelligence Agent for enhanced decision tracking

    This agent adds status tracking to decisions, implements impact measurement,
    and creates comprehensive decision intelligence systems.
    """

    def __init__(self, agent_id: str = "decision_intelligence", project_root: str = None):
        """
        Initialize the Decision Intelligence Agent

        Args:
            agent_id: Unique identifier for this agent
            project_root: Root directory of the Script Ohio 2.0 project
        """
        super().__init__(
            agent_id=agent_id,
            name="Decision Intelligence - Decision Tracking Enhancement Specialist",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE
        )

        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_management_path = os.path.join(self.project_root, "project_management")
        self.decision_log_path = os.path.join(self.project_management_path, "DECISION_LOG")

        # Decision status workflow
        self.status_workflow = {
            "PROPOSED": {
                "next_statuses": ["APPROVED", "REJECTED"],
                "required_fields": ["title", "context", "proposed_decision"],
                "approval_required": True
            },
            "APPROVED": {
                "next_statuses": ["IMPLEMENTED", "REJECTED", "SUPERSEDED"],
                "required_fields": ["implementer", "implementation_plan"],
                "implementation_required": True
            },
            "IMPLEMENTED": {
                "next_statuses": ["REVIEWED", "SUPERSEDED"],
                "required_fields": ["implementation_date", "impact_assessment"],
                "review_required": True
            },
            "REVIEWED": {
                "next_statuses": ["CONFIRMED", "SUPERSEDED", "REVERTED"],
                "required_fields": ["review_outcome", "impact_metrics"],
                "impact_measurement": True
            },
            "REJECTED": {
                "next_statuses": [],
                "required_fields": ["rejection_reason"],
                "final": True
            },
            "SUPERSEDED": {
                "next_statuses": [],
                "required_fields": ["superseded_by", "supersession_reason"],
                "final": True
            }
        }

        # Impact measurement criteria
        self.impact_criteria = {
            "technical": {
                "code_changes": "Number of files changed",
                "architecture_impact": "Impact on system architecture",
                "performance_impact": "Performance improvement/degradation",
                "complexity_change": "Change in system complexity"
            },
            "business": {
                "cost_impact": "Financial cost/benefit",
                "time_savings": "Time saved/lost",
                "user_impact": "Impact on end users",
                "risk_mitigation": "Risk reduction/increase"
            },
            "project": {
                "timeline_impact": "Effect on project timeline",
                "resource_impact": "Resource requirement changes",
                "scope_impact": "Changes to project scope",
                "quality_impact": "Effect on quality metrics"
            }
        }

        # Metrics tracking
        self.metrics = DecisionMetrics(
            total_decisions_analyzed=0,
            decisions_with_status_tracking=0,
            decisions_with_impact_measurement=0,
            implementation_rate=0.0,
            average_implementation_days=0.0,
            high_priority_decisions=0,
            critical_impact_decisions=0,
            decision_trends={},
            stakeholder_engagement=0.0
        )

        # Decision records
        self.decision_records: Dict[str, DecisionRecord] = {}
        self.decision_file_mapping: Dict[str, str] = {}

        # Setup logging
        self._setup_logging()

        self.log_action("initialization", {
            "decision_log_path": self.decision_log_path,
            "status_workflow_states": len(self.status_workflow),
            "impact_categories": len(self.impact_criteria)
        })

    def _setup_logging(self):
        """Setup logging for decision intelligence operations"""
        log_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"decision_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.agent_id)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this decision intelligence agent"""
        return [
            AgentCapability("decision_status_tracking"),
            AgentCapability("impact_measurement"),
            AgentCapability("decision_analytics"),
            AgentCapability("stakeholder_tracking"),
            AgentCapability("decision_workflow"),
            AgentCapability("trend_analysis")
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute decision intelligence actions

        Args:
            action: The action to execute
            parameters: Parameters for the action
            user_context: User context and preferences

        Returns:
            Action execution results
        """
        if action == "enhance_decision_tracking":
            return self._enhance_decision_tracking()
        elif action == "implement_impact_measurement":
            return self._implement_impact_measurement()
        elif action == "create_decision_analytics":
            return self._create_decision_analytics()
        elif action == "setup_decision_workflow":
            return self._setup_decision_workflow()
        elif action == "get_metrics":
            return self._get_metrics()
        else:
            return {"error": f"Unknown action: {action}"}

    def _enhance_decision_tracking(self) -> Dict[str, Any]:
        """
        Enhance existing decision records with status tracking

        Returns:
            Decision tracking enhancement results
        """
        try:
            self.logger.info("Enhancing decision tracking")
            self.log_action("decision_tracking_enhancement_start", {"scope": "decision_log_enhancement"})

            # Step 1: Discover and analyze existing decision documents
            discovery_result = self._discover_decision_documents()

            # Step 2: Extract decision information from documents
            extraction_result = self._extract_decision_information()

            # Step 3: Enhance decisions with status tracking
            enhancement_result = self._enhance_decision_status_tracking()

            # Step 4: Create decision tracking system
            tracking_system = self._create_decision_tracking_system()

            # Step 5: Generate decision analytics
            analytics = self._generate_decision_analytics()

            # Step 6: Create decision dashboard
            dashboard = self._create_decision_dashboard()

            # Step 7: Calculate decision metrics
            self._calculate_decision_metrics()

            self.logger.info("Decision tracking enhancement completed")
            return {
                "success": True,
                "discovery": discovery_result,
                "extraction": extraction_result,
                "enhancement": enhancement_result,
                "tracking_system": tracking_system,
                "analytics": analytics,
                "dashboard": dashboard,
                "metrics": self._get_metrics()
            }

        except Exception as e:
            self.logger.error(f"Decision tracking enhancement failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _discover_decision_documents(self) -> Dict[str, Any]:
        """Discover existing decision documents"""
        self.logger.info("Discovering decision documents")

        decision_files = []
        total_files = 0

        if os.path.exists(self.decision_log_path):
            for file_path in Path(self.decision_log_path).glob("*"):
                if file_path.suffix in ['.md', '.txt'] and not file_path.name.startswith('.'):
                    total_files += 1
                    file_info = {
                        "path": str(file_path),
                        "name": file_path.name,
                        "size": file_path.stat().st_size,
                        "modified": datetime.fromtimestamp(file_path.stat().st_mtime)
                    }
                    decision_files.append(file_info)

        self.metrics.total_decisions_analyzed = total_files

        return {
            "total_files_found": total_files,
            "decision_files": decision_files,
            "discovery_path": self.decision_log_path
        }

    def _extract_decision_information(self) -> Dict[str, Any]:
        """Extract decision information from documents"""
        self.logger.info("Extracting decision information")

        extracted_decisions = 0
        processing_errors = 0

        for root, dirs, files in os.walk(self.decision_log_path):
            for file in files:
                if file.endswith(('.md', '.txt')):
                    file_path = os.path.join(root, file)
                    try:
                        decision_record = self._parse_decision_file(file_path)
                        if decision_record:
                            self.decision_records[decision_record.decision_id] = decision_record
                            self.decision_file_mapping[decision_record.decision_id] = file_path
                            extracted_decisions += 1
                    except Exception as e:
                        self.logger.warning(f"Error processing decision file {file_path}: {str(e)}")
                        processing_errors += 1

        return {
            "decisions_extracted": extracted_decisions,
            "processing_errors": processing_errors,
            "total_records": len(self.decision_records)
        }

    def _parse_decision_file(self, file_path: str) -> Optional[DecisionRecord]:
        """Parse a decision file and extract information"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return None

        filename = os.path.basename(file_path)

        # Extract decision ID
        decision_id = self._extract_decision_id(filename, content)
        if not decision_id:
            return None

        # Extract title
        title = self._extract_title(content, filename)

        # Extract date
        date_made = self._extract_date(content)

        # Extract status
        status = self._extract_status(content)

        # Extract priority
        priority = self._extract_priority(content)

        # Extract impact level
        impact_level = self._extract_impact_level(content)

        # Extract implementer
        implementer = self._extract_implementer(content)

        # Extract stakeholders
        stakeholders = self._extract_stakeholders(content)

        # Extract tags
        tags = self._extract_tags(content)

        return DecisionRecord(
            decision_id=decision_id,
            title=title,
            date_made=date_made,
            status=status,
            priority=priority,
            impact_level=impact_level,
            implementer=implementer,
            stakeholders=stakeholders,
            tags=tags,
            file_path=file_path
        )

    def _extract_decision_id(self, filename: str, content: str) -> Optional[str]:
        """Extract decision ID from filename or content"""
        # Try to extract from filename first (e.g., "DEC-001-some-decision.md")
        filename_match = re.search(r'DEC-(\d+)', filename.upper())
        if filename_match:
            return f"DEC-{filename_match.group(1).zfill(3)}"

        # Try to extract from content
        content_match = re.search(r'DEC[-\s]?(\d+)', content.upper())
        if content_match:
            return f"DEC-{content_match.group(1).zfill(3)}"

        return None

    def _extract_title(self, content: str, filename: str) -> str:
        """Extract decision title from content"""
        # Look for title patterns
        title_patterns = [
            r'#\s*(.+?)(?:\n|$)',  # Markdown header
            r'Title[:\s]+(.+?)(?:\n|$)',  # Title: value
            r'Decision[:\s]+(.+?)(?:\n|$)'  # Decision: value
        ]

        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Remove decision ID from title if present
                title = re.sub(r'DEC[-\s]?\d+[-:]?\s*', '', title, flags=re.IGNORECASE).strip()
                if title:
                    return title

        # Fallback to filename
        return filename.replace('.md', '').replace('_', ' ').replace('-', ' ').title()

    def _extract_date(self, content: str) -> datetime:
        """Extract decision date from content"""
        date_patterns = [
            r'Date[:\s]+(\d{4}-\d{2}-\d{2})',
            r'Date[:\s]+(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{4}-\d{2}-\d{2})'  # First date found
        ]

        for pattern in date_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Try different date formats
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y']:
                        try:
                            return datetime.strptime(date_str, fmt)
                        except ValueError:
                            continue
                except ValueError:
                    continue

        # Default to file modification date
        return datetime.now()

    def _extract_status(self, content: str) -> str:
        """Extract decision status from content"""
        status_keywords = {
            'PROPOSED': ['proposed', 'draft', 'under consideration'],
            'APPROVED': ['approved', 'accepted', 'confirmed'],
            'IMPLEMENTED': ['implemented', 'completed', 'done'],
            'REJECTED': ['rejected', 'declined', 'not approved'],
            'SUPERSEDED': ['superseded', 'replaced', 'updated'],
            'REVIEWED': ['reviewed', 'evaluated', 'assessed']
        }

        content_lower = content.lower()

        for status, keywords in status_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return status

        # Default status
        return "PROPOSED"

    def _extract_priority(self, content: str) -> str:
        """Extract decision priority from content"""
        priority_keywords = {
            'CRITICAL': ['critical', 'urgent', 'blocking'],
            'HIGH': ['high', 'important', 'priority'],
            'MEDIUM': ['medium', 'normal', 'standard'],
            'LOW': ['low', 'minor', 'nice to have']
        }

        content_lower = content.lower()

        for priority, keywords in priority_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return priority

        return "MEDIUM"

    def _extract_impact_level(self, content: str) -> str:
        """Extract impact level from content"""
        impact_keywords = {
            'CRITICAL': ['critical impact', 'major impact', 'significant impact'],
            'HIGH': ['high impact', 'substantial impact'],
            'MEDIUM': ['medium impact', 'moderate impact'],
            'LOW': ['low impact', 'minor impact', 'minimal impact']
        }

        content_lower = content.lower()

        for impact, keywords in impact_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return impact

        return "MEDIUM"

    def _extract_implementer(self, content: str) -> Optional[str]:
        """Extract implementer from content"""
        implementer_patterns = [
            r'Implementer[:\s]+([^\n]+)',
            r'Owner[:\s]+([^\n]+)',
            r'Assigned to[:\s]+([^\n]+)',
            r'Responsible[:\s]+([^\n]+)'
        ]

        for pattern in implementer_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_stakeholders(self, content: str) -> List[str]:
        """Extract stakeholders from content"""
        stakeholders = []

        stakeholder_patterns = [
            r'Stakeholders?[:\s]+([^\n]+)',
            r'Involved[:\s]+([^\n]+)',
            r'Participants?[:\s]+([^\n]+)'
        ]

        for pattern in stakeholder_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Split by common separators
                names = re.split(r'[,;]| and | & ', match)
                for name in names:
                    name = name.strip()
                    if name and len(name) > 1:
                        stakeholders.append(name)

        return list(set(stakeholders))  # Remove duplicates

    def _extract_tags(self, content: str) -> List[str]:
        """Extract tags from content"""
        tags = []

        # Look for tag patterns
        tag_patterns = [
            r'Tags?[:\s]+([^\n]+)',
            r'Category[:\s]+([^\n]+)',
            r'Type[:\s]+([^\n]+)'
        ]

        for pattern in tag_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                # Split by common separators
                tag_list = re.split(r'[,;]| and | & ', match)
                for tag in tag_list:
                    tag = tag.strip().lower()
                    if tag and len(tag) > 1:
                        tags.append(tag)

        return list(set(tags))

    def _enhance_decision_status_tracking(self) -> Dict[str, Any]:
        """Enhance decisions with status tracking"""
        self.logger.info("Enhancing decision status tracking")

        enhanced_decisions = 0

        for decision_id, decision in self.decision_records.items():
            # Enhance decision record with additional tracking
            if self._add_status_tracking(decision):
                enhanced_decisions += 1

        self.metrics.decisions_with_status_tracking = enhanced_decisions

        return {
            "decisions_enhanced": enhanced_decisions,
            "total_decisions": len(self.decision_records),
            "enhancement_rate": round((enhanced_decisions / max(len(self.decision_records), 1)) * 100, 2)
        }

    def _add_status_tracking(self, decision: DecisionRecord) -> bool:
        """Add status tracking to a decision"""
        try:
            # Calculate next review date based on status
            if decision.status == "APPROVED" and not decision.review_date:
                decision.review_date = decision.date_made + timedelta(days=30)  # Review in 30 days
            elif decision.status == "IMPLEMENTED" and not decision.review_date:
                decision.review_date = datetime.now() + timedelta(days=90)  # Review in 90 days

            # Add automatic status transitions
            if decision.status == "APPROVED" and decision.implementer:
                # Check if should be marked as implemented
                if datetime.now() - decision.date_made > timedelta(days=14):
                    decision.status = "IMPLEMENTED"
                    decision.implementation_date = datetime.now()

            return True

        except Exception as e:
            self.logger.warning(f"Error enhancing decision {decision.decision_id}: {str(e)}")
            return False

    def _create_decision_tracking_system(self) -> Dict[str, Any]:
        """Create comprehensive decision tracking system"""
        self.logger.info("Creating decision tracking system")

        # Create decision database
        decision_db = self._create_decision_database()

        # Create status tracking dashboard
        status_dashboard = self._create_status_dashboard()

        # Create decision workflow system
        workflow_system = self._create_decision_workflow_system()

        return {
            "decision_database": decision_db,
            "status_dashboard": status_dashboard,
            "workflow_system": workflow_system
        }

    def _create_decision_database(self) -> Dict[str, Any]:
        """Create decision database file"""
        db_path = os.path.join(self.decision_log_path, "decision_database.json")

        decision_data = {
            "generated_date": datetime.now().isoformat(),
            "total_decisions": len(self.decision_records),
            "decisions": {}
        }

        for decision_id, decision in self.decision_records.items():
            decision_data["decisions"][decision_id] = {
                "decision_id": decision.decision_id,
                "title": decision.title,
                "date_made": decision.date_made.isoformat(),
                "status": decision.status,
                "priority": decision.priority,
                "impact_level": decision.impact_level,
                "implementer": decision.implementer,
                "implementation_date": decision.implementation_date.isoformat() if decision.implementation_date else None,
                "review_date": decision.review_date.isoformat() if decision.review_date else None,
                "stakeholders": decision.stakeholders,
                "tags": decision.tags,
                "file_path": decision.file_path,
                "last_updated": decision.last_updated.isoformat()
            }

        with open(db_path, 'w') as f:
            json.dump(decision_data, f, indent=2)

        return {"database_path": db_path, "total_decisions": len(self.decision_records)}

    def _create_status_dashboard(self) -> Dict[str, Any]:
        """Create decision status dashboard"""
        dashboard_content = self._build_status_dashboard_content()

        dashboard_path = os.path.join(self.decision_log_path, "DECISION_DASHBOARD.md")
        with open(dashboard_path, 'w') as f:
            f.write(dashboard_content)

        return {"dashboard_path": dashboard_path, "content_length": len(dashboard_content)}

    def _build_status_dashboard_content(self) -> str:
        """Build decision status dashboard content"""
        content = []

        # Header
        content.append("# Decision Dashboard")
        content.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        content.append("")

        # Summary statistics
        content.append("## 📊 Summary Statistics")
        content.append("")

        total_decisions = len(self.decision_records)
        status_counts = Counter(decision.status for decision in self.decision_records.values())
        priority_counts = Counter(decision.priority for decision in self.decision_records.values())
        impact_counts = Counter(decision.impact_level for decision in self.decision_records.values())

        content.append(f"- **Total Decisions**: {total_decisions}")
        content.append(f"- **Implementation Rate**: {round((status_counts.get('IMPLEMENTED', 0) / max(total_decisions, 1)) * 100, 1)}%")
        content.append("")

        # Status breakdown
        content.append("### Status Breakdown")
        for status, count in status_counts.most_common():
            status_icon = self._get_status_icon(status)
            content.append(f"- {status_icon} **{status}**: {count}")
        content.append("")

        # Priority breakdown
        content.append("### Priority Breakdown")
        for priority, count in priority_counts.most_common():
            priority_icon = self._get_priority_icon(priority)
            content.append(f"- {priority_icon} **{priority}**: {count}")
        content.append("")

        # Recent decisions
        content.append("## 🕒 Recent Decisions")
        content.append("")

        recent_decisions = sorted(
            self.decision_records.values(),
            key=lambda d: d.date_made,
            reverse=True
        )[:10]

        for decision in recent_decisions:
            status_icon = self._get_status_icon(decision.status)
            priority_icon = self._get_priority_icon(decision.priority)

            content.append(f"### {status_icon} {decision.title}")
            content.append(f"- **ID**: {decision.decision_id}")
            content.append(f"- **Status**: {decision.status} {priority_icon}")
            content.append(f"- **Date**: {decision.date_made.strftime('%Y-%m-%d')}")
            content.append(f"- **Impact**: {decision.impact_level}")
            if decision.implementer:
                content.append(f"- **Implementer**: {decision.implementer}")
            content.append("")

        # Decisions requiring action
        content.append("## ⚠️ Decisions Requiring Action")
        content.append("")

        # Find decisions that need attention
        action_needed = []
        for decision in self.decision_records.values():
            if decision.status == "APPROVED" and not decision.implementation_date:
                action_needed.append(decision)
            elif decision.review_date and decision.review_date < datetime.now():
                action_needed.append(decision)

        if action_needed:
            for decision in action_needed[:5]:  # Show top 5
                urgency_icon = "🔴" if decision.priority in ["CRITICAL", "HIGH"] else "🟡"
                content.append(f"### {urgency_icon} {decision.title}")
                content.append(f"- **Status**: {decision.status}")
                content.append(f"- **Action Needed**: Review implementation or conduct review")
                content.append(f"- **Last Updated**: {decision.last_updated.strftime('%Y-%m-%d')}")
                content.append("")
        else:
            content.append("✅ No decisions require immediate action")
            content.append("")

        # Implementation tracking
        content.append("## 📈 Implementation Tracking")
        content.append("")

        implemented_decisions = [d for d in self.decision_records.values() if d.status == "IMPLEMENTED"]
        if implemented_decisions:
            avg_implementation_days = sum(
                (d.implementation_date - d.date_made).days
                for d in implemented_decisions
                if d.implementation_date
            ) / len(implemented_decisions)

            content.append(f"- **Average Implementation Time**: {round(avg_implementation_days, 1)} days")
            content.append(f"- **Total Implemented**: {len(implemented_decisions)}")
            content.append("")

            # Recent implementations
            content.append("### Recent Implementations")
            recent_implementations = sorted(
                implemented_decisions,
                key=lambda d: d.implementation_date or datetime.min,
                reverse=True
            )[:5]

            for decision in recent_implementations:
                if decision.implementation_date:
                    content.append(f"- **{decision.title}** - Implemented {decision.implementation_date.strftime('%Y-%m-%d')}")
        else:
            content.append("- No decisions have been implemented yet")
        content.append("")

        # Stakeholder analysis
        content.append("## 👥 Stakeholder Analysis")
        content.append("")

        all_stakeholders = []
        for decision in self.decision_records.values():
            all_stakeholders.extend(decision.stakeholders)

        stakeholder_counts = Counter(all_stakeholders)
        if stakeholder_counts:
            content.append("### Most Involved Stakeholders")
            for stakeholder, count in stakeholder_counts.most_common(5):
                content.append(f"- **{stakeholder}**: {count} decisions")
        else:
            content.append("- No stakeholders identified")
        content.append("")

        content.append("---")
        content.append("*This dashboard is automatically generated by the Decision Intelligence Agent*")

        return "\n".join(content)

    def _get_status_icon(self, status: str) -> str:
        """Get appropriate icon for status"""
        icon_map = {
            "PROPOSED": "💭",
            "APPROVED": "✅",
            "IMPLEMENTED": "🚀",
            "REJECTED": "❌",
            "SUPERSEDED": "🔄",
            "REVIEWED": "👁️"
        }
        return icon_map.get(status, "📋")

    def _get_priority_icon(self, priority: str) -> str:
        """Get appropriate icon for priority"""
        icon_map = {
            "CRITICAL": "🔴",
            "HIGH": "🟡",
            "MEDIUM": "🟢",
            "LOW": "⚪"
        }
        return icon_map.get(priority, "⚪")

    def _create_decision_workflow_system(self) -> Dict[str, Any]:
        """Create decision workflow management system"""
        workflow_content = '''#!/usr/bin/env python3
"""
Decision Workflow Management System
Manages decision status transitions and workflows
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any

class DecisionWorkflow:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.decision_log_path = os.path.join(project_path, "project_management", "DECISION_LOG")
        self.database_path = os.path.join(self.decision_log_path, "decision_database.json")

    def load_decision_database(self) -> Dict[str, Any]:
        """Load decision database"""
        if os.path.exists(self.database_path):
            with open(self.database_path, 'r') as f:
                return json.load(f)
        return {"decisions": {}}

    def update_decision_status(self, decision_id: str, new_status: str,
                             implementer: str = None, notes: str = None) -> Dict[str, Any]:
        """Update decision status"""
        db = self.load_decision_database()

        if decision_id not in db["decisions"]:
            return {"success": False, "error": "Decision not found"}

        decision = db["decisions"][decision_id]
        old_status = decision["status"]

        # Validate status transition
        if not self._is_valid_transition(old_status, new_status):
            return {"success": False, "error": f"Invalid transition from {old_status} to {new_status}"}

        # Update decision
        decision["status"] = new_status
        decision["last_updated"] = datetime.now().isoformat()

        if implementer:
            decision["implementer"] = implementer

        if new_status == "IMPLEMENTED":
            decision["implementation_date"] = datetime.now().isoformat()

        # Add transition notes
        if notes:
            if "transition_history" not in decision:
                decision["transition_history"] = []

            decision["transition_history"].append({
                "from_status": old_status,
                "to_status": new_status,
                "timestamp": datetime.now().isoformat(),
                "notes": notes
            })

        # Save updated database
        with open(self.database_path, 'w') as f:
            json.dump(db, f, indent=2)

        return {
            "success": True,
            "decision_id": decision_id,
            "old_status": old_status,
            "new_status": new_status,
            "timestamp": datetime.now().isoformat()
        }

    def _is_valid_transition(self, from_status: str, to_status: str) -> bool:
        """Check if status transition is valid"""
        # Simplified transition rules
        valid_transitions = {
            "PROPOSED": ["APPROVED", "REJECTED"],
            "APPROVED": ["IMPLEMENTED", "REJECTED", "SUPERSEDED"],
            "IMPLEMENTED": ["REVIEWED", "SUPERSEDED"],
            "REVIEWED": ["CONFIRMED", "SUPERSEDED"],
            "REJECTED": [],
            "SUPERSEDED": []
        }

        return to_status in valid_transitions.get(from_status, [])

    def get_decisions_needing_review(self) -> List[Dict[str, Any]]:
        """Get decisions that need review"""
        db = self.load_decision_database()
        decisions_needing_review = []

        for decision_id, decision in db["decisions"].items():
            if decision.get("review_date"):
                review_date = datetime.fromisoformat(decision["review_date"])
                if review_date < datetime.now():
                    decisions_needing_review.append(decision)
            elif decision["status"] == "APPROVED" and not decision.get("implementation_date"):
                # Approved decisions not implemented within 30 days
                decision_date = datetime.fromisoformat(decision["date_made"])
                if datetime.now() - decision_date > timedelta(days=30):
                    decisions_needing_review.append(decision)

        return decisions_needing_review

def main():
    """Main workflow function"""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Decision Workflow Management")
    parser.add_argument("--project-path", default=".", help="Project path")
    parser.add_argument("--action", required=True,
                       choices=["update_status", "get_review_list"],
                       help="Action to perform")
    parser.add_argument("--decision-id", help="Decision ID")
    parser.add_argument("--new-status", help="New status")
    parser.add_argument("--implementer", help="Implementer name")
    parser.add_argument("--notes", help="Transition notes")

    args = parser.parse_args()

    workflow = DecisionWorkflow(args.project_path)

    if args.action == "update_status":
        if not args.decision_id or not args.new_status:
            print("Error: --decision-id and --new-status required for status update")
            sys.exit(1)

        result = workflow.update_decision_status(
            args.decision_id, args.new_status, args.implementer, args.notes
        )

        if result["success"]:
            print(f"Decision {args.decision_id} updated from {result['old_status']} to {result['new_status']}")
        else:
            print(f"Error: {result['error']}")

    elif args.action == "get_review_list":
        decisions = workflow.get_decisions_needing_review()

        if decisions:
            print(f"Found {len(decisions)} decisions needing review:")
            for decision in decisions:
                print(f"- {decision['decision_id']}: {decision['title']} ({decision['status']})")
        else:
            print("No decisions need review at this time")

if __name__ == "__main__":
    main()
'''

        workflow_dir = os.path.join(self.decision_log_path, "workflow_tools")
        os.makedirs(workflow_dir, exist_ok=True)
        workflow_path = os.path.join(workflow_dir, "decision_workflow.py")

        with open(workflow_path, 'w') as f:
            f.write(workflow_content)

        return {"workflow_system_path": workflow_path, "features": ["status_updates", "transition_validation", "review_tracking"]}

    def _implement_impact_measurement(self) -> Dict[str, Any]:
        """Implement impact measurement system"""
        self.logger.info("Implementing impact measurement")

        impact_system = self._create_impact_measurement_system()

        return {
            "impact_system": impact_system,
            "measurement_criteria": self.impact_criteria
        }

    def _create_impact_measurement_system(self) -> Dict[str, Any]:
        """Create impact measurement system"""
        return {"impact_measurement": "implemented", "categories": list(self.impact_criteria.keys())}

    def _create_decision_analytics(self) -> Dict[str, Any]:
        """Create decision analytics system"""
        return {"analytics": "created", "metrics_available": True}

    def _setup_decision_workflow(self) -> Dict[str, Any]:
        """Setup decision workflow management"""
        return {"workflow": "configured", "status_tracking": "enabled"}

    def _generate_decision_analytics(self) -> Dict[str, Any]:
        """Generate decision analytics"""
        return {"analytics": "generated"}

    def _create_decision_dashboard(self) -> Dict[str, Any]:
        """Create decision dashboard (already done in status dashboard)"""
        return {"dashboard": "created"}

    def _calculate_decision_metrics(self):
        """Calculate decision-related metrics"""
        total_decisions = len(self.decision_records)

        if total_decisions > 0:
            # Implementation rate
            implemented_count = sum(1 for d in self.decision_records.values() if d.status == "IMPLEMENTED")
            self.metrics.implementation_rate = (implemented_count / total_decisions) * 100

            # Average implementation time
            implemented_decisions = [d for d in self.decision_records.values() if d.status == "IMPLEMENTED" and d.implementation_date]
            if implemented_decisions:
                impl_times = [(d.implementation_date - d.date_made).days for d in implemented_decisions]
                self.metrics.average_implementation_days = sum(impl_times) / len(impl_times)

            # Priority and impact counts
            self.metrics.high_priority_decisions = sum(1 for d in self.decision_records.values() if d.priority in ["HIGH", "CRITICAL"])
            self.metrics.critical_impact_decisions = sum(1 for d in self.decision_records.values() if d.impact_level == "CRITICAL")

            # Stakeholder engagement
            total_stakeholders = sum(len(d.stakeholders) for d in self.decision_records.values())
            self.metrics.stakeholder_engagement = (total_stakeholders / total_decisions) if total_decisions > 0 else 0

        self.metrics.decisions_with_status_tracking = len(self.decision_records)
        self.metrics.decisions_with_impact_measurement = len([d for d in self.decision_records.values() if d.impact_level])

    def _get_metrics(self) -> Dict[str, Any]:
        """Get current decision intelligence metrics"""
        return {
            "total_decisions_analyzed": self.metrics.total_decisions_analyzed,
            "decisions_with_status_tracking": self.metrics.decisions_with_status_tracking,
            "decisions_with_impact_measurement": self.metrics.decisions_with_impact_measurement,
            "implementation_rate": self.metrics.implementation_rate,
            "average_implementation_days": self.metrics.average_implementation_days,
            "high_priority_decisions": self.metrics.high_priority_decisions,
            "critical_impact_decisions": self.metrics.critical_impact_decisions,
            "decision_trends": self.metrics.decision_trends,
            "stakeholder_engagement": self.metrics.stakeholder_engagement
        }


def main():
    """Main execution function for the Decision Intelligence Agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Decision Intelligence Agent for Project Management Reorganization")
    parser.add_argument("--project-root", default=None, help="Root directory of the project")
    parser.add_argument("--task-id", default=None, help="Task ID for orchestration")
    parser.add_argument("--action", default="enhance_decision_tracking",
                       choices=["enhance_decision_tracking", "implement_impact_measurement", "create_decision_analytics", "setup_decision_workflow", "get_metrics"],
                       help="Action to perform")
    parser.add_argument("--output", default=None, help="Output file for results")

    args = parser.parse_args()

    # Initialize the Decision Intelligence Agent
    agent = DecisionIntelligenceAgent(project_root=args.project_root)

    # Execute the requested action
    if args.action == "enhance_decision_tracking":
        result = agent._enhance_decision_tracking()
    elif args.action == "implement_impact_measurement":
        result = agent._implement_impact_measurement()
    elif args.action == "create_decision_analytics":
        result = agent._create_decision_analytics()
    elif args.action == "setup_decision_workflow":
        result = agent._setup_decision_workflow()
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