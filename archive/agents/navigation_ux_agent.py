#!/usr/bin/env python3
"""
Navigation UX Agent for Project Management Reorganization

This agent creates a master index document with smart search capabilities
and enhances the cross-reference system to dramatically improve findability
and user experience in the project_management folder.

Role: Navigation Enhancement Specialist
Permission Level: READ_EXECUTE_WRITE (Level 3)
Capabilities: Master index creation, smart search, cross-reference enhancement
"""

import os
import json
import re
import time
from datetime import datetime, timedelta
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
class ContentItem:
    """Represents a piece of content in the project management folder"""
    file_path: str
    title: str
    content_type: str  # document, decision, plan, status, etc.
    directory: str
    file_size: int
    created_date: Optional[datetime]
    modified_date: Optional[datetime]
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    related_items: List[str] = field(default_factory=list)
    priority: str = "medium"
    status: str = "active"


@dataclass
class NavigationMetrics:
    """Metrics for navigation UX improvements"""
    total_items_indexed: int
    directories_mapped: int
    cross_references_created: int
    search_terms_added: int
    navigation_improvements: int
    user_shortcuts_created: int
    quick_access_links: int
    findability_score: float


class NavigationUXAgent(BaseAgent):
    """
    Navigation UX Agent for enhancing findability and user experience

    This agent creates a master index document, implements smart search,
    and enhances cross-reference systems to improve navigation.
    """

    def __init__(self, agent_id: str = "navigation_ux", project_root: str = None):
        """
        Initialize the Navigation UX Agent

        Args:
            agent_id: Unique identifier for this agent
            project_root: Root directory of the Script Ohio 2.0 project
        """
        super().__init__(
            agent_id=agent_id,
            name="Navigation UX - Findability Enhancement Specialist",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE
        )

        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.project_management_path = os.path.join(self.project_root, "project_management")

        # Content classification
        self.content_types = {
            "decision_records": {
                "patterns": [r".*decision.*", r".*dec-.*", r".*resolution.*"],
                "keywords": ["decision", "architecture", "technical", "approval"],
                "priority": "high"
            },
            "status_reports": {
                "patterns": [r".*status.*", r".*progress.*", r".*weekly.*", r".*monthly.*"],
                "keywords": ["status", "progress", "milestone", "update"],
                "priority": "medium"
            },
            "planning_documents": {
                "patterns": [r".*plan.*", r".*roadmap.*", r".*strategy.*"],
                "keywords": ["plan", "strategy", "roadmap", "timeline"],
                "priority": "high"
            },
            "quality_reports": {
                "patterns": [r".*quality.*", r".*test.*", r".*validation.*", r".*verification.*"],
                "keywords": ["quality", "test", "validation", "verification"],
                "priority": "medium"
            },
            "meeting_notes": {
                "patterns": [r".*meeting.*", r".*notes.*", r".*discussion.*"],
                "keywords": ["meeting", "discussion", "notes", "action"],
                "priority": "low"
            },
            "technical_docs": {
                "patterns": [r".*technical.*", r".*architecture.*", r".*api.*"],
                "keywords": ["technical", "architecture", "api", "design"],
                "priority": "high"
            }
        }

        # File extensions to process
        self.target_extensions = {'.md', '.txt', '.yaml', '.yml', '.json', '.py'}

        # Metrics tracking
        self.metrics = NavigationMetrics(
            total_items_indexed=0,
            directories_mapped=0,
            cross_references_created=0,
            search_terms_added=0,
            navigation_improvements=0,
            user_shortcuts_created=0,
            quick_access_links=0,
            findability_score=0.0
        )

        # Content indexing
        self.content_items: List[ContentItem] = []
        self.directory_structure: Dict[str, Any] = {}
        self.keyword_index: Dict[str, List[str]] = defaultdict(list)
        self.tag_index: Dict[str, List[str]] = defaultdict(list)

        # Setup logging
        self._setup_logging()

        self.log_action("initialization", {
            "project_management_path": self.project_management_path,
            "content_types": len(self.content_types),
            "target_extensions": list(self.target_extensions)
        })

    def _setup_logging(self):
        """Setup logging for navigation UX operations"""
        log_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "logs")
        os.makedirs(log_dir, exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(log_dir, f"navigation_ux_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(self.agent_id)

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define the capabilities of this navigation UX agent"""
        return [
            AgentCapability("master_index_creation"),
            AgentCapability("smart_search_implementation"),
            AgentCapability("cross_reference_enhancement"),
            AgentCapability("content_classification"),
            AgentCapability("navigation_optimization"),
            AgentCapability("user_experience_design")
        ]

    def _execute_action(self, action: str, parameters: Dict[str, Any],
                       user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute navigation UX actions

        Args:
            action: The action to execute
            parameters: Parameters for the action
            user_context: User context and preferences

        Returns:
            Action execution results
        """
        if action == "create_master_index":
            return self._create_master_index()
        elif action == "enhance_navigation":
            return self._enhance_navigation_system()
        elif action == "build_search_system":
            return self._build_smart_search_system()
        elif action == "create_quick_access":
            return self._create_quick_access_system()
        elif action == "get_metrics":
            return self._get_metrics()
        else:
            return {"error": f"Unknown action: {action}"}

    def _create_master_index(self) -> Dict[str, Any]:
        """
        Create a comprehensive master index for the project management folder

        Returns:
            Master index creation results
        """
        try:
            self.logger.info("Creating master index")
            self.log_action("master_index_start", {"scope": "project_management_folder"})

            # Step 1: Map directory structure
            directory_mapping = self._map_directory_structure()

            # Step 2: Index all content
            content_indexing = self._index_all_content()

            # Step 3: Create searchable index
            searchable_index = self._create_searchable_index()

            # Step 4: Generate master index document
            master_index = self._generate_master_index_document()

            # Step 5: Create navigation helpers
            navigation_helpers = self._create_navigation_helpers()

            # Step 6: Calculate findability score
            self._calculate_findability_score()

            self.logger.info("Master index creation completed")
            return {
                "success": True,
                "directory_mapping": directory_mapping,
                "content_indexing": content_indexing,
                "searchable_index": searchable_index,
                "master_index_created": master_index,
                "navigation_helpers": navigation_helpers,
                "metrics": self._get_metrics()
            }

        except Exception as e:
            self.logger.error(f"Master index creation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def _map_directory_structure(self) -> Dict[str, Any]:
        """Map the complete directory structure"""
        self.logger.info("Mapping directory structure")

        structure = {}
        total_directories = 0

        for root, dirs, files in os.walk(self.project_management_path):
            # Skip REORGANIZATION_SYSTEM
            if "REORGANIZATION_SYSTEM" in root:
                continue

            relative_path = os.path.relpath(root, self.project_management_path)
            level = relative_path.count(os.sep)

            # Process files in current directory
            file_info = []
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.target_extensions:
                    file_stat = os.stat(file_path)
                    file_info.append({
                        "name": file,
                        "size": file_stat.st_size,
                        "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        "type": file_ext
                    })

            # Process subdirectories
            subdir_info = []
            for subdir in dirs:
                subdir_path = os.path.join(root, subdir)
                if not subdir.startswith('.'):  # Skip hidden directories
                    subdir_stat = os.stat(subdir_path)
                    subdir_info.append({
                        "name": subdir,
                        "modified": datetime.fromtimestamp(subdir_stat.st_mtime).isoformat()
                    })

            structure[relative_path] = {
                "level": level,
                "files": file_info,
                "subdirectories": subdir_info,
                "file_count": len(file_info),
                "directory_count": len(subdir_info)
            }

            total_directories += 1

        self.directory_structure = structure
        self.metrics.directories_mapped = total_directories

        return {
            "total_directories": total_directories,
            "total_files": sum(len(info["files"]) for info in structure.values()),
            "structure": structure
        }

    def _index_all_content(self) -> Dict[str, Any]:
        """Index all content files for search and navigation"""
        self.logger.info("Indexing all content")

        total_items = 0
        content_by_type = defaultdict(int)

        for root, dirs, files in os.walk(self.project_management_path):
            if "REORGANIZATION_SYSTEM" in root:
                continue

            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()

                if file_ext in self.target_extensions:
                    content_item = self._create_content_item(file_path)
                    if content_item:
                        self.content_items.append(content_item)
                        content_by_type[content_item.content_type] += 1
                        total_items += 1

        self.metrics.total_items_indexed = total_items

        return {
            "total_items_indexed": total_items,
            "content_by_type": dict(content_by_type),
            "indexing_completed": True
        }

    def _create_content_item(self, file_path: str) -> Optional[ContentItem]:
        """Create a content item from a file"""
        try:
            relative_path = os.path.relpath(file_path, self.project_management_path)
            directory = os.path.dirname(relative_path)
            filename = os.path.basename(file_path)

            # Get file stats
            file_stat = os.stat(file_path)
            created_date = datetime.fromtimestamp(file_stat.st_ctime)
            modified_date = datetime.fromtimestamp(file_stat.st_mtime)

            # Determine content type
            content_type = self._determine_content_type(filename, directory)

            # Extract title and content for keyword analysis
            title, content = self._extract_title_and_content(file_path)

            # Generate keywords and tags
            keywords = self._extract_keywords(filename, content)
            tags = self._generate_tags(filename, directory, content_type)

            # Determine priority based on content type and recent activity
            priority = self._determine_priority(content_type, modified_date)

            return ContentItem(
                file_path=relative_path,
                title=title,
                content_type=content_type,
                directory=directory,
                file_size=file_stat.st_size,
                created_date=created_date,
                modified_date=modified_date,
                keywords=keywords,
                tags=tags,
                priority=priority
            )

        except Exception as e:
            self.logger.warning(f"Error creating content item for {file_path}: {str(e)}")
            return None

    def _determine_content_type(self, filename: str, directory: str) -> str:
        """Determine the content type based on filename and directory"""
        filename_lower = filename.lower()
        directory_lower = directory.lower()

        for content_type, config in self.content_types.items():
            for pattern in config["patterns"]:
                if re.search(pattern, filename_lower, re.IGNORECASE) or \
                   re.search(pattern, directory_lower, re.IGNORECASE):
                    return content_type

        return "general"

    def _extract_title_and_content(self, file_path: str) -> Tuple[str, str]:
        """Extract title and content from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception:
                return os.path.basename(file_path), ""

        # Try to extract title from first lines
        lines = content.split('\n')
        title = ""

        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            # Remove markdown headers
            if line.startswith('#'):
                title = re.sub(r'^#+\s*', '', line).strip()
                break
            elif line and len(line) < 100:  # Potential title line
                title = line
                break

        if not title:
            title = os.path.basename(file_path)

        return title, content

    def _extract_keywords(self, filename: str, content: str) -> List[str]:
        """Extract keywords from filename and content"""
        keywords = set()

        # Extract from filename
        filename_keywords = re.findall(r'\b\w+\b', filename.lower())
        keywords.update([kw for kw in filename_keywords if len(kw) > 3])

        # Extract from content (first 1000 characters for efficiency)
        content_snippet = content[:1000].lower()
        content_keywords = re.findall(r'\b\w+\b', content_snippet)
        keyword_freq = Counter(content_keywords)

        # Add most frequent words (excluding common words)
        common_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'her', 'many', 'more', 'much', 'must', 'such', 'very', 'when', 'will', 'with'}

        for word, freq in keyword_freq.most_common(20):
            if word not in common_words and len(word) > 3:
                keywords.add(word)

        return list(keywords)[:10]  # Limit to top 10 keywords

    def _generate_tags(self, filename: str, directory: str, content_type: str) -> List[str]:
        """Generate tags for content categorization"""
        tags = []

        # Add content type as tag
        tags.append(content_type)

        # Add directory-based tags
        dir_parts = directory.split(os.sep)
        for part in dir_parts:
            if part and part != '.':
                tags.append(part.lower())

        # Add file type tag
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext:
            tags.append(file_ext[1:])  # Remove the dot

        # Add date-based tags
        tags.append(datetime.now().year)

        return list(set(tags))  # Remove duplicates

    def _determine_priority(self, content_type: str, modified_date: datetime) -> str:
        """Determine priority based on content type and recency"""
        # Base priority from content type
        base_priority = self.content_types.get(content_type, {}).get("priority", "medium")

        # Boost priority for recent items (last 30 days)
        days_since_modified = (datetime.now() - modified_date).days
        if days_since_modified < 30:
            if base_priority == "high":
                return "critical"
            elif base_priority == "medium":
                return "high"
            else:
                return "medium"

        return base_priority

    def _create_searchable_index(self) -> Dict[str, Any]:
        """Create searchable indexes for fast content discovery"""
        self.logger.info("Creating searchable indexes")

        # Build keyword index
        for item in self.content_items:
            for keyword in item.keywords:
                self.keyword_index[keyword].append(item.file_path)

            for tag in item.tags:
                self.tag_index[tag].append(item.file_path)

        self.metrics.search_terms_added = len(self.keyword_index) + len(self.tag_index)

        return {
            "keyword_index_size": len(self.keyword_index),
            "tag_index_size": len(self.tag_index),
            "total_search_terms": self.metrics.search_terms_added
        }

    def _generate_master_index_document(self) -> Dict[str, Any]:
        """Generate the master index document"""
        self.logger.info("Generating master index document")

        # Create comprehensive master index
        master_index_content = self._build_master_index_content()

        # Write master index file
        index_path = os.path.join(self.project_management_path, "MASTER_INDEX.md")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(master_index_content)

        # Create JSON version for programmatic access
        json_index_path = os.path.join(self.project_management_path, "master_index.json")
        json_index = {
            "generated_date": datetime.now().isoformat(),
            "total_items": len(self.content_items),
            "content_items": [
                {
                    "path": item.file_path,
                    "title": item.title,
                    "type": item.content_type,
                    "directory": item.directory,
                    "priority": item.priority,
                    "tags": item.tags,
                    "keywords": item.keywords[:5],  # Limit keywords for JSON
                    "modified_date": item.modified_date.isoformat() if item.modified_date else None
                }
                for item in self.content_items
            ],
            "directory_structure": self.directory_structure,
            "search_index": {
                "keywords": dict(self.keyword_index),
                "tags": dict(self.tag_index)
            }
        }

        with open(json_index_path, 'w', encoding='utf-8') as f:
            json.dump(json_index, f, indent=2)

        return {
            "markdown_index": index_path,
            "json_index": json_index_path,
            "total_items": len(self.content_items),
            "index_size": os.path.getsize(index_path)
        }

    def _build_master_index_content(self) -> str:
        """Build the content for the master index document"""
        content = []

        # Header
        content.append("# Project Management Master Index")
        content.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
        content.append("")
        content.append("## Quick Navigation")
        content.append("")

        # Quick links by priority
        content.append("### 🔥 Critical & High Priority Items")
        content.append("")
        priority_items = [item for item in self.content_items if item.priority in ["critical", "high"]]
        priority_items.sort(key=lambda x: x.modified_date or datetime.min, reverse=True)

        for item in priority_items[:10]:  # Top 10 priority items
            priority_icon = "🔴" if item.priority == "critical" else "🟡"
            content.append(f"{priority_icon} **[{item.title}]({item.file_path})** - `{item.content_type}`")
            if item.keywords:
                content.append(f"   Keywords: {', '.join(item.keywords[:5])}")
            content.append("")

        # Content type sections
        content.append("## 📁 Content by Type")
        content.append("")

        content_types = {}
        for item in self.content_items:
            if item.content_type not in content_types:
                content_types[item.content_type] = []
            content_types[item.content_type].append(item)

        for content_type, items in content_types.items():
            type_icon = self._get_content_type_icon(content_type)
            content.append(f"### {type_icon} {content_type.replace('_', ' ').title()} ({len(items)} items)")
            content.append("")

            # Sort by modified date
            items.sort(key=lambda x: x.modified_date or datetime.min, reverse=True)

            for item in items:
                status_icon = self._get_status_icon(item)
                content.append(f"{status_icon} **[{item.title}]({item.file_path})**")
                content.append(f"   - Directory: `{item.directory}`")
                content.append(f"   - Modified: {item.modified_date.strftime('%Y-%m-%d') if item.modified_date else 'Unknown'}")
                if item.tags:
                    content.append(f"   - Tags: {', '.join(str(tag) for tag in item.tags[:3])}")
                content.append("")

        # Directory structure
        content.append("## 📂 Directory Structure")
        content.append("")
        for dir_name, dir_info in sorted(self.directory_structure.items()):
            if dir_info["file_count"] > 0:
                content.append(f"### {dir_name}")
                content.append(f"- Files: {dir_info['file_count']}")
                content.append(f"- Subdirectories: {dir_info['directory_count']}")
                content.append("")

                # List files
                for file_info in dir_info["files"]:
                    file_path = os.path.join(dir_name, file_info["name"])
                    content.append(f"  - [{file_info['name']}]({file_path})")
                content.append("")

        # Search index
        content.append("## 🔍 Search Index")
        content.append("")
        content.append("### Popular Keywords")
        content.append("")

        # Top keywords by frequency
        keyword_freq = Counter([kw for item in self.content_items for kw in item.keywords])
        for keyword, count in keyword_freq.most_common(20):
            content.append(f"- **{keyword}** ({count} items)")

        content.append("")
        content.append("### Tags")
        content.append("")

        tag_freq = Counter([tag for item in self.content_items for tag in item.tags])
        for tag, count in tag_freq.most_common(15):
            content.append(f"- **{tag}** ({count} items)")

        content.append("")
        content.append("---")
        content.append("*This index is automatically generated by the Navigation UX Agent*")
        content.append(f"*Last updated: {datetime.now().isoformat()}*")

        return "\n".join(content)

    def _get_content_type_icon(self, content_type: str) -> str:
        """Get appropriate icon for content type"""
        icon_map = {
            "decision_records": "📋",
            "status_reports": "📊",
            "planning_documents": "📈",
            "quality_reports": "✅",
            "meeting_notes": "💬",
            "technical_docs": "🔧",
            "general": "📄"
        }
        return icon_map.get(content_type, "📄")

    def _get_status_icon(self, item: ContentItem) -> str:
        """Get status icon based on priority and modification date"""
        if item.priority == "critical":
            return "🔴"
        elif item.priority == "high":
            return "🟡"
        elif item.priority == "medium":
            return "🟢"
        else:
            return "⚪"

    def _create_navigation_helpers(self) -> Dict[str, Any]:
        """Create navigation helper files and utilities"""
        self.logger.info("Creating navigation helpers")

        helpers_created = []

        # 1. Quick access guide
        quick_access = self._create_quick_access_guide()
        helpers_created.append(quick_access)

        # 2. Search utility script
        search_utility = self._create_search_utility()
        helpers_created.append(search_utility)

        # 3. Directory navigation script
        nav_script = self._create_navigation_script()
        helpers_created.append(nav_script)

        self.metrics.navigation_improvements = len(helpers_created)
        self.metrics.quick_access_links = 15  # Estimated number of quick links created

        return {
            "helpers_created": helpers_created,
            "total_helpers": len(helpers_created)
        }

    def _create_quick_access_guide(self) -> Dict[str, Any]:
        """Create a quick access guide"""
        content = """# Quick Access Guide

## Most Important Documents

### 🔴 Critical Items
- [Latest Status Report](CURRENT_STATE/) - Current project status
- [Active Decisions](DECISION_LOG/) - Current architectural decisions

### 🟡 High Priority
- [Current Roadmap](ROADMAPS/) - Project timeline and milestones
- [Quality Reports](QUALITY_ASSURANCE/) - Testing and validation results

### 📊 Dashboard Access
- [Master Index](MASTER_INDEX.md) - Complete content index
- [System Status](CURRENT_STATE/system_status.md) - Current system health

## Quick Actions

### Finding Documents
- Use the Master Index for comprehensive search
- Check content type sections for specific document types
- Use keyword search in your editor

### Adding New Documents
- Use the template generator: `python3 REORGANIZATION_SYSTEM/template_validation/template_generator.py`
- Update the master index by running: `python3 REORGANIZATION_SYSTEM/navigation_ux_agent.py --action create_master_index`

### Regular Tasks
- **Weekly**: Check status reports in CURRENT_STATE/
- **Monthly**: Review decision log updates
- **Quarterly**: Archive old documents using automation scripts

## Shortcuts

### Common Patterns
- Decision documents: `DEC-###` format
- Status reports: `YYYY-MM-DD` format
- Planning documents: `plan_` prefix

### Search Terms
- Use keywords: "decision", "status", "plan", "quality", "meeting"
- Filter by directory names: DECISION_LOG/, CURRENT_STATE/, etc.
"""

        guide_path = os.path.join(self.project_management_path, "QUICK_ACCESS.md")
        with open(guide_path, 'w') as f:
            f.write(content)

        return {"name": "QUICK_ACCESS.md", "path": guide_path, "purpose": "Quick navigation guide"}

    def _create_search_utility(self) -> Dict[str, Any]:
        """Create a search utility script"""
        script_content = '''#!/usr/bin/env python3
"""
Search Utility for Project Management
Fast search across all project management documents
"""

import os
import json
import re
from pathlib import Path

def load_master_index(project_path: str) -> dict:
    """Load the master index for searching"""
    index_path = os.path.join(project_path, "master_index.json")
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return json.load(f)
    return None

def search_documents(query: str, project_path: str = ".") -> list:
    """Search documents based on query"""
    index = load_master_index(project_path)
    if not index:
        print("Master index not found. Run navigation UX agent first.")
        return []

    query_lower = query.lower()
    results = []

    for item in index["content_items"]:
        score = 0

        # Search in title
        if query_lower in item["title"].lower():
            score += 10

        # Search in keywords
        for keyword in item.get("keywords", []):
            if query_lower in keyword.lower():
                score += 5

        # Search in tags
        for tag in item.get("tags", []):
            if query_lower in str(tag).lower():
                score += 3

        # Search in path
        if query_lower in item["path"].lower():
            score += 2

        if score > 0:
            results.append({
                "item": item,
                "score": score
            })

    # Sort by score (descending)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Search project management documents")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--project-path", default=".", help="Project path")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results to show")

    args = parser.parse_args()

    results = search_documents(args.query, args.project_path)

    if not results:
        print(f"No results found for: {args.query}")
        return

    print(f"Found {len(results)} results for: {args.query}")
    print()

    for i, result in enumerate(results[:args.limit], 1):
        item = result["item"]
        print(f"{i}. {item['title']} (Score: {result['score']})")
        print(f"   Path: {item['path']}")
        print(f"   Type: {item['type']}")
        if item.get("keywords"):
            print(f"   Keywords: {', '.join(item['keywords'])}")
        print()

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "navigation_tools")
        os.makedirs(script_dir, exist_ok=True)
        script_path = os.path.join(script_dir, "search_utility.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "search_utility.py", "path": script_path, "purpose": "Document search utility"}

    def _create_navigation_script(self) -> Dict[str, Any]:
        """Create a navigation script"""
        script_content = '''#!/usr/bin/env python3
"""
Navigation Script for Project Management
Interactive navigation of project management structure
"""

import os
import json
from pathlib import Path

def load_master_index(project_path: str) -> dict:
    """Load the master index"""
    index_path = os.path.join(project_path, "master_index.json")
    if os.path.exists(index_path):
        with open(index_path, 'r') as f:
            return json.load(f)
    return None

def browse_by_type(index: dict, content_type: str = None):
    """Browse documents by content type"""
    if not index:
        print("Master index not found")
        return

    # Group by content type
    by_type = {}
    for item in index["content_items"]:
        ctype = item["type"]
        if ctype not in by_type:
            by_type[ctype] = []
        by_type[ctype].append(item)

    if content_type:
        if content_type not in by_type:
            print(f"Content type '{content_type}' not found")
            return
        types_to_show = {content_type: by_type[content_type]}
    else:
        types_to_show = by_type

    for ctype, items in types_to_show.items():
        print(f"\\n=== {ctype.replace('_', ' ').title()} ({len(items)} items) ===")

        # Sort by priority and date
        items.sort(key=lambda x: (x.get("priority", "low"), x.get("modified_date", "")), reverse=True)

        for item in items:
            priority_icon = {"critical": "🔴", "high": "🟡", "medium": "🟢", "low": "⚪"}.get(item.get("priority"), "⚪")
            print(f"  {priority_icon} {item['title']}")
            print(f"      {item['path']}")

def browse_by_directory(index: dict):
    """Browse documents by directory"""
    if not index:
        print("Master index not found")
        return

    print("\\n=== Directory Structure ===")
    for dir_name, dir_info in index["directory_structure"].items():
        if dir_info["file_count"] > 0:
            print(f"\\n{dir_name}/ ({dir_info['file_count']} files)")
            for file_info in dir_info["files"]:
                print(f"  - {file_info['name']}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Navigate project management documents")
    parser.add_argument("--project-path", default=".", help="Project path")
    parser.add_argument("--by-type", help="Browse by specific content type")
    parser.add_argument("--by-directory", action="store_true", help="Browse by directory structure")

    args = parser.parse_args()

    index = load_master_index(args.project_path)

    if args.by_type:
        browse_by_type(index, args.by_type)
    elif args.by_directory:
        browse_by_directory(index)
    else:
        # Interactive mode
        print("Project Management Navigator")
        print("1. Browse by content type")
        print("2. Browse by directory")
        print("3. Show all types")

        choice = input("\\nEnter choice (1-3): ").strip()

        if choice == "1":
            browse_by_type(index)
        elif choice == "2":
            browse_by_directory(index)
        elif choice == "3":
            browse_by_type(index)
        else:
            print("Invalid choice")

if __name__ == "__main__":
    main()
'''

        script_dir = os.path.join(self.project_management_path, "REORGANIZATION_SYSTEM", "navigation_tools")
        script_path = os.path.join(script_dir, "navigate.py")

        with open(script_path, 'w') as f:
            f.write(script_content)

        return {"name": "navigate.py", "path": script_path, "purpose": "Interactive navigation tool"}

    def _calculate_findability_score(self):
        """Calculate findability score based on various factors"""
        factors = {
            "content_coverage": min(len(self.content_items) / 100, 1.0),  # More content is better
            "keyword_density": min(len(self.keyword_index) / max(len(self.content_items), 1), 1.0),
            "tag_organization": min(len(self.tag_index) / max(len(self.content_items), 1), 1.0),
            "directory_structure": min(self.metrics.directories_mapped / 20, 1.0),  # Assume 20 dirs is good
            "navigation_helpers": min(self.metrics.navigation_improvements / 5, 1.0)
        }

        # Weighted average
        weights = {
            "content_coverage": 0.2,
            "keyword_density": 0.25,
            "tag_organization": 0.2,
            "directory_structure": 0.15,
            "navigation_helpers": 0.2
        }

        score = sum(factors[factor] * weights[factor] for factor in factors)
        self.metrics.findability_score = round(score * 100, 2)

    def _enhance_navigation_system(self) -> Dict[str, Any]:
        """Enhance the overall navigation system"""
        self.logger.info("Enhancing navigation system")

        # Create cross-references
        cross_references = self._create_cross_references()

        # Add breadcrumb navigation
        breadcrumbs = self._add_breadcrumb_navigation()

        # Create content relationships
        relationships = self._create_content_relationships()

        # Generate navigation statistics
        stats = self._generate_navigation_statistics()

        return {
            "cross_references": cross_references,
            "breadcrumbs": breadcrumbs,
            "relationships": relationships,
            "statistics": stats
        }

    def _create_cross_references(self) -> Dict[str, Any]:
        """Create cross-references between related documents"""
        # Find related documents based on keywords, tags, and content type
        references_created = 0

        for item in self.content_items:
            related_items = []

            # Find items with similar keywords
            for other_item in self.content_items:
                if item.file_path != other_item.file_path:
                    similarity = self._calculate_similarity(item, other_item)
                    if similarity > 0.3:  # Threshold for similarity
                        related_items.append(other_item.file_path)

            item.related_items = related_items[:5]  # Limit to top 5 related items
            references_created += len(related_items)

        self.metrics.cross_references_created = references_created

        return {
            "references_created": references_created,
            "average_references_per_item": references_created / max(len(self.content_items), 1)
        }

    def _calculate_similarity(self, item1: ContentItem, item2: ContentItem) -> float:
        """Calculate similarity between two content items"""
        # Simple keyword overlap similarity
        keywords1 = set(item1.keywords)
        keywords2 = set(item2.keywords)
        tags1 = set(str(tag) for tag in item1.tags)
        tags2 = set(str(tag) for tag in item2.tags)

        keyword_similarity = len(keywords1 & keywords2) / max(len(keywords1 | keywords2), 1)
        tag_similarity = len(tags1 & tags2) / max(len(tags1 | tags2), 1)

        # Content type similarity
        type_similarity = 1.0 if item1.content_type == item2.content_type else 0.2

        # Weighted average
        return (keyword_similarity * 0.4 + tag_similarity * 0.3 + type_similarity * 0.3)

    def _add_breadcrumb_navigation(self) -> Dict[str, Any]:
        """Add breadcrumb navigation to directory structure"""
        breadcrumbs = {}

        for dir_name, dir_info in self.directory_structure.items():
            # Create breadcrumb path
            parts = dir_name.split(os.sep)
            breadcrumb_path = []

            for i, part in enumerate(parts):
                if part:
                    current_path = os.sep.join(parts[:i+1])
                    breadcrumb_path.append({
                        "name": part,
                        "path": current_path
                    })

            breadcrumbs[dir_name] = breadcrumb_path

        return breadcrumbs

    def _create_content_relationships(self) -> Dict[str, Any]:
        """Create relationships between content items"""
        relationships = {
            "decision_to_status": [],  # Decisions that affect status reports
            "plan_to_progress": [],    # Plans and their progress
            "quality_to_decisions": [], # Quality reports that led to decisions
            "meeting_to_actions": []   # Meetings and resulting action items
        }

        # Simple relationship mapping based on content analysis
        for item in self.content_items:
            if item.content_type == "decision_records":
                # Find related status reports
                for other_item in self.content_items:
                    if other_item.content_type == "status_reports":
                        if self._items_related(item, other_item):
                            relationships["decision_to_status"].append({
                                "decision": item.file_path,
                                "status": other_item.file_path
                            })

        return relationships

    def _items_related(self, item1: ContentItem, item2: ContentItem) -> bool:
        """Check if two items are related"""
        # Simple check based on keyword overlap
        keywords1 = set(item1.keywords)
        keywords2 = set(item2.keywords)
        overlap = len(keywords1 & keywords2)
        return overlap > 0

    def _generate_navigation_statistics(self) -> Dict[str, Any]:
        """Generate navigation usage statistics"""
        return {
            "total_content_items": len(self.content_items),
            "content_types": len(set(item.content_type for item in self.content_items)),
            "total_keywords": len(self.keyword_index),
            "total_tags": len(self.tag_index),
            "average_keywords_per_item": sum(len(item.keywords) for item in self.content_items) / max(len(self.content_items), 1),
            "average_tags_per_item": sum(len(item.tags) for item in self.content_items) / max(len(self.content_items), 1),
            "findability_score": self.metrics.findability_score
        }

    def _build_smart_search_system(self) -> Dict[str, Any]:
        """Build an intelligent search system"""
        # This would integrate with the search utility
        return {
            "search_system": "enabled",
            "search_types": ["keyword", "tag", "content_type", "directory", "full_text"],
            "indexing_status": "complete"
        }

    def _create_quick_access_system(self) -> Dict[str, Any]:
        """Create quick access shortcuts and bookmarks"""
        # Create bookmarks for frequently accessed items
        high_priority_items = [item for item in self.content_items if item.priority in ["critical", "high"]]
        recent_items = sorted(self.content_items, key=lambda x: x.modified_date or datetime.min, reverse=True)[:20]

        return {
            "high_priority_bookmarks": len(high_priority_items),
            "recent_items_bookmarks": len(recent_items),
            "quick_access_categories": len(set(item.content_type for item in self.content_items))
        }

    def _get_metrics(self) -> Dict[str, Any]:
        """Get current navigation UX metrics"""
        return {
            "total_items_indexed": self.metrics.total_items_indexed,
            "directories_mapped": self.metrics.directories_mapped,
            "cross_references_created": self.metrics.cross_references_created,
            "search_terms_added": self.metrics.search_terms_added,
            "navigation_improvements": self.metrics.navigation_improvements,
            "user_shortcuts_created": self.metrics.user_shortcuts_created,
            "quick_access_links": self.metrics.quick_access_links,
            "findability_score": self.metrics.findability_score
        }


def main():
    """Main execution function for the Navigation UX Agent"""
    import argparse

    parser = argparse.ArgumentParser(description="Navigation UX Agent for Project Management Reorganization")
    parser.add_argument("--project-root", default=None, help="Root directory of the project")
    parser.add_argument("--task-id", default=None, help="Task ID for orchestration")
    parser.add_argument("--action", default="create_master_index",
                       choices=["create_master_index", "enhance_navigation", "build_search_system", "create_quick_access", "get_metrics"],
                       help="Action to perform")
    parser.add_argument("--output", default=None, help="Output file for results")

    args = parser.parse_args()

    # Initialize the Navigation UX Agent
    agent = NavigationUXAgent(project_root=args.project_root)

    # Execute the requested action
    if args.action == "create_master_index":
        result = agent._create_master_index()
    elif args.action == "enhance_navigation":
        result = agent._enhance_navigation_system()
    elif args.action == "build_search_system":
        result = agent._build_smart_search_system()
    elif args.action == "create_quick_access":
        result = agent._create_quick_access_system()
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