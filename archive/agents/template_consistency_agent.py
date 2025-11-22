#!/usr/bin/env python3
"""
Template Consistency Agent for Project Management Reorganization

This agent audits all documents against templates and implements validation scripts
to ensure template compliance and standardization across the project management folder.

Role: Template Compliance Specialist
Permission Level: READ_EXECUTE_WRITE (Level 3)
Capabilities: Template auditing, validation scripting, compliance enforcement
"""

import os
import json
import re
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Set
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
class TemplateField:
    """Represents a field in a template"""
    name: str
    field_type: str  # text, date, list, boolean, etc.
    required: bool = True
    validation_pattern: Optional[str] = None
    description: str = ""
    default_value: Any = None
    allowed_values: Optional[List[str]] = None


@dataclass
class TemplateDefinition:
    """Represents a template definition"""
    name: str
    file_patterns: List[str]
    fields: List[TemplateField]
    description: str = ""
    version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceIssue:
    """Represents a template compliance issue"""
    file_path: str
    template_name: str
    issue_type: str  # missing_field, invalid_format, etc.
    field_name: Optional[str] = None
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    severity: str = "medium"  # low, medium, high, critical
    suggestion: str = ""


@dataclass
class TemplateMetrics:
    """Metrics for template consistency analysis"""
    total_files_analyzed: int
    files_compliant: int
    files_with_issues: int
    total_issues_found: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    compliance_percentage: float
    templates_validated: int
    validation_scripts_created: int
    files_fixed: int = 0


class TemplateConsistencyAgent(BaseAgent):
    """
    Template Consistency Agent for auditing and enforcing template compliance

    This agent audits all documents against templates, creates validation scripts,
    and implements template enforcement systems to ensure consistency.
    """

    def __init__(self, agent_id: str = "template_consistency", project_root: str = None):
        """
        Initialize the Template Consistency Agent

        Args:
            agent_id: Unique identifier for this agent
            project_root: Root directory of the Script Ohio 2.0 project
        """
        super().__init__(
            agent_id=agent_id,
            name="Template Consistency - Compliance Auditor",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE
        )

        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_management_path = os.path.join(self.project_root, "project_management")
        self.templates_path = os.path.join(self.project_management_path, "TEMPLATES")

        # Template definitions
        self.template_definitions = self._initialize_template_definitions()

        # File extensions to analyze
        self.target_extensions = {'.md', '.txt', '.yaml', '.yml', '.json'}

        # Metrics tracking
        self.metrics = TemplateMetrics(
            total_files_analyzed=0,
            files_compliant=0,
            files_with_issues=0,
            total_issues_found=0,
            critical_issues=0,
            high_issues=0,
            medium_issues=0,
            low_issues=0,
            compliance_percentage=0.0,
            templates_validated=0,
            validation_scripts_created=0
        )

        # Analysis results
        self.compliance_issues: List[ComplianceIssue] = []
        self.template_files: Dict[str, List[str]] = defaultdict(list)
        self.analysis_log: List[Dict[str, Any]] = []

        # Setup logging
        self._setup_logging()

        self.log_action("initialization", {
            "project_management_path": self.project_management_path,
            "templates_path": self.templates_path,
            "template_definitions": len(self.template_definitions),
            "target_extensions": list(self.target_extensions)
        })

    def _setup_logging(self):
        """Setup logging for template consistency operations"""
        log_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"template_consistency_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.agent_id)

    def _initialize_template_definitions(self) -> Dict[str, TemplateDefinition]:
        """Initialize template definitions for different document types"""
        return {
            "decision_record": TemplateDefinition(
                name="decision_record",
                file_patterns=[r".*decision.*", r".*dec-.*", r".*resolution.*"],
                fields=[
                    TemplateField("decision_id", "text", True, r"DEC-\d{3}", "Unique decision identifier"),
                    TemplateField("title", "text", True, "Brief decision title"),
                    TemplateField("date", "date", True, "Decision date"),
                    TemplateField("status", "text", True, "Current decision status", allowed_values=["PROPOSED", "APPROVED", "IMPLEMENTED", "REJECTED"]),
                    TemplateField("context", "text", True, "Background and context"),
                    TemplateField("decision", "text", True, "The actual decision made"),
                    TemplateField("alternatives", "list", False, "Alternative options considered"),
                    TemplateField("impact", "text", False, "Expected impact of decision"),
                    TemplateField("implementation", "text", False, "Implementation plan")
                ],
                description="Template for recording architectural and project decisions"
            ),

            "status_report": TemplateDefinition(
                name="status_report",
                file_patterns=[r".*status.*", r".*progress.*", r".*weekly.*", r".*monthly.*"],
                fields=[
                    TemplateField("report_date", "date", True, description="Date of status report"),
                    TemplateField("report_period", "text", True, description="Period covered (e.g., 'Week 45, 2025')"),
                    TemplateField("overall_status", "text", True, "Overall project status", allowed_values=["ON_TRACK", "AT_RISK", "DELAYED", "COMPLETED"]),
                    TemplateField("key_achievements", "list", True, description="Key accomplishments"),
                    TemplateField("blockers", "list", False, description="Current blockers or issues"),
                    TemplateField("next_steps", "list", True, description="Planned next steps"),
                    TemplateField("metrics", "dict", False, description="Key performance metrics")
                ],
                description="Template for project status and progress reports"
            ),

            "plan_document": TemplateDefinition(
                name="plan_document",
                file_patterns=[r".*plan.*", r".*roadmap.*", r".*strategy.*"],
                fields=[
                    TemplateField("plan_name", "text", True, description="Name of the plan"),
                    TemplateField("version", "text", True, r"\d+\.\d+", "Plan version number"),
                    TemplateField("created_date", "date", True, description="Plan creation date"),
                    TemplateField("last_updated", "date", True, description="Last update date"),
                    TemplateField("objectives", "list", True, description="Plan objectives"),
                    TemplateField("scope", "text", True, description="Plan scope and boundaries"),
                    TemplateField("timeline", "dict", True, description="Key milestones and dates"),
                    TemplateField("resources", "list", False, description="Required resources"),
                    TemplateField("risks", "list", False, description="Known risks and mitigations")
                ],
                description="Template for planning documents and roadmaps"
            ),

            "quality_report": TemplateDefinition(
                name="quality_report",
                file_patterns=[r".*quality.*", r".*test.*", r".*validation.*", r".*verification.*"],
                fields=[
                    TemplateField("report_date", "date", True, description="Date of quality report"),
                    Query("test_type", "text", True, description="Type of quality test performed"),
                    TemplateField("test_scope", "text", True, description="Scope of testing"),
                    TemplateField("results_summary", "text", True, description="Summary of test results"),
                    TemplateField("pass_rate", "number", False, description="Pass rate percentage"),
                    TemplateField("critical_issues", "list", False, description="Critical issues found"),
                    TemplateField("recommendations", "list", True, description="Quality recommendations")
                ],
                description="Template for quality assurance and testing reports"
            ),

            "meeting_notes": TemplateDefinition(
                name="meeting_notes",
                file_patterns=[r".*meeting.*", r".*notes.*", r".*discussion.*"],
                fields=[
                    TemplateField("meeting_date", "date", True, description="Date of meeting"),
                    TemplateField("meeting_type", "text", True, description="Type of meeting"),
                    TemplateField("attendees", "list", True, description="Meeting attendees"),
                    TemplateField("agenda", "list", True, description="Meeting agenda items"),
                    TemplateField("key_decisions", "list", False, description="Key decisions made"),
                    TemplateField("action_items", "list", True, description="Action items with owners"),
                    TemplateField("next_meeting", "date", False, description="Date of next meeting")
                ],
                description="Template for meeting notes and discussions"
            )
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this template consistency agent"""
        return [
            AgentCapability("template_auditing"),
            AgentCapability("compliance_validation"),
            AgentCapability("field_validation"),
            AgentCapability("template_enforcement"),
            AgentCapability("automation_scripting"),
            AgentCapability("quality_metrics")
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute template consistency actions

        Args:
            action: The action to execute
            parameters: Parameters for the action
            user_context: User context and preferences

        Returns:
            Action execution results
        """
        if action == "audit_templates":
            return self._audit_template_compliance()
        elif action == "create_validation_scripts":
            return self._create_validation_scripts()
        elif action == "enforce_templates":
            return self._enforce_template_compliance()
        elif action == "generate_template_report":
            return self._generate_template_report()
        elif action == "get_metrics":
            return self._get_metrics()
        else:
            return {"error": f"Unknown action: {action}"}

    def _audit_template_compliance(self) -> Dict[str, Any]:
        """
        Audit all files in project_management for template compliance

        Returns:
            Compliance audit results
        """
        try:
            self.logger.info("Starting template compliance audit")
            self.log_action("template_audit_start", {"scope": "project_management_folder"})

            # Step 1: Discover and categorize files
            file_discovery_result = self._discover_and_categorize_files()

            # Step 2: Analyze each file against its template
            compliance_results = self._analyze_file_compliance()

            # Step 3: Generate compliance issues
            self._generate_compliance_issues()

            # Step 4: Calculate metrics
            self._calculate_compliance_metrics()

            self.logger.info("Template compliance audit completed")
            return {
                "success": True,
                "file_discovery": file_discovery_result,
                "compliance_results": compliance_results,
                "total_issues": len(self.compliance_issues),
                "compliance_percentage": self.metrics.compliance_percentage,
                "metrics": self._get_metrics(),
                "critical_files": self._get_critical_files()
            }

        except Exception as e:
            self.logger.error(f"Template compliance audit failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _discover_and_categorize_files(self) -> Dict[str, Any]:
        """Discover all files and categorize them by template type"""
        self.logger.info("Discovering and categorizing files")

        total_files = 0
        categorized_files = 0
        uncategorized_files = 0

        # Walk through project_management directory
        for root, dirs, files in os.walk(self.project_management_path):
            # Skip REORGANIZATION_SYSTEM directory
            if "REORGANIZATION_SYSTEM" in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()

                if file_ext in self.target_extensions:
                    total_files += 1
                    relative_path = os.path.relpath(file_path, self.project_management_path)

                    # Determine template type
                    template_type = self._determine_template_type(file)

                    if template_type:
                        self.template_files[template_type].append(file_path)
                        categorized_files += 1
                    else:
                        self.template_files["uncategorized"].append(file_path)
                        uncategorized_files += 1

        self.metrics.total_files_analyzed = total_files

        return {
            "total_files_found": total_files,
            "categorized_files": categorized_files,
            "uncategorized_files": uncategorized_files,
            "template_distribution": {k: len(v) for k, v in self.template_files.items()},
            "target_extensions": list(self.target_extensions)
        }

    def _determine_template_type(self, filename: str) -> Optional[str]:
        """Determine the template type based on filename patterns"""
        filename_lower = filename.lower()

        for template_name, template_def in self.template_definitions.items():
            for pattern in template_def.file_patterns:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    return template_name

        return None

    def _analyze_file_compliance(self) -> Dict[str, Any]:
        """Analyze each file against its template definition"""
        self.logger.info("Analyzing file compliance")

        analysis_results = {}
        files_with_issues = 0

        for template_name, files in self.template_files.items():
            if template_name == "uncategorized":
                continue

            template_def = self.template_definitions[template_name]
            template_results = []

            for file_path in files:
                try:
                    file_analysis = self._analyze_single_file(file_path, template_def)
                    template_results.append(file_analysis)

                    if file_analysis["has_issues"]:
                        files_with_issues += 1

                except Exception as e:
                    self.logger.warning(f"Error analyzing file {file_path}: {str(e)}")
                    template_results.append({
                        "file_path": file_path,
                        "has_issues": True,
                        "error": str(e)
                    })

            analysis_results[template_name] = {
                "total_files": len(files),
                "files_with_issues": files_with_issues,
                "compliance_rate": round(((len(files) - files_with_issues) / len(files)) * 100, 2) if files else 100,
                "details": template_results
            }

        self.metrics.files_with_issues = files_with_issues
        self.metrics.files_compliant = self.metrics.total_files_analyzed - files_with_issues

        return analysis_results

    def _analyze_single_file(self, file_path: str, template_def: TemplateDefinition) -> Dict[str, Any]:
        """Analyze a single file against its template definition"""
        file_content = self._read_file_content(file_path)
        file_issues = []
        found_fields = set()

        # Check for required fields
        for field in template_def.fields:
            field_value = self._extract_field_value(file_content, field.name)

            if field_value is not None:
                found_fields.add(field.name)

                # Validate field format if pattern is specified
                if field.validation_pattern and not re.search(field.validation_pattern, str(field_value), re.IGNORECASE):
                    issue = ComplianceIssue(
                        file_path=file_path,
                        template_name=template_def.name,
                        issue_type="invalid_format",
                        field_name=field.name,
                        expected_value=field.validation_pattern,
                        actual_value=str(field_value)[:100],  # Truncate long values
                        severity="medium" if field.required else "low",
                        suggestion=f"Format should match pattern: {field.validation_pattern}"
                    )
                    file_issues.append(issue)
                    self.compliance_issues.append(issue)

                # Validate allowed values if specified
                if field.allowed_values and field_value not in field.allowed_values:
                    issue = ComplianceIssue(
                        file_path=file_path,
                        template_name=template_def.name,
                        issue_type="invalid_value",
                        field_name=field.name,
                        expected_value=f"One of: {field.allowed_values}",
                        actual_value=str(field_value),
                        severity="high" if field.required else "medium",
                        suggestion=f"Value should be one of: {field.allowed_values}"
                    )
                    file_issues.append(issue)
                    self.compliance_issues.append(issue)

            elif field.required:
                # Missing required field
                issue = ComplianceIssue(
                    file_path=file_path,
                    template_name=template_def.name,
                    issue_type="missing_field",
                    field_name=field.name,
                    expected_value="Required field",
                    actual_value="Not found",
                    severity="high",
                    suggestion=f"Add required field: {field.name}"
                )
                file_issues.append(issue)
                self.compliance_issues.append(issue)

        return {
            "file_path": file_path,
            "template_name": template_def.name,
            "has_issues": len(file_issues) > 0,
            "issues_count": len(file_issues),
            "found_fields": list(found_fields),
            "missing_required_fields": [f.name for f in template_def.fields if f.required and f.name not in found_fields],
            "issues": [
                {
                    "type": issue.issue_type,
                    "field": issue.field_name,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion
                }
                for issue in file_issues
            ]
        }

    def _read_file_content(self, file_path: str) -> str:
        """Read file content based on file extension"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return ""

    def _extract_field_value(self, content: str, field_name: str) -> Optional[Any]:
        """Extract field value from file content"""
        field_name_lower = field_name.lower().replace(" ", "_").replace("-", "_")

        # Common patterns for field extraction
        patterns = [
            rf"# {field_name}[:\s]*\n?(.*?)(?=\n# |\n\n|\Z)",  # Markdown headers
            rf"{field_name}[:\s=]+\s*(.*?)(?=\n|\Z)",  # Key: value format
            rf"{field_name_lower}[:\s=]+\s*(.*?)(?=\n|\Z)",  # lowercase version
            rf"['\"]{field_name}['\"]\s*[:=]\s*['\"](.*?)['\"]",  # JSON/YAML format
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Clean up the value
                value = re.sub(r'^[\'"\s]+|[\'"\s]+$', '', value)  # Remove quotes and extra spaces
                return value if value else None

        return None

    def _generate_compliance_issues(self):
        """Generate detailed compliance issues summary"""
        self.logger.info("Generating compliance issues summary")

        # Count issues by severity
        severity_counts = Counter([issue.severity for issue in self.compliance_issues])
        self.metrics.critical_issues = severity_counts.get("critical", 0)
        self.metrics.high_issues = severity_counts.get("high", 0)
        self.metrics.medium_issues = severity_counts.get("medium", 0)
        self.metrics.low_issues = severity_counts.get("low", 0)
        self.metrics.total_issues_found = len(self.compliance_issues)

    def _calculate_compliance_metrics(self):
        """Calculate compliance percentage and other metrics"""
        if self.metrics.total_files_analyzed > 0:
            self.metrics.compliance_percentage = round(
                (self.metrics.files_compliant / self.metrics.total_files_analyzed) * 100, 2
            )
        else:
            self.metrics.compliance_percentage = 100.0

        self.metrics.templates_validated = len(self.template_definitions)

    def _get_critical_files(self) -> List[Dict[str, Any]]:
        """Get files with critical or high severity issues"""
        critical_files = defaultdict(list)

        for issue in self.compliance_issues:
            if issue.severity in ["critical", "high"]:
                critical_files[issue.file_path].append({
                    "template": issue.template_name,
                    "field": issue.field_name,
                    "issue_type": issue.issue_type,
                    "severity": issue.severity,
                    "suggestion": issue.suggestion
                })

        return [
            {
                "file_path": file_path,
                "issue_count": len(issues),
                "issues": issues
            }
            for file_path, issues in critical_files.items()
        ]

    def _create_validation_scripts(self) -> Dict[str, Any]:
        """Create validation scripts for ongoing template compliance"""
        self.logger.info("Creating template validation scripts")

        scripts_created = []

        # 1. Template validation script
        template_validator = self._create_template_validator_script()
        scripts_created.append(template_validator)

        # 2. Pre-commit validation hook
        precommit_hook = self._create_precommit_hook()
        scripts_created.append(precommit_hook)

        # 3. Template generation script
        template_generator = self._create_template_generator_script()
        scripts_created.append(template_generator)

        # 4. Compliance monitoring script
        compliance_monitor = self._create_compliance_monitor_script()
        scripts_created.append(compliance_monitor)

        self.metrics.validation_scripts_created = len(scripts_created)

        return {
            "scripts_created": scripts_created,
            "total_scripts": len(scripts_created),
            "scripts_directory": os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "template_validation")
        }

    def _create_template_validator_script(self) -> Dict[str, Any]:
        """Create a comprehensive template validation script"""
        script_content = f'''#!/usr/bin/env python3
"""
Template Validator Script
Validates files against template definitions for compliance
"""

import os
import re
import json
import sys
from datetime import datetime
from pathlib import Path

# Template definitions (embedded)
TEMPLATE_DEFINITIONS = {json.dumps({k: {
    "name": v.name,
    "file_patterns": v.file_patterns,
    "fields": [
        {
            "name": f.name,
            "field_type": f.field_type,
            "required": f.required,
            "validation_pattern": f.validation_pattern,
            "allowed_values": f.allowed_values
        }
        for f in v.fields
    ]
} for k, v in self.template_definitions.items()}, indent=2)}

def validate_file(file_path: str, template_name: str) -> dict:
    """Validate a single file against its template"""
    if template_name not in TEMPLATE_DEFINITIONS:
        return {{"valid": False, "error": "Unknown template"}}

    template = TEMPLATE_DEFINITIONS[template_name]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {{"valid": False, "error": f"Could not read file: {{e}}"}}

    issues = []
    found_fields = set()

    for field in template["fields"]:
        field_value = extract_field_value(content, field["name"])

        if field_value is not None:
            found_fields.add(field["name"])

            # Validate format
            if field["validation_pattern"] and not re.search(field["validation_pattern"], str(field_value), re.IGNORECASE):
                issues.append({{
                    "field": field["name"],
                    "issue": "invalid_format",
                    "expected": field["validation_pattern"],
                    "actual": str(field_value)[:100]
                }})

            # Validate allowed values
            if field["allowed_values"] and field_value not in field["allowed_values"]:
                issues.append({{
                    "field": field["name"],
                    "issue": "invalid_value",
                    "expected": field["allowed_values"],
                    "actual": str(field_value)
                }})
        elif field["required"]:
            issues.append({{
                "field": field["name"],
                "issue": "missing_field",
                "expected": "Required field",
                "actual": "Not found"
            }})

    return {{
        "valid": len(issues) == 0,
        "issues_count": len(issues),
        "issues": issues,
        "found_fields": list(found_fields),
        "missing_required": [f["name"] for f in template["fields"] if f["required"] and f["name"] not in found_fields]
    }}

def extract_field_value(content: str, field_name: str) -> str:
    """Extract field value from content"""
    patterns = [
        rf"# {{field_name}}[:\\s]*\\n?(.*?)(?=\\n# |\\n\\n|\\Z)",
        rf"{{field_name}}[:\\s=]+\\s*(.*?)(?=\\n|\\Z)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None

def determine_template_type(filename: str) -> str:
    """Determine template type from filename"""
    filename_lower = filename.lower()

    for template_name, template in TEMPLATE_DEFINITIONS.items():
        for pattern in template["file_patterns"]:
            if re.search(pattern, filename_lower, re.IGNORECASE):
                return template_name
    return None

def main():
    """Main validation function"""
    if len(sys.argv) < 2:
        print("Usage: python template_validator.py <file_or_directory>")
        sys.exit(1)

    target = sys.argv[1]
    all_valid = True
    total_files = 0
    valid_files = 0

    if os.path.isfile(target):
        template_type = determine_template_type(os.path.basename(target))
        if template_type:
            result = validate_file(target, template_type)
            total_files += 1
            if result["valid"]:
                valid_files += 1
                print(f"✅ {{target}} - Valid")
            else:
                all_valid = False
                print(f"❌ {{target}} - {{result['issues_count']}} issues found")
                for issue in result["issues"]:
                    print(f"   - {{issue['field']}}: {{issue['issue']}}")
        else:
            print(f"⚠️  {{target}} - Could not determine template type")

    elif os.path.isdir(target):
        for root, dirs, files in os.walk(target):
            for file in files:
                file_path = os.path.join(root, file)
                template_type = determine_template_type(file)

                if template_type:
                    result = validate_file(file_path, template_type)
                    total_files += 1
                    if result["valid"]:
                        valid_files += 1
                        print(f"✅ {{file_path}} - Valid")
                    else:
                        all_valid = False
                        print(f"❌ {{file_path}} - {{result['issues_count']}} issues")
                        for issue in result["issues"]:
                            print(f"   - {{issue['field']}}: {{issue['issue']}}")

    print(f"\\nValidation Summary: {{valid_files}}/{{total_files}} files valid")

    if not all_valid:
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "template_validation")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, "template_validator.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "template_validator.py", "path": script_path, "purpose": "Validate files against templates"}

    def _create_precommit_hook(self) -> Dict[str, Any]:
        """Create a pre-commit hook for template validation"""
        script_content = '''#!/bin/bash
# Pre-commit hook for template validation
# Place this in .git/hooks/pre-commit

echo "Running template validation..."

# Get list of changed files
CHANGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E "\\.(md|txt|yaml|yml|json)$")

if [ -z "$CHANGED_FILES" ]; then
    echo "No template files to validate"
    exit 0
fi

# Run template validator on changed files
VALIDATOR_PATH="$(git rev-parse --show-toplevel)/project_management/REORGANIZATION_SYSTEM/template_validation/template_validator.py"

if [ ! -f "$VALIDATOR_PATH" ]; then
    echo "Template validator not found at $VALIDATOR_PATH"
    exit 1
fi

VALIDATION_FAILED=false

for file in $CHANGED_FILES; do
    if [[ "$file" == project_management/* ]]; then
        echo "Validating $file..."
        python3 "$VALIDATOR_PATH" "$file"
        if [ $? -ne 0 ]; then
            VALIDATION_FAILED=true
            echo "Template validation failed for $file"
        fi
    fi
done

if [ "$VALIDATION_FAILED" = true ]; then
    echo "Template validation failed. Please fix the issues before committing."
    echo "Run 'python3 project_management/REORGANIZATION_SYSTEM/template_validation/template_validator.py <file>' to see detailed issues."
    exit 1
else
    echo "All template files passed validation"
    exit 0
fi
'''

        hook_path = os.path.join(self.project_root, ".git", "hooks", "pre-commit.template")
        os.makedirs(os.path.dirname(hook_path), exist_ok=True)

        with open(hook_path, 'w') as f:
            f.write(script_content)

        return {"name": "pre-commit.template", "path": hook_path, "purpose": "Git pre-commit hook for validation"}

    def _create_template_generator_script(self) -> Dict[str, Any]:
        """Create a script to generate new files from templates"""
        script_content = '''#!/usr/bin/env python3
"""
Template Generator Script
Generates new files from template definitions
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

# Template definitions (embedded)
TEMPLATE_DEFINITIONS = ''' + json.dumps({k: {
            "name": v.name,
            "fields": [
                {
                    "name": f.name,
                    "field_type": f.field_type,
                    "required": f.required,
                    "description": f.description,
                    "default_value": f.default_value,
                    "allowed_values": f.allowed_values
                }
                for f in v.fields
            ]
        } for k, v in self.template_definitions.items()}, indent=2) + '''

def generate_template_file(template_name: str, output_path: str, values: Dict[str, Any] = None) -> str:
    """Generate a new file from a template"""
    if template_name not in TEMPLATE_DEFINITIONS:
        raise ValueError(f"Unknown template: {template_name}")

    template = TEMPLATE_DEFINITIONS[template_name]
    values = values or {}

    # Build file content
    content = []
    content.append(f"# {template_name.replace('_', ' ').title()}")
    content.append(f"# Generated: {datetime.now().isoformat()}")
    content.append("")

    for field in template["fields"]:
        field_value = values.get(field["name"], field.get("default_value", ""))

        if field["field_type"] == "date" and not field_value:
            field_value = datetime.now().strftime("%Y-%m-%d")

        content.append(f"# {field['name'].replace('_', ' ').title()}")
        if field["description"]:
            content.append(f"# {field['description']}")
        if field["allowed_values"]:
            content.append(f"# Allowed values: {', '.join(field['allowed_values'])}")
        if field["required"]:
            content.append(f"# Required: Yes")
        content.append(f"{field['name']}: {field_value}")
        content.append("")

    # Write to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write("\\n".join(content))

    return output_path

def list_templates():
    """List available templates"""
    print("Available templates:")
    for template_name in TEMPLATE_DEFINITIONS.keys():
        template = TEMPLATE_DEFINITIONS[template_name]
        print(f"  - {template_name}: {template.get('name', template_name)}")

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Generate files from templates")
    parser.add_argument("template", nargs="?", help="Template name to use")
    parser.add_argument("output", nargs="?", help="Output file path")
    parser.add_argument("--list", action="store_true", help="List available templates")
    parser.add_argument("--values", help="JSON file with field values")

    args = parser.parse_args()

    if args.list:
        list_templates()
        return

    if not args.template or not args.output:
        print("Usage: python3 template_generator.py <template> <output_file>")
        print("Use --list to see available templates")
        return

    # Load values if provided
    values = {}
    if args.values and os.path.exists(args.values):
        with open(args.values, 'r') as f:
            values = json.load(f)

    try:
        output_path = generate_template_file(args.template, args.output, values)
        print(f"Generated: {output_path}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "template_validation")
        script_path = os.path.join(script_dir, "template_generator.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "template_generator.py", "path": script_path, "purpose": "Generate new files from templates"}

    def _create_compliance_monitor_script(self) -> Dict[str, Any]:
        """Create a script for ongoing compliance monitoring"""
        script_content = '''#!/usr/bin/env python3
"""
Compliance Monitor Script
Monitors template compliance over time and generates reports
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path

def monitor_compliance(project_path: str) -> dict:
    """Monitor compliance across the project"""
    # This would integrate with the template validator
    # For now, return a placeholder structure

    report = {
        "monitoring_date": datetime.now().isoformat(),
        "project_path": project_path,
        "compliance_score": 0.0,
        "total_files": 0,
        "compliant_files": 0,
        "issues_by_type": {},
        "trends": {
            "last_week": {"compliance": 0.0},
            "last_month": {"compliance": 0.0}
        },
        "recommendations": []
    }

    # Run template validator and collect results
    validator_path = os.path.join(project_path, "project_management", "REORGANIZATION_SYSTEM", "template_validation", "template_validator.py")

    if os.path.exists(validator_path):
        import subprocess
        result = subprocess.run([
            "python3", validator_path,
            os.path.join(project_path, "project_management")
        ], capture_output=True, text=True)

        # Parse results and update report
        # This would need more sophisticated parsing in a real implementation
        pass

    return report

def generate_compliance_dashboard(reports: list) -> str:
    """Generate a compliance dashboard from multiple reports"""
    dashboard = "# Template Compliance Dashboard\\n\\n"
    dashboard += f"Generated: {datetime.now().isoformat()}\\n\\n"

    # Add summary statistics
    dashboard += "## Summary\\n\\n"
    # Add compliance charts, trends, etc.

    return dashboard

def main():
    """Main monitoring function"""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor template compliance")
    parser.add_argument("--project-path", default=".", help="Project path to monitor")
    parser.add_argument("--output", help="Output file for report")

    args = parser.parse_args()

    report = monitor_compliance(args.project_path)

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Compliance report saved to {args.output}")
    else:
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "template_validation")
        script_path = os.path.join(script_dir, "compliance_monitor.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "compliance_monitor.py", "path": script_path, "purpose": "Ongoing compliance monitoring"}

    def _enforce_template_compliance(self) -> Dict[str, Any]:
        """Enforce template compliance by fixing issues where possible"""
        self.logger.info("Enforcing template compliance")

        files_fixed = 0

        for issue in self.compliance_issues:
            if issue.severity in ["medium", "high"] and issue.issue_type in ["missing_field", "invalid_format"]:
                try:
                    if self._fix_compliance_issue(issue):
                        files_fixed += 1
                except Exception as e:
                    self.logger.warning(f"Could not fix issue in {issue.file_path}: {str(e)}")

        self.metrics.files_fixed = files_fixed

        return {
            "issues_attempted": len([i for i in self.compliance_issues if i.severity in ["medium", "high"]]),
            "files_fixed": files_fixed,
            "success_rate": round((files_fixed / max(len(self.compliance_issues), 1)) * 100, 2)
        }

    def _fix_compliance_issue(self, issue: ComplianceIssue) -> bool:
        """Attempt to fix a specific compliance issue"""
        # This is a simplified implementation
        # In practice, you'd want more sophisticated fixing logic

        try:
            with open(issue.file_path, 'r') as f:
                content = f.read()

            if issue.issue_type == "missing_field" and issue.field_name:
                # Add missing field at the end of the file
                if not content.endswith('\n'):
                    content += '\n'

                content += f"\n# {issue.field_name.replace('_', ' ').title()}\n"
                content += f"{issue.field_name}: \n"

                with open(issue.file_path, 'w') as f:
                    f.write(content)
                return True

        except Exception:
            return False

        return False

    def _generate_template_report(self) -> Dict[str, Any]:
        """Generate comprehensive template compliance report"""
        return {
            "report_date": datetime.now().isoformat(),
            "project_path": self.project_management_path,
            "metrics": self._get_metrics(),
            "template_definitions": {
                name: {
                    "name": template_def.name,
                    "description": template_def.description,
                    "field_count": len(template_def.fields),
                    "required_fields": len([f for f in template_def.fields if f.required])
                }
                for name, template_def in self.template_definitions.items()
            },
            "compliance_issues_summary": {
                "total_issues": len(self.compliance_issues),
                "by_severity": {
                    "critical": self.metrics.critical_issues,
                    "high": self.metrics.high_issues,
                    "medium": self.metrics.medium_issues,
                    "low": self.metrics.low_issues
                },
                "by_template": {
                    template: len([i for i in self.compliance_issues if i.template_name == template])
                    for template in self.template_definitions.keys()
                }
            },
            "critical_files": self._get_critical_files(),
            "recommendations": [
                "Run template validation before committing changes",
                "Use template generator for new documents",
                "Set up pre-commit hooks for automated validation",
                "Review and fix high-priority compliance issues"
            ]
        }

    def _get_metrics(self) -> Dict[str, Any]:
        """Get current template consistency metrics"""
        return {
            "total_files_analyzed": self.metrics.total_files_analyzed,
            "files_compliant": self.metrics.files_compliant,
            "files_with_issues": self.metrics.files_with_issues,
            "total_issues_found": self.metrics.total_issues_found,
            "critical_issues": self.metrics.critical_issues,
            "high_issues": self.metrics.high_issues,
            "medium_issues": self.metrics.medium_issues,
            "low_issues": self.metrics.low_issues,
            "compliance_percentage": self.metrics.compliance_percentage,
            "templates_validated": self.metrics.templates_validated,
            "validation_scripts_created": self.metrics.validation_scripts_created,
            "files_fixed": self.metrics.files_fixed
        }


def main():
    """Main execution function for the Template Consistency Agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Template Consistency Agent for Project Management Reorganization")
    parser.add_argument("--project-root", default=None, help="Root directory of the project")
    parser.add_argument("--task-id", default=None, help="Task ID for orchestration")
    parser.add_argument("--action", default="audit_templates",
                       choices=["audit_templates", "create_validation_scripts", "enforce_templates", "generate_template_report", "get_metrics"],
                       help="Action to perform")
    parser.add_argument("--output", default=None, help="Output file for results")

    args = parser.parse_args()

    # Initialize the Template Consistency Agent
    agent = TemplateConsistencyAgent(project_root=args.project_root)

    # Execute the requested action
    if args.action == "audit_templates":
        result = agent._audit_template_compliance()
    elif args.action == "create_validation_scripts":
        result = agent._create_validation_scripts()
    elif args.action == "enforce_templates":
        result = agent._enforce_template_compliance()
    elif args.action == "generate_template_report":
        result = agent._generate_template_report()
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