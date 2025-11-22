#!/usr/bin/env python3
"""
Documentation Analyzer Agent
Specialized agent for analyzing and organizing CLAUDE.md files across Script Ohio 2.0

This agent performs comprehensive analysis of the 16 CLAUDE.md files to:
- Identify content overlap and redundancies
- Categorize documentation by purpose and scope
- Recommend optimal hierarchical structure
- Flag outdated or conflicting information
"""

import os
import re
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ClaudeMdFile:
    """Represents a CLAUDE.md file with metadata"""
    path: Path
    relative_path: str
    size_bytes: int
    line_count: int
    content_hash: str
    last_modified: datetime
    content_sections: List[str]
    key_topics: List[str]
    purpose_score: float  # 0-1, how essential this file is

@dataclass
class ContentOverlap:
    """Represents overlapping content between files"""
    file1_path: str
    file2_path: str
    overlap_percentage: float
    common_sections: List[str]
    recommendation: str

@dataclass
class DocumentationAnalysis:
    """Complete analysis results for documentation cleanup"""
    total_files: int
    files_by_purpose: Dict[str, List[ClaudeMdFile]]
    content_overlaps: List[ContentOverlap]
    hierarchical_recommendation: Dict[str, Any]
    files_to_archive: List[str]
    files_to_keep: List[str]
    files_to_merge: List[Tuple[str, str]]
    estimated_complexity_reduction: float

class DocumentationAnalyzer:
    """
    Specialized agent for analyzing CLAUDE.md file organization and recommending
    optimal hierarchical structure for Script Ohio 2.0 documentation
    """

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.claude_files: List[ClaudeMdFile] = []
        self.analysis_cache = {}
        logger.info("🔍 DocumentationAnalyzer initialized")

    def discover_claude_files(self) -> List[ClaudeMdFile]:
        """Discover all CLAUDE.md files in the project"""
        logger.info("🔍 Discovering all CLAUDE.md files...")

        claude_files = []
        total_files = 0

        for root, dirs, files in os.walk(self.project_root):
            # Skip hidden directories and cleanup backup
            dirs[:] = [d for d in dirs if not d.startswith('.') and 'CLEANUP_BACKUP' not in d]

            for file in files:
                if file == 'CLAUDE.md':
                    total_files += 1
                    file_path = Path(root) / file

                    try:
                        claude_file = self._analyze_claude_file(file_path)
                        claude_files.append(claude_file)

                        logger.info(f"📄 Found: {claude_file.relative_path} "
                                  f"({claude_file.line_count} lines, "
                                  f"{claude_file.size_bytes:,} bytes)")

                    except Exception as e:
                        logger.error(f"❌ Error analyzing {file_path}: {e}")

        self.claude_files = claude_files
        logger.info(f"✅ Discovered {len(claude_files)} CLAUDE.md files")

        return claude_files

    def _analyze_claude_file(self, file_path: Path) -> ClaudeMdFile:
        """Analyze individual CLAUDE.md file"""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Calculate file metrics
        size_bytes = len(content.encode('utf-8'))
        lines = content.split('\n')
        line_count = len(lines)
        content_hash = hashlib.md5(content.encode()).hexdigest()
        last_modified = datetime.fromtimestamp(file_path.stat().st_mtime)

        # Extract sections (headers)
        sections = re.findall(r'^#{1,6}\s+(.+)$', content, re.MULTILINE)

        # Extract key topics (identify common themes)
        key_topics = self._extract_key_topics(content)

        # Score importance based on content depth and specificity
        purpose_score = self._calculate_purpose_score(file_path, content, sections)

        relative_path = str(file_path.relative_to(self.project_root))

        return ClaudeMdFile(
            path=file_path,
            relative_path=relative_path,
            size_bytes=size_bytes,
            line_count=line_count,
            content_hash=content_hash,
            last_modified=last_modified,
            content_sections=sections,
            key_topics=key_topics,
            purpose_score=purpose_score
        )

    def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics from content"""
        topics = []

        # Common documentation themes for this project
        topic_patterns = [
            r'agent.*system',
            r'machine learning',
            r'data.*analytic',
            r'college.*football',
            r'jupyter.*notebook',
            r'model.*training',
            r'python',
            r'documentation',
            r'project.*management',
            r'quality.*assurance',
            r'test.*suite',
            r'deployment',
            r'docker',
            r'api'
        ]

        for pattern in topic_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                topics.append(pattern.replace(r'.*', ' ').strip())

        return list(set(topics))

    def _calculate_purpose_score(self, file_path: Path, content: str, sections: List[str]) -> float:
        """Calculate how essential this CLAUDE.md file is"""
        score = 0.0

        # Location-based scoring
        path_parts = file_path.parts

        # Root directory - most important
        if len(path_parts) == 1:
            score += 0.4

        # Core directories - very important
        elif any(part in path_parts for part in ['agents', 'tests', 'model_pack']):
            score += 0.3

        # Project management - important but potentially redundant
        elif 'project_management' in path_parts:
            score += 0.2

        # Other directories - less critical
        else:
            score += 0.1

        # Content depth scoring
        if len(content) > 10000:  # Substantial content
            score += 0.2
        elif len(content) > 5000:
            score += 0.1
        elif len(content) < 1000:  # Minimal content
            score -= 0.1

        # Section diversity scoring
        unique_section_types = set()
        for section in sections:
            if 'command' in section.lower():
                unique_section_types.add('commands')
            elif 'install' in section.lower():
                unique_section_types.add('installation')
            elif 'structure' in section.lower():
                unique_section_types.add('structure')
            elif 'develop' in section.lower():
                unique_section_types.add('development')

        score += min(len(unique_section_types) * 0.1, 0.3)

        # Specificity scoring - look for project-specific content
        if 'Script Ohio' in content:
            score += 0.1
        if 'college football' in content.lower():
            score += 0.1

        return min(max(score, 0.0), 1.0)

    def analyze_content_overlap(self) -> List[ContentOverlap]:
        """Analyze content overlap between CLAUDE.md files"""
        logger.info("🔍 Analyzing content overlap...")

        overlaps = []
        files_analyzed = 0

        for i, file1 in enumerate(self.claude_files):
            for j, file2 in enumerate(self.claude_files[i+1:], i+1):
                files_analyzed += 1

                try:
                    overlap = self._compare_file_contents(file1, file2)
                    if overlap.overlap_percentage > 20:  # Only significant overlaps
                        overlaps.append(overlap)

                except Exception as e:
                    logger.error(f"❌ Error comparing {file1.relative_path} and {file2.relative_path}: {e}")

        logger.info(f"✅ Analyzed {files_analyzed} file comparisons, found {len(overlaps)} significant overlaps")

        return overlaps

    def _compare_file_contents(self, file1: ClaudeMdFile, file2: ClaudeMdFile) -> ContentOverlap:
        """Compare two files for content overlap"""

        # Read content
        with open(file1.path, 'r', encoding='utf-8', errors='ignore') as f:
            content1 = f.read().lower()

        with open(file2.path, 'r', encoding='utf-8', errors='ignore') as f:
            content2 = f.read().lower()

        # Split into sentences for comparison
        sentences1 = set(re.split(r'[.!?]+', content1))
        sentences2 = set(re.split(r'[.!?]+', content2))

        # Calculate overlap
        if len(sentences1) == 0 or len(sentences2) == 0:
            overlap_percentage = 0.0
        else:
            common_sentences = sentences1.intersection(sentences2)
            overlap_percentage = (len(common_sentences) / min(len(sentences1), len(sentences2))) * 100

        # Find common sections
        common_sections = list(set(file1.content_sections).intersection(file2.content_sections))

        # Generate recommendation
        if overlap_percentage > 70:
            recommendation = "CONSIDER_MERGE"
        elif overlap_percentage > 40:
            recommendation = "PARTIAL_CONSOLIDATION"
        elif overlap_percentage > 20:
            recommendation = "CROSS_REFERENCE"
        else:
            recommendation = "KEEP_SEPARATE"

        return ContentOverlap(
            file1_path=file1.relative_path,
            file2_path=file2.relative_path,
            overlap_percentage=overlap_percentage,
            common_sections=common_sections,
            recommendation=recommendation
        )

    def categorize_files_by_purpose(self) -> Dict[str, List[ClaudeMdFile]]:
        """Categorize CLAUDE.md files by their primary purpose"""
        logger.info("📂 Categorizing files by purpose...")

        categories = {
            'project_root': [],
            'core_system': [],
            'project_management': [],
            'development': [],
            'educational': [],
            'testing': [],
            'other': []
        }

        for claude_file in self.claude_files:
            path_parts = claude_file.relative_path.split('/')

            # Categorize based on location and content
            if len(path_parts) == 1:  # Root directory
                categories['project_root'].append(claude_file)
            elif 'agents' in path_parts:
                categories['core_system'].append(claude_file)
            elif 'project_management' in path_parts:
                categories['project_management'].append(claude_file)
            elif 'tests' in path_parts:
                categories['testing'].append(claude_file)
            elif 'starter_pack' in path_parts or 'model_pack' in path_parts:
                categories['educational'].append(claude_file)
            elif any(dev_dir in path_parts for dev_dir in ['src', 'lib', 'utils']):
                categories['development'].append(claude_file)
            else:
                categories['other'].append(claude_file)

        # Log categorization results
        for category, files in categories.items():
            if files:
                logger.info(f"   {category}: {len(files)} files")
                for f in files:
                    logger.info(f"      - {f.relative_path} (purpose_score: {f.purpose_score:.2f})")

        return categories

    def recommend_hierarchical_structure(self, files_by_purpose: Dict[str, List[ClaudeMdFile]],
                                       overlaps: List[ContentOverlap]) -> Dict[str, Any]:
        """Recommend optimal hierarchical documentation structure"""
        logger.info("🏗️ Recommending hierarchical structure...")

        recommendation = {
            'new_structure': {},
            'files_to_archive': [],
            'files_to_merge': [],
            'files_to_keep_primary': [],
            'estimated_files_reduction': 0,
            'complexity_reduction_score': 0.0,
            'implementation_priority': []
        }

        # Analyze each category
        for category, files in files_by_purpose.items():
            if not files:
                continue

            # Sort by purpose score
            files.sort(key=lambda f: f.purpose_score, reverse=True)

            if category == 'project_root':
                # Keep the highest scoring root file as primary
                recommendation['files_to_keep_primary'].append(files[0].relative_path)
                # Archive others
                recommendation['files_to_archive'].extend([f.relative_path for f in files[1:]])

            elif category == 'project_management':
                # Keep the most comprehensive one, archive others
                if len(files) > 1:
                    # Find the most comprehensive (largest, highest scored)
                    primary = max(files, key=lambda f: (f.purpose_score, f.line_count))
                    recommendation['files_to_keep_primary'].append(primary.relative_path)
                    recommendation['files_to_archive'].extend([
                        f.relative_path for f in files if f != primary
                    ])

            elif category == 'core_system':
                # Keep specialized files for core system directories
                recommendation['files_to_keep_primary'].extend([f.relative_path for f in files])

            elif category == 'testing':
                # Keep one comprehensive testing guide
                if len(files) > 1:
                    primary = max(files, key=lambda f: f.purpose_score)
                    recommendation['files_to_keep_primary'].append(primary.relative_path)
                    recommendation['files_to_archive'].extend([
                        f.relative_path for f in files if f != primary
                    ])

            else:
                # For other categories, keep only high-scoring files
                high_score_files = [f for f in files if f.purpose_score > 0.5]
                recommendation['files_to_keep_primary'].extend([f.relative_path for f in high_score_files])
                low_score_files = [f for f in files if f.purpose_score <= 0.5]
                recommendation['files_to_archive'].extend([f.relative_path for f in low_score_files])

        # Add merge recommendations based on overlaps
        for overlap in overlaps:
            if overlap.recommendation in ['CONSIDER_MERGE', 'PARTIAL_CONSOLIDATION']:
                recommendation['files_to_merge'].append((
                    overlap.file1_path,
                    overlap.file2_path,
                    overlap.overlap_percentage
                ))

        # Calculate reduction estimates
        total_files = len(self.claude_files)
        files_to_keep = len(recommendation['files_to_keep_primary'])
        recommendation['estimated_files_reduction'] = total_files - files_to_keep
        recommendation['complexity_reduction_score'] = recommendation['estimated_files_reduction'] / total_files

        # Set implementation priority
        recommendation['implementation_priority'] = [
            {'phase': 'archive_low_value', 'files': recommendation['files_to_archive']},
            {'phase': 'merge_overlaps', 'files': recommendation['files_to_merge']},
            {'phase': 'optimize_structure', 'files': recommendation['files_to_keep_primary']}
        ]

        return recommendation

    def generate_analysis_report(self) -> DocumentationAnalysis:
        """Generate complete documentation analysis"""
        logger.info("📋 Generating complete analysis report...")

        # Discover files
        claude_files = self.discover_claude_files()

        # Analyze overlaps
        overlaps = self.analyze_content_overlap()

        # Categorize by purpose
        files_by_purpose = self.categorize_files_by_purpose()

        # Generate recommendations
        hierarchical_recommendation = self.recommend_hierarchical_structure(files_by_purpose, overlaps)

        # Create analysis object
        analysis = DocumentationAnalysis(
            total_files=len(claude_files),
            files_by_purpose=files_by_purpose,
            content_overlaps=overlaps,
            hierarchical_recommendation=hierarchical_recommendation,
            files_to_archive=hierarchical_recommendation['files_to_archive'],
            files_to_keep=hierarchical_recommendation['files_to_keep_primary'],
            files_to_merge=hierarchical_recommendation['files_to_merge'],
            estimated_complexity_reduction=hierarchical_recommendation['complexity_reduction_score']
        )

        logger.info(f"✅ Analysis complete:")
        logger.info(f"   Total CLAUDE.md files: {analysis.total_files}")
        logger.info(f"   Files to archive: {len(analysis.files_to_archive)}")
        logger.info(f"   Files to keep: {len(analysis.files_to_keep)}")
        logger.info(f"   Potential complexity reduction: {analysis.estimated_complexity_reduction:.1%}")

        return analysis

def main():
    """Main execution function for testing"""
    print("🔍 Documentation Analyzer Agent")
    print("=" * 40)

    project_root = Path("/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0")
    analyzer = DocumentationAnalyzer(project_root)

    # Generate analysis
    analysis = analyzer.generate_analysis_report()

    print(f"\n📊 Analysis Results:")
    print(f"   Total CLAUDE.md files: {analysis.total_files}")
    print(f"   Files recommended for archival: {len(analysis.files_to_archive)}")
    print(f"   Files to keep as primary: {len(analysis.files_to_keep)}")
    print(f"   Estimated complexity reduction: {analysis.estimated_complexity_reduction:.1%}")

    if analysis.files_to_archive:
        print(f"\n📦 Files to Archive:")
        for file in analysis.files_to_archive:
            print(f"   - {file}")

    if analysis.files_to_keep:
        print(f"\n🎯 Primary Files to Keep:")
        for file in analysis.files_to_keep:
            print(f"   - {file}")

    return analysis

if __name__ == "__main__":
    main()