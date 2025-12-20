#!/usr/bin/env python3
"""
Commit Analyzer Agent - Analyzes Changes for Optimal Commit Strategy

This agent analyzes the scope of changes in the repository and creates
optimal commit batches based on dependencies, risk levels, and logical grouping.

Author: Claude Code Assistant
Created: 2025-12-20
Version: 1.0
"""

import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Add src to path for imports
SRC_ROOT = Path(__file__).resolve().parents[1] / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from agents.core.agent_framework import (
    AgentCapability,
    BaseAgent,
    PermissionLevel,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import for agent registry
try:
    from agents.meta_agent import meta_agent
except ImportError:
    logger.warning("Meta Agent not available - registration disabled")
    meta_agent = None

# Import existing GitHub operations
try:
    sys.path.append(Path(__file__).resolve().parents[1] / "scripts" / "github_operations")
    from git_utils import GitUtils
except ImportError:
    logger.error("GitUtils not found")
    GitUtils = None


class CommitAnalyzerAgent(BaseAgent):
    """
    Analyzes changes and creates optimal commit strategies.

    This agent provides intelligent analysis of repository changes to:
    - Categorize files by type and function
    - Assess risk level of changes
    - Identify dependencies between files
    - Create optimal commit batches
    - Recommend commit message structure

    Capabilities:
    - Analyze file changes comprehensively
    - Create dependency graphs
    - Assess risk levels
    - Generate commit strategies
    - Optimize commit batching
    """

    def __init__(self, agent_id: str, tool_loader=None):
        """Initialize the Commit Analyzer Agent."""
        super().__init__(
            agent_id=agent_id,
            name="Commit Analyzer Agent",
            permission_level=PermissionLevel.READ_ONLY,
            tool_loader=tool_loader,
        )

        self.project_root = Path.cwd()
        self.git_utils = GitUtils() if GitUtils else None

        # File type mappings
        self.file_type_patterns = {
            "python": r"\.py$",
            "javascript": r"\.(js|jsx|ts|tsx)$",
            "markdown": r"\.md$",
            "json": r"\.json$",
            "yaml": r"\.(yml|yaml)$",
            "shell": r"\.(sh|bash)$",
            "docker": r"(Dockerfile|docker-compose.*\.yml)$",
            "config": r"\.(ini|cfg|conf|toml)$",
        }

        # Risk assessment rules
        self.risk_patterns = {
            "high": [
                r"agents/core/",
                r"agents/meta_agent\.py",
                r"src/cfbd_client/",
                r"requirements\.txt$",
                r"package\.json$",
                r"docker-compose\.yml$",
            ],
            "medium": [
                r"agents/",
                r"src/",
                r"scripts/",
                r"web_app/src/",
            ],
            "low": [
                r"docs/",
                r"README",
                r"\.md$",
                r"tests/",
            ]
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define agent capabilities following BaseAgent pattern."""
        return [
            AgentCapability(
                name="analyze_changes",
                description="Comprehensively analyze all file changes in the repository",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["git", "pathlib", "re"],
                data_access=["filesystem", "git_history"],
                execution_time_estimate=30.0,
            ),
            AgentCapability(
                name="assess_risk_level",
                description="Assess risk level of changes based on file types and locations",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["re", "pathlib"],
                data_access=["filesystem"],
                execution_time_estimate=10.0,
            ),
            AgentCapability(
                name="create_dependency_graph",
                description="Analyze dependencies between changed files",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["ast", "re"],
                data_access=["filesystem", "python_modules"],
                execution_time_estimate=45.0,
            ),
            AgentCapability(
                name="generate_commit_strategy",
                description="Generate optimal commit strategy with batching recommendations",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["python"],
                data_access=["analysis_results"],
                execution_time_estimate=15.0,
            ),
            AgentCapability(
                name="create_commit_batches",
                description="Create optimal commit batches based on analysis",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["python"],
                data_access=["analysis_results"],
                execution_time_estimate=20.0,
            ),
            AgentCapability(
                name="suggest_commit_messages",
                description="Suggest appropriate commit messages for each batch",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["python"],
                data_access=["analysis_results"],
                execution_time_estimate=10.0,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict[str, Any], user_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute agent actions with proper error handling and logging."""

        try:
            start_time = time.time()
            logger.info(f"Executing action: {action} with parameters: {list(parameters.keys())}")

            if action == "analyze_changes":
                result = self._analyze_changes(parameters)
            elif action == "assess_risk_level":
                result = self._assess_risk_level(parameters.get("files", []))
            elif action == "create_dependency_graph":
                result = self._create_dependency_graph(parameters.get("files", []))
            elif action == "generate_commit_strategy":
                result = self._generate_commit_strategy(parameters)
            elif action == "create_commit_batches":
                result = self._create_commit_batches(parameters.get("files", []))
            elif action == "suggest_commit_messages":
                result = self._suggest_commit_messages(parameters.get("batches", []))
            else:
                raise ValueError(f"Unknown action: {action}")

            # Update performance metrics
            execution_time = time.time() - start_time
            self._update_metrics(action, True, execution_time)

            logger.info(f"Action {action} completed successfully in {execution_time:.2f}s")

            return {
                "status": "success",
                "result": result,
                "execution_time": execution_time,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Action {action} failed: {str(e)}")
            self._update_metrics(action, False, 0)

            return {
                "status": "error",
                "error": str(e),
                "error_type": type(e).__name__,
                "agent_id": self.agent_id,
                "timestamp": datetime.now().isoformat(),
            }

    def _analyze_changes(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensively analyze all file changes."""
        if not self.git_utils:
            raise RuntimeError("GitUtils not available")

        # Get all changes
        modified_files = self.git_utils.get_modified_files()
        staged_files = self.git_utils.get_staged_files()
        untracked_files = self.git_utils.get_untracked_files()

        all_files = list(set(modified_files + staged_files + untracked_files))

        analysis = {
            "summary": {
                "total_files": len(all_files),
                "modified": len(modified_files),
                "staged": len(staged_files),
                "untracked": len(untracked_files),
                "timestamp": datetime.now().isoformat(),
            },
            "file_analysis": {
                "by_type": defaultdict(int),
                "by_category": defaultdict(int),
                "by_risk": defaultdict(int),
                "by_directory": defaultdict(int),
            },
            "files": []
        }

        # Analyze each file
        for file_path in all_files:
            file_info = {
                "path": file_path,
                "type": self._get_file_type(file_path),
                "category": self._get_file_category(file_path),
                "risk_level": self._assess_file_risk(file_path),
                "directory": str(Path(file_path).parent),
                "size": self._get_file_size(file_path),
                "dependencies": self._get_file_dependencies(file_path),
            }

            # Update counts
            analysis["file_analysis"]["by_type"][file_info["type"]] += 1
            analysis["file_analysis"]["by_category"][file_info["category"]] += 1
            analysis["file_analysis"]["by_risk"][file_info["risk_level"]] += 1
            analysis["file_analysis"]["by_directory"][file_info["directory"]] += 1

            analysis["files"].append(file_info)

        # Convert defaultdicts to regular dicts
        for key in analysis["file_analysis"]:
            analysis["file_analysis"][key] = dict(analysis["file_analysis"][key])

        # Add insights
        analysis["insights"] = self._generate_analysis_insights(analysis)

        logger.info(f"Analysis complete: {len(all_files)} files analyzed")

        return analysis

    def _assess_risk_level(self, files: List[str]) -> Dict[str, Any]:
        """Assess overall risk level of changes."""
        risk_counts = {"high": 0, "medium": 0, "low": 0}

        for file_path in files:
            risk_level = self._assess_file_risk(file_path)
            risk_counts[risk_level] += 1

        # Determine overall risk
        total_files = len(files)
        if total_files == 0:
            overall_risk = "none"
        elif risk_counts["high"] > 0:
            overall_risk = "high"
        elif risk_counts["medium"] > total_files * 0.3:
            overall_risk = "high"
        elif risk_counts["medium"] > 0:
            overall_risk = "medium"
        else:
            overall_risk = "low"

        return {
            "overall_risk": overall_risk,
            "risk_counts": risk_counts,
            "risk_percentage": {
                level: (count / total_files * 100) if total_files > 0 else 0
                for level, count in risk_counts.items()
            },
            "recommendations": self._get_risk_recommendations(overall_risk, risk_counts)
        }

    def _create_dependency_graph(self, files: List[str]) -> Dict[str, Any]:
        """Create dependency graph between changed files."""
        dependencies = {}

        for file_path in files:
            file_deps = self._analyze_file_dependencies(file_path)
            dependencies[file_path] = {
                "dependencies": file_deps,
                "dependents": [],  # Will be filled later
                "dependency_count": len(file_deps),
            }

        # Fill dependents (reverse dependencies)
        for file_path, dep_info in dependencies.items():
            for dep in dep_info["dependencies"]:
                if dep in dependencies:
                    dependencies[dep]["dependents"].append(file_path)

        # Create visualization data
        graph_data = {
            "nodes": [
                {
                    "id": file_path,
                    "type": self._get_file_type(file_path),
                    "category": self._get_file_category(file_path),
                    "risk": self._assess_file_risk(file_path),
                    "dependency_count": deps["dependency_count"],
                }
                for file_path, deps in dependencies.items()
            ],
            "edges": [
                {
                    "from": dep,
                    "to": file_path,
                    "type": "dependency"
                }
                for file_path, deps in dependencies.items()
                for dep in deps["dependencies"]
                if dep in dependencies
            ]
        }

        # Identify dependency clusters
        clusters = self._identify_dependency_clusters(dependencies)

        return {
            "dependencies": dependencies,
            "graph_data": graph_data,
            "clusters": clusters,
            "max_dependency_chain": self._calculate_max_dependency_chain(dependencies),
        }

    def _generate_commit_strategy(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimal commit strategy."""
        files = parameters.get("files", [])
        if not files:
            # Get all changes if not provided
            if self.git_utils:
                all_changes = (self.git_utils.get_modified_files() +
                             self.git_utils.get_staged_files() +
                             self.git_utils.get_untracked_files())
                files = list(set(all_changes))

        # Analyze changes
        analysis = self._analyze_changes({"files": files}) if files else {"files": []}

        # Assess risk
        risk_assessment = self._assess_risk_level(files)

        # Create dependency graph
        dep_graph = self._create_dependency_graph(files)

        # Generate strategy
        strategy = {
            "risk_level": risk_assessment["overall_risk"],
            "total_files": len(files),
            "recommended_approach": self._get_recommended_approach(risk_assessment, analysis),
            "batching_strategy": self._determine_batching_strategy(risk_assessment, dep_graph),
            "safety_measures": self._get_safety_measures(risk_assessment),
            "estimated_duration": self._estimate_commit_duration(files),
        }

        logger.info(f"Commit strategy generated: {strategy['risk_level']} risk, {strategy['total_files']} files")

        return strategy

    def _create_commit_batches(self, files: List[str]) -> List[Dict[str, Any]]:
        """Create optimal commit batches."""
        if not files:
            # Get all changes if not provided
            if self.git_utils:
                all_changes = (self.git_utils.get_modified_files() +
                             self.git_utils.get_staged_files() +
                             self.git_utils.get_untracked_files())
                files = list(set(all_changes))

        # Get risk assessment and dependencies
        risk_assessment = self._assess_risk_level(files)
        dep_graph = self._create_dependency_graph(files)

        # Determine batching strategy
        if risk_assessment["overall_risk"] == "high":
            batches = self._create_conservative_batches(files, dep_graph)
        elif risk_assessment["overall_risk"] == "medium":
            batches = self._create_balanced_batches(files, dep_graph)
        else:
            batches = self._create_aggressive_batches(files, dep_graph)

        # Add commit messages to batches
        for i, batch in enumerate(batches):
            batch["commit_message"] = self._generate_commit_message(batch, i + 1)
            batch["batch_number"] = i + 1

        logger.info(f"Created {len(batches)} commit batches for {len(files)} files")

        return batches

    def _suggest_commit_messages(self, batches: List[Dict[str, Any]]) -> List[str]:
        """Suggest appropriate commit messages for each batch."""
        messages = []

        for batch in batches:
            message = self._generate_commit_message(batch, batch.get("batch_number", 1))
            messages.append(message)

        return messages

    # Helper methods
    def _get_file_type(self, file_path: str) -> str:
        """Determine file type from path."""
        for file_type, pattern in self.file_type_patterns.items():
            if re.search(pattern, file_path):
                return file_type
        return "unknown"

    def _get_file_category(self, file_path: str) -> str:
        """Categorize file by its location in the project."""
        if file_path.startswith("agents/"):
            return "agent"
        elif file_path.startswith("src/"):
            return "source"
        elif file_path.startswith("scripts/"):
            return "script"
        elif file_path.startswith("docs/") or file_path.endswith(".md"):
            return "documentation"
        elif file_path.startswith("data/"):
            return "data"
        elif file_path.startswith("web_app/"):
            return "web_app"
        elif file_path.startswith("tests/"):
            return "test"
        elif file_path.startswith("config/"):
            return "config"
        else:
            return "other"

    def _assess_file_risk(self, file_path: str) -> str:
        """Assess risk level of an individual file."""
        for risk_level, patterns in self.risk_patterns.items():
            for pattern in patterns:
                if re.search(pattern, file_path):
                    return risk_level
        return "low"

    def _get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        try:
            return os.path.getsize(file_path)
        except:
            return 0

    def _get_file_dependencies(self, file_path: str) -> List[str]:
        """Get dependencies for a specific file."""
        dependencies = []

        try:
            if file_path.endswith('.py'):
                dependencies.extend(self._get_python_dependencies(file_path))
            elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                dependencies.extend(self._get_javascript_dependencies(file_path))
            elif file_path.endswith(('.json', '.yml', '.yaml')):
                dependencies.extend(self._get_config_dependencies(file_path))
        except Exception as e:
            logger.debug(f"Error getting dependencies for {file_path}: {e}")

        return dependencies

    def _get_python_dependencies(self, file_path: str) -> List[str]:
        """Extract Python import dependencies."""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find import statements
            import_patterns = [
                r'from (agents|src)\.([^ ]+) import',
                r'import (agents|src)\.([^ \n]+)',
                r'from \.([^ ]+) import',
                r'from \.\.([^ ]+) import',
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        dep = f"{match[0]}.{match[1]}"
                    else:
                        dep = match
                    dependencies.append(dep)

        except Exception as e:
            logger.debug(f"Error parsing Python file {file_path}: {e}")

        return list(set(dependencies))

    def _get_javascript_dependencies(self, file_path: str) -> List[str]:
        """Extract JavaScript/TypeScript dependencies."""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Find import statements
            import_patterns = [
                r'import .+ from [\'"]([^\'"]+)[\'"]',
                r'require\([\'"]([^\'"]+)[\'"]\)',
            ]

            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                dependencies.extend(matches)

        except Exception as e:
            logger.debug(f"Error parsing JavaScript file {file_path}: {e}")

        return list(set(dependencies))

    def _get_config_dependencies(self, file_path: str) -> List[str]:
        """Extract configuration file dependencies."""
        dependencies = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Look for file references
            if file_path.endswith('.json'):
                # JSON files might reference other files
                file_refs = re.findall(r'"([^"]*\.(?:yml|yaml|json|txt))"', content)
                dependencies.extend(file_refs)
            elif file_path.endswith(('.yml', '.yaml')):
                # YAML files might reference other files
                file_refs = re.findall(r'[ ]*([^:\n]+\.(?:yml|yaml|json|txt))', content)
                dependencies.extend(file_refs)

        except Exception as e:
            logger.debug(f"Error parsing config file {file_path}: {e}")

        return list(set(dependencies))

    def _analyze_file_dependencies(self, file_path: str) -> List[str]:
        """Analyze dependencies for a file (alias for _get_file_dependencies)."""
        return self._get_file_dependencies(file_path)

    def _generate_analysis_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate insights from analysis."""
        insights = []

        # File type insights
        types = analysis["file_analysis"]["by_type"]
        if "python" in types and types["python"] > 20:
            insights.append(f"Large Python codebase change: {types['python']} Python files modified")

        # Category insights
        categories = analysis["file_analysis"]["by_category"]
        if "agent" in categories and categories["agent"] > 0:
            insights.append(f"Agent system changes detected: {categories['agent']} agent files modified")

        # Risk insights
        risks = analysis["file_analysis"]["by_risk"]
        if risks.get("high", 0) > 0:
            insights.append(f"High-risk changes: {risks['high']} critical files modified")

        # Directory insights
        dirs = analysis["file_analysis"]["by_directory"]
        if len(dirs) > 10:
            insights.append(f"Wide-reaching changes: {len(dirs)} directories affected")

        return insights

    def _get_risk_recommendations(self, overall_risk: str, risk_counts: Dict[str, int]) -> List[str]:
        """Get recommendations based on risk assessment."""
        recommendations = []

        if overall_risk == "high":
            recommendations.extend([
                "Create small, focused commits",
                "Test each batch thoroughly before proceeding",
                "Consider creating a feature branch",
                "Have rollback plan ready"
            ])
        elif overall_risk == "medium":
            recommendations.extend([
                "Group related files together",
                "Run comprehensive tests",
                "Monitor system health after each commit"
            ])
        else:
            recommendations.extend([
                "Can commit in larger batches",
                "Standard validation sufficient"
            ])

        return recommendations

    def _get_recommended_approach(self, risk_assessment: Dict, analysis: Dict) -> str:
        """Get recommended commit approach based on analysis."""
        risk = risk_assessment["overall_risk"]

        if risk == "high":
            return "conservative"
        elif risk == "medium":
            return "balanced"
        else:
            return "aggressive"

    def _determine_batching_strategy(self, risk_assessment: Dict, dep_graph: Dict) -> str:
        """Determine optimal batching strategy."""
        risk = risk_assessment["overall_risk"]

        if risk == "high":
            return "dependency_aware"
        elif risk == "medium":
            return "category_based"
        else:
            return "size_based"

    def _get_safety_measures(self, risk_assessment: Dict) -> List[str]:
        """Get recommended safety measures."""
        risk = risk_assessment["overall_risk"]
        measures = []

        if risk == "high":
            measures.extend([
                "Create backup branch before starting",
                "Test in isolated environment first",
                "Enable automatic rollback",
                "Monitor system health continuously"
            ])
        elif risk == "medium":
            measures.extend([
                "Run pre-commit validation",
                "Test after each batch",
                "Have rollback plan ready"
            ])
        else:
            measures.extend([
                "Standard validation checks",
                "Monitor for unexpected errors"
            ])

        return measures

    def _estimate_commit_duration(self, files: List[str]) -> Dict[str, float]:
        """Estimate commit duration in minutes."""
        # Base time per file type
        time_per_file = {
            "python": 0.5,
            "javascript": 0.3,
            "markdown": 0.1,
            "config": 0.2,
            "unknown": 0.3
        }

        total_time = 0
        for file_path in files:
            file_type = self._get_file_type(file_path)
            total_time += time_per_file.get(file_type, time_per_file["unknown"])

        # Add overhead for validation and testing
        overhead = 5.0  # 5 minutes base overhead

        return {
            "estimated_minutes": total_time + overhead,
            "per_file_average": total_time / len(files) if files else 0,
            "confidence": 0.8  # 80% confidence in estimate
        }

    def _create_conservative_batches(self, files: List[str], dep_graph: Dict) -> List[Dict]:
        """Create conservative batches (small, dependency-aware)."""
        # Sort by risk level and dependencies
        sorted_files = sorted(files, key=lambda f: (
            0 if self._assess_file_risk(f) == "high" else
            1 if self._assess_file_risk(f) == "medium" else 2,
            len(dep_graph["dependencies"].get(f, {}).get("dependencies", []))
        ))

        batches = []
        batch_size = 10  # Small batches for conservative approach

        for i in range(0, len(sorted_files), batch_size):
            batch_files = sorted_files[i:i + batch_size]

            batches.append({
                "files": batch_files,
                "size": len(batch_files),
                "risk_level": self._get_batch_risk(batch_files),
                "description": f"Conservative batch {i//batch_size + 1}",
                "strategy": "conservative"
            })

        return batches

    def _create_balanced_batches(self, files: List[str], dep_graph: Dict) -> List[Dict]:
        """Create balanced batches (category-based)."""
        # Group by category
        categories = defaultdict(list)
        for file_path in files:
            category = self._get_file_category(file_path)
            categories[category].append(file_path)

        batches = []
        batch_size = 25  # Medium batches

        # Create batches per category
        for category, category_files in categories.items():
            for i in range(0, len(category_files), batch_size):
                batch_files = category_files[i:i + batch_size]

                batches.append({
                    "files": batch_files,
                    "size": len(batch_files),
                    "category": category,
                    "risk_level": self._get_batch_risk(batch_files),
                    "description": f"{category.title()} files (batch {len(batches)+1})",
                    "strategy": "balanced"
                })

        return batches

    def _create_aggressive_batches(self, files: List[str], dep_graph: Dict) -> List[Dict]:
        """Create aggressive batches (size-based)."""
        batches = []
        batch_size = 50  # Large batches for low risk

        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]

            batches.append({
                "files": batch_files,
                "size": len(batch_files),
                "risk_level": self._get_batch_risk(batch_files),
                "description": f"Files {i+1}-{min(i+batch_size, len(files))}",
                "strategy": "aggressive"
            })

        return batches

    def _get_batch_risk(self, files: List[str]) -> str:
        """Get risk level for a batch of files."""
        risk_levels = [self._assess_file_risk(f) for f in files]

        if "high" in risk_levels:
            return "high"
        elif risk_levels.count("medium") > len(files) * 0.5:
            return "medium"
        else:
            return "low"

    def _generate_commit_message(self, batch: Dict[str, Any], batch_number: int) -> str:
        """Generate appropriate commit message for a batch."""
        files = batch["files"]
        strategy = batch.get("strategy", "balanced")

        # Get file summary
        file_types = defaultdict(int)
        categories = defaultdict(int)

        for file_path in files:
            file_types[self._get_file_type(file_path)] += 1
            categories[self._get_file_category(file_path)] += 1

        # Create message
        if strategy == "conservative":
            prefix = "UPDATE:"
        elif strategy == "balanced":
            prefix = "ENHANCE:"
        else:
            prefix = "FEAT:"

        # Main description
        if batch.get("category"):
            main_desc = f"{batch['category'].title()} files"
        else:
            main_desc = f"Batch {batch_number} updates"

        # Details
        details = []
        if categories:
            details.append(f"Categories: {', '.join(categories.keys())}")
        if len(files) <= 10:
            details.append(f"Files: {len(files)}")

        # Build message
        message = f"{prefix} {main_desc}"

        if details:
            message += f"\n\n{'. '.join(details)}"

        message += f"\n\nCommit created by Commit Coordinator Agent\nSession: {self.agent_id}"

        return message

    def _identify_dependency_clusters(self, dependencies: Dict) -> List[List[str]]:
        """Identify clusters of dependent files."""
        # Simple implementation - group files with mutual dependencies
        clusters = []
        visited = set()

        for file_path, dep_info in dependencies.items():
            if file_path in visited:
                continue

            cluster = [file_path]
            visited.add(file_path)

            # Find connected files
            to_visit = set(dep_info["dependencies"])
            while to_visit:
                current = to_visit.pop()
                if current in dependencies and current not in visited:
                    cluster.append(current)
                    visited.add(current)
                    to_visit.update(dependencies[current]["dependencies"])

            if len(cluster) > 1:
                clusters.append(cluster)

        return clusters

    def _calculate_max_dependency_chain(self, dependencies: Dict) -> int:
        """Calculate maximum dependency chain length."""
        max_chain = 0

        for file_path in dependencies:
            chain_length = self._calculate_dependency_chain_length(
                file_path, dependencies, set()
            )
            max_chain = max(max_chain, chain_length)

        return max_chain

    def _calculate_dependency_chain_length(
        self, file_path: str, dependencies: Dict, visited: Set[str]
    ) -> int:
        """Calculate dependency chain length for a file."""
        if file_path in visited or file_path not in dependencies:
            return 0

        visited.add(file_path)

        deps = dependencies[file_path]["dependencies"]
        if not deps:
            return 1

        max_child = 0
        for dep in deps:
            child_length = self._calculate_dependency_chain_length(dep, dependencies, visited.copy())
            max_child = max(max_child, child_length)

        return 1 + max_child

    def _update_metrics(self, action: str, success: bool, execution_time: float) -> None:
        """Update performance metrics."""
        self.performance_metrics["total_requests"] += 1

        if success:
            self.performance_metrics["successful_requests"] += 1
        else:
            self.performance_metrics["failed_requests"] += 1

        # Update average execution time
        total_time = self.performance_metrics.get("total_execution_time", 0) + execution_time
        self.performance_metrics["total_execution_time"] = total_time
        self.performance_metrics["average_execution_time"] = total_time / self.performance_metrics["total_requests"]


# Register agent with Meta Agent if available
if meta_agent and __name__ != "__main__":
    try:
        registration_result = meta_agent._register_agent({
            "agent_id": "commit_analyzer",
            "agent_name": "Commit Analyzer Agent",
            "class_name": "CommitAnalyzerAgent",
            "file_path": "agents/commit_analyzer_agent.py",
            "created_by": "claude_code",
            "capabilities": [
                "analyze_changes",
                "assess_risk_level",
                "create_dependency_graph",
                "generate_commit_strategy",
                "create_commit_batches",
                "suggest_commit_messages"
            ],
            "dependencies": [
                "git_utils"
            ],
            "metadata": {
                "max_execution_time": 60,  # 1 minute
                "memory_limit_mb": 50,
                "description": "Analyzes repository changes and creates optimal commit strategies with risk assessment and dependency analysis",
                "version": "1.0.0"
            }
        }, {"agent_id": "meta_agent"})

        if registration_result.get("success"):
            logger.info("Commit Analyzer Agent successfully registered with Meta Agent")
        else:
            logger.warning(f"Failed to register with Meta Agent: {registration_result.get('error', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Error registering with Meta Agent: {str(e)}")


if __name__ == "__main__":
    # Test the agent
    agent = CommitAnalyzerAgent("test_commit_analyzer")

    # Test capabilities
    capabilities = agent._define_capabilities()
    print(f"Commit Analyzer Agent initialized with {len(capabilities)} capabilities")

    # Test basic functionality
    try:
        result = agent._execute_action("assess_risk_level", {"files": ["test.py"]}, {})
        print(f"Risk assessment test: {result['status']}")
    except Exception as e:
        print(f"Test failed: {str(e)}")