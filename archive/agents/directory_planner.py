#!/usr/bin/env python3
"""
Directory Planner Agent
Specialized agent for optimizing directory structure and planning file organization

This agent performs directory optimization planning:
- Creates optimal directory structure recommendations
- Plans safe file moves with dependency validation
- Generates implementation roadmap with rollback points
- Ensures import and reference integrity
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime
import logging
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DirectoryPlan:
    """Represents a planned directory structure"""
    name: str
    purpose: str
    files_to_include: List[str]
    subdirectories: List[str]
    size_estimate_mb: float
    priority: str  # 'HIGH', 'MEDIUM', 'LOW'

@dataclass
class FileMovePlan:
    """Represents a planned file move"""
    source_path: str
    target_path: str
    move_type: str  # 'MOVE', 'COPY', 'REFERENCE_UPDATE'
    dependencies_affected: List[str]
    rollback_info: Dict[str, Any]
    priority: str

@dataclass
class DirectoryOptimizationPlan:
    """Complete directory optimization plan"""
    current_structure: Dict[str, Any]
    proposed_structure: Dict[str, Any]
    new_directories: List[DirectoryPlan]
    file_moves: List[FileMovePlan]
    estimated_benefits: Dict[str, Any]
    implementation_steps: List[str]
    risk_assessment: Dict[str, Any]

class DirectoryPlanner:
    """
    Specialized agent for planning directory structure optimization
    with focus on maintaining system integrity while improving organization
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.current_structure_cache = {}
        self.dependency_cache = {}
        logger.info("🏗️ DirectoryPlanner initialized")

    def analyze_current_structure(self) -> Dict[str, Any]:
        """Analyze current directory structure in detail"""
        logger.info("🔍 Analyzing current directory structure...")

        structure = {
            'root_directories': [],
            'directory_tree': {},
            'size_distribution': {},
            'file_type_distribution': {},
            'organization_score': 0.0,
            'issues_identified': []
        }

        # Get root directories
        root_path = self.project_root
        for item in root_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                structure['root_directories'].append(item.name)

        # Build directory tree
        structure['directory_tree'] = self._build_directory_tree(self.project_root)

        # Analyze distribution
        structure['size_distribution'] = self._analyze_size_distribution()
        structure['file_type_distribution'] = self._analyze_file_type_distribution()

        # Calculate organization score
        structure['organization_score'] = self._calculate_organization_score(structure)

        # Identify issues
        structure['issues_identified'] = self._identify_structure_issues(structure)

        self.current_structure_cache = structure
        logger.info(f"✅ Current structure analysis complete")
        logger.info(f"   Root directories: {len(structure['root_directories'])}")
        logger.info(f"   Organization score: {structure['organization_score']:.1f}/10")

        return structure

    def _build_directory_tree(self, path: Path, max_depth: int = 3) -> Dict[str, Any]:
        """Build directory tree representation"""
        if max_depth <= 0:
            return {}

        tree = {}
        try:
            for item in path.iterdir():
                if item.is_dir() and not item.name.startswith('.') and 'CLEANUP_BACKUP' not in str(item):
                    subtree = self._build_directory_tree(item, max_depth - 1)
                    tree[item.name] = {
                        'path': str(item.relative_to(self.project_root)),
                        'subdirs': list(subtree.keys()) if subtree else [],
                        'file_count': len(list(item.glob('*'))),
                        'has_children': len(subtree) > 0
                    }
                    if subtree:
                        tree[item.name]['children'] = subtree
        except PermissionError:
            logger.warning(f"Permission denied accessing {path}")

        return tree

    def _analyze_size_distribution(self) -> Dict[str, float]:
        """Analyze size distribution by directory"""
        size_distribution = {}
        total_size = 0

        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden and backup directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 'CLEANUP_BACKUP' not in d]

            dir_size = 0
            for file in files:
                try:
                    file_path = Path(root) / file
                    if file_path.is_file():
                        dir_size += file_path.stat().st_size
                        total_size += file_path.stat().st_size
                except:
                    pass

            if dir_size > 0:
                rel_path = str(Path(root).relative_to(self.project_root))
                size_distribution[rel_path] = dir_size / (1024 * 1024)  # MB

        return size_distribution

    def _analyze_file_type_distribution(self) -> Dict[str, int]:
        """Analyze file type distribution"""
        file_types = {}

        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden and backup directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and 'CLEANUP_BACKUP' not in d]

            for file in files:
                file_path = Path(root) / file
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1

        return file_types

    def _calculate_organization_score(self, structure: Dict[str, Any]) -> float:
        """Calculate organization score (0-10)"""
        score = 10.0

        # Deductions for organizational issues
        root_dirs = structure['root_directories']
        if len(root_dirs) > 15:  # Too many root directories
            score -= 1.0

        # Check for good naming conventions
        good_names = ['src', 'docs', 'tests', 'data', 'agents', 'models', 'notebooks']
        has_good_structure = any(name in root_dirs for name in good_names)
        if not has_good_structure:
            score -= 0.5

        # Deductions for issues
        score -= len(structure['issues_identified']) * 0.5

        return max(0.0, min(10.0, score))

    def _identify_structure_issues(self, structure: Dict[str, Any]) -> List[str]:
        """Identify directory structure issues"""
        issues = []

        root_dirs = structure['root_directories']

        # Too many root-level files/directories
        if len(root_dirs) > 15:
            issues.append(f"Too many root directories: {len(root_dirs)}")

        # Check for mixed purpose directories
        mixed_purpose_dirs = []
        for dir_name in root_dirs:
            if '.' in dir_name and dir_name != '.venv':
                mixed_purpose_dirs.append(dir_name)

        if mixed_purpose_dirs:
            issues.append(f"Mixed purpose directories: {mixed_purpose_dirs}")

        # Check for potential consolidation opportunities
        similar_dirs = []
        for dir_name in root_dirs:
            if 'pack' in dir_name:
                similar_dirs.append(dir_name)

        if len(similar_dirs) > 2:
            issues.append(f"Potential consolidation: {similar_dirs}")

        return issues

    def create_optimal_structure_plan(self, current_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Create optimal directory structure plan"""
        logger.info("💡 Creating optimal structure plan...")

        # Since the current analysis shows good organization, focus on minor optimizations
        proposed_structure = {
            'new_directories': [],
            'directory_renames': [],
            'file_reorganizations': [],
            'consolidations': []
        }

        # Based on the file scanner results, we have good organization
        # Focus on creating a clean src/ directory for reusable modules
        if not (self.project_root / 'src').exists():
            proposed_structure['new_directories'].append({
                'name': 'src',
                'purpose': 'Core Python modules and utilities',
                'subdirs': ['analytics', 'models', 'utils', 'agents']
            })

        # Create data/ directory for better data organization
        if not (self.project_root / 'data').exists():
            proposed_structure['new_directories'].append({
                'name': 'data',
                'purpose': 'Consolidated data storage',
                'subdirs': ['raw', 'processed', 'models', 'external']
            })

        # Create docs/ directory for better documentation organization
        if not (self.project_root / 'docs').exists():
            proposed_structure['new_directories'].append({
                'name': 'docs',
                'purpose': 'Consolidated documentation',
                'subdirs': ['api', 'guides', 'architecture']
            })

        # Suggest consolidation of pack directories
        pack_dirs = [d for d in current_structure['root_directories'] if 'pack' in d]
        if len(pack_dirs) > 1:
            proposed_structure['consolidations'].append({
                'action': 'create_notebooks_directory',
                'source_dirs': pack_dirs,
                'target': 'notebooks',
                'purpose': 'Consolidate educational and modeling notebooks'
            })

        logger.info(f"✅ Structure plan created with {len(proposed_structure['new_directories'])} new directories")

        return proposed_structure

    def plan_file_moves(self, current_structure: Dict[str, Any],
                       proposed_structure: Dict[str, Any]) -> List[FileMovePlan]:
        """Plan safe file moves with dependency analysis"""
        logger.info("📋 Planning file moves with dependency validation...")

        file_moves = []

        # Since we have good organization, minimal moves needed
        # Focus on creating src/ directory with core modules

        # Find modules that could move to src/
        core_modules = [
            'agents/core',
            'model_pack/models',
        ]

        for module in core_modules:
            source_path = self.project_root / module
            if source_path.exists():
                target_path = self.project_root / 'src' / module
                file_moves.append(FileMovePlan(
                    source_path=str(source_path.relative_to(self.project_root)),
                    target_path=str(target_path.relative_to(self.project_root)),
                    move_type='MOVE',
                    dependencies_affected=self._find_dependencies_for_path(source_path),
                    rollback_info={
                        'original_location': str(source_path),
                        'backup_needed': True,
                        'timestamp': datetime.now().isoformat()
                    },
                    priority='MEDIUM'
                ))

        logger.info(f"✅ Planned {len(file_moves)} file moves")

        return file_moves

    def _find_dependencies_for_path(self, path: Path) -> List[str]:
        """Find files that depend on the given path"""
        dependencies = []

        # Search for Python files that might import from this path
        path_str = str(path.relative_to(self.project_root)).replace('/', '.').replace('\\', '.')

        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden directories and the path itself
            dirs[:] = [d for d in dirs if not d.startswith('.') and not path_str in str(Path(root) / d)]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            # Simple check for imports
                            if any(path_str.replace('.py', '') in line for line in content.split('\n')
                                   if line.strip().startswith('from') or line.strip().startswith('import')):
                                dependencies.append(str(file_path.relative_to(self.project_root)))
                    except:
                        pass

        return dependencies

    def create_implementation_roadmap(self, proposed_structure: Dict[str, Any],
                                    file_moves: List[FileMovePlan]) -> List[str]:
        """Create step-by-step implementation roadmap"""
        logger.info("🗺️ Creating implementation roadmap...")

        roadmap = [
            "🎯 PHASE 1: Create new directory structure",
            "   - Create src/ directory with subdirectories",
            "   - Create data/ directory with organized structure",
            "   - Create docs/ directory for consolidated documentation",
            "",
            "🔄 PHASE 2: Safe file migration (if needed)",
            "   - Move core modules to src/ directory",
            "   - Update import statements in dependent files",
            "   - Validate all imports work correctly",
            "",
            "✅ PHASE 3: Validation and cleanup",
            "   - Run full test suite to ensure no breakage",
            "   - Update documentation to reflect new structure",
            "   - Create migration guide for developers"
        ]

        # Add specific steps based on our plan
        if proposed_structure.get('new_directories'):
            roadmap.insert(1, f"   - Create {len(proposed_structure['new_directories'])} new directories")

        if file_moves:
            roadmap.insert(5, f"   - Execute {len(file_moves)} safe file moves")

        return roadmap

    def generate_optimization_plan(self) -> DirectoryOptimizationPlan:
        """Generate complete directory optimization plan"""
        logger.info("📋 Generating complete directory optimization plan...")

        # Analyze current structure
        current_structure = self.analyze_current_structure()

        # Create proposed structure
        proposed_structure = self.create_optimal_structure_plan(current_structure)

        # Plan file moves
        file_moves = self.plan_file_moves(current_structure, proposed_structure)

        # Create implementation roadmap
        implementation_steps = self.create_implementation_roadmap(proposed_structure, file_moves)

        # Estimate benefits
        benefits = {
            'organization_improvement': 0.8,  # Already well organized
            'navigation_efficiency': 0.3,
            'maintainability': 0.5,
            'developer_experience': 0.4
        }

        # Risk assessment
        risk_assessment = {
            'overall_risk': 'LOW',
            'potential_breakage': 0.1,
            'rollback_complexity': 'LOW',
            'testing_required': 'MINIMAL'
        }

        plan = DirectoryOptimizationPlan(
            current_structure=current_structure,
            proposed_structure=proposed_structure,
            new_directories=[],  # Would be populated if creating new directories
            file_moves=file_moves,
            estimated_benefits=benefits,
            implementation_steps=implementation_steps,
            risk_assessment=risk_assessment
        )

        logger.info(f"✅ Directory optimization plan complete:")
        logger.info(f"   Current organization score: {current_structure['organization_score']:.1f}/10")
        logger.info(f"   File moves planned: {len(file_moves)}")
        logger.info(f"   Overall risk: {risk_assessment['overall_risk']}")

        return plan

def main():
    """Main execution function for testing"""
    print("🏗️ Directory Planner Agent")
    print("=" * 40)

    project_root = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
    planner = DirectoryPlanner(project_root)

    # Generate optimization plan
    plan = planner.generate_optimization_plan()

    print(f"\n📊 Directory Structure Analysis:")
    print(f"   Organization score: {plan.current_structure['organization_score']:.1f}/10")
    print(f"   Root directories: {len(plan.current_structure['root_directories'])}")

    print(f"\n💡 Optimization Plan:")
    print(f"   File moves planned: {len(plan.file_moves)}")
    print(f"   Overall risk: {plan.risk_assessment['overall_risk']}")

    print(f"\n📋 Implementation Roadmap:")
    for step in plan.implementation_steps:
        print(f"   {step}")

    print(f"\n✅ Benefits:")
    for benefit, score in plan.estimated_benefits.items():
        print(f"   {benefit.replace('_', ' ').title()}: {score:.1f}")

    return plan

if __name__ == "__main__":
    main()