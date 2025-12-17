"""
Documentation Agent

Maintains knowledge base, validates documentation freshness, and manages
documentation versioning for the Script Ohio 2.0 multi-agent system.

Follows OpenAI agents.md best practices:
- Single responsibility: Documentation management only
- Non-overlapping tools: No overlap with other agents
- Clear communication: Standardized documentation formats
- Quality validation: Automated doc freshness checks
"""

import json
import os
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from agents.core.agent_framework import BaseAgent, AgentCapability, PermissionLevel


@dataclass
class DocumentationEntry:
    """Structure for documentation entries"""
    doc_id: str
    title: str
    file_path: str
    category: str  # 'agent', 'api', 'workflow', 'architecture', 'user_guide'
    created_at: datetime
    updated_at: datetime
    author: str
    version: str
    checksum: str  # File integrity check
    metadata: Dict[str, Any]
    freshness_score: float  # 0-1, how recent/relevant the doc is
    dependencies: List[str]  # Other docs this depends on


@dataclass
class ValidationResult:
    """Structure for documentation validation results"""
    doc_id: str
    is_valid: bool
    issues: List[str]
    warnings: List[str]
    freshness_score: float
    last_checked: datetime


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent

    Responsible for:
    - Maintaining comprehensive knowledge base
    - Validating documentation freshness and accuracy
    - Managing documentation versions and dependencies
    - Checking for documentation gaps and inconsistencies
    """

    def __init__(self):
        super().__init__(
            agent_id="documentation_agent",
            agent_name="Documentation Agent",
            permission_level=PermissionLevel.READ_WRITE
        )

        # Set up directories
        self.base_dir = Path(".")
        self.docs_registry_file = Path("docs/documentation_registry.json")
        self.validation_cache_file = Path("docs/validation_cache.json")

        # Ensure docs directory exists
        Path("docs").mkdir(exist_ok=True)

        # Documentation patterns to monitor
        self.doc_patterns = {
            "agent": ["agents/*.py", "agents/README.md", "AGENTS.md"],
            "api": ["api/*.py", "web_app/*.py", "CLAUDE.md"],
            "workflow": ["scripts/*.py", "workflows/*.md"],
            "architecture": ["*.md", "docs/ARCHITECTURE.md"],
            "user_guide": ["README.md", "starter_pack/*.md"]
        }

        # Freshness thresholds (in days)
        self.freshness_thresholds = {
            "agent": 7,      # Agent docs should be current
            "api": 14,       # API docs can be slightly older
            "workflow": 30,  # Workflow docs change less frequently
            "architecture": 90,  # Architecture docs are stable
            "user_guide": 14     # User guides should be current
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following OpenAI best practices"""
        return [
            AgentCapability(
                name="register_documentation",
                description="Register new documentation in the knowledge base",
                execution_time_estimate=1.0,
                required_permissions=["read", "write"],
                tools_used=["file_operations", "hash_calculation"]
            ),
            AgentCapability(
                name="validate_freshness",
                description="Validate documentation freshness and accuracy",
                execution_time_estimate=3.0,
                required_permissions=["read"],
                tools_used=["file_operations", "timestamp_analysis", "content_analysis"]
            ),
            AgentCapability(
                name="check_coverage",
                description="Check for documentation gaps and missing coverage",
                execution_time_estimate=2.0,
                required_permissions=["read"],
                tools_used=["file_scanning", "coverage_analysis"]
            ),
            AgentCapability(
                name="get_knowledge_base",
                description="Retrieve knowledge base entries by category or search",
                execution_time_estimate=1.0,
                required_permissions=["read"],
                tools_used=["file_operations", "search"]
            ),
            AgentCapability(
                name="update_registry",
                description="Update documentation registry with changes",
                execution_time_estimate=1.5,
                required_permissions=["read", "write"],
                tools_used=["file_operations", "registry_management"]
            )
        ]

    def _execute_action(self, action: str, parameters: Dict, user_context: Dict) -> Dict:
        """Execute agent actions with proper error handling"""
        try:
            if action == "register_documentation":
                return self._register_documentation(parameters, user_context)
            elif action == "validate_freshness":
                return self._validate_freshness(parameters, user_context)
            elif action == "check_coverage":
                return self._check_coverage(parameters, user_context)
            elif action == "get_knowledge_base":
                return self._get_knowledge_base(parameters, user_context)
            elif action == "update_registry":
                return self._update_registry(parameters, user_context)
            else:
                return {
                    "success": False,
                    "error": f"Unknown action: {action}",
                    "available_actions": [cap.name for cap in self._define_capabilities()]
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "action": action,
                "parameters": parameters
            }

    def _register_documentation(self, params: Dict, context: Dict) -> Dict:
        """Register new documentation in the knowledge base"""
        required_fields = ["doc_id", "title", "file_path", "category", "author"]
        for field in required_fields:
            if field not in params:
                return {"success": False, "error": f"Missing required field: {field}"}

        file_path = Path(params["file_path"])
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        # Calculate file checksum
        checksum = self._calculate_checksum(file_path)

        # Load existing registry
        registry = self._load_registry()

        # Create documentation entry
        doc_entry = DocumentationEntry(
            doc_id=params["doc_id"],
            title=params["title"],
            file_path=str(file_path),
            category=params["category"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc),
            author=params["author"],
            version=params.get("version", "1.0.0"),
            checksum=checksum,
            metadata=params.get("metadata", {}),
            freshness_score=1.0,  # New docs start fresh
            dependencies=params.get("dependencies", [])
        )

        # Update or add entry
        registry[doc_entry.doc_id] = asdict(doc_entry)
        registry[doc_entry.doc_id]["created_at"] = doc_entry.created_at.isoformat()
        registry[doc_entry.doc_id]["updated_at"] = doc_entry.updated_at.isoformat()

        # Save registry
        self._save_registry(registry)

        return {
            "success": True,
            "doc_id": doc_entry.doc_id,
            "category": doc_entry.category,
            "freshness_score": doc_entry.freshness_score,
            "registry_size": len(registry)
        }

    def _validate_freshness(self, params: Dict, context: Dict) -> Dict:
        """Validate documentation freshness and accuracy"""
        category_filter = params.get("category")
        force_refresh = params.get("force_refresh", False)

        # Load validation cache
        cache = self._load_validation_cache()
        now = datetime.now(timezone.utc)

        # Load registry
        registry = self._load_registry()
        results = []

        for doc_id, doc_data in registry.items():
            # Skip if category filter is set and doesn't match
            if category_filter and doc_data["category"] != category_filter:
                continue

            # Check if we need to revalidate (cache is 24 hours)
            cache_key = f"{doc_id}_freshness"
            if not force_refresh and cache_key in cache:
                last_check = datetime.fromisoformat(cache[cache_key]["last_checked"])
                if (now - last_check) < timedelta(hours=24):
                    results.append(cache[cache_key])
                    continue

            # Perform validation
            validation_result = self._validate_document(doc_data)
            results.append(asdict(validation_result))

            # Update cache
            cache[cache_key] = asdict(validation_result)
            cache[cache_key]["last_checked"] = now.isoformat()

        # Save cache
        self._save_validation_cache(cache)

        # Calculate summary statistics
        valid_docs = sum(1 for r in results if r["is_valid"])
        avg_freshness = sum(r["freshness_score"] for r in results) / len(results) if results else 0

        return {
            "success": True,
            "results": results,
            "summary": {
                "total_checked": len(results),
                "valid_docs": valid_docs,
                "invalid_docs": len(results) - valid_docs,
                "average_freshness": avg_freshness,
                "validation_timestamp": now.isoformat()
            }
        }

    def _check_coverage(self, params: Dict, context: Dict) -> Dict:
        """Check for documentation gaps and missing coverage"""
        # Analyze current codebase
        agent_files = list(Path("agents").glob("*.py"))
        script_files = list(Path("scripts").glob("*.py"))
        src_files = list(Path("src").rglob("*.py"))

        # Load registry
        registry = self._load_registry()
        documented_files = set(doc_data["file_path"] for doc_data in registry.values())

        # Check for undocumented files
        all_code_files = agent_files + script_files + src_files
        undocumented_files = []

        for file_path in all_code_files:
            if str(file_path) not in documented_files:
                # Check if file has meaningful content (more than imports)
                if self._has_meaningful_content(file_path):
                    undocumented_files.append(str(file_path))

        # Check for missing documentation types
        coverage_by_category = {}
        for category in self.doc_patterns.keys():
            category_docs = [
                doc for doc in registry.values()
                if doc["category"] == category
            ]
            coverage_by_category[category] = len(category_docs)

        # Identify gaps
        gaps = []
        for category, count in coverage_by_category.items():
            if count == 0:
                gaps.append(f"No {category} documentation found")

        return {
            "success": True,
            "undocumented_files": undocumented_files,
            "total_code_files": len(all_code_files),
            "coverage_by_category": coverage_by_category,
            "gaps": gaps,
            "documentation_coverage": (
                (len(all_code_files) - len(undocumented_files)) / len(all_code_files) * 100
                if all_code_files else 0
            )
        }

    def _get_knowledge_base(self, params: Dict, context: Dict) -> Dict:
        """Retrieve knowledge base entries by category or search"""
        category = params.get("category")
        search_term = params.get("search_term")
        include_content = params.get("include_content", False)

        registry = self._load_registry()
        results = []

        for doc_id, doc_data in registry.items():
            # Filter by category
            if category and doc_data["category"] != category:
                continue

            # Filter by search term
            if search_term:
                search_lower = search_term.lower()
                if (search_lower not in doc_data["title"].lower() and
                    search_lower not in doc_data["description"].lower() if "description" in doc_data else True):
                    continue

            # Prepare result
            result = {
                "doc_id": doc_id,
                "title": doc_data["title"],
                "category": doc_data["category"],
                "updated_at": doc_data["updated_at"],
                "freshness_score": doc_data["freshness_score"],
                "version": doc_data["version"]
            }

            # Include content if requested
            if include_content:
                file_path = Path(doc_data["file_path"])
                if file_path.exists():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            result["content"] = f.read()
                    except Exception as e:
                        result["content"] = f"Error reading file: {e}"

            results.append(result)

        # Sort by freshness score
        results.sort(key=lambda x: x["freshness_score"], reverse=True)

        return {
            "success": True,
            "results": results,
            "total_count": len(results),
            "filters_applied": {
                "category": category,
                "search_term": search_term
            }
        }

    def _update_registry(self, params: Dict, context: Dict) -> Dict:
        """Update documentation registry with changes"""
        scan_files = params.get("scan_files", False)

        if scan_files:
            # Scan for new or changed files
            updated_count = 0
            registry = self._load_registry()

            for category, patterns in self.doc_patterns.items():
                for pattern in patterns:
                    for file_path in Path(".").glob(pattern):
                        if not file_path.is_file():
                            continue

                        file_str = str(file_path)
                        existing_doc = None

                        # Check if already documented
                        for doc_data in registry.values():
                            if doc_data["file_path"] == file_str:
                                existing_doc = doc_data
                                break

                        # Calculate current checksum
                        current_checksum = self._calculate_checksum(file_path)

                        # Update if new or changed
                        if not existing_doc:
                            # Create new entry
                            doc_id = f"doc_{category}_{file_path.stem}"
                            doc_entry = DocumentationEntry(
                                doc_id=doc_id,
                                title=f"{category.title()}: {file_path.name}",
                                file_path=file_str,
                                category=category,
                                created_at=datetime.now(timezone.utc),
                                updated_at=datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc),
                                author="auto_scan",
                                version="1.0.0",
                                checksum=current_checksum,
                                metadata={"auto_generated": True},
                                freshness_score=1.0,
                                dependencies=[]
                            )
                            registry[doc_id] = asdict(doc_entry)
                            registry[doc_id]["created_at"] = doc_entry.created_at.isoformat()
                            registry[doc_id]["updated_at"] = doc_entry.updated_at.isoformat()
                            updated_count += 1

                        elif existing_doc["checksum"] != current_checksum:
                            # Update existing entry
                            existing_doc["updated_at"] = datetime.now(timezone.utc).isoformat()
                            existing_doc["checksum"] = current_checksum
                            existing_doc["freshness_score"] = 1.0
                            updated_count += 1

            # Save updated registry
            self._save_registry(registry)

            return {
                "success": True,
                "updated_entries": updated_count,
                "registry_size": len(registry)
            }

        return {"success": False, "error": "No update action specified"}

    # Helper methods
    def _load_registry(self) -> Dict:
        """Load documentation registry"""
        if self.docs_registry_file.exists():
            with open(self.docs_registry_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_registry(self, registry: Dict):
        """Save documentation registry"""
        with open(self.docs_registry_file, 'w') as f:
            json.dump(registry, f, indent=2)

    def _load_validation_cache(self) -> Dict:
        """Load validation cache"""
        if self.validation_cache_file.exists():
            with open(self.validation_cache_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_validation_cache(self, cache: Dict):
        """Save validation cache"""
        with open(self.validation_cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate MD5 checksum of file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _validate_document(self, doc_data: Dict) -> ValidationResult:
        """Validate a single document"""
        file_path = Path(doc_data["file_path"])
        now = datetime.now(timezone.utc)

        issues = []
        warnings = []

        # Check if file exists
        if not file_path.exists():
            return ValidationResult(
                doc_id=doc_data["doc_id"],
                is_valid=False,
                issues=["File no longer exists"],
                warnings=[],
                freshness_score=0.0,
                last_checked=now
            )

        # Check file integrity
        current_checksum = self._calculate_checksum(file_path)
        if current_checksum != doc_data["checksum"]:
            issues.append("File has been modified since registration")

        # Calculate freshness score
        category = doc_data["category"]
        threshold_days = self.freshness_thresholds.get(category, 30)
        last_updated = datetime.fromisoformat(doc_data["updated_at"])
        days_old = (now - last_updated).days

        if days_old > threshold_days:
            freshness_score = max(0, 1.0 - (days_old - threshold_days) / threshold_days)
            if freshness_score < 0.5:
                warnings.append(f"Documentation is {days_old} days old")
        else:
            freshness_score = 1.0

        # Check for basic documentation structure
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic content checks
            if len(content.strip()) < 50:
                warnings.append("Document appears to be very short")

            # Check for markdown formatting if it's a markdown file
            if file_path.suffix in ['.md', '.MD']:
                if '##' not in content and '###' not in content:
                    warnings.append("Markdown document lacks section headers")

        except Exception as e:
            issues.append(f"Error reading file: {e}")

        is_valid = len(issues) == 0

        return ValidationResult(
            doc_id=doc_data["doc_id"],
            is_valid=is_valid,
            issues=issues,
            warnings=warnings,
            freshness_score=freshness_score,
            last_checked=now
        )

    def _has_meaningful_content(self, file_path: Path) -> bool:
        """Check if Python file has meaningful content beyond imports"""
        if file_path.suffix != '.py':
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Remove imports and basic structure
            lines = [line.strip() for line in content.split('\n')
                    if line.strip() and
                    not line.strip().startswith(('import ', 'from ', '#', '"""', "'''"))]

            # Check if there are meaningful lines
            return len(lines) > 5
        except Exception:
            return False


# Singleton instance for easy access
documentation_agent = DocumentationAgent()