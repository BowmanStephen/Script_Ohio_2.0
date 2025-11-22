#!/usr/bin/env python3.13
"""
Content Analysis Agent - Phase 1 of Project Management Reorganization

This agent analyzes documentation content to identify consolidation opportunities,
redundancies, and relationships between files.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from collections import defaultdict, Counter

@dataclass
class ContentInfo:
    """Information about document content for analysis"""
    path: str
    name: str
    extension: str
    size_bytes: int
    word_count: int
    line_count: int
    topic_areas: List[str]
    key_topics: List[str]
    content_type: str
    creation_date: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    similarity_score: float = 0.0
    redundancy_level: str = "low"  # low, medium, high
    consolidation_potential: str = "low"  # low, medium, high
    recommended_action: str = "keep"
    related_files: List[str] = None

    def __post_init__(self):
        if self.related_files is None:
            self.related_files = []

@dataclass
class ConsolidationOpportunity:
    """Represents a consolidation opportunity between files"""
    files: List[str]
    topic: str
    reason: str
    confidence: float
    suggested_filename: str
    estimated_size_reduction: int  # in bytes

class ContentAnalysisAgent:
    """Analyzes content for consolidation opportunities"""

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.pm_directory = self.project_root / "project_management"
        self.content_files = []
        self.consolidation_opportunities = []

    def load_categorization_report(self) -> Dict:
        """Load the categorization report to get file list"""
        report_path = self.pm_directory / "categorization_report.json"
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️  Categorization report not found. Run categorization_agent.py first.")
            return {}

    def analyze_document_content(self, file_path: Path) -> ContentInfo:
        """Analyze the content of a document"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Basic stats
            word_count = len(content.split())
            line_count = len(content.splitlines())

            # Topic extraction
            topic_areas = self._extract_topic_areas(content)
            key_topics = self._extract_key_topics(content)
            content_type = self._determine_content_type(file_path.name, content)

            # File stats
            stat_info = file_path.stat()

            return ContentInfo(
                path=str(file_path.relative_to(self.project_root)),
                name=file_path.name,
                extension=file_path.suffix,
                size_bytes=stat_info.st_size,
                word_count=word_count,
                line_count=line_count,
                topic_areas=topic_areas,
                key_topics=key_topics,
                content_type=content_type,
                last_modified=datetime.fromtimestamp(stat_info.st_mtime)
            )

        except Exception as e:
            print(f"⚠️  Could not analyze {file_path}: {e}")
            return ContentInfo(
                path=str(file_path.relative_to(self.project_root)),
                name=file_path.name,
                extension=file_path.suffix,
                size_bytes=0,
                word_count=0,
                line_count=0,
                topic_areas=[],
                key_topics=[],
                content_type="error"
            )

    def _extract_topic_areas(self, content: str) -> List[str]:
        """Extract topic areas from content"""
        topic_keywords = {
            "development": ["development", "coding", "programming", "implementation", "code"],
            "planning": ["plan", "roadmap", "strategy", "timeline", "milestone"],
            "documentation": ["documentation", "guide", "manual", "tutorial", "readme"],
            "testing": ["test", "validation", "quality", "assurance", "verification"],
            "agents": ["agent", "orchestrator", "framework", "automation"],
            "models": ["model", "training", "prediction", "machine learning", "ml"],
            "data": ["data", "dataset", "pipeline", "etl", "workflow"],
            "architecture": ["architecture", "design", "structure", "framework"],
            "deployment": ["deployment", "production", "release", "environment"],
            "monitoring": ["monitoring", "performance", "metrics", "kpi"]
        }

        content_lower = content.lower()
        found_topics = []

        for topic, keywords in topic_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                found_topics.append(topic)

        return found_topics

    def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics using simple keyword extraction"""
        # Look for repeated important terms
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        word_freq = Counter(words)

        # Filter out common words
        stop_words = {
            'this', 'that', 'with', 'from', 'they', 'have', 'been', 'their', 'what',
            'when', 'make', 'like', 'just', 'know', 'take', 'into', 'year', 'your',
            'good', 'some', 'could', 'them', 'see', 'other', 'than', 'then', 'now',
            'look', 'only', 'come', 'over', 'think', 'also', 'back', 'after', 'use',
            'two', 'how', 'our', 'work', 'well', 'way', 'even', 'because', 'any',
            'give', 'day', 'most', 'find', 'will', 'would', 'about', 'should'
        }

        # Get most frequent meaningful words
        key_topics = [word for word, count in word_freq.most_common(20)
                     if count > 3 and word not in stop_words and len(word) > 4]

        return key_topics[:10]  # Top 10 topics

    def _determine_content_type(self, filename: str, content: str) -> str:
        """Determine the type of content"""
        filename_lower = filename.lower()
        content_lower = content.lower()

        if 'readme' in filename_lower:
            return "readme"
        elif any(word in filename_lower for word in ['guide', 'tutorial', 'how']):
            return "user_guide"
        elif any(word in filename_lower for word in ['plan', 'roadmap', 'strategy']):
            return "planning"
        elif any(word in filename_lower for word in ['log', 'decision', 'meeting']):
            return "log_record"
        elif any(word in filename_lower for word in ['api', 'reference', 'technical']):
            return "technical_doc"
        elif any(word in content_lower for word in ['## summary', '# summary', 'conclusion']):
            return "summary_report"
        elif any(word in content_lower for word in ['status', 'progress', 'update']):
            return "status_report"
        else:
            return "general_doc"

    def find_content_similarities(self, content_list: List[ContentInfo]) -> List[Tuple[str, str, float]]:
        """Find similarities between content files"""
        similarities = []

        for i, content1 in enumerate(content_list):
            for j, content2 in enumerate(content_list[i+1:], i+1):
                similarity = self._calculate_similarity(content1, content2)
                if similarity > 0.3:  # Threshold for similarity
                    similarities.append((content1.path, content2.path, similarity))

        # Sort by similarity score
        similarities.sort(key=lambda x: x[2], reverse=True)
        return similarities

    def _calculate_similarity(self, content1: ContentInfo, content2: ContentInfo) -> float:
        """Calculate similarity score between two content pieces"""
        # Topic overlap
        topic_overlap = len(set(content1.topic_areas) & set(content2.topic_areas))
        topic_union = len(set(content1.topic_areas) | set(content2.topic_areas))
        topic_similarity = topic_overlap / topic_union if topic_union > 0 else 0

        # Key topic overlap
        key_topic_overlap = len(set(content1.key_topics) & set(content2.key_topics))
        key_topic_union = len(set(content1.key_topics) | set(content2.key_topics))
        key_topic_similarity = key_topic_overlap / key_topic_union if key_topic_union > 0 else 0

        # Content type similarity
        type_similarity = 1.0 if content1.content_type == content2.content_type else 0.3

        # Weighted average
        overall_similarity = (topic_similarity * 0.4 + key_topic_similarity * 0.4 + type_similarity * 0.2)

        return overall_similarity

    def identify_consolidation_opportunities(self, content_list: List[ContentInfo]) -> List[ConsolidationOpportunity]:
        """Identify opportunities to consolidate content"""
        opportunities = []

        # Group by content type
        by_type = defaultdict(list)
        for content in content_list:
            by_type[content.content_type].append(content)

        # Find similar content within each type
        for content_type, contents in by_type.items():
            if len(contents) > 1:
                # Group by topic similarity
                processed = set()
                for i, content1 in enumerate(contents):
                    if content1.path in processed:
                        continue

                    similar_group = [content1]
                    processed.add(content1.path)

                    for j, content2 in enumerate(contents[i+1:], i+1):
                        if content2.path in processed:
                            continue

                        similarity = self._calculate_similarity(content1, content2)
                        if similarity > 0.5:  # High similarity threshold
                            similar_group.append(content2)
                            processed.add(content2.path)

                    if len(similar_group) > 1:
                        # Create consolidation opportunity
                        total_size = sum(c.size_bytes for c in similar_group)
                        avg_size = total_size // len(similar_group)
                        estimated_reduction = total_size - avg_size  # Assume 50% reduction

                        opportunity = ConsolidationOpportunity(
                            files=[c.path for c in similar_group],
                            topic=self._get_common_topic(similar_group),
                            reason=f"High similarity {content_type} documents",
                            confidence=min(0.9, max(similar_group[0].similarity_score, 0.6)),
                            suggested_filename=self._suggest_consolidated_filename(similar_group, content_type),
                            estimated_size_reduction=estimated_reduction
                        )
                        opportunities.append(opportunity)

        # Sort by confidence and size reduction
        opportunities.sort(key=lambda x: (x.confidence, x.estimated_size_reduction), reverse=True)

        return opportunities

    def _get_common_topic(self, contents: List[ContentInfo]) -> str:
        """Get the most common topic among similar contents"""
        all_topics = []
        for content in contents:
            all_topics.extend(content.topic_areas)

        if all_topics:
            topic_counts = Counter(all_topics)
            return topic_counts.most_common(1)[0][0]
        else:
            return "general"

    def _suggest_consolidated_filename(self, contents: List[ContentInfo], content_type: str) -> str:
        """Suggest a filename for consolidated content"""
        topic = self._get_common_topic(contents)

        type_suffixes = {
            "planning": "roadmap_and_planning.md",
            "status_report": "status_reports.md",
            "log_record": "development_logs.md",
            "technical_doc": "technical_documentation.md",
            "user_guide": "user_guides.md",
            "general_doc": "comprehensive_guide.md"
        }

        base_name = type_suffixes.get(content_type, "consolidated_documentation.md")

        if topic != "general":
            base_name = f"{topic}_{base_name}"

        return base_name

    def analyze_content(self) -> Dict:
        """Main content analysis logic"""
        print("📝 Starting content analysis...")

        # Load categorization report
        cat_report = self.load_categorization_report()
        if not cat_report:
            return {}

        # Filter for documentation files
        doc_files = []
        for file_info in cat_report.get("files", []):
            if file_info.get("extension") in ['.md', '.txt']:
                file_path = self.project_root / file_info["path"]
                if file_path.exists():
                    content_info = self.analyze_document_content(file_path)
                    doc_files.append(content_info)

        print(f"📄 Analyzed {len(doc_files)} documentation files")

        self.content_files = doc_files

        # Find similarities
        similarities = self.find_content_similarities(doc_files)
        print(f"🔗 Found {len(similarities)} similarity relationships")

        # Update similarity scores
        for content in doc_files:
            for sim_path, _, score in similarities:
                if content.path == sim_path:
                    content.similarity_score = max(content.similarity_score, score)

        # Identify consolidation opportunities
        opportunities = self.identify_consolidation_opportunities(doc_files)
        print(f"🔄 Found {len(opportunities)} consolidation opportunities")

        self.consolidation_opportunities = opportunities

        return {
            "content_files": [asdict(c) for c in doc_files],
            "similarities": [{"file1": s[0], "file2": s[1], "score": s[2]} for s in similarities],
            "consolidation_opportunities": [asdict(o) for o in opportunities],
            "summary": {
                "total_files": len(doc_files),
                "total_words": sum(c.word_count for c in doc_files),
                "total_size_mb": round(sum(c.size_bytes for c in doc_files) / (1024 * 1024), 2),
                "similarities_found": len(similarities),
                "consolidation_opportunities": len(opportunities),
                "estimated_size_reduction_mb": round(sum(o.estimated_size_reduction for o in opportunities) / (1024 * 1024), 2)
            }
        }

    def save_analysis_report(self, output_path: str = None) -> str:
        """Save content analysis report"""
        if output_path is None:
            output_path = self.pm_directory / "content_analysis_report.json"

        analysis = self.analyze_content()
        analysis["generated_at"] = datetime.now().isoformat()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, default=str)

        print(f"📊 Content analysis report saved to: {output_path}")
        return str(output_path)

    def generate_consolidation_plan(self) -> Dict:
        """Generate a specific consolidation plan"""
        if not self.consolidation_opportunities:
            self.analyze_content()

        # Group opportunities by action type
        high_confidence = [o for o in self.consolidation_opportunities if o.confidence > 0.7]
        medium_confidence = [o for o in self.consolidation_opportunities if 0.5 <= o.confidence <= 0.7]

        plan = {
            "immediate_consolidations": [
                {
                    "files": opp.files,
                    "suggested_name": opp.suggested_filename,
                    "reason": opp.reason,
                    "estimated_reduction_kb": opp.estimated_size_reduction // 1024
                }
                for opp in high_confidence[:5]  # Top 5 high-confidence
            ],
            "future_consolidations": [
                {
                    "files": opp.files,
                    "suggested_name": opp.suggested_filename,
                    "reason": opp.reason,
                    "estimated_reduction_kb": opp.estimated_size_reduction // 1024
                }
                for opp in medium_confidence[:3]  # Top 3 medium-confidence
            ],
            "archive_candidates": [
                f.path for f in self.content_files
                if f.content_type in ["log_record", "status_report"] and f.size_bytes < 5000
            ]
        }

        return plan

def main():
    """Main execution function"""
    print("🚀 Content Analysis Agent - Starting Analysis")
    print("=" * 60)

    agent = ContentAnalysisAgent()

    # Run analysis
    analysis = agent.analyze_content()

    if not analysis:
        print("❌ No categorization report found. Please run categorization_agent.py first.")
        return

    # Save detailed report
    report_path = agent.save_analysis_report()

    # Generate consolidation plan
    consolidation_plan = agent.generate_consolidation_plan()
    plan_path = agent.pm_directory / "consolidation_plan.json"
    with open(plan_path, 'w', encoding='utf-8') as f:
        json.dump(consolidation_plan, f, indent=2, default=str)

    # Print summary
    summary = analysis["summary"]
    print(f"\n📊 CONTENT ANALYSIS SUMMARY")
    print(f"   Documentation files: {summary['total_files']}")
    print(f"   Total words: {summary['total_words']:,}")
    print(f"   Total size: {summary['total_size_mb']} MB")
    print(f"   Similar relationships: {summary['similarities_found']}")
    print(f"   Consolidation opportunities: {summary['consolidation_opportunities']}")
    print(f"   Estimated size reduction: {summary['estimated_size_reduction_mb']} MB")

    print(f"\n🔄 CONSOLIDATION PLAN")
    print(f"   Immediate consolidations: {len(consolidation_plan['immediate_consolidations'])}")
    print(f"   Future consolidations: {len(consolidation_plan['future_consolidations'])}")
    print(f"   Archive candidates: {len(consolidation_plan['archive_candidates'])}")

    print(f"\n📄 Reports saved:")
    print(f"   Detailed analysis: {report_path}")
    print(f"   Consolidation plan: {plan_path}")
    print("✅ Content Analysis Agent - Analysis Complete!")

if __name__ == "__main__":
    main()