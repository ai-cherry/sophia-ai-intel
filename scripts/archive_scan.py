#!/usr/bin/env python3
"""
Archive File Scanner for Sophia AI Codebase
Scans for archived, backup, and potentially obsolete files
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple
import hashlib

class ArchiveScanner:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.archived_files = []
        self.backup_files = []
        self.temp_files = []
        self.old_versions = []
        self.duplicate_candidates = []
        self.obsolete_patterns = []
        self.large_archives = []
        self.file_hashes = {}
        
        # Patterns for archived/backup files
        self.archive_patterns = [
            r'.*\.bak$', r'.*\.backup$', r'.*\.old$', r'.*\.orig$',
            r'.*\.save$', r'.*\.tmp$', r'.*\.temp$', r'.*\.swp$',
            r'.*~$', r'.*\.archive$', r'.*\.archived$',
            r'.*\.deprecated$', r'.*\.obsolete$', r'.*\.legacy$',
            r'.*_backup.*', r'.*_old.*', r'.*_archive.*',
            r'.*\.tar$', r'.*\.tar\.gz$', r'.*\.zip$', r'.*\.rar$',
            r'.*\.7z$', r'.*\.bz2$', r'.*\.gz$',
            r'.*\.\d{8}$',  # Date-stamped files
            r'.*\.\d{14}$',  # Timestamp files
            r'.*_\d{8}_\d{6}.*',  # Date-time patterns
            r'.*\.v\d+$',  # Version numbered files
            r'.*\.copy$', r'.*\.Copy$', r'.*\(copy\).*',
            r'.*\(backup\).*', r'.*\(old\).*',
            r'.*\.BACKUP-.*', r'.*\.BASE-.*', r'.*\.LOCAL-.*',
            r'.*\.REMOTE-.*', r'.*\.orig\..*'
        ]
        
        # Patterns for potentially obsolete files
        self.obsolete_name_patterns = [
            r'test_.*\.py$', r'demo_.*\.py$', r'example_.*\.py$',
            r'.*_test\.py$', r'.*_demo\.py$', r'.*_example\.py$',
            r'TODO.*', r'FIXME.*', r'DELETE.*', r'REMOVE.*',
            r'old_.*', r'legacy_.*', r'deprecated_.*',
            r'unused_.*', r'draft_.*', r'temp_.*'
        ]
        
        # Ignore directories
        self.ignore_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            'venv', 'env', '.venv', 'dist', 'build', '.next',
            'coverage', '.coverage', 'htmlcov', '.tox'
        }
        
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        for part in path.parts:
            if part in self.ignore_dirs:
                return True
        return False
    
    def is_archive_file(self, filepath: Path) -> Tuple[bool, str]:
        """Check if file matches archive patterns"""
        filename = filepath.name
        for pattern in self.archive_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True, pattern
        return False, ""
    
    def is_obsolete_file(self, filepath: Path) -> Tuple[bool, str]:
        """Check if file matches obsolete patterns"""
        filename = filepath.name
        for pattern in self.obsolete_name_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                return True, pattern
        return False, ""
    
    def get_file_hash(self, filepath: Path) -> str:
        """Calculate file hash for duplicate detection"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def scan_directory(self):
        """Scan entire directory tree"""
        print(f"Scanning {self.root_dir}...")
        total_files = 0
        scanned_files = 0
        
        # First pass: count total files
        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            if self.should_ignore(root_path):
                continue
            total_files += len(files)
        
        print(f"Total files to scan: {total_files}")
        
        # Second pass: scan files
        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            
            # Skip ignored directories
            if self.should_ignore(root_path):
                dirs.clear()
                continue
            
            for file in files:
                filepath = root_path / file
                rel_path = filepath.relative_to(self.root_dir)
                scanned_files += 1
                
                if scanned_files % 1000 == 0:
                    print(f"Progress: {scanned_files}/{total_files} files scanned...")
                
                # Get file stats once for all checks
                try:
                    file_stats = filepath.stat()
                except:
                    continue  # Skip files we can't stat
                
                # Check for archive files
                is_archive, pattern = self.is_archive_file(filepath)
                if is_archive:
                    self.archived_files.append({
                        'path': str(rel_path),
                        'pattern': pattern,
                        'size': file_stats.st_size,
                        'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    })
                    
                    # Check if it's a large archive
                    if file_stats.st_size > 10 * 1024 * 1024:  # > 10MB
                        self.large_archives.append({
                            'path': str(rel_path),
                            'size_mb': round(file_stats.st_size / (1024 * 1024), 2)
                        })
                
                # Check for obsolete files
                is_obsolete, obs_pattern = self.is_obsolete_file(filepath)
                if is_obsolete:
                    self.obsolete_patterns.append({
                        'path': str(rel_path),
                        'pattern': obs_pattern,
                        'size': file_stats.st_size,
                        'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
                    })
                
                # Check for temp files
                if file.startswith('.') and not file.startswith('.git'):
                    self.temp_files.append(str(rel_path))
                
                # Check for backup files
                if 'backup' in file.lower() or 'bak' in file.lower():
                    self.backup_files.append(str(rel_path))
                
                # Check for old versions (files with version numbers or dates)
                if re.search(r'_v\d+|_\d{8}|_old|_copy', file.lower()):
                    self.old_versions.append(str(rel_path))
                
                # Hash small files for duplicate detection
                if filepath.is_file() and file_stats.st_size < 1024 * 1024:  # < 1MB
                    file_hash = self.get_file_hash(filepath)
                    if file_hash:
                        if file_hash in self.file_hashes:
                            self.duplicate_candidates.append({
                                'file1': self.file_hashes[file_hash],
                                'file2': str(rel_path),
                                'hash': file_hash
                            })
                        else:
                            self.file_hashes[file_hash] = str(rel_path)
        
        print(f"Scan complete: {scanned_files} files processed")
    
    def analyze_results(self) -> Dict:
        """Analyze scan results"""
        total_archive_size = sum(f['size'] for f in self.archived_files)
        total_obsolete_size = sum(f['size'] for f in self.obsolete_patterns)
        
        # Group archives by type
        archive_types = {}
        for file in self.archived_files:
            ext = Path(file['path']).suffix.lower()
            if ext not in archive_types:
                archive_types[ext] = []
            archive_types[ext].append(file['path'])
        
        # Find oldest files
        sorted_archives = sorted(self.archived_files, key=lambda x: x['modified'])
        oldest_archives = sorted_archives[:10] if len(sorted_archives) >= 10 else sorted_archives
        
        return {
            'summary': {
                'total_archived_files': len(self.archived_files),
                'total_backup_files': len(self.backup_files),
                'total_temp_files': len(self.temp_files),
                'total_old_versions': len(self.old_versions),
                'total_obsolete_files': len(self.obsolete_patterns),
                'total_duplicate_candidates': len(self.duplicate_candidates),
                'total_large_archives': len(self.large_archives),
                'total_archive_size_mb': round(total_archive_size / (1024 * 1024), 2),
                'total_obsolete_size_mb': round(total_obsolete_size / (1024 * 1024), 2),
                'potential_space_savings_mb': round((total_archive_size + total_obsolete_size) / (1024 * 1024), 2)
            },
            'archive_types': archive_types,
            'oldest_archives': oldest_archives,
            'large_archives': self.large_archives[:20],  # Top 20 largest
            'duplicate_groups': self.duplicate_candidates[:50],  # First 50 duplicates
            'cleanup_recommendations': self.generate_recommendations()
        }
    
    def generate_recommendations(self) -> List[str]:
        """Generate cleanup recommendations"""
        recommendations = []
        
        if len(self.archived_files) > 50:
            recommendations.append(f"CRITICAL: Found {len(self.archived_files)} archived files. Consider archiving to external storage.")
        
        if len(self.backup_files) > 20:
            recommendations.append(f"WARNING: {len(self.backup_files)} backup files detected. Use version control instead.")
        
        if len(self.temp_files) > 10:
            recommendations.append(f"INFO: {len(self.temp_files)} temporary files can be safely removed.")
        
        if len(self.duplicate_candidates) > 30:
            recommendations.append(f"WARNING: {len(self.duplicate_candidates)} potential duplicate files found.")
        
        if len(self.large_archives) > 0:
            total_size = sum(f['size_mb'] for f in self.large_archives)
            recommendations.append(f"CRITICAL: {len(self.large_archives)} large archives consuming {total_size:.2f}MB.")
        
        if len(self.obsolete_patterns) > 100:
            recommendations.append(f"WARNING: {len(self.obsolete_patterns)} potentially obsolete files found.")
        
        # Specific file type recommendations
        tar_gz_files = [f for f in self.archived_files if '.tar.gz' in f['path']]
        if tar_gz_files:
            recommendations.append(f"INFO: Found {len(tar_gz_files)} tar.gz archives. Consider extracting needed files and removing.")
        
        test_files = [f for f in self.obsolete_patterns if 'test' in f['path'].lower()]
        if len(test_files) > 50:
            recommendations.append(f"INFO: {len(test_files)} test files found. Ensure they're in proper test directories.")
        
        return recommendations
    
    def generate_report(self) -> str:
        """Generate detailed report"""
        analysis = self.analyze_results()
        
        report = []
        report.append("=" * 80)
        report.append("SOPHIA AI - ARCHIVE FILE SCAN REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        for key, value in analysis['summary'].items():
            report.append(f"  {key.replace('_', ' ').title()}: {value}")
        report.append("")
        
        # Recommendations
        if analysis['cleanup_recommendations']:
            report.append("CLEANUP RECOMMENDATIONS")
            report.append("-" * 40)
            for rec in analysis['cleanup_recommendations']:
                report.append(f"  • {rec}")
            report.append("")
        
        # Archive Types Distribution
        if analysis['archive_types']:
            report.append("ARCHIVE FILES BY TYPE")
            report.append("-" * 40)
            for ext, files in sorted(analysis['archive_types'].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
                report.append(f"  {ext or 'no extension'}: {len(files)} files")
            report.append("")
        
        # Large Archives
        if analysis['large_archives']:
            report.append("LARGEST ARCHIVE FILES (TOP 10)")
            report.append("-" * 40)
            for archive in analysis['large_archives'][:10]:
                report.append(f"  • {archive['path']} ({archive['size_mb']}MB)")
            report.append("")
        
        # Oldest Archives
        if analysis['oldest_archives']:
            report.append("OLDEST ARCHIVE FILES (TOP 10)")
            report.append("-" * 40)
            for archive in analysis['oldest_archives']:
                report.append(f"  • {archive['path']} (modified: {archive['modified'][:10]})")
            report.append("")
        
        # Detailed Lists (first 20 of each)
        if self.archived_files:
            report.append("ARCHIVED FILES (FIRST 20)")
            report.append("-" * 40)
            for file in self.archived_files[:20]:
                report.append(f"  • {file['path']}")
            if len(self.archived_files) > 20:
                report.append(f"  ... and {len(self.archived_files) - 20} more")
            report.append("")
        
        if self.backup_files:
            report.append("BACKUP FILES (FIRST 20)")
            report.append("-" * 40)
            for file in self.backup_files[:20]:
                report.append(f"  • {file}")
            if len(self.backup_files) > 20:
                report.append(f"  ... and {len(self.backup_files) - 20} more")
            report.append("")
        
        if self.duplicate_candidates:
            report.append("DUPLICATE FILE CANDIDATES (FIRST 10)")
            report.append("-" * 40)
            for dup in self.duplicate_candidates[:10]:
                report.append(f"  • {dup['file1']}")
                report.append(f"    = {dup['file2']}")
            if len(self.duplicate_candidates) > 10:
                report.append(f"  ... and {len(self.duplicate_candidates) - 10} more pairs")
            report.append("")
        
        # Action Items
        report.append("RECOMMENDED ACTIONS")
        report.append("-" * 40)
        report.append("  1. Review and remove unnecessary archive files")
        report.append("  2. Move large archives to external storage")
        report.append("  3. Delete temporary and backup files")
        report.append("  4. Consolidate duplicate files")
        report.append("  5. Update .gitignore to prevent future accumulation")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, output_dir: str = "archive_scan_results"):
        """Save scan results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed JSON
        json_file = output_path / f"archive_scan_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'scan_time': datetime.now().isoformat(),
                'root_directory': str(self.root_dir),
                'archived_files': self.archived_files,
                'backup_files': self.backup_files,
                'temp_files': self.temp_files,
                'old_versions': self.old_versions,
                'obsolete_files': self.obsolete_patterns,
                'duplicate_candidates': self.duplicate_candidates,
                'large_archives': self.large_archives,
                'analysis': self.analyze_results()
            }, f, indent=2)
        
        # Save human-readable report
        report_file = output_path / f"archive_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(self.generate_report())
        
        # Save cleanup script
        cleanup_script = output_path / f"cleanup_archived_{timestamp}.sh"
        with open(cleanup_script, 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("# Auto-generated cleanup script for archived files\n")
            f.write("# Review carefully before running!\n\n")
            f.write("echo 'This script will remove archived files. Continue? (y/n)'\n")
            f.write("read -r response\n")
            f.write("if [[ ! $response =~ ^[Yy]$ ]]; then\n")
            f.write("    echo 'Aborted'\n")
            f.write("    exit 1\n")
            f.write("fi\n\n")
            f.write("# Remove temp files\n")
            for file in self.temp_files[:50]:  # Limit to first 50
                f.write(f"rm -f '{file}'\n")
            f.write("\n# Remove small archive files\n")
            for file in self.archived_files[:30]:  # Limit to first 30
                if file['size'] < 1024 * 1024:  # < 1MB
                    f.write(f"rm -f '{file['path']}'\n")
        
        os.chmod(cleanup_script, 0o755)
        
        print(f"\nResults saved to:")
        print(f"  JSON: {json_file}")
        print(f"  Report: {report_file}")
        print(f"  Cleanup script: {cleanup_script}")
        
        return str(report_file)


def main():
    """Main execution"""
    scanner = ArchiveScanner()
    scanner.scan_directory()
    report_file = scanner.save_results()
    
    # Print summary
    print("\n" + "=" * 80)
    print("SCAN COMPLETE")
    print("=" * 80)
    
    analysis = scanner.analyze_results()
    print("\nSUMMARY:")
    for key, value in analysis['summary'].items():
        print(f"  {key.replace('_', ' ').title()}: {value}")
    
    print("\nRECOMMENDATIONS:")
    for rec in analysis['cleanup_recommendations']:
        print(f"  • {rec}")
    
    print(f"\nFull report saved to: {report_file}")
    
    # Also print the report
    print("\n" + "=" * 80)
    print("DETAILED REPORT")
    print("=" * 80)
    print(scanner.generate_report())


if __name__ == "__main__":
    main()
