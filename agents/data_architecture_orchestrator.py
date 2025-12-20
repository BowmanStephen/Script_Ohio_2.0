#!/usr/bin/env python3
"""
Data Architecture Orchestrator
Master coordination agent for data analysis and reorganization

Coordinates specialized agents to:
1. Inventory all data files and their relationships
2. Map data lineage and dependencies
3. Assess quality and identify gaps
4. Design and implement improved organization
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the agent framework
from agents.core.agent_framework import AgentCapability, BaseAgent, PermissionLevel


@dataclass
class AnalysisTask:
    """Represents a data analysis task to be coordinated"""

    task_id: str
    agent_type: str  # inventory, lineage, quality, design
    description: str
    parameters: Dict[str, Any]
    dependencies: List[str] = None
    status: str = "pending"  # pending, in_progress, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DataArchitectureOrchestrator(BaseAgent):
    """
    Master coordinator for data architecture analysis and reorganization.

    Manages the workflow of specialized agents to analyze current state,
    design improvements, and implement changes safely.
    """

    def __init__(self):
        super().__init__(
            agent_id="data_architecture_orchestrator",
            name="Data Architecture Orchestrator",
            permission_level=PermissionLevel.READ_EXECUTE_WRITE,
        )

        self.root_path = Path(".")
        self.tasks: Dict[str, AnalysisTask] = {}
        self.analysis_results: Dict[str, Any] = {}
        self.phases = {
            "discovery": ["inventory", "lineage", "quality"],
            "design": ["architecture_design"],
            "implementation": ["migration"],
            "verification": ["validation"],
        }

    def _define_capabilities(self) -> List[AgentCapability]:
        """Define orchestrator capabilities"""
        return [
            AgentCapability(
                name="coordinate_analysis",
                description="Coordinate data analysis across specialized agents",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["agent_framework"],
                data_access=["starter_pack", "model_pack", "data", "predictions"],
                execution_time_estimate=300,
            ),
            AgentCapability(
                name="map_data_lineage",
                description="Create comprehensive data lineage maps",
                permission_required=PermissionLevel.READ_ONLY,
                tools_required=["inventory_analysis"],
                data_access=["scripts", "src", "agents"],
                execution_time_estimate=600,
            ),
            AgentCapability(
                name="design_organization",
                description="Design improved data organization structure",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["filesystem", "architecture_design"],
                data_access=["starter_pack", "model_pack", "data", "predictions"],
                execution_time_estimate=900,
            ),
            AgentCapability(
                name="coordinate_migration",
                description="Safely coordinate data migration with validation",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["filesystem", "validation", "backup"],
                data_access=["starter_pack", "model_pack", "data", "predictions"],
                execution_time_estimate=1800,
            ),
            AgentCapability(
                name="generate_documentation",
                description="Create comprehensive documentation and reports",
                permission_required=PermissionLevel.READ_EXECUTE_WRITE,
                tools_required=["documentation", "reporting"],
                data_access=["docs", "reports"],
                execution_time_estimate=600,
            ),
        ]

    def _execute_action(
        self, action: str, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Execute orchestrator actions"""
        try:
            if action == "coordinate_analysis":
                return self._coordinate_full_analysis(parameters, user_context)
            elif action == "get_analysis_status":
                return self._get_analysis_status(parameters, user_context)
            elif action == "generate_report":
                return self._generate_comprehensive_report(parameters, user_context)
            else:
                return {"status": "error", "message": f"Unknown action: {action}"}
        except Exception as e:
            return {"status": "error", "message": f"Execution failed: {str(e)}"}

    def _coordinate_full_analysis(self, parameters: Dict, user_context: Dict) -> Dict:
        """Coordinate full data architecture analysis"""
        print("🏗️  Starting Data Architecture Analysis...")

        # Initialize phase 1: Discovery
        discovery_tasks = self._create_discovery_tasks()

        # Execute discovery phase
        discovery_results = self._execute_phase_tasks("discovery", discovery_tasks)

        # Store results for next phases
        self.analysis_results.update(discovery_results)

        return {
            "status": "success",
            "phase": "discovery_complete",
            "results": discovery_results,
            "summary": {
                "total_tasks": len(discovery_tasks),
                "completed_tasks": len(
                    [
                        r
                        for r in discovery_results.values()
                        if r.get("status") == "success"
                    ]
                ),
                "next_phase": "design_ready",
            },
        }

    def _create_discovery_tasks(self) -> List[AnalysisTask]:
        """Create discovery phase tasks"""
        return [
            AnalysisTask(
                task_id="inventory_001",
                agent_type="inventory",
                description="Catalog all CSV files with metadata",
                parameters={
                    "target_directories": [
                        "starter_pack",
                        "model_pack",
                        "data",
                        "predictions",
                    ],
                    "file_types": [".csv", ".json", ".pkl", ".joblib"],
                    "include_metadata": True,
                },
            ),
            AnalysisTask(
                task_id="lineage_001",
                agent_type="lineage",
                description="Map data dependencies and flows",
                parameters={
                    "scan_scripts": True,
                    "identify_sources": True,
                    "trace_transformations": True,
                },
            ),
            AnalysisTask(
                task_id="quality_001",
                agent_type="quality",
                description="Assess data quality and completeness",
                parameters={
                    "validate_schemas": True,
                    "check_coverage": True,
                    "identify_gaps": True,
                },
            ),
        ]

    def _execute_phase_tasks(
        self, phase: str, tasks: List[AnalysisTask]
    ) -> Dict[str, Any]:
        """Execute all tasks for a phase and return results"""
        phase_results = {}

        for task in tasks:
            print(f"🔍 Executing task: {task.description}")

            try:
                # Store task
                self.tasks[task.task_id] = task
                task.status = "in_progress"

                # Execute based on agent type
                if task.agent_type == "inventory":
                    result = self._execute_inventory_task(task)
                elif task.agent_type == "lineage":
                    result = self._execute_lineage_task(task)
                elif task.agent_type == "quality":
                    result = self._execute_quality_task(task)
                else:
                    result = {
                        "status": "error",
                        "message": f"Unknown agent type: {task.agent_type}",
                    }

                task.status = (
                    "completed" if result.get("status") == "success" else "failed"
                )
                task.result = result

                phase_results[task.task_id] = result

                print(f"✅ Task {task.task_id}: {task.status}")

            except Exception as e:
                task.status = "failed"
                task.error = str(e)
                phase_results[task.task_id] = {"status": "error", "message": str(e)}
                print(f"❌ Task {task.task_id} failed: {str(e)}")

        return phase_results

    def _execute_inventory_task(self, task: AnalysisTask) -> Dict[str, Any]:
        """Execute data inventory analysis"""
        try:
            # This would delegate to the Data Inventory Agent
            # For now, implementing basic inventory logic
            target_dirs = task.parameters.get("target_directories", [])
            file_info = {}
            total_files = 0
            total_size = 0

            for directory in target_dirs:
                dir_path = self.root_path / directory
                if dir_path.exists():
                    for file_path in dir_path.rglob("*"):
                        if file_path.is_file() and file_path.suffix.lower() in [
                            ".csv",
                            ".json",
                            ".pkl",
                            ".joblib",
                        ]:
                            try:
                                stat = file_path.stat()
                                file_info[
                                    str(file_path.relative_to(self.root_path))
                                ] = {
                                    "size_bytes": stat.st_size,
                                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                                    "modified": datetime.fromtimestamp(
                                        stat.st_mtime
                                    ).isoformat(),
                                    "extension": file_path.suffix.lower(),
                                }
                                total_files += 1
                                total_size += stat.st_size
                            except OSError:
                                continue

            return {
                "status": "success",
                "data": {
                    "total_files": total_files,
                    "total_size_mb": round(total_size / (1024 * 1024), 2),
                    "files_by_extension": self._count_by_extension(file_info),
                    "largest_files": self._get_largest_files(file_info, 10),
                    "file_details": file_info,
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Inventory analysis failed: {str(e)}",
            }

    def _execute_lineage_task(self, task: AnalysisTask) -> Dict[str, Any]:
        """Execute data lineage analysis"""
        try:
            # This would delegate to the Lineage Analysis Agent
            # For now, implementing basic lineage detection

            # Look for script files that reference data directories
            script_patterns = []
            data_dependencies = {}

            # Scan Python scripts for data references
            for script_file in self.root_path.rglob("*.py"):
                if script_file.is_file():
                    try:
                        content = script_file.read_text(
                            encoding="utf-8", errors="ignore"
                        )
                        script_path = str(script_file.relative_to(self.root_path))

                        # Find data references
                        data_refs = []
                        for data_dir in [
                            "starter_pack",
                            "model_pack",
                            "data",
                            "predictions",
                        ]:
                            if data_dir in content:
                                data_refs.append(data_dir)

                        if data_refs:
                            data_dependencies[script_path] = {
                                "data_directories": data_refs,
                                "cfbd_references": "cfbd" in content,
                                "model_references": any(
                                    x in content for x in ["model", "predict", "train"]
                                ),
                            }

                    except Exception:
                        continue

            return {
                "status": "success",
                "data": {
                    "data_dependencies": data_dependencies,
                    "data_flow_estimates": self._estimate_data_flow(data_dependencies),
                    "master_sources": self._identify_master_sources(data_dependencies),
                },
            }

        except Exception as e:
            return {"status": "error", "message": f"Lineage analysis failed: {str(e)}"}

    def _execute_quality_task(self, task: AnalysisTask) -> Dict[str, Any]:
        """Execute data quality assessment"""
        try:
            # This would delegate to the Quality Assessment Agent
            # For now, implementing basic quality checks

            quality_issues = []
            completeness_scores = {}

            # Check master training data
            master_data_path = (
                self.root_path / "model_pack" / "updated_training_data.csv"
            )
            if master_data_path.exists():
                try:
                    import pandas as pd

                    df = pd.read_csv(master_data_path)
                    completeness_scores["master_training_data"] = {
                        "rows": len(df),
                        "columns": len(df.columns),
                        "null_percentage": round(
                            df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100,
                            2,
                        ),
                        "data_types": df.dtypes.value_counts().to_dict(),
                    }
                except Exception as e:
                    quality_issues.append(f"Master training data read error: {str(e)}")
            else:
                quality_issues.append("Master training data file missing")

            # Check for common data quality issues
            for directory in ["data", "starter_pack", "predictions"]:
                dir_path = self.root_path / directory
                if dir_path.exists():
                    # Look for empty files
                    for file_path in dir_path.rglob("*.csv"):
                        if file_path.is_file():
                            try:
                                if file_path.stat().st_size == 0:
                                    quality_issues.append(
                                        f"Empty file: {file_path.relative_to(self.root_path)}"
                                    )
                            except OSError:
                                continue

            return {
                "status": "success",
                "data": {
                    "quality_issues": quality_issues,
                    "completeness_scores": completeness_scores,
                    "quality_score": max(
                        0, 100 - len(quality_issues) * 5
                    ),  # Simple scoring
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Quality assessment failed: {str(e)}",
            }

    def _count_by_extension(self, file_info: Dict) -> Dict[str, int]:
        """Count files by extension"""
        counts = {}
        for file_data in file_info.values():
            ext = file_data["extension"]
            counts[ext] = counts.get(ext, 0) + 1
        return counts

    def _get_largest_files(self, file_info: Dict, limit: int) -> List[Dict]:
        """Get largest files by size"""
        files = [{"path": path, **info} for path, info in file_info.items()]
        files.sort(key=lambda x: x["size_bytes"], reverse=True)
        return files[:limit]

    def _estimate_data_flow(self, dependencies: Dict) -> List[Dict]:
        """Estimate data flow from dependencies"""
        flows = []

        # Look for common patterns
        for script_path, info in dependencies.items():
            if "cfbd" in script_path.lower() or info.get("cfbd_references"):
                flows.append(
                    {
                        "source": "CFBD_API",
                        "destination": script_path,
                        "type": "data_ingestion",
                    }
                )

            if info.get("model_references"):
                flows.append(
                    {
                        "source": "model_pack",
                        "destination": script_path,
                        "type": "model_training",
                    }
                )

        return flows

    def _identify_master_sources(self, dependencies: Dict) -> Dict[str, str]:
        """Identify master data sources"""
        sources = {
            "starter_pack": "Historical archive and educational datasets",
            "model_pack/updated_training_data.csv": "Canonical training dataset for ML models",
            "cfbd_api": "External API for current season data",
        }

        return sources

    def _get_analysis_status(self, parameters: Dict, user_context: Dict) -> Dict:
        """Get current analysis status"""
        return {
            "status": "success",
            "total_tasks": len(self.tasks),
            "completed_tasks": len(
                [t for t in self.tasks.values() if t.status == "completed"]
            ),
            "failed_tasks": len(
                [t for t in self.tasks.values() if t.status == "failed"]
            ),
            "in_progress_tasks": len(
                [t for t in self.tasks.values() if t.status == "in_progress"]
            ),
            "tasks": {
                task_id: {"status": task.status, "description": task.description}
                for task_id, task in self.tasks.items()
            },
        }

    def _generate_comprehensive_report(
        self, parameters: Dict, user_context: Dict
    ) -> Dict:
        """Generate comprehensive analysis report"""
        report = {
            "analysis_summary": {
                "timestamp": datetime.now().isoformat(),
                "total_files_analyzed": 0,
                "total_size_mb": 0,
                "quality_score": 0,
                "issues_found": [],
            },
            "detailed_findings": {},
            "recommendations": [],
        }

        # Aggregate results from all tasks
        for task_id, task in self.tasks.items():
            if task.result and task.result.get("status") == "success":
                task_data = task.result.get("data", {})
                report["detailed_findings"][task_id] = task_data

                # Update summary
                if task.agent_type == "inventory":
                    report["analysis_summary"]["total_files_analyzed"] = task_data.get(
                        "total_files", 0
                    )
                    report["analysis_summary"]["total_size_mb"] = task_data.get(
                        "total_size_mb", 0
                    )
                elif task.agent_type == "quality":
                    report["analysis_summary"]["quality_score"] = task_data.get(
                        "quality_score", 0
                    )
                    report["analysis_summary"]["issues_found"] = task_data.get(
                        "quality_issues", []
                    )

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(report)

        return {"status": "success", "report": report}

    def _generate_recommendations(self, report: Dict) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []

        quality_score = report["analysis_summary"]["quality_score"]
        total_files = report["analysis_summary"]["total_files_analyzed"]
        issues_count = len(report["analysis_summary"]["issues_found"])

        if quality_score < 80:
            recommendations.append("Address data quality issues to improve reliability")

        if total_files > 500:
            recommendations.append(
                "Consider consolidating and archiving old files to reduce complexity"
            )

        if issues_count > 10:
            recommendations.append(
                "Implement automated data validation to prevent quality issues"
            )

        recommendations.extend(
            [
                "Create clear documentation of data sources and lineage",
                "Establish consistent naming conventions across all directories",
                "Implement automated backup and versioning for critical datasets",
            ]
        )

        return recommendations


# Create the orchestrator instance
data_architecture_orchestrator = DataArchitectureOrchestrator()

if __name__ == "__main__":
    # Test the orchestrator
    print("🏗️  Data Architecture Orchestrator initialized")

    # Run full analysis
    result = data_architecture_orchestrator._execute_action(
        "coordinate_analysis",
        {"target_directories": ["starter_pack", "model_pack", "data", "predictions"]},
        {"user_id": "stephen_bowman"},
    )

    print(f"\n📊 Analysis Results:")

    # Helper function to make JSON serializable
    def make_serializable(obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif hasattr(obj, "tolist"):
            return obj.tolist()
        elif hasattr(obj, "item"):
            return obj.item()
        elif isinstance(obj, dict):
            return {str(k): make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        else:
            return str(obj)

    try:
        serializable_result = make_serializable(result)
        print(json.dumps(serializable_result, indent=2))
    except Exception as e:
        print(f"JSON serialization error: {e}")
        print("Raw result:")
        print(str(result)[:1000] + "..." if len(str(result)) > 1000 else str(result))
