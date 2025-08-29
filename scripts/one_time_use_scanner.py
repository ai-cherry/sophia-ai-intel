#!/usr/bin/env python3
"""
One-Time Use & Backup Files Scanner
Identifies backup files, temporary scripts, outdated documents, and one-time use cases
"""

import os
import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

class OneTimeUseScanner:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.backup_files = []
        self.one_time_scripts = []
        self.outdated_docs = []
        self.deployment_scripts = []
        self.test_scripts = []
        self.migration_scripts = []
        self.setup_scripts = []
        self.temp_scripts = []
        self.analysis_docs = []
        self.report_docs = []
        
        # Patterns for one-time use indicators
        self.one_time_patterns = [
            r'test[-_].*\.(py|sh|js)$',
            r'.*[-_]test\.(py|sh|js)$',
            r'migrate[-_].*\.(py|sh)$',
            r'.*[-_]migration\.(py|sh)$',
            r'setup[-_].*\.(py|sh)$',
            r'deploy[-_].*\.(sh|py)$',
            r'fix[-_].*\.(py|sh)$',
            r'patch[-_].*\.(py|sh)$',
            r'cleanup[-_].*\.(py|sh)$',
            r'.*[-_]cleanup\.(py|sh)$',
            r'temp[-_].*\.(py|sh|js)$',
            r'tmp[-_].*\.(py|sh|js)$',
            r'quick[-_].*\.(py|sh)$',
            r'simple[-_].*\.(py|sh)$',
            r'check[-_].*\.(py|sh)$',
            r'verify[-_].*\.(py|sh)$',
            r'analyze[-_].*\.(py|sh)$',
            r'audit[-_].*\.(py|sh)$',
            r'scan[-_].*\.(py|sh)$',
            r'init[-_].*\.(py|sh)$',
            r'bootstrap[-_].*\.(py|sh)$',
            r'.*_\d{8}.*\.(py|sh|md)$',  # Date-stamped files
            r'.*_\d{14}.*\.(py|sh|md)$',  # Timestamp files
        ]
        
        # Document patterns that might be outdated
        self.doc_patterns = [
            r'.*_REPORT.*\.md$',
            r'.*_ANALYSIS.*\.md$',
            r'.*_AUDIT.*\.md$',
            r'.*_STATUS.*\.md$',
            r'.*_SUMMARY.*\.md$',
            r'.*_PLAN.*\.md$',
            r'.*_GUIDE.*\.md$',
            r'.*_PROMPT.*\.md$',
            r'.*_SESSION.*\.md$',
            r'.*_FINAL.*\.md$',
            r'.*_COMPLETE.*\.md$',
            r'.*_TODO.*\.md$',
            r'.*_FIXME.*\.md$',
            r'.*_DEPRECATED.*\.md$',
            r'.*_OLD.*\.md$',
            r'.*_LEGACY.*\.md$',
            r'.*\d{8}.*\.md$',  # Date in filename
        ]
        
        # Backup patterns
        self.backup_patterns = [
            r'.*\.backup$',
            r'.*\.bak$',
            r'.*\.old$',
            r'.*\.orig$',
            r'.*\.save$',
            r'.*\.swp$',
            r'.*~$',
            r'.*\.tmp$',
            r'.*\.temp$',
            r'backup[-_].*',
            r'.*[-_]backup.*',
        ]
        
        # Ignore directories
        self.ignore_dirs = {
            '.git', 'node_modules', '__pycache__', '.pytest_cache',
            'venv', 'env', '.venv', 'dist', 'build', '.next',
            'coverage', '.coverage', 'htmlcov', '.tox',
            'archive_scan_results'  # Don't scan our own results
        }
    
    def should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        for part in path.parts:
            if part in self.ignore_dirs:
                return True
        return False
    
    def analyze_script_content(self, filepath: Path) -> Dict:
        """Analyze script content for one-time use indicators"""
        indicators = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
                
                # Check for one-time use indicators in content
                if 'if __name__ == "__main__"' in content and len(lines) < 100:
                    indicators.append("Small standalone script")
                
                if re.search(r'(temporary|temp|quick|test|demo|example|poc|proof)', content, re.IGNORECASE):
                    indicators.append("Contains temporary/test keywords")
                
                if re.search(r'TODO:?\s*delete|remove\s*this|temporary\s*fix', content, re.IGNORECASE):
                    indicators.append("Contains deletion TODO")
                
                if re.search(r'hardcoded|hard-coded|FIXME', content, re.IGNORECASE):
                    indicators.append("Contains hardcoded values or FIXME")
                
                # Check for date references suggesting one-time use
                if re.search(r'(August|Aug)\s*2[0-9]|08[-/]2[0-9][-/]202[4-5]', content):
                    indicators.append("Contains specific date references")
                
                # Check shebang and first lines for temporary indicators
                if lines and len(lines) > 0:
                    first_lines = '\n'.join(lines[:10])
                    if re.search(r'temporary|one-time|single use|migration|cleanup', first_lines, re.IGNORECASE):
                        indicators.append("Header indicates temporary use")
                
                return {
                    'has_indicators': len(indicators) > 0,
                    'indicators': indicators,
                    'line_count': len(lines),
                    'likely_one_time': len(indicators) >= 2
                }
        except Exception as e:
            return {
                'has_indicators': False,
                'indicators': [],
                'error': str(e)
            }
    
    def analyze_document_content(self, filepath: Path) -> Dict:
        """Analyze document content for outdated/one-time indicators"""
        indicators = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Check for completion/final status
                if re.search(r'(COMPLETE|COMPLETED|DONE|FINISHED|FINAL)', content[:500], re.IGNORECASE):
                    indicators.append("Marked as complete/final")
                
                # Check for specific dates (August 2024/2025)
                date_matches = re.findall(r'(August|Aug)\s*\d+,?\s*202[4-5]|08[-/]\d+[-/]202[4-5]', content)
                if date_matches:
                    indicators.append(f"Contains {len(date_matches)} date references")
                
                # Check for session/temporary language
                if re.search(r'(session|temporary|one-time|migration|handover)', content[:1000], re.IGNORECASE):
                    indicators.append("Contains temporary/session language")
                
                # Check for deployment/implementation specific content
                if re.search(r'(deployment\s*complete|implementation\s*complete|migration\s*complete)', content, re.IGNORECASE):
                    indicators.append("Describes completed deployment/migration")
                
                return {
                    'has_indicators': len(indicators) > 0,
                    'indicators': indicators,
                    'likely_outdated': len(indicators) >= 2
                }
        except Exception as e:
            return {'has_indicators': False, 'indicators': [], 'error': str(e)}
    
    def categorize_script(self, filepath: Path, rel_path: str) -> str:
        """Categorize script by its purpose"""
        name = filepath.name.lower()
        
        if 'deploy' in name:
            return 'deployment'
        elif 'test' in name:
            return 'test'
        elif 'migrate' in name or 'migration' in name:
            return 'migration'
        elif 'setup' in name or 'init' in name or 'bootstrap' in name:
            return 'setup'
        elif 'fix' in name or 'patch' in name or 'cleanup' in name:
            return 'fix/cleanup'
        elif 'check' in name or 'verify' in name or 'audit' in name or 'scan' in name:
            return 'verification'
        elif 'temp' in name or 'tmp' in name or 'quick' in name:
            return 'temporary'
        else:
            return 'utility'
    
    def scan_directory(self):
        """Scan entire directory tree"""
        print(f"Scanning {self.root_dir} for one-time use files...")
        
        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            
            # Skip ignored directories
            if self.should_ignore(root_path):
                dirs.clear()
                continue
            
            for file in files:
                filepath = root_path / file
                rel_path = str(filepath.relative_to(self.root_dir))
                
                # Skip if file doesn't exist or is a symlink
                if not filepath.is_file() or filepath.is_symlink():
                    continue
                
                # Get file stats
                try:
                    stats = filepath.stat()
                    modified = datetime.fromtimestamp(stats.st_mtime)
                    age_days = (datetime.now() - modified).days
                except:
                    continue
                
                # Check for backup files
                is_backup = False
                for pattern in self.backup_patterns:
                    if re.match(pattern, file, re.IGNORECASE):
                        self.backup_files.append({
                            'path': rel_path,
                            'size': stats.st_size,
                            'modified': modified.isoformat(),
                            'age_days': age_days,
                            'pattern': pattern
                        })
                        is_backup = True
                        break
                
                if is_backup:
                    continue
                
                # Check scripts for one-time use
                if file.endswith(('.py', '.sh', '.js')):
                    for pattern in self.one_time_patterns:
                        if re.match(pattern, file, re.IGNORECASE):
                            analysis = self.analyze_script_content(filepath)
                            category = self.categorize_script(filepath, rel_path)
                            
                            script_info = {
                                'path': rel_path,
                                'category': category,
                                'size': stats.st_size,
                                'modified': modified.isoformat(),
                                'age_days': age_days,
                                'pattern': pattern,
                                'analysis': analysis
                            }
                            
                            self.one_time_scripts.append(script_info)
                            
                            # Also categorize by type
                            if category == 'deployment':
                                self.deployment_scripts.append(script_info)
                            elif category == 'test':
                                self.test_scripts.append(script_info)
                            elif category == 'migration':
                                self.migration_scripts.append(script_info)
                            elif category == 'setup':
                                self.setup_scripts.append(script_info)
                            elif category == 'temporary':
                                self.temp_scripts.append(script_info)
                            break
                
                # Check documents for outdated content
                if file.endswith('.md'):
                    for pattern in self.doc_patterns:
                        if re.match(pattern, file, re.IGNORECASE):
                            analysis = self.analyze_document_content(filepath)
                            
                            doc_info = {
                                'path': rel_path,
                                'size': stats.st_size,
                                'modified': modified.isoformat(),
                                'age_days': age_days,
                                'pattern': pattern,
                                'analysis': analysis
                            }
                            
                            self.outdated_docs.append(doc_info)
                            
                            # Categorize document type
                            if 'REPORT' in file.upper():
                                self.report_docs.append(doc_info)
                            elif 'ANALYSIS' in file.upper() or 'AUDIT' in file.upper():
                                self.analysis_docs.append(doc_info)
                            break
        
        print(f"Scan complete!")
    
    def generate_report(self) -> str:
        """Generate comprehensive report"""
        report = []
        report.append("=" * 80)
        report.append("ONE-TIME USE FILES & BACKUP SCAN REPORT")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("=" * 80)
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 40)
        report.append(f"  Total Backup Files: {len(self.backup_files)}")
        report.append(f"  Total One-Time Scripts: {len(self.one_time_scripts)}")
        report.append(f"  Total Outdated Documents: {len(self.outdated_docs)}")
        report.append(f"  Deployment Scripts: {len(self.deployment_scripts)}")
        report.append(f"  Test Scripts: {len(self.test_scripts)}")
        report.append(f"  Migration Scripts: {len(self.migration_scripts)}")
        report.append(f"  Setup Scripts: {len(self.setup_scripts)}")
        report.append(f"  Temporary Scripts: {len(self.temp_scripts)}")
        report.append("")
        
        # Backup Files
        if self.backup_files:
            report.append("BACKUP FILES FOUND")
            report.append("-" * 40)
            for backup in sorted(self.backup_files, key=lambda x: x['age_days'], reverse=True)[:20]:
                age = f"{backup['age_days']}d old" if backup['age_days'] > 0 else "today"
                report.append(f"  • {backup['path']} ({age})")
            if len(self.backup_files) > 20:
                report.append(f"  ... and {len(self.backup_files) - 20} more")
            report.append("")
        
        # One-Time Scripts by Category
        categories = [
            ('DEPLOYMENT SCRIPTS', self.deployment_scripts),
            ('TEST SCRIPTS', self.test_scripts),
            ('MIGRATION SCRIPTS', self.migration_scripts),
            ('SETUP/INIT SCRIPTS', self.setup_scripts),
            ('TEMPORARY SCRIPTS', self.temp_scripts)
        ]
        
        for category_name, scripts in categories:
            if scripts:
                report.append(f"{category_name}")
                report.append("-" * 40)
                for script in sorted(scripts, key=lambda x: x['age_days'], reverse=True)[:10]:
                    age = f"{script['age_days']}d old" if script['age_days'] > 0 else "today"
                    likely = " [LIKELY ONE-TIME]" if script['analysis'].get('likely_one_time', False) else ""
                    report.append(f"  • {script['path']} ({age}){likely}")
                    if script['analysis'].get('indicators'):
                        for indicator in script['analysis']['indicators'][:2]:
                            report.append(f"    - {indicator}")
                if len(scripts) > 10:
                    report.append(f"  ... and {len(scripts) - 10} more")
                report.append("")
        
        # Outdated Documents
        if self.outdated_docs:
            report.append("POTENTIALLY OUTDATED DOCUMENTS")
            report.append("-" * 40)
            for doc in sorted(self.outdated_docs, key=lambda x: x['age_days'], reverse=True)[:15]:
                age = f"{doc['age_days']}d old" if doc['age_days'] > 0 else "today"
                likely = " [LIKELY OUTDATED]" if doc['analysis'].get('likely_outdated', False) else ""
                report.append(f"  • {doc['path']} ({age}){likely}")
                if doc['analysis'].get('indicators'):
                    for indicator in doc['analysis']['indicators'][:2]:
                        report.append(f"    - {indicator}")
            if len(self.outdated_docs) > 15:
                report.append(f"  ... and {len(self.outdated_docs) - 15} more")
            report.append("")
        
        # High Priority Cleanup Candidates
        report.append("HIGH PRIORITY CLEANUP CANDIDATES")
        report.append("-" * 40)
        
        # Old deployment scripts (>7 days)
        old_deploys = [s for s in self.deployment_scripts if s['age_days'] > 7]
        if old_deploys:
            report.append("  Deployment scripts older than 7 days:")
            for script in old_deploys[:5]:
                report.append(f"    • {script['path']} ({script['age_days']}d old)")
        
        # Scripts with strong one-time indicators
        strong_one_time = [s for s in self.one_time_scripts if s['analysis'].get('likely_one_time', False)]
        if strong_one_time:
            report.append("  Scripts with multiple one-time indicators:")
            for script in strong_one_time[:5]:
                report.append(f"    • {script['path']}")
        
        # Documents marked as complete/final
        final_docs = [d for d in self.outdated_docs if 'complete/final' in str(d['analysis'].get('indicators', [])).lower()]
        if final_docs:
            report.append("  Documents marked as complete/final:")
            for doc in final_docs[:5]:
                report.append(f"    • {doc['path']}")
        report.append("")
        
        # Recommendations
        report.append("RECOMMENDATIONS")
        report.append("-" * 40)
        
        total_candidates = len(self.backup_files) + len(strong_one_time) + len(final_docs)
        if total_candidates > 0:
            report.append(f"  1. Review and remove {total_candidates} high-priority cleanup candidates")
        
        if len(self.deployment_scripts) > 10:
            report.append(f"  2. Archive {len(self.deployment_scripts)} deployment scripts to deployment_history/")
        
        if len(self.test_scripts) > 20:
            report.append(f"  3. Move {len(self.test_scripts)} test scripts to proper test directories")
        
        if len(self.migration_scripts) > 0:
            report.append(f"  4. Document and archive {len(self.migration_scripts)} completed migration scripts")
        
        if len(self.outdated_docs) > 10:
            report.append(f"  5. Archive {len(self.outdated_docs)} outdated documents to docs/archive/")
        
        report.append("")
        report.append("  General cleanup strategy:")
        report.append("    • Create archive/ directory for historical records")
        report.append("    • Move completed one-time scripts to archive/scripts/")
        report.append("    • Move outdated docs to archive/docs/")
        report.append("    • Update .gitignore to prevent future accumulation")
        report.append("    • Implement naming convention to identify temporary files")
        report.append("")
        
        # Space Impact
        total_size = sum(f['size'] for f in self.backup_files)
        total_size += sum(s['size'] for s in self.one_time_scripts)
        total_size += sum(d['size'] for d in self.outdated_docs)
        
        report.append("SPACE IMPACT")
        report.append("-" * 40)
        report.append(f"  Total size of identified files: {total_size / (1024*1024):.2f} MB")
        report.append(f"  Potential space savings: {(total_size * 0.7) / (1024*1024):.2f} MB (70% removal estimate)")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def save_results(self, output_dir: str = "one_time_scan_results"):
        """Save scan results"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON data
        json_file = output_path / f"one_time_scan_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump({
                'scan_time': datetime.now().isoformat(),
                'backup_files': self.backup_files,
                'one_time_scripts': self.one_time_scripts,
                'outdated_docs': self.outdated_docs,
                'deployment_scripts': self.deployment_scripts,
                'test_scripts': self.test_scripts,
                'migration_scripts': self.migration_scripts,
                'setup_scripts': self.setup_scripts,
                'temp_scripts': self.temp_scripts,
                'summary': {
                    'total_backups': len(self.backup_files),
                    'total_one_time_scripts': len(self.one_time_scripts),
                    'total_outdated_docs': len(self.outdated_docs)
                }
            }, f, indent=2)
        
        # Save report
        report_file = output_path / f"one_time_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(self.generate_report())
        
        print(f"\nResults saved to:")
        print(f"  JSON: {json_file}")
        print(f"  Report: {report_file}")
        
        return str(report_file)


def main():
    """Main execution"""
    scanner = OneTimeUseScanner()
    scanner.scan_directory()
    report_file = scanner.save_results()
    
    # Print report
    print("\n" + scanner.generate_report())


if __name__ == "__main__":
    main()
