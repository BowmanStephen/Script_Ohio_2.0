#!/usr/bin/env python3
"""
Model Audit and Cleanup Script

Scans model directories for model files (.joblib, .pkl), identifies which models
are actually referenced in code, checks file existence, and generates a comprehensive
audit report.

Usage:
    python scripts/audit_model_files.py
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ModelAuditor:
    """Audits model files and their usage across the codebase."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.model_extensions = {'.joblib', '.pkl'}
        self.scan_directories = [
            project_root / 'model_pack',
            project_root / 'starter_pack',
        ]
        
        # Files to check for model references
        self.reference_files = [
            project_root / 'agents' / 'model_execution_engine.py',
            project_root / 'config' / 'model_config.py',
            project_root / 'model_pack' / 'model_training_agent.py',
            project_root / 'scripts' / 'retrain_models_full_features.py',
        ]

    def find_model_files(self) -> Dict[str, Dict[str, Any]]:
        """Scan directories for all model files."""
        model_files = {}
        
        for directory in self.scan_directories:
            if not directory.exists():
                continue
                
            for file_path in directory.rglob('*'):
                if file_path.suffix.lower() in self.model_extensions:
                    # Skip memory/conversation files
                    if 'memory' in str(file_path) or 'conversation' in str(file_path):
                        continue
                    
                    rel_path = file_path.relative_to(self.project_root)
                    stat = file_path.stat()
                    
                    model_files[str(rel_path)] = {
                        'full_path': str(file_path),
                        'relative_path': str(rel_path),
                        'directory': str(directory.relative_to(self.project_root)),
                        'size_bytes': stat.st_size,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'extension': file_path.suffix.lower(),
                    }
        
        return model_files

    def find_model_references(self) -> Dict[str, List[str]]:
        """Find all model file references in code."""
        references = {}
        
        for ref_file in self.reference_files:
            if not ref_file.exists():
                continue
                
            try:
                content = ref_file.read_text(encoding='utf-8')
                
                # Find model file references (both quoted strings and path operations)
                patterns = [
                    r'["\']([^"\']*\.(?:joblib|pkl))["\']',  # Quoted paths
                    r'/([^/\s]+\.(?:joblib|pkl))',  # Path separators
                    r'Path\(["\']([^"\']*\.(?:joblib|pkl))["\']\)',  # Path() calls
                    r'([^/\s]+\.(?:joblib|pkl))',  # Standalone filenames
                ]
                
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        model_ref = match.group(1) if match.groups() else match.group(0)
                        
                        # Normalize path
                        if '/' in model_ref:
                            model_ref = model_ref.split('/')[-1]
                        
                        if model_ref not in references:
                            references[model_ref] = []
                        
                        references[model_ref].append({
                            'file': str(ref_file.relative_to(self.project_root)),
                            'line': content[:match.start()].count('\n') + 1,
                            'context': self._extract_context(content, match.start(), match.end())
                        })
            except Exception as e:
                print(f"Warning: Could not read {ref_file}: {e}")
        
        return references

    def _extract_context(self, content: str, start: int, end: int, context_lines: int = 2) -> str:
        """Extract context around a match."""
        lines = content.split('\n')
        start_line = content[:start].count('\n')
        end_line = content[:end].count('\n')
        
        context_start = max(0, start_line - context_lines)
        context_end = min(len(lines), end_line + context_lines + 1)
        
        context = []
        for i in range(context_start, context_end):
            prefix = '>>> ' if i == start_line else '    '
            context.append(f"{prefix}{i+1:4d}: {lines[i]}")
        
        return '\n'.join(context)

    def categorize_models(self, model_files: Dict[str, Dict], references: Dict[str, List]) -> Dict[str, Any]:
        """Categorize models into production, legacy, outdated, etc."""
        production_models = {
            'ridge_model_2025.joblib',
            'xgb_home_win_model_2025.pkl',
            'fastai_home_win_model_2025.pkl',
        }
        
        categories = {
            'production': [],
            'referenced': [],
            'legacy': [],
            'outdated': [],
            'orphaned': [],
            'backup': [],
        }
        
        for rel_path, file_info in model_files.items():
            filename = Path(rel_path).name
            
            # Check if it's a production model
            if filename in production_models:
                categories['production'].append(rel_path)
            
            # Check if referenced in code
            is_referenced = any(
                filename in ref or filename.endswith(ref) 
                for ref in references.keys()
            )
            
            if is_referenced:
                categories['referenced'].append(rel_path)
            
            # Categorize by naming patterns
            if 'backup' in rel_path.lower() or 'backups' in rel_path.lower():
                categories['backup'].append(rel_path)
            elif '_fixed' in filename:
                categories['outdated'].append(rel_path)
            elif '_2025' not in filename and filename not in production_models:
                categories['legacy'].append(rel_path)
            elif not is_referenced and filename not in production_models:
                categories['orphaned'].append(rel_path)
        
        return categories

    def check_file_existence(self, references: Dict[str, List]) -> Dict[str, Any]:
        """Check if referenced model files actually exist."""
        existence_report = {
            'missing': [],
            'found': [],
            'multiple_locations': {},
        }
        
        for model_ref, ref_locations in references.items():
            # Try to find the file
            found_locations = []
            
            # Check common locations
            search_paths = [
                self.project_root / 'model_pack' / model_ref,
                self.project_root / model_ref,
            ]
            
            # Also search by filename if it's a full path
            if '/' in model_ref:
                filename = Path(model_ref).name
                search_paths.append(self.project_root / 'model_pack' / filename)
            
            for search_path in search_paths:
                if search_path.exists():
                    found_locations.append(str(search_path.relative_to(self.project_root)))
            
            if not found_locations:
                existence_report['missing'].append({
                    'reference': model_ref,
                    'referenced_in': ref_locations
                })
            elif len(found_locations) == 1:
                existence_report['found'].append({
                    'reference': model_ref,
                    'location': found_locations[0],
                    'referenced_in': ref_locations
                })
            else:
                existence_report['multiple_locations'][model_ref] = {
                    'locations': found_locations,
                    'referenced_in': ref_locations
                }
        
        return existence_report

    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report."""
        print("🔍 Scanning for model files...")
        model_files = self.find_model_files()
        print(f"   Found {len(model_files)} model files")
        
        print("🔍 Scanning for model references in code...")
        references = self.find_model_references()
        print(f"   Found {len(references)} unique model references")
        
        print("🔍 Categorizing models...")
        categories = self.categorize_models(model_files, references)
        
        print("🔍 Checking file existence...")
        existence = self.check_file_existence(references)
        
        # Identify files to archive
        files_to_archive = []
        for category, files in categories.items():
            if category in ['legacy', 'outdated']:
                files_to_archive.extend(files)
        
        # Remove duplicates and sort
        files_to_archive = sorted(set(files_to_archive))
        
        report = {
            'audit_date': datetime.now().isoformat(),
            'project_root': str(self.project_root),
            'summary': {
                'total_model_files': len(model_files),
                'total_references': len(references),
                'production_models': len(categories['production']),
                'referenced_models': len(categories['referenced']),
                'legacy_models': len(categories['legacy']),
                'outdated_models': len(categories['outdated']),
                'orphaned_models': len(categories['orphaned']),
                'backup_models': len(categories['backup']),
                'files_to_archive': len(files_to_archive),
                'missing_files': len(existence['missing']),
            },
            'model_files': model_files,
            'references': references,
            'categories': categories,
            'existence_check': existence,
            'files_to_archive': files_to_archive,
        }
        
        return report

    def save_report(self, report: Dict[str, Any], output_dir: Path = None):
        """Save audit report in JSON and Markdown formats."""
        if output_dir is None:
            output_dir = self.project_root / 'reports'
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d')
        
        # Save JSON report
        json_path = output_dir / f'model_audit_report_{timestamp}.json'
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✅ JSON report saved: {json_path}")
        
        # Save Markdown report
        md_path = output_dir / f'model_audit_report_{timestamp}.md'
        md_content = self._generate_markdown_report(report)
        md_path.write_text(md_content)
        print(f"✅ Markdown report saved: {md_path}")
        
        return json_path, md_path

    def _generate_markdown_report(self, report: Dict[str, Any]) -> str:
        """Generate Markdown summary report."""
        summary = report['summary']
        categories = report['categories']
        existence = report['existence_check']
        
        md_lines = [
            "# Model Audit Report",
            f"**Audit Date:** {report['audit_date']}",
            f"**Project Root:** {report['project_root']}",
            "",
            "## Summary",
            "",
            f"- **Total Model Files Found:** {summary['total_model_files']}",
            f"- **Total Code References:** {summary['total_references']}",
            f"- **Production Models:** {summary['production_models']}",
            f"- **Referenced Models:** {summary['referenced_models']}",
            f"- **Legacy Models:** {summary['legacy_models']}",
            f"- **Outdated Models (with _fixed suffix):** {summary['outdated_models']}",
            f"- **Orphaned Models:** {summary['orphaned_models']}",
            f"- **Backup Models:** {summary['backup_models']}",
            f"- **Files to Archive:** {summary['files_to_archive']}",
            f"- **Missing Files:** {summary['missing_files']}",
            "",
            "## Production Models",
            "",
        ]
        
        for model_path in categories['production']:
            file_info = report['model_files'][model_path]
            md_lines.append(f"- `{model_path}` ({file_info['size_mb']} MB, modified: {file_info['modified_time']})")
        
        md_lines.extend([
            "",
            "## Files to Archive",
            "",
            "The following files should be archived (legacy and outdated variants):",
            "",
        ])
        
        for file_path in report['files_to_archive']:
            file_info = report['model_files'].get(file_path, {})
            size = file_info.get('size_mb', 'unknown')
            md_lines.append(f"- `{file_path}` ({size} MB)")
        
        md_lines.extend([
            "",
            "## Missing Files",
            "",
        ])
        
        if existence['missing']:
            for missing in existence['missing']:
                md_lines.append(f"- **{missing['reference']}**")
                md_lines.append(f"  - Referenced in: {', '.join([r['file'] for r in missing['referenced_in']])}")
        else:
            md_lines.append("✅ All referenced model files exist")
        
        md_lines.extend([
            "",
            "## Configuration Mismatches",
            "",
        ])
        
        # Check for _fixed suffix in references
        fixed_refs = [ref for ref in report['references'].keys() if '_fixed' in ref]
        if fixed_refs:
            md_lines.append("⚠️ The following references use `_fixed` suffix (should be removed):")
            for ref in fixed_refs:
                md_lines.append(f"- `{ref}`")
                for location in report['references'][ref]:
                    md_lines.append(f"  - {location['file']}:{location['line']}")
        else:
            md_lines.append("✅ No `_fixed` suffix references found")
        
        md_lines.extend([
            "",
            "## Detailed Model Files",
            "",
            "### All Model Files",
            "",
        ])
        
        for rel_path, file_info in sorted(report['model_files'].items()):
            md_lines.append(f"- `{rel_path}`")
            md_lines.append(f"  - Size: {file_info['size_mb']} MB")
            md_lines.append(f"  - Modified: {file_info['modified_time']}")
            md_lines.append(f"  - Directory: {file_info['directory']}")
        
        return '\n'.join(md_lines)


def main():
    """Main execution function."""
    project_root = Path(__file__).parent.parent
    
    print("=" * 60)
    print("Model Audit and Cleanup Script")
    print("=" * 60)
    print()
    
    auditor = ModelAuditor(project_root)
    report = auditor.generate_audit_report()
    
    print()
    print("=" * 60)
    print("Generating Reports...")
    print("=" * 60)
    
    json_path, md_path = auditor.save_report(report)
    
    print()
    print("=" * 60)
    print("Audit Complete!")
    print("=" * 60)
    print()
    print(f"Summary:")
    print(f"  - Total model files: {report['summary']['total_model_files']}")
    print(f"  - Production models: {report['summary']['production_models']}")
    print(f"  - Files to archive: {report['summary']['files_to_archive']}")
    print(f"  - Missing files: {report['summary']['missing_files']}")
    print()
    print(f"Reports saved:")
    print(f"  - {json_path}")
    print(f"  - {md_path}")


if __name__ == '__main__':
    main()

