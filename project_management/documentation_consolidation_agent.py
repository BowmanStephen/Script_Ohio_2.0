#!/usr/bin/env python3.13
"""
Documentation Consolidation Agent - Phase 3 of Project Management Reorganization

This agent consolidates redundant documentation files into comprehensive guides
as identified by the content analysis.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

@dataclass
class ConsolidatedDocument:
    """Represents a consolidated document"""
    title: str
    filename: str
    content: str
    source_files: List[str]
    topic: str
    word_count: int
    created_at: datetime

@dataclass
class ConsolidationResult:
    """Result of a consolidation operation"""
    success: bool
    consolidated_file: str
    archived_files: List[str]
    word_count_reduction: int
    size_reduction_bytes: int
    error_message: str = ""

class DocumentationConsolidationAgent:
    """Consolidates documentation files based on content analysis"""

    def __init__(self, project_root: str = "/Users/stephen_bowman/Documents/GitHub/Script_Ohio_2.0"):
        self.project_root = Path(project_root)
        self.pm_directory = self.project_root / "project_management"
        self.comprehensive_guides_dir = self.pm_directory / "docs/comprehensive_guides"
        self.archive_dir = self.pm_directory / "archive"
        self.consolidated_documents = []

    def load_consolidation_plan(self) -> Dict:
        """Load the consolidation plan from content analysis"""
        try:
            plan_path = self.pm_directory / "consolidation_plan.json"
            with open(plan_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Failed to load consolidation plan: {e}")
            return {}

    def read_document_content(self, file_path: str) -> Tuple[str, Dict]:
        """Read and analyze document content"""
        full_path = self.project_root / file_path

        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Extract metadata
            metadata = self._extract_metadata(content, file_path)

            return content, metadata

        except Exception as e:
            print(f"⚠️  Could not read {file_path}: {e}")
            return "", {}

    def _extract_metadata(self, content: str, file_path: str) -> Dict:
        """Extract metadata from document content"""
        metadata = {
            "title": Path(file_path).stem.replace("_", " ").title(),
            "file_path": file_path,
            "creation_date": None,
            "last_modified": None,
            "sections": [],
            "key_topics": []
        }

        # Try to get file stats
        try:
            full_path = self.project_root / file_path
            stat_info = full_path.stat()
            metadata["last_modified"] = datetime.fromtimestamp(stat_info.st_mtime)
        except:
            pass

        # Extract title from content
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            metadata["title"] = title_match.group(1).strip()

        # Extract sections
        section_matches = re.findall(r'^#{1,3}\s+(.+)$', content, re.MULTILINE)
        metadata["sections"] = section_matches

        # Extract date from filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', file_path)
        if date_match:
            try:
                metadata["creation_date"] = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            except:
                pass

        return metadata

    def create_consolidated_document(self, file_group: List[str], suggested_name: str, reason: str) -> ConsolidatedDocument:
        """Create a consolidated document from multiple files"""
        print(f"📝 Consolidating {len(file_group)} files into {suggested_name}")

        all_content = []
        all_metadata = []
        total_word_count = 0

        for file_path in file_group:
            content, metadata = self.read_document_content(file_path)
            if content:
                all_content.append((content, metadata))
                all_metadata.append(metadata)
                total_word_count += len(content.split())

        # Generate consolidated content
        consolidated_content = self._generate_consolidated_content(all_content, all_metadata, suggested_name, reason)

        # Determine title
        title = self._generate_title(suggested_name, all_metadata)

        return ConsolidatedDocument(
            title=title,
            filename=suggested_name,
            content=consolidated_content,
            source_files=file_group,
            topic=self._extract_topic(suggested_name, reason),
            word_count=total_word_count,
            created_at=datetime.now()
        )

    def _generate_consolidated_content(self, content_list: List[Tuple[str, Dict]], metadata_list: List[Dict], suggested_name: str, reason: str) -> str:
        """Generate the consolidated document content"""
        topic = self._extract_topic(suggested_name, reason)

        # Start with header
        content_parts = [
            f"# {self._generate_title(suggested_name, metadata_list)}",
            "",
            f"**Consolidated Document** - Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            f"**Purpose**: This document consolidates {len(content_list)} related {topic.lower()} documents to improve organization and accessibility.",
            f"**Source Files**: {len(content_list)} documents were consolidated into this comprehensive guide.",
            "",
            "---",
            "",
            "## 📋 Table of Contents",
            ""
        ]

        # Add table of contents
        toc_items = []
        for i, (content, metadata) in enumerate(content_list, 1):
            title = metadata.get("title", f"Document {i}")
            clean_title = re.sub(r'[^a-zA-Z0-9\s-]', '', title).strip()
            anchor = re.sub(r'\s+', '-', clean_title.lower()).strip('-')
            toc_items.append(f"{i}. [{title}](#{anchor})")

        content_parts.extend(toc_items)
        content_parts.extend(["", "---", ""])

        # Add consolidated content
        for i, (content, metadata) in enumerate(content_list, 1):
            title = metadata.get("title", f"Document {i}")
            file_path = metadata.get("file_path", "unknown")

            content_parts.extend([
                f"## {i}. {title}",
                "",
                f"**Source**: `{file_path}`",
                ""
            ])

            # Clean up the content
            clean_content = self._clean_content_for_consolidation(content)

            # Add content
            content_parts.extend([
                clean_content,
                "",
                "---",
                ""
            ])

        # Add summary at the end
        content_parts.extend([
            "## 📊 Consolidation Summary",
            "",
            f"This document successfully consolidates {len(content_list)} {topic.lower()} documents:",
            "",
            "**Source Documents:**"
        ])

        for i, (_, metadata) in enumerate(content_list, 1):
            title = metadata.get("title", f"Document {i}")
            file_path = metadata.get("file_path", "unknown")
            last_mod = metadata.get("last_modified")
            mod_str = last_mod.strftime("%Y-%m-%d") if last_mod else "Unknown"

            content_parts.append(f"{i}. **{title}** (`{file_path}` - {mod_str})")

        content_parts.extend([
            "",
            "**Benefits of Consolidation:**",
            f"- ✅ Single comprehensive reference instead of {len(content_list)} separate documents",
            "- ✅ Improved searchability and navigation",
            "- ✅ Reduced duplication and redundancy",
            "- ✅ Easier maintenance and updates",
            "",
            f"**Total Words**: {sum(len(content.split()) for content, _ in content_list):,}",
            f"**Consolidated On**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "*This document was automatically generated by the Documentation Consolidation Agent as part of the Script Ohio 2.0 project management reorganization.*"
        ])

        return "\n".join(content_parts)

    def _clean_content_for_consolidation(self, content: str) -> str:
        """Clean content for consolidation"""
        lines = content.split('\n')
        clean_lines = []

        # Remove leading/trailing empty lines
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()

        for line in lines:
            # Skip title if it's the first line (we'll add our own)
            if clean_lines or not line.strip().startswith('#'):
                clean_lines.append(line)

        return '\n'.join(clean_lines)

    def _generate_title(self, suggested_name: str, metadata_list: List[Dict]) -> str:
        """Generate a title for the consolidated document"""
        base_name = Path(suggested_name).stem

        # Convert filename to title
        title = base_name.replace('_', ' ').replace('-', ' ').title()

        # Fix common abbreviations
        title = title.replace('Cfbd', 'CFBD').replace('Api', 'API').replace('Ml', 'ML')
        title = title.replace('Qa', 'QA').replace('Ui', 'UI').replace('Ux', 'UX')

        # Remove file extension if present
        title = title.replace('.Md', '')

        return title

    def _extract_topic(self, suggested_name: str, reason: str) -> str:
        """Extract the main topic from filename and reason"""
        name_lower = suggested_name.lower()
        reason_lower = reason.lower()

        if any(word in name_lower for word in ['documentation', 'guide', 'tutorial']):
            return "Documentation"
        elif any(word in name_lower for word in ['report', 'summary', 'status']):
            return "Status Report"
        elif any(word in name_lower for word in ['plan', 'roadmap', 'strategy']):
            return "Planning"
        elif any(word in name_lower for word in ['testing', 'validation', 'qa']):
            return "Testing"
        elif any(word in name_lower for word in ['development', 'implementation']):
            return "Development"
        else:
            return "General"

    def save_consolidated_document(self, doc: ConsolidatedDocument) -> str:
        """Save the consolidated document"""
        # Ensure directory exists
        self.comprehensive_guides_dir.mkdir(parents=True, exist_ok=True)

        file_path = self.comprehensive_guides_dir / doc.filename

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(doc.content)

            print(f"   ✅ Saved: {doc.filename} ({doc.word_count:,} words)")
            return str(file_path)

        except Exception as e:
            print(f"   ❌ Failed to save {doc.filename}: {e}")
            return ""

    def archive_source_files(self, source_files: List[str]) -> List[str]:
        """Archive the source files that were consolidated"""
        archived_files = []

        # Create archive subdirectory
        archive_subdir = self.archive_dir / "consolidated_docs"
        archive_subdir.mkdir(parents=True, exist_ok=True)

        for file_path in source_files:
            try:
                source_full = self.project_root / file_path
                if source_full.exists():
                    dest_full = archive_subdir / Path(file_path).name

                    # If file already exists in archive, add timestamp
                    if dest_full.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        dest_full = archive_subdir / f"{Path(file_path).stem}_{timestamp}{Path(file_path).suffix}"

                    shutil.move(str(source_full), str(dest_full))
                    archived_files.append(file_path)
                    print(f"   📦 Archived: {file_path}")

            except Exception as e:
                print(f"   ⚠️  Could not archive {file_path}: {e}")

        return archived_files

    def execute_immediate_consolidations(self, plan: Dict, dry_run: bool = False) -> List[ConsolidationResult]:
        """Execute immediate consolidations from the plan"""
        immediate_cons = plan.get("immediate_consolidations", [])
        results = []

        print(f"🔄 Executing {len(immediate_cons)} immediate consolidations")

        for i, con in enumerate(immediate_cons, 1):
            print(f"[{i:2d}/{len(immediate_cons)}] ", end="")

            files = con.get("files", [])
            suggested_name = con.get("suggested_name", "")
            reason = con.get("reason", "")

            if not files or not suggested_name:
                print("❌ Missing files or filename")
                continue

            try:
                # Create consolidated document
                consolidated_doc = self.create_consolidated_document(files, suggested_name, reason)

                if dry_run:
                    print(f"DRY RUN: Would consolidate {len(files)} files into {suggested_name}")
                    result = ConsolidationResult(
                        success=True,
                        consolidated_file=f"docs/comprehensive_guides/{suggested_name}",
                        archived_files=files,
                        word_count_reduction=consolidated_doc.word_count,
                        size_reduction_bytes=con.get("estimated_reduction_kb", 0) * 1024
                    )
                else:
                    # Save consolidated document
                    saved_path = self.save_consolidated_document(consolidated_doc)

                    if saved_path:
                        # Archive source files
                        archived = self.archive_source_files(files)

                        # Calculate reductions
                        word_reduction = consolidated_doc.word_count
                        size_reduction = con.get("estimated_reduction_kb", 0) * 1024

                        result = ConsolidationResult(
                            success=True,
                            consolidated_file=saved_path,
                            archived_files=archived,
                            word_count_reduction=word_reduction,
                            size_reduction_bytes=size_reduction
                        )

                        self.consolidated_documents.append(consolidated_doc)
                    else:
                        result = ConsolidationResult(
                            success=False,
                            consolidated_file="",
                            archived_files=[],
                            word_count_reduction=0,
                            size_reduction_bytes=0,
                            error_message="Failed to save consolidated document"
                        )

                results.append(result)

            except Exception as e:
                print(f"❌ Failed: {e}")
                result = ConsolidationResult(
                    success=False,
                    consolidated_file="",
                    archived_files=[],
                    word_count_reduction=0,
                    size_reduction_bytes=0,
                    error_message=str(e)
                )
                results.append(result)

        return results

    def create_archive_candidates_file(self, archive_candidates: List[str]) -> str:
        """Create a file listing archive candidates for future reference"""
        archive_info = [
            "# Archive Candidates",
            "",
            f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            "The following files are candidates for archiving or consolidation in the future:",
            "",
            "## Files to Consider",
            ""
        ]

        for file_path in archive_candidates:
            archive_info.append(f"- `{file_path}`")

        archive_info.extend([
            "",
            "## Notes",
            "",
            "- These files were not immediately consolidated but may be candidates for future cleanup",
            "- Review these files periodically to determine if they can be consolidated or removed",
            "- Consider archiving files that are no longer actively referenced",
            "",
            "---",
            "",
            "*This file was generated by the Documentation Consolidation Agent*"
        ])

        content = "\n".join(archive_info)
        file_path = self.archive_dir / "archive_candidates.md"

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return str(file_path)
        except Exception as e:
            print(f"⚠️  Could not save archive candidates file: {e}")
            return ""

    def generate_consolidation_report(self, results: List[ConsolidationResult]) -> Dict:
        """Generate a report of the consolidation operations"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]

        total_word_reduction = sum(r.word_count_reduction for r in successful_results)
        total_size_reduction = sum(r.size_reduction_bytes for r in successful_results)
        total_files_consolidated = sum(len(r.archived_files) for r in successful_results)

        return {
            "summary": {
                "total_consolidations": len(results),
                "successful": len(successful_results),
                "failed": len(failed_results),
                "files_consolidated": total_files_consolidated,
                "documents_created": len(successful_results),
                "word_count_reduction": total_word_reduction,
                "size_reduction_bytes": total_size_reduction,
                "size_reduction_mb": round(total_size_reduction / (1024 * 1024), 2),
                "timestamp": datetime.now().isoformat()
            },
            "successful_consolidations": [
                {
                    "consolidated_file": r.consolidated_file,
                    "archived_files": r.archived_files,
                    "word_count_reduction": r.word_count_reduction,
                    "size_reduction_bytes": r.size_reduction_bytes
                }
                for r in successful_results
            ],
            "failed_consolidations": [
                {
                    "error_message": r.error_message
                }
                for r in failed_results
            ],
            "consolidated_documents": [
                {
                    "title": doc.title,
                    "filename": doc.filename,
                    "topic": doc.topic,
                    "word_count": doc.word_count,
                    "source_files": doc.source_files
                }
                for doc in self.consolidated_documents
            ]
        }

    def execute_consolidation(self, dry_run: bool = False) -> bool:
        """Execute the complete documentation consolidation"""
        print("🚀 Starting Documentation Consolidation")
        print("=" * 60)

        if dry_run:
            print("🔍 DRY RUN MODE - No actual changes will be made")

        # Load consolidation plan
        plan = self.load_consolidation_plan()
        if not plan:
            print("❌ Could not load consolidation plan")
            return False

        # Execute immediate consolidations
        results = self.execute_immediate_consolidations(plan, dry_run)

        # Create archive candidates file
        archive_candidates = plan.get("archive_candidates", [])
        if archive_candidates and not dry_run:
            archive_file = self.create_archive_candidates_file(archive_candidates)
            print(f"📄 Archive candidates list created: {archive_file}")

        # Generate report
        report = self.generate_consolidation_report(results)
        report_path = self.pm_directory / "consolidation_execution_report.json"

        if not dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, default=str)

        # Print summary
        summary = report["summary"]
        print(f"\n📊 CONSOLIDATION SUMMARY")
        print(f"   Total consolidations: {summary['total_consolidations']}")
        print(f"   Successful: {summary['successful']}")
        print(f"   Failed: {summary['failed']}")
        print(f"   Files consolidated: {summary['files_consolidated']}")
        print(f"   Documents created: {summary['documents_created']}")
        print(f"   Word count reduction: {summary['word_count_reduction']:,}")
        print(f"   Size reduction: {summary['size_reduction_mb']} MB")

        if not dry_run:
            print(f"   Report saved: {report_path}")

        return summary["failed"] == 0

def main():
    """Main execution function"""
    import argparse
    import shutil

    parser = argparse.ArgumentParser(description="Documentation Consolidation Agent")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    print("🚀 Documentation Consolidation Agent - Starting")
    if args.dry_run:
        print("🔍 DRY RUN MODE - No actual changes will be made")
    print("=" * 60)

    agent = DocumentationConsolidationAgent()

    success = agent.execute_consolidation(dry_run=args.dry_run)

    if args.dry_run:
        print("\n🔍 DRY RUN COMPLETE - Use without --dry-run to execute consolidation")
    elif success:
        print("\n✅ Documentation Consolidation Agent - Consolidation Complete!")
    else:
        print("\n❌ Documentation Consolidation Agent - Some operations failed")

if __name__ == "__main__":
    main()