#!/usr/bin/env python3
"""
File Scanner Agent
Specialized agent for comprehensive file analysis and organization planning

This agent performs detailed file system analysis to:
- Catalog all project files and categorize by type
- Identify file relationships and dependencies
- Analyze directory structure for optimization opportunities
- Recommend optimal organizational structure
"""

import os
import ast
import json
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import mimetypes

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Represents a file with comprehensive metadata"""
    path: Path
    relative_path: str
    size_bytes: int
    file_type: str
    extension: str
    purpose_category: str
    last_modified: datetime
    imports: List[str]  # For Python files
    is_executable: bool
    dependencies: List[str]

@dataclass
class DirectoryAnalysis:
    """Analysis of a directory structure"""
    path: Path
    relative_path: str
    file_count: int
    total_size_mb: float
    file_types: Dict[str, int]
    purpose_coherence: float  # 0-1, how coherent the directory purpose is
    recommended_action: str

@dataclass
class FileOrganizationReport:
    """Complete file system analysis report"""
    total_files: int
    total_size_mb: float
    files_by_type: Dict[str, List[FileInfo]]
    directories: List[DirectoryAnalysis]
    import_dependencies: Dict[str, List[str]]
    organization_issues: List[str]
    reorganization_recommendations: Dict[str, Any]

class FileScanner:
    """
    Specialized agent for analyzing file organization and recommending
    optimal directory structure for Script Ohio 2.0
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.file_catalog: List[FileInfo] = []
        self.dependency_graph: Dict[str, Set[str]] = {}
        self.scan_cache = {}
        logger.info("🔍 FileScanner initialized")

    def scan_project_files(self, exclude_patterns: List[str] = None) -> List[FileInfo]:
        """Comprehensive scan of all project files"""
        if exclude_patterns is None:
            exclude_patterns = [
                '.git', '__pycache__', '.pytest_cache', 'node_modules',
                '.venv', 'venv', 'CLEANUP_BACKUP', '.DS_Store'
            ]

        logger.info("🔍 Starting comprehensive file scan...")

        file_catalog = []
        total_files = 0
        python_files = 0

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]

            for file in files:
                total_files += 1
                file_path = Path(root) / file

                try:
                    file_info = self._analyze_file(file_path)
                    file_catalog.append(file_info)

                    if file_info.extension == '.py':
                        python_files += 1

                    # Log progress every 100 files
                    if total_files % 100 == 0:
                        logger.info(f"   Scanned {total_files} files...")

                except Exception as e:
                    logger.warning(f"⚠️ Could not analyze {file_path}: {e}")

        self.file_catalog = file_catalog
        logger.info(f"✅ File scan complete:")
        logger.info(f"   Total files: {total_files}")
        logger.info(f"   Python files: {python_files}")
        logger.info(f"   Total size: {sum(f.size_bytes for f in file_catalog) / (1024*1024):.1f} MB")

        return file_catalog

    def _analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze individual file and extract metadata"""
        relative_path = str(file_path.relative_to(self.project_root))
        stat = file_path.stat()

        # Basic file info
        size_bytes = stat.st_size
        extension = file_path.suffix.lower()
        file_type = self._categorize_file_type(extension, file_path.name)
        purpose_category = self._categorize_purpose(relative_path)
        last_modified = datetime.fromtimestamp(stat.st_mtime)
        is_executable = os.access(file_path, os.X_OK)

        # Extract imports for Python files
        imports = []
        if extension == '.py':
            imports = self._extract_python_imports(file_path)

        # Determine dependencies
        dependencies = self._identify_dependencies(file_path, imports)

        return FileInfo(
            path=file_path,
            relative_path=relative_path,
            size_bytes=size_bytes,
            file_type=file_type,
            extension=extension,
            purpose_category=purpose_category,
            last_modified=last_modified,
            imports=imports,
            is_executable=is_executable,
            dependencies=dependencies
        )

    def _categorize_file_type(self, extension: str, filename: str) -> str:
        """Categorize file by type"""
        extension_map = {
            '.py': 'python_source',
            '.ipynb': 'jupyter_notebook',
            '.md': 'documentation',
            '.txt': 'text',
            '.csv': 'data_csv',
            '.json': 'data_json',
            '.pkl': 'pickle_model',
            '.joblib': 'joblib_model',
            '.yaml': 'configuration',
            '.yml': 'configuration',
            '.dockerfile': 'docker_config',
            '.sh': 'shell_script',
            '.html': 'web_content',
            '.css': 'web_style',
            '.js': 'javascript',
        }

        # Special cases
        if 'requirements' in filename.lower():
            return 'requirements'
        elif 'docker' in filename.lower():
            return 'docker_config'
        elif filename in ['LICENSE', 'README', 'CHANGELOG']:
            return 'project_metadata'

        return extension_map.get(extension, 'other')

    def _categorize_purpose(self, relative_path: str) -> str:
        """Categorize file by purpose based on path"""
        path_parts = relative_path.split('/')

        # Core system files
        if 'agents' in path_parts:
            return 'agent_system'
        elif 'tests' in path_parts:
            return 'testing'
        elif path_parts[0] in ['starter_pack', 'model_pack']:
            return 'educational_content'

        # Project management
        elif 'project_management' in path_parts:
            return 'project_management'

        # Configuration and deployment
        elif 'deployment' in path_parts or any(ext in relative_path for ext in ['.dockerfile', 'requirements.txt']):
            return 'deployment_config'

        # Data files
        elif path_parts[0] in ['data', 'model_pack'] and any(ext in relative_path for ext in ['.csv', '.pkl', '.joblib']):
            return 'data_models'

        # Documentation
        elif relative_path.endswith('.md') or 'docs' in path_parts:
            return 'documentation'

        # Root level files
        elif len(path_parts) == 1:
            return 'root_level'

        else:
            return 'general'

    def _extract_python_imports(self, file_path: Path) -> List[str]:
        """Extract imports from Python file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content)
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for alias in node.names:
                        if alias.name == '*':
                            imports.append(f"{module}.*")
                        else:
                            imports.append(f"{module}.{alias.name}" if module else alias.name)

            return imports

        except Exception as e:
            logger.debug(f"Could not extract imports from {file_path}: {e}")
            return []

    def _identify_dependencies(self, file_path: Path, imports: List[str]) -> List[str]:
        """Identify file dependencies from imports and other factors"""
        dependencies = []

        # Python imports
        if imports:
            dependencies.extend([imp for imp in imports if not imp.startswith(('os', 'sys', 'json', 'datetime', 'pathlib'))])

        # Data file dependencies
        if file_path.suffix in ['.py', '.ipynb']:
            # Look for common data file patterns in content
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()

                data_patterns = ['.csv', '.pkl', '.joblib', '.json', '.parquet']
                for pattern in data_patterns:
                    if pattern in content:
                        dependencies.append(f"data_file_{pattern.replace('.', '')}")
            except:
                pass

        return list(set(dependencies))

    def analyze_directory_structure(self) -> List[DirectoryAnalysis]:
        """Analyze directory structure for organization issues"""
        logger.info("📂 Analyzing directory structure...")

        directories = {}
        root_path = str(self.project_root)

        # Group files by directory
        for file_info in self.file_catalog:
            dir_path = str(file_info.path.parent)
            if dir_path not in directories:
                directories[dir_path] = []

            directories[dir_path].append(file_info)

        # Analyze each directory
        directory_analyses = []
        for dir_path, files in directories.items():
            analysis = self._analyze_directory(dir_path, files)
            directory_analyses.append(analysis)

        # Sort by size (largest first)
        directory_analyses.sort(key=lambda x: x.total_size_mb, reverse=True)

        logger.info(f"✅ Directory analysis complete for {len(directory_analyses)} directories")

        return directory_analyses

    def _analyze_directory(self, dir_path: str, files: List[FileInfo]) -> DirectoryAnalysis:
        """Analyze a single directory"""
        path_obj = Path(dir_path)
        relative_path = str(path_obj.relative_to(self.project_root))

        # Basic metrics
        file_count = len(files)
        total_size_mb = sum(f.size_bytes for f in files) / (1024 * 1024)

        # File type distribution
        file_types = {}
        for file_info in files:
            file_types[file_info.file_type] = file_types.get(file_info.file_type, 0) + 1

        # Calculate purpose coherence
        purpose_categories = [f.purpose_category for f in files]
        unique_purposes = len(set(purpose_categories))
        coherence = 1.0 - (unique_purposes - 1) / max(len(purpose_categories), 1)
        coherence = max(0.0, min(1.0, coherence))

        # Recommend action
        recommended_action = self._recommend_directory_action(relative_path, file_count, total_size_mb, coherence, file_types)

        return DirectoryAnalysis(
            path=path_obj,
            relative_path=relative_path,
            file_count=file_count,
            total_size_mb=total_size_mb,
            file_types=file_types,
            purpose_coherence=coherence,
            recommended_action=recommended_action
        )

    def _recommend_directory_action(self, relative_path: str, file_count: int,
                                  total_size_mb: float, coherence: float,
                                  file_types: Dict[str, int]) -> str:
        """Recommend action for directory organization"""
        # Skip certain critical directories
        if relative_path in ['.', 'agents', 'tests']:
            return 'KEEP_AS_IS'

        # Large directories with low coherence
        if total_size_mb > 50 and coherence < 0.5:
            return 'SPLIT_BY_PURPOSE'

        # Directories with mixed file types
        if len(file_types) > 4 and coherence < 0.7:
            return 'REORGANIZE_BY_TYPE'

        # Small but incoherent directories
        if file_count < 10 and coherence < 0.6:
            return 'MERGE_WITH_SIMILAR'

        # Well-organized directories
        if coherence > 0.8:
            return 'KEEP_AS_IS'

        # Default recommendation
        return 'REVIEW_MANUALLY'

    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """Analyze file dependencies"""
        logger.info("🔗 Analyzing file dependencies...")

        dependency_graph = {}
        for file_info in self.file_catalog:
            if file_info.dependencies:
                dependency_graph[file_info.relative_path] = file_info.dependencies

        self.dependency_graph = dependency_graph
        logger.info(f"✅ Dependency analysis complete for {len(dependency_graph)} files with dependencies")

        return dependency_graph

    def generate_organization_recommendations(self) -> Dict[str, Any]:
        """Generate comprehensive reorganization recommendations"""
        logger.info("💡 Generating organization recommendations...")

        directory_analyses = self.analyze_directory_structure()

        recommendations = {
            'high_priority_issues': [],
            'directory_reorganization': {},
            'file_moves': [],
            'new_directories': [],
            'consolidation_opportunities': [],
            'estimated_impact': {}
        }

        # Analyze each directory for issues
        for analysis in directory_analyses:
            if analysis.recommended_action != 'KEEP_AS_IS':
                issue = {
                    'directory': analysis.relative_path,
                    'issue_type': analysis.recommended_action,
                    'file_count': analysis.file_count,
                    'size_mb': analysis.total_size_mb,
                    'coherence': analysis.purpose_coherence,
                    'file_types': analysis.file_types
                }

                if analysis.recommended_action in ['SPLIT_BY_PURPOSE', 'REORGANIZE_BY_TYPE']:
                    recommendations['high_priority_issues'].append(issue)
                    recommendations['directory_reorganization'][analysis.relative_path] = {
                        'action': analysis.recommended_action,
                        'files': analysis.file_count,
                        'size_mb': analysis.total_size_mb
                    }

        # Identify consolidation opportunities
        purpose_groups = {}
        for file_info in self.file_catalog:
            if file_info.purpose_category not in purpose_groups:
                purpose_groups[file_info.purpose_category] = []
            purpose_groups[file_info.purpose_category].append(file_info)

        for purpose, files in purpose_groups.items():
            if len(files) > 10:  # Large groups that could be consolidated
                recommendations['consolidation_opportunities'].append({
                    'purpose': purpose,
                    'file_count': len(files),
                    'total_size_mb': sum(f.size_bytes for f in files) / (1024 * 1024),
                    'current_directories': list(set(str(f.path.parent) for f in files))
                })

        # Estimate impact
        recommendations['estimated_impact'] = {
            'files_affected': sum(issue['file_count'] for issue in recommendations['high_priority_issues']),
            'size_reorganized_mb': sum(issue['size_mb'] for issue in recommendations['high_priority_issues']),
            'new_directories_needed': len(recommendations['consolidation_opportunities'])
        }

        logger.info("✅ Organization recommendations generated")
        return recommendations

    def generate_complete_report(self) -> FileOrganizationReport:
        """Generate complete file organization analysis report"""
        logger.info("📋 Generating complete file organization report...")

        # Scan all files
        files = self.scan_project_files()

        # Analyze directories
        directories = self.analyze_directory_structure()

        # Analyze dependencies
        dependencies = self.analyze_dependencies()

        # Generate recommendations
        recommendations = self.generate_organization_recommendations()

        # Identify organization issues
        issues = []
        for analysis in directories:
            if analysis.recommended_action != 'KEEP_AS_IS':
                issues.append(f"{analysis.relative_path}: {analysis.recommended_action}")

        # Create report
        report = FileOrganizationReport(
            total_files=len(files),
            total_size_mb=sum(f.size_bytes for f in files) / (1024 * 1024),
            files_by_type=self._group_files_by_type(files),
            directories=directories,
            import_dependencies=dependencies,
            organization_issues=issues,
            reorganization_recommendations=recommendations
        )

        logger.info(f"✅ File organization report complete:")
        logger.info(f"   Total files: {report.total_files}")
        logger.info(f"   Total size: {report.total_size_mb:.1f} MB")
        logger.info(f"   Organization issues: {len(issues)}")
        logger.info(f"   High priority reorganizations: {len(recommendations['high_priority_issues'])}")

        return report

    def _group_files_by_type(self, files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Group files by type"""
        by_type = {}
        for file_info in files:
            if file_info.file_type not in by_type:
                by_type[file_info.file_type] = []
            by_type[file_info.file_type].append(file_info)
        return by_type

def main():
    """Main execution function for testing"""
    print("🔍 File Scanner Agent")
    print("=" * 35)

    project_root = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
    scanner = FileScanner(project_root)

    # Generate complete report
    report = scanner.generate_complete_report()

    print(f"\n📊 File Organization Analysis:")
    print(f"   Total files: {report.total_files}")
    print(f"   Total size: {report.total_size_mb:.1f} MB")

    print(f"\n📁 File Types:")
    for file_type, files in sorted(report.files_by_type.items(), key=lambda x: len(x[1]), reverse=True):
        size_mb = sum(f.size_bytes for f in files) / (1024 * 1024)
        print(f"   {file_type}: {len(files)} files ({size_mb:.1f} MB)")

    print(f"\n🔍 Organization Issues ({len(report.organization_issues)}):")
    for issue in report.organization_issues[:10]:  # Show first 10
        print(f"   - {issue}")

    print(f"\n💡 High Priority Reorganizations ({len(report.reorganization_recommendations['high_priority_issues'])}):")
    for issue in report.reorganization_recommendations['high_priority_issues']:
        print(f"   - {issue['directory']}: {issue['issue_type']} ({issue['file_count']} files)")

    return report

if __name__ == "__main__":
    main()