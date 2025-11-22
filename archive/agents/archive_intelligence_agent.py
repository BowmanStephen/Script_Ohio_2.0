#!/usr/bin/env python3
"""
Archive Intelligence Agent for Project Management Reorganization

This agent transforms chaotic archival into intelligent quarterly structure,
implementing automated archival scripts and historical indexing system.

Role: Archive Transformation Specialist
Permission Level: READ_EXECUTE_WRITE (Level 3)
Capabilities: Archive restructuring, automated archival, historical indexing
"""

import os
import json
import shutil
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict
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
class ArchiveFile:
    """Represents a file in the archive with metadata"""
    original_path: str
    filename: str
    file_size: int
    created_date: Optional[datetime]
    modified_date: Optional[datetime]
    file_type: str
    quarter: Optional[str] = None
    year: Optional[int] = None
    content_category: Optional[str] = None
    priority: str = "medium"  # high, medium, low


@dataclass
class ArchiveMetrics:
    """Metrics for archive transformation"""
    total_files_processed: int
    files_reorganized: int
    quarters_created: int
    archive_size_reduction_mb: float
    indexing_entries_created: int
    automation_scripts_created: int
    historical_links_established: int


class ArchiveIntelligenceAgent(BaseAgent):
    """
    Archive Intelligence Agent for transforming project management archival

    This agent transforms the chaotic ARCHIVE/ folder into an intelligent
    quarterly structure with automated archival scripts and historical indexing.
    """

    def __init__(self, agent_id: str = "archive_intelligence", project_root: str = None):
        """
        Initialize the Archive Intelligence Agent

        Args:
            agent_id: Unique identifier for this agent
            project_root: Root directory of the Script Ohio 2.0 project
        """
        super().__init__(
            agent_id=agent_id,
            name="Archive Intelligence - Quarterly Reorganization Specialist",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE
        )

        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_management_path = os.path.join(self.project_root, "project_management")
        self.archive_path = os.path.join(self.project_management_path, "ARCHIVE")
        self.new_archive_path = os.path.join(self.project_management_path, "archive")

        # Archive configuration
        self.quarterly_structure = {
            "current_year": datetime.now().year,
            "quarters": ["Q1", "Q2", "Q3", "Q4"],
            "quarter_months": {
                "Q1": [1, 2, 3],
                "Q2": [4, 5, 6],
                "Q3": [7, 8, 9],
                "Q4": [10, 11, 12]
            }
        }

        # File categorization rules
        self.category_patterns = {
            "status_reports": [r".*status.*", r".*progress.*", r".*weekly.*", r".*monthly.*"],
            "decision_records": [r".*decision.*", r".*dec-.*", r".*resolution.*"],
            "planning_docs": [r".*plan.*", r".*roadmap.*", r".*strategy.*"],
            "meeting_notes": [r".*meeting.*", r".*notes.*", r".*discussion.*"],
            "technical_docs": [r".*technical.*", r".*architecture.*", r".*api.*"],
            "quality_reports": [r".*quality.*", r".*test.*", r".*validation.*"],
            "risk_management": [r".*risk.*", r".*mitigation.*", r".*issue.*"],
            "project_docs": [r".*project.*", r".*overview.*", r".*summary.*"]
        }

        # Metrics tracking
        self.metrics = ArchiveMetrics(
            total_files_processed=0,
            files_reorganized=0,
            quarters_created=0,
            archive_size_reduction_mb=0.0,
            indexing_entries_created=0,
            automation_scripts_created=0,
            historical_links_established=0
        )

        # Processing state
        self.archive_files = []
        self.processing_log = []
        self.errors_encountered = []

        # Setup logging
        self._setup_logging()

        self.log_action("initialization", {
            "archive_path": self.archive_path,
            "new_archive_path": self.new_archive_path,
            "quarters_configured": len(self.quarterly_structure["quarters"]),
            "categories_configured": len(self.category_patterns)
        })

    def _setup_logging(self):
        """Setup logging for archive operations"""
        log_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"archive_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.agent_id)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this archive intelligence agent"""
        return [
            AgentCapability("archive_restructuring"),
            AgentCapability("quarterly_organization"),
            AgentCapability("automated_archival"),
            AgentCapability("historical_indexing"),
            AgentCapability("file_categorization"),
            AgentCapability("automation_scripting")
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute archive intelligence actions

        Args:
            action: The action to execute
            parameters: Parameters for the action
            user_context: User context and preferences

        Returns:
            Action execution results
        """
        if action == "reorganize_archive":
            return self._reorganize_archive()
        elif action == "analyze_current_archive":
            return self._analyze_current_archive()
        elif action == "create_automation_scripts":
            return self._create_automation_scripts()
        elif action == "build_historical_index":
            return self._build_historical_index()
        elif action == "get_metrics":
            return self._get_metrics()
        else:
            return {"error": f"Unknown action: {action}"}

    def _reorganize_archive(self) -> Dict[str, Any]:
        """
        Main method to reorganize the archive into quarterly structure

        Returns:
            Reorganization results and metrics
        """
        try:
            self.logger.info("Starting archive reorganization")
            self.log_action("archive_reorganization_start", {"method": "quarterly_structure"})

            # Step 1: Analyze current archive structure
            current_analysis = self._analyze_current_archive()
            if not current_analysis.get("success", False):
                return current_analysis

            # Step 2: Create new quarterly archive structure
            self._create_quarterly_structure()

            # Step 3: Categorize and organize files
            organization_result = self._organize_files_by_quarter()

            # Step 4: Build historical index
            index_result = self._build_historical_index()

            # Step 5: Create automation scripts
            automation_result = self._create_automation_scripts()

            # Step 6: Generate reorganization report
            report = self._generate_reorganization_report()

            # Calculate size reduction
            original_size = current_analysis.get("total_size_mb", 0)
            new_size = self._calculate_archive_size()
            self.metrics.archive_size_reduction_mb = original_size - new_size

            self.logger.info("Archive reorganization completed successfully")
            return {
                "success": True,
                "original_structure": current_analysis,
                "organization_result": organization_result,
                "index_result": index_result,
                "automation_result": automation_result,
                "metrics": self._get_metrics(),
                "report": report
            }

        except Exception as e:
            self.logger.error(f"Archive reorganization failed: {str(e)}")
            self.errors_encountered.append(str(e))
            return {"success": False, "error": str(e)}

    def _analyze_current_archive(self) -> Dict[str, Any]:
        """Analyze the current archive structure"""
        if not os.path.exists(self.archive_path):
            self.logger.warning(f"Archive path does not exist: {self.archive_path}")
            return {"success": False, "error": "Archive path not found"}

        self.logger.info("Analyzing current archive structure")
        total_files = 0
        total_size = 0
        file_types = defaultdict(int)
        date_range = {"earliest": None, "latest": None}

        # Scan archive directory
        for root, dirs, files in os.walk(self.archive_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_stat = os.stat(file_path)
                    file_size = file_stat.st_size
                    created_date = datetime.fromtimestamp(file_stat.st_ctime)
                    modified_date = datetime.fromtimestamp(file_stat.st_mtime)

                    # Create ArchiveFile object
                    archive_file = ArchiveFile(
                        original_path=file_path,
                        filename=file,
                        file_size=file_size,
                        created_date=created_date,
                        modified_date=modified_date,
                        file_type=os.path.splitext(file)[1].lower()
                    )

                    # Categorize file
                    archive_file.content_category = self._categorize_file(file)
                    archive_file.quarter = self._determine_quarter(modified_date)
                    archive_file.year = modified_date.year

                    self.archive_files.append(archive_file)

                    # Update statistics
                    total_files += 1
                    total_size += file_size
                    file_types[archive_file.file_type] += 1

                    # Track date range
                    if date_range["earliest"] is None or created_date < date_range["earliest"]:
                        date_range["earliest"] = created_date
                    if date_range["latest"] is None or modified_date > date_range["latest"]:
                        date_range["latest"] = modified_date

                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {str(e)}")
                    self.errors_encountered.append(f"File processing error: {file_path}")

        self.metrics.total_files_processed = total_files

        return {
            "success": True,
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_types": dict(file_types),
            "date_range": {
                "earliest": date_range["earliest"].isoformat() if date_range["earliest"] else None,
                "latest": date_range["latest"].isoformat() if date_range["latest"] else None
            },
            "content_categories": dict(Counter([af.content_category for af in self.archive_files if af.content_category]))
        }

    def _categorize_file(self, filename: str) -> str:
        """Categorize file based on filename patterns"""
        filename_lower = filename.lower()

        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename_lower, re.IGNORECASE):
                    return category

        return "general"

    def _determine_quarter(self, date: datetime) -> str:
        """Determine quarter for a given date"""
        month = date.month
        for quarter, months in self.quarterly_structure["quarter_months"].items():
            if month in months:
                return quarter
        return "Q4"  # Default to Q4

    def _create_quarterly_structure(self):
        """Create the new quarterly archive directory structure"""
        self.logger.info("Creating quarterly archive structure")

        # Create main archive directory
        os.makedirs(self.new_archive_path, exist_ok=True)

        # Create quarterly directories for the past 3 years + current year
        current_year = self.quarterly_structure["current_year"]
        years = list(range(current_year - 3, current_year + 1))

        for year in years:
            for quarter in self.quarterly_structure["quarters"]:
                quarter_path = os.path.join(self.new_archive_path, f"{year}_{quarter}")
                os.makedirs(quarter_path, exist_ok=True)

                # Create category subdirectories
                for category in self.category_patterns.keys():
                    category_path = os.path.join(quarter_path, category)
                    os.makedirs(category_path, exist_ok=True)

                # Add general category for uncategorized files
                general_path = os.path.join(quarter_path, "general")
                os.makedirs(general_path, exist_ok=True)

        # Create older_years directory for files older than 3 years
        older_years_path = os.path.join(self.new_archive_path, "older_years")
        os.makedirs(older_years_path, exist_ok=True)

        self.metrics.quarters_created = len(years) * len(self.quarterly_structure["quarters"])

    def _organize_files_by_quarter(self) -> Dict[str, Any]:
        """Organize files into the new quarterly structure"""
        self.logger.info("Organizing files into quarterly structure")

        files_moved = 0
        files_with_issues = 0

        for archive_file in self.archive_files:
            try:
                # Determine target directory
                year = archive_file.year
                quarter = archive_file.quarter
                category = archive_file.content_category or "general"

                # Handle older files
                if year < self.quarterly_structure["current_year"] - 3:
                    target_dir = os.path.join(self.new_archive_path, "older_years", category)
                else:
                    target_dir = os.path.join(self.new_archive_path, f"{year}_{quarter}", category)

                os.makedirs(target_dir, exist_ok=True)

                # Create unique filename to avoid conflicts
                target_filename = self._create_unique_filename(archive_file.filename, target_dir)
                target_path = os.path.join(target_dir, target_filename)

                # Copy file to new location
                shutil.copy2(archive_file.original_path, target_path)

                # Create metadata file
                self._create_file_metadata(archive_file, target_path)

                files_moved += 1
                self.metrics.files_reorganized = files_moved

            except Exception as e:
                self.logger.warning(f"Error organizing file {archive_file.filename}: {str(e)}")
                self.errors_encountered.append(f"Organization error: {archive_file.filename}")
                files_with_issues += 1

        return {
            "files_moved": files_moved,
            "files_with_issues": files_with_issues,
            "success_rate": round((files_moved / len(self.archive_files)) * 100, 2) if self.archive_files else 0
        }

    def _create_unique_filename(self, original_filename: str, target_dir: str) -> str:
        """Create a unique filename in the target directory"""
        base_name, extension = os.path.splitext(original_filename)
        counter = 1
        new_filename = original_filename

        while os.path.exists(os.path.join(target_dir, new_filename)):
            new_filename = f"{base_name}_{counter}{extension}"
            counter += 1

        return new_filename

    def _create_file_metadata(self, archive_file: ArchiveFile, target_path: str):
        """Create metadata file for an archived file"""
        metadata = {
            "original_filename": archive_file.filename,
            "original_path": archive_file.original_path,
            "archived_date": datetime.now().isoformat(),
            "created_date": archive_file.created_date.isoformat() if archive_file.created_date else None,
            "modified_date": archive_file.modified_date.isoformat() if archive_file.modified_date else None,
            "file_size": archive_file.file_size,
            "file_type": archive_file.file_type,
            "category": archive_file.content_category,
            "quarter": archive_file.quarter,
            "year": archive_file.year,
            "priority": archive_file.priority
        }

        metadata_path = target_path + ".meta.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _build_historical_index(self) -> Dict[str, Any]:
        """Build a comprehensive historical index of archived content"""
        self.logger.info("Building historical index")

        index = {
            "created_date": datetime.now().isoformat(),
            "archive_version": "2.0",
            "total_files": len(self.archive_files),
            "quarters": {},
            "categories": {},
            "yearly_summary": {},
            "search_index": {}
        }

        # Build quarterly index
        for archive_file in self.archive_files:
            year_quarter = f"{archive_file.year}_{archive_file.quarter}"
            category = archive_file.content_category or "general"

            # Quarterly breakdown
            if year_quarter not in index["quarters"]:
                index["quarters"][year_quarter] = {
                    "total_files": 0,
                    "total_size_mb": 0,
                    "categories": {}
                }

            index["quarters"][year_quarter]["total_files"] += 1
            index["quarters"][year_quarter]["total_size_mb"] += archive_file.file_size / (1024 * 1024)

            if category not in index["quarters"][year_quarter]["categories"]:
                index["quarters"][year_quarter]["categories"][category] = 0
            index["quarters"][year_quarter]["categories"][category] += 1

            # Category breakdown
            if category not in index["categories"]:
                index["categories"][category] = {
                    "total_files": 0,
                    "quarters": {}
                }

            index["categories"][category]["total_files"] += 1

            if year_quarter not in index["categories"][category]["quarters"]:
                index["categories"][category]["quarters"][year_quarter] = 0
            index["categories"][category]["quarters"][year_quarter] += 1

            # Yearly summary
            if archive_file.year not in index["yearly_summary"]:
                index["yearly_summary"][archive_file.year] = {
                    "total_files": 0,
                    "total_size_mb": 0,
                    "categories": {}
                }

            index["yearly_summary"][archive_file.year]["total_files"] += 1
            index["yearly_summary"][archive_file.year]["total_size_mb"] += archive_file.file_size / (1024 * 1024)

            if category not in index["yearly_summary"][archive_file.year]["categories"]:
                index["yearly_summary"][archive_file.year]["categories"][category] = 0
            index["yearly_summary"][archive_file.year]["categories"][category] += 1

        # Save index
        index_path = os.path.join(self.new_archive_path, "historical_index.json")
        with open(index_path, 'w') as f:
            json.dump(index, f, indent=2)

        self.metrics.indexing_entries_created = len(self.archive_files)

        return {
            "index_created": True,
            "index_path": index_path,
            "total_entries": len(self.archive_files),
            "quarters_indexed": len(index["quarters"]),
            "categories_indexed": len(index["categories"])
        }

    def _create_automation_scripts(self) -> Dict[str, Any]:
        """Create automation scripts for ongoing archive management"""
        self.logger.info("Creating automation scripts")

        scripts_created = []

        # 1. Monthly archival script
        monthly_script = self._create_monthly_archival_script()
        scripts_created.append(monthly_script)

        # 2. Quarterly cleanup script
        quarterly_script = self._create_quarterly_cleanup_script()
        scripts_created.append(quarterly_script)

        # 3. Index update script
        index_script = self._create_index_update_script()
        scripts_created.append(index_script)

        # 4. Archive maintenance script
        maintenance_script = self._create_maintenance_script()
        scripts_created.append(maintenance_script)

        self.metrics.automation_scripts_created = len(scripts_created)

        return {
            "scripts_created": scripts_created,
            "total_scripts": len(scripts_created),
            "scripts_directory": os.path.join(self.new_archive_path, "automation_scripts")
        }

    def _create_monthly_archival_script(self) -> Dict[str, Any]:
        """Create a script for monthly archival of old files"""
        script_content = '''#!/usr/bin/env python3
"""
Monthly Archival Script
Automatically moves old files from project_management to archive structure
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path

def monthly_archive():
    """Archive files older than 6 months"""
    project_root = Path(__file__).parent.parent.parent
    project_management_path = project_root / "project_management"
    archive_path = project_management_path / "archive"

    # Define directories to archive from
    archival_targets = [
        "CURRENT_STATE",
        "DECISION_LOG",
        "PLANNING_LOG"
    ]

    cutoff_date = datetime.now() - timedelta(days=180)
    files_archived = 0

    for target_dir in archival_targets:
        target_path = project_management_path / target_dir
        if target_path.exists():
            for file_path in target_path.glob("*"):
                if file_path.is_file():
                    file_modified = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_modified < cutoff_date:
                        # Move to archive
                        quarter = _determine_quarter(file_modified)
                        year = file_modified.year
                        category = _categorize_file(file_path.name)

                        archive_dir = archive_path / f"{year}_{quarter}" / category
                        archive_dir.mkdir(parents=True, exist_ok=True)

                        shutil.move(str(file_path), archive_dir / file_path.name)
                        files_archived += 1

    print(f"Monthly archival completed: {files_archived} files archived")

if __name__ == "__main__":
    monthly_archive()
'''

        script_path = os.path.join(self.new_archive_path, "automation_scripts", "monthly_archival.py")
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "monthly_archival.py", "path": script_path, "purpose": "Monthly automated archival"}

    def _create_quarterly_cleanup_script(self) -> Dict[str, Any]:
        """Create quarterly cleanup and optimization script"""
        script_content = '''#!/usr/bin/env python3
"""
Quarterly Cleanup Script
Optimizes archive structure and performs cleanup operations
"""

import os
import json
import gzip
from datetime import datetime
from pathlib import Path

def quarterly_cleanup():
    """Perform quarterly archive cleanup"""
    archive_path = Path(__file__).parent.parent
    current_quarter = f"{datetime.now().year}_Q{((datetime.now().month - 1) // 3) + 1}"

    # Compress old metadata files
    metadata_files = list(archive_path.rglob("*.meta.json"))
    compressed = 0

    for meta_file in metadata_files:
        # Only compress files older than 1 year
        if datetime.fromtimestamp(meta_file.stat().st_mtime) < datetime.now() - timedelta(days=365):
            compressed_path = meta_file.with_suffix(meta_file.suffix + '.gz')
            with open(meta_file, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            meta_file.unlink()
            compressed += 1

    # Update historical index
    update_historical_index(archive_path)

    print(f"Quarterly cleanup completed: {compressed} files compressed")

if __name__ == "__main__":
    quarterly_cleanup()
'''

        script_path = os.path.join(self.new_archive_path, "automation_scripts", "quarterly_cleanup.py")
        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "quarterly_cleanup.py", "path": script_path, "purpose": "Quarterly cleanup and optimization"}

    def _create_index_update_script(self) -> Dict[str, Any]:
        """Create script to update the historical index"""
        script_content = '''#!/usr/bin/env python3
"""
Index Update Script
Updates the historical index with new archived files
"""

import os
import json
from datetime import datetime
from pathlib import Path

def update_index():
    """Update historical index with new files"""
    archive_path = Path(__file__).parent.parent
    index_path = archive_path / "historical_index.json"

    # Load existing index
    if index_path.exists():
        with open(index_path, 'r') as f:
            index = json.load(f)
    else:
        index = {"created_date": datetime.now().isoformat(), "files": {}}

    # Scan for new files
    new_files = 0
    for meta_file in archive_path.rglob("*.meta.json"):
        if meta_file.name not in index.get("files", {}):
            with open(meta_file, 'r') as f:
                metadata = json.load(f)

            file_id = f"{metadata['year']}_{metadata['quarter']}_{metadata['original_filename']}"
            index["files"][file_id] = metadata
            new_files += 1

    # Save updated index
    index["last_updated"] = datetime.now().isoformat()
    with open(index_path, 'w') as f:
        json.dump(index, f, indent=2)

    print(f"Index updated: {new_files} new files added")

if __name__ == "__main__":
    update_index()
'''

        script_path = os.path.join(self.new_archive_path, "automation_scripts", "update_index.py")
        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "update_index.py", "path": script_path, "purpose": "Historical index updates"}

    def _create_maintenance_script(self) -> Dict[str, Any]:
        """Create general archive maintenance script"""
        script_content = '''#!/usr/bin/env python3
"""
Archive Maintenance Script
Performs regular maintenance tasks on the archive
"""

import os
import json
from datetime import datetime
from pathlib import Path

def archive_maintenance():
    """Perform archive maintenance tasks"""
    archive_path = Path(__file__).parent.parent

    # Check for broken links
    broken_links = 0
    for file_path in archive_path.rglob("*"):
        if file_path.is_symlink() and not file_path.exists():
            print(f"Broken symlink found: {file_path}")
            broken_links += 1

    # Validate metadata files
    invalid_metadata = 0
    for meta_file in archive_path.rglob("*.meta.json"):
        try:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)

            # Check if the actual file exists
            actual_file = meta_file.with_suffix('')
            if not actual_file.exists():
                print(f"Metadata without file: {meta_file}")
                invalid_metadata += 1

        except json.JSONDecodeError:
            print(f"Invalid metadata file: {meta_file}")
            invalid_metadata += 1

    # Generate maintenance report
    report = {
        "maintenance_date": datetime.now().isoformat(),
        "broken_links": broken_links,
        "invalid_metadata": invalid_metadata,
        "total_files": len(list(archive_path.rglob("*")))
    }

    report_path = archive_path / "maintenance_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Archive maintenance completed. Report saved to: {report_path}")

if __name__ == "__main__":
    archive_maintenance()
'''

        script_path = os.path.join(self.new_archive_path, "automation_scripts", "archive_maintenance.py")
        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "archive_maintenance.py", "path": script_path, "purpose": "General archive maintenance"}

    def _calculate_archive_size(self) -> float:
        """Calculate the total size of the new archive"""
        total_size = 0
        if os.path.exists(self.new_archive_path):
            for root, dirs, files in os.walk(self.new_archive_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        continue
        return round(total_size / (1024 * 1024), 2)

    def _generate_reorganization_report(self) -> Dict[str, Any]:
        """Generate comprehensive reorganization report"""
        return {
            "reorganization_date": datetime.now().isoformat(),
            "original_archive_path": self.archive_path,
            "new_archive_path": self.new_archive_path,
            "files_processed": len(self.archive_files),
            "quarters_created": self.metrics.quarters_created,
            "categories_used": len(self.category_patterns),
            "automation_scripts": self.metrics.automation_scripts_created,
            "indexing_entries": self.metrics.indexing_entries_created,
            "size_reduction_mb": self.metrics.archive_size_reduction_mb,
            "errors_encountered": len(self.errors_encountered),
            "recommendations": [
                "Run monthly archival script to maintain organization",
                "Review quarterly cleanup results quarterly",
                "Update historical index after major changes",
                "Monitor maintenance reports for issues"
            ]
        }

    def _get_metrics(self) -> Dict[str, Any]:
        """Get current metrics for archive transformation"""
        return {
            "total_files_processed": self.metrics.total_files_processed,
            "files_reorganized": self.metrics.files_reorganized,
            "quarters_created": self.metrics.quarters_created,
            "archive_size_reduction_mb": self.metrics.archive_size_reduction_mb,
            "indexing_entries_created": self.metrics.indexing_entries_created,
            "automation_scripts_created": self.metrics.automation_scripts_created,
            "historical_links_established": self.metrics.historical_links_established,
            "errors_encountered": len(self.errors_encountered),
            "success_rate": round((self.metrics.files_reorganized / max(self.metrics.total_files_processed, 1)) * 100, 2)
        }


def main():
    """Main execution function for the Archive Intelligence Agent"""
    import argparse
    from collections import Counter

    parser = argparse.ArgumentParser(description="Archive Intelligence Agent for Project Management Reorganization")
    parser.add_argument("--project-root", default=None, help="Root directory of the project")
    parser.add_argument("--task-id", default=None, help="Task ID for orchestration")
    parser.add_argument("--action", default="reorganize_archive",
                       choices=["reorganize_archive", "analyze_current_archive", "create_automation_scripts", "build_historical_index", "get_metrics"],
                       help="Action to perform")
    parser.add_argument("--output", default=None, help="Output file for results")

    args = parser.parse_args()

    # Initialize the Archive Intelligence Agent
    agent = ArchiveIntelligenceAgent(project_root=args.project_root)

    # Execute the requested action
    if args.action == "reorganize_archive":
        result = agent._reorganize_archive()
    elif args.action == "analyze_current_archive":
        result = agent._analyze_current_archive()
    elif args.action == "create_automation_scripts":
        result = agent._create_automation_scripts()
    elif args.action == "build_historical_index":
        result = agent._build_historical_index()
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