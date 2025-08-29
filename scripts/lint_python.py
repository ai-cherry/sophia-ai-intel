#!/usr/bin/env python3
"""
Python Linting Script for Sophia AI Repo
Runs comprehensive syntax and linter checks
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import json

class PythonLinter:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.python_files = []
        self.results = {}

    def find_python_files(self) -> List[Path]:
        """Find all Python files excluding virtual environments and build artifacts"""
        exclude_dirs = {
            '.venv', 'venv', '__pycache__', 'node_modules',
            '.git', '.pytest_cache', '.mypy_cache', '.next',
            'darwin-arm64', 'dist', 'build', '.vscode'
        }

        python_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Remove excluded directories from dirs list to avoid traversing them
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

            for file in files:
                if file.endswith('.py'):
                    filepath = Path(root) / file
                    python_files.append(filepath)

        return sorted(python_files)

    def run_syntax_check(self, files: List[Path] = None) -> Dict[str, Any]:
        """Check Python syntax"""
        if files is None:
            files = self.python_files

        syntax_errors = []
        for file_path in files:
            try:
                subprocess.run(
                    [sys.executable, '-m', 'py_compile', str(file_path)],
                    capture_output=True,
                    check=True
                )
            except subprocess.CalledProcessError as e:
                # Extract filename from path
                filename = file_path.relative_to(self.root_dir)
                error_output = e.stderr.decode('utf-8').strip()
                syntax_errors.append({
                    'file': str(filename),
                    'error': error_output,
                    'type': 'syntax_error'
                })

        return {
            'syntax_errors': syntax_errors,
            'passed': len(files) - len(syntax_errors),
            'total': len(files)
        }

    def run_flake8(self, files: List[Path] = None) -> Dict[str, Any]:
        """Run flake8 style checking"""
        if files is None:
            files = self.python_files

        try:
            result = subprocess.run(
                ['flake8'] + [str(f) for f in files],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )

            if result.stdout:
                lines = result.stdout.strip().split('\n')
                errors = []
                for line in lines:
                    if ':' in line:
                        parts = line.split(':', 3)
                        if len(parts) >= 4:
                            errors.append({
                                'file': parts[0],
                                'line': parts[1],
                                'column': parts[2],
                                'message': parts[3].strip(),
                                'type': 'style_error'
                            })

                return {
                    'style_errors': errors,
                    'passed': len(files) - len(errors) if errors else len(files),
                    'total': len(files)
                }
            else:
                return {
                    'style_errors': [],
                    'passed': len(files),
                    'total': len(files)
                }

        except FileNotFoundError:
            return {
                'style_errors': [{'error': 'flake8 not installed', 'type': 'missing_dependency'}],
                'passed': 0,
                'total': len(files)
            }

    def run_bandit(self, files: List[Path] = None) -> Dict[str, Any]:
        """Run security vulnerability scanning with bandit"""
        if files is None:
            files = self.python_files

        try:
            result = subprocess.run(
                ['bandit', '-r', '-f', 'json'] + [str(f) for f in files],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )

            if result.stdout:
                bandit_output = json.loads(result.stdout)
                security_issues = []
                for issue in bandit_output.get('results', []):
                    security_issues.append({
                        'file': Path(issue['filename']).relative_to(self.root_dir),
                        'line': issue['line_number'],
                        'severity': issue['issue_severity'],
                        'confidence': issue['issue_confidence'],
                        'cwe': issue.get('issue_cwe', {}).get('id', ''),
                        'message': issue['issue_text'],
                        'type': 'security_issue'
                    })

                return {
                    'security_issues': security_issues,
                    'passed': len(files) - len(security_issues),
                    'total': len(files)
                }
            else:
                return {
                    'security_issues': [],
                    'passed': len(files),
                    'total': len(files)
                }

        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'security_issues': [{'error': 'bandit not installed or output error', 'type': 'missing_dependency'}],
                'passed': 0,
                'total': len(files)
            }

    def run_safety_check(self) -> Dict[str, Any]:
        """Run safety check for insecure dependencies"""
        try:
            result = subprocess.run(
                ['safety', 'check', '--output', 'json'],
                capture_output=True,
                text=True,
                cwd=self.root_dir
            )

            if result.stdout:
                safety_output = json.loads(result.stdout)
                vulnerabilities = []

                for vuln in safety_output:
                    vulnerabilities.append({
                        'package': vuln.get('package', 'unknown'),
                        'version': vuln.get('installed_version', 'unknown'),
                        'cve': vuln.get('cve', ''),
                        'severity': vuln.get('severity', 'unknown'),
                        'description': vuln.get('vulnerability', ''),
                        'type': 'dependency_vulnerability'
                    })

                return {
                    'vulnerabilities': vulnerabilities,
                    'total_packages': len(vulnerabilities),
                    'severity_levels': self._categorize_vulnerabilities(vulnerabilities)
                }
            else:
                return {
                    'vulnerabilities': [],
                    'total_packages': 0,
                    'severity_levels': {'high': 0, 'medium': 0, 'low': 0}
                }

        except (FileNotFoundError, json.JSONDecodeError):
            return {
                'vulnerabilities': [{'error': 'safety not installed', 'type': 'missing_dependency'}],
                'total_packages': 0,
                'severity_levels': {'high': 0, 'medium': 0, 'low': 0}
            }

    def _categorize_vulnerabilities(self, vulnerabilities: List[Dict]) -> Dict[str, int]:
        """Categorize vulnerabilities by severity"""
        levels = {'high': 0, 'medium': 0, 'low': 0, 'unknown': 0}

        for vuln in vulnerabilities:
            severity = vuln.get('severity', 'unknown').lower()
            if severity in levels:
                levels[severity] += 1
            else:
                levels['unknown'] += 1

        return levels

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive linting report"""
        self.python_files = self.find_python_files()

        print(f"Found {len(self.python_files)} Python files to check")

        results = {}

        # Run all checks
        print("1. Running syntax checks...")
        results['syntax'] = self.run_syntax_check()
        print(f"   - Syntax: {results['syntax']['passed']}/{results['syntax']['total']} passed")

        print("2. Running style checks...")
        results['style'] = self.run_flake8()
        print(f"   - Style: {results['style']['passed']}/{results['style']['total']} passed")

        print("3. Running security scans...")
        results['security'] = self.run_bandit()
        print(f"   - Security: {results['security']['passed']}/{results['security']['total']} passed")

        print("4. Running dependency scans...")
        results['dependencies'] = self.run_safety_check()
        print(f"   - Dependencies: {len([v for v in results['dependencies']['vulnerabilities'] if v.get('type') != 'missing_dependency'])} vulnerabilities found")

        return results

    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print a concise summary"""
        total_files = len(self.python_files)
        total_errors = 0
        total_warnings = 0
        critical_issues = 0

        # Count errors
        if results['syntax']['syntax_errors']:
            syntax_errors = [e for e in results['syntax']['syntax_errors'] if e.get('type') == 'syntax_error']
            total_errors += len(syntax_errors)
            critical_issues += 1 if syntax_errors else 0

        if results['style']['style_errors']:
            total_errors += len(results['style']['style_errors'])

        if results['security']['security_issues']:
            security_high = [s for s in results['security']['security_issues'] if s.get('severity') == 'HIGH']
            total_errors += len(security_high)
            critical_issues += len(security_high)

        dep_vulns = len([v for v in results['dependencies']['vulnerabilities']
                        if v.get('type') != 'missing_dependency'])
        total_errors += dep_vulns

        print("\n" + "="*60)
        print("SOPHIA AI - PYTHON LINTING SUMMARY")
        print("="*60)
        print(f"Total Python Files: {total_files}")
        print(f"Total Issues Found: {total_errors}")
        print(f"Critical Issues: {critical_issues}")
        print("-" * 30)
        print("BREAKDOWN:")
        print(f"  Syntax Errors: {len([e for e in results['syntax']['syntax_errors'] if e.get('type') == 'syntax_error'])}")
        print(f"  Style Issues: {len(results['style']['style_errors'])}")
        print(f"  Security Issues: {len(results['security']['security_issues'])}")
        print(f"  Dependency Vulnerabilities: {dep_vulns}")
        print("-" * 30)

        if critical_issues > 0:
            print("⚠️  CRITICAL: Issues detected that may break the application")
        elif total_errors > 0:
            print("✅ No critical issues, but some improvements needed")
        else:
            print("🎉 All checks passed! Code quality is excellent")

        return total_errors, critical_issues

def main():
    """Main execution"""
    print("🔧 Sophia AI Python Linting Suite")
    print("=" * 40)

    # Check if we're in the right directory
    if not Path('.flake8').exists() and not Path('scripts').exists():
        print("Error: Please run from the Sophia AI root directory")
        sys.exit(1)

    parser = argparse.ArgumentParser(description='Python linting for Sophia AI')
    parser.add_argument('--fix', action='store_true', help='Attempt automatic fixes')
    args = parser.parse_args()

    linter = PythonLinter()

    try:
        results = linter.generate_report()
        total_errors, critical_issues = linter.print_summary(results)

        # Generate timestamped report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path('lint_reports')
        report_dir.mkdir(exist_ok=True)

        # Save detailed report
        report_file = report_dir / f'python_lint_report_{timestamp}.json'
        results['generated_at'] = datetime.now().isoformat()
        results['summary'] = {
            'total_files': len(linter.python_files),
            'total_errors': total_errors,
            'critical_issues': critical_issues
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\nDetailed report saved to: {report_file}")
        print("Run './scripts/run_linter_checks.py' for full project linting")

        # Exit with appropriate code
        if critical_issues > 0:
            sys.exit(1)  # Critical errors found

    except KeyboardInterrupt:
        print("\nLinting interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nError during linting: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
