#!/usr/bin/env python3
"""
Comprehensive Linter Runner for Sophia AI Repository
Runs all syntax and linting checks across Python, TypeScript, and configuration files
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

class ComprehensiveLinter:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.aws_installed_tools = []
        self.python_files = []
        self.ts_files = []
        self.config_files = []
        self.results = {}

    def check_installations(self):
        """Check which linting tools are installed"""
        tools_status = {
            'python': {},
            'typescript': {},
            'config': {},
            'general': {}
        }

        # Python tools
        python_tools = ['flake8', 'bandit', 'safety', 'black']
        for tool in python_tools:
            tools_status['python'][tool] = self._is_tool_installed(tool)

        # TypeScript tools
        ts_tools = ['tsc', 'eslint']
        for tool in ts_tools:
            tools_status['typescript'][tool] = self._is_tool_installed(tool)

        # Config tools
        config_tools = ['yamllint', 'jsonlint', 'shellcheck']
        for tool in config_tools:
            tools_status['config'][tool] = self._is_tool_installed(tool)

        return tools_status

    def _is_tool_installed(self, tool: str) -> bool:
        """Check if a tool is installed and available"""
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def find_files(self):
        """Find all source files to check"""
        exclude_dirs = {
            '.venv', 'venv', '__pycache__', 'node_modules',
            '.git', '.pytest_cache', '.mypy_cache', '.next',
            'darwin-arm64', 'dist', 'build', '.vscode'
        }

        # Find Python files
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            for file in files:
                if file.endswith('.py'):
                    self.python_files.append(Path(root) / file)

        # Find TypeScript/JavaScript files (only in dashboard)
        dashboard_src = self.root_dir / 'apps' / 'sophia-dashboard' / 'src'
        if dashboard_src.exists():
            for root, dirs, files in os.walk(dashboard_src):
                for file in files:
                    if file.endswith(('.ts', '.tsx', '.js', '.jsx')):
                        self.ts_files.append(Path(root) / file)

        # Find configuration files
        config_extensions = ['.yml', '.yaml', '.json', '.sh', '.Dockerfile']
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
            for file in files:
                file_path = Path(root) / file
                if any(file.endswith(ext) for ext in config_extensions):
                    self.config_files.append(file_path)

        # Sort for consistency
        self.python_files.sort()
        self.ts_files.sort()
        self.config_files.sort()

    def run_python_lints(self, tools_status: Dict) -> Dict[str, Any]:
        """Run Python linting suite"""
        results = {
            'syntax': {},
            'style': {},
            'security': {},
            'dependencies': {},
            'available': tools_status['python']
        }

        if not self.python_files:
            results['status'] = 'no_files'
            return results

        # Import and use our Python linter
        try:
            sys.path.insert(0, str(self.root_dir / 'scripts'))
            from lint_python import PythonLinter

            linter = PythonLinter()
            linter.python_files = self.python_files  # Override file detection

            print("Running Python syntax checks...")
            results['syntax'] = linter.run_syntax_check()

            print("Running Python style checks...")
            results['style'] = linter.run_flake8()

            print("Running Python security scans...")
            results['security'] = linter.run_bandit()

            print("Running Python dependency scans...")
            results['dependencies'] = linter.run_safety_check()

            results['status'] = 'completed'

        except ImportError as e:
            results['status'] = f'import_error: {e}'
        except Exception as e:
            results['status'] = f'error: {e}'

        return results

    def run_typescript_lints(self, tools_status: Dict) -> Dict[str, Any]:
        """Run TypeScript/JavaScript linting"""
        results = {
            'eslint': {},
            'tsc': {},
            'available': tools_status['typescript'],
            'status': 'no_tools' if not any(tools_status['typescript'].values()) else 'completed'
        }

        if not self.ts_files:
            results['status'] = 'no_files'
            return results

        # Run ESLint
        if tools_status['typescript']['eslint']:
            try:
                cmd = ['npx', 'eslint', '--format=json'] + [str(f) for f in self.ts_files]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root_dir)

                if result.stdout:
                    eslint_output = json.loads(result.stdout)
                    errors = []
                    for file_result in eslint_output:
                        for message in file_result.get('messages', []):
                            relative_file = Path(file_result['filePath']).relative_to(self.root_dir)
                            errors.append({
                                'file': str(relative_file),
                                'line': message.get('line', 0),
                                'column': message.get('column', 0),
                                'rule': message.get('ruleId', ''),
                                'severity': message.get('severity', 'unknown'),
                                'message': message.get('message', ''),
                                'type': 'lint_error'
                            })

                    results['eslint'] = {
                        'errors': errors,
                        'file_count': len(self.ts_files),
                        'error_count': len(errors)
                    }
                else:
                    results['eslint'] = {
                        'errors': [],
                        'file_count': len(self.ts_files),
                        'error_count': 0
                    }
            except Exception as e:
                results['eslint'] = {'error': str(e), 'type': 'execution_error'}

        # Run TypeScript compiler (only type checking)
        if tools_status['typescript']['tsc']:
            try:
                # Check if there's a tsconfig.json in dashboard
                tsconfig_path = self.root_dir / 'apps' / 'sophia-dashboard' / 'tsconfig.json'
                cmd = ['npx', 'tsc', '--noEmit']
                if tsconfig_path.exists():
                    cmd.append('--project')
                    cmd.append(str(tsconfig_path))

                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root_dir)

                if result.stderr:
                    results['tsc'] = {'errors': result.stderr, 'type': 'compilation_errors'}
                else:
                    results['tsc'] = {'errors': None, 'type': 'success'}
            except Exception as e:
                results['tsc'] = {'error': str(e), 'type': 'execution_error'}

        return results

    def run_config_lints(self, tools_status: Dict) -> Dict[str, Any]:
        """Run configuration file linting"""
        results = {
            'yaml': {},
            'json': {},
            'shell': {},
            'available': tools_status['config'],
            'status': 'no_tools' if not any(tools_status['config'].values()) else 'completed'
        }

        if not self.config_files:
            results['status'] = 'no_files'
            return results

        # Categorize config files
        yaml_files = [f for f in self.config_files if f.name.endswith(('.yml', '.yaml'))]
        json_files = [f for f in self.config_files if f.name.endswith('.json')]
        shell_files = [f for f in self.config_files if f.name.endswith('.sh')]
        docker_files = [f for f in self.config_files if 'Dockerfile' in f.name]

        # Run yamllint
        if tools_status['config']['yamllint'] and yaml_files:
            try:
                cmd = ['yamllint'] + [str(f) for f in yaml_files]
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.root_dir)

                if result.stdout:
                    errors = []
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line and line.count(':') >= 3:
                            parts = line.split(':', 3)
                            relative_file = Path(parts[0]).relative_to(self.root_dir)
                            errors.append({
                                'file': str(relative_file),
                                'line': parts[1],
                                'column': parts[2],
                                'message': parts[3].strip(),
                                'type': 'yaml_error'
                            })

                    results['yaml'] = {
                        'errors': errors,
                        'file_count': len(yaml_files),
                        'error_count': len(errors)
                    }
                else:
                    results['yaml'] = {
                        'errors': [],
                        'file_count': len(yaml_files),
                        'error_count': 0
                    }
            except Exception as e:
                results['yaml'] = {'error': str(e), 'type': 'execution_error'}

        # Run shellcheck
        if tools_status['config']['shellcheck'] and shell_files:
            try:
                errors = []
                for shell_file in shell_files:
                    result = subprocess.run(
                        ['shellcheck', '-f', 'json1', str(shell_file)],
                        capture_output=True,
                        text=True,
                        cwd=self.root_dir
                    )

                    if result.stdout:
                        shellcheck_output = json.loads(result.stdout)
                        for issue in shellcheck_output.get('comments', []):
                            relative_file = Path(shell_file).relative_to(self.root_dir)
                            errors.append({
                                'file': str(relative_file),
                                'line': issue.get('line', 0),
                                'column': issue.get('column', 0),
                                'code': issue.get('code', ''),
                                'level': issue.get('level', 'unknown'),
                                'message': issue.get('message', ''),
                                'type': 'shell_error'
                            })

                results['shell'] = {
                    'errors': errors,
                    'file_count': len(shell_files),
                    'error_count': len(errors)
                }
            except Exception as e:
                results['shell'] = {'error': str(e), 'type': 'execution_error'}

        return results

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report across all linting types"""
        print("🔍 Sophia AI Comprehensive Linting Analysis")
        print("=" * 50)

        # Check installations
        tools_status = self.check_installations()

        print("\n📋 Tool Availability Check:")
        for category, tools in tools_status.items():
            installed = [t for t, avail in tools.items() if avail]
            missing = [t for t, avail in tools.items() if not avail]
            if installed:
                print(f"  ✅ {category.title()}: {', '.join(installed)}")
            if missing:
                print(f"  ❌ {category.title()}: Missing {', '.join(missing)}")

        # Find all files
        self.find_files()

        print(f"\n📂 Files Found:")
        print(f"  Python: {len(self.python_files)} files")
        print(f"  TypeScript: {len(self.ts_files)} files")
        print(f"  Config: {len(self.config_files)} files")

        results = {
            'timestamp': datetime.now().isoformat(),
            'tools_status': tools_status,
            'file_counts': {
                'python': len(self.python_files),
                'typescript': len(self.ts_files),
                'config': len(self.config_files)
            }
        }

        # Run all linting checks
        print("\n🔧 Running Python Lints...")
        results['python'] = self.run_python_lints(tools_status)

        print("\n🔧 Running TypeScript Lints...")
        results['typescript'] = self.run_typescript_lints(tools_status)

        print("\n🔧 Running Configuration Lints...")
        results['config'] = self.run_config_lints(tools_status)

        # Generate summary
        results['summary'] = self._generate_summary(results)

        return results

    def _generate_summary(self, results: Dict) -> Dict[str, Any]:
        """Generate summary statistics"""
        summary = {
            'total_files_checked': 0,
            'total_errors': 0,
            'total_warnings': 0,
            'files_with_errors': 0,
            'category_breakdown': {}
        }

        # Count files and issues
        for category, data in results.items():
            if category in ['python', 'typescript', 'config'] and isinstance(data, dict):
                if 'file_count' in data:
                    summary['total_files_checked'] += data.get('file_count', 0)
                elif 'style_errors' in data:
                    summary['total_files_checked'] += data.get('total', 0)

                # Count errors
                if 'syntax_errors' in data:
                    syntax_errors = [e for e in data['syntax_errors'] if e.get('type') == 'syntax_error']
                    summary['total_errors'] += len(syntax_errors)

                if 'style_errors' in data:
                    style_issues = [e for e in data['style_errors'] if e.get('type') != 'missing_dependency']
                    summary['total_errors'] += len(style_issues)

                if 'security_issues' in data:
                    security_issues = [e for e in data['security_issues'] if e.get('type') != 'missing_dependency']
                    summary['total_errors'] += len([s for s in security_issues if s.get('severity') == 'HIGH'])
                    summary['total_warnings'] += len([s for s in security_issues if s.get('severity') in ['MEDIUM', 'LOW']])

                if 'dependencies' in data and 'vulnerabilities' in data['dependencies']:
                    vuln_errors = [v for v in data['dependencies']['vulnerabilities'] if v.get('type') != 'missing_dependency']
                    summary['total_errors'] += len([v for v in vuln_errors if v.get('severity', '').lower() in ['high', 'critical']])
                    summary['total_warnings'] += len([v for v in vuln_errors if v.get('severity', '').lower() in ['medium', 'low']])

        summary['category_breakdown'] = {
            'syntax_errors': len([e for e in results['python']['syntax']['syntax_errors'] if e.get('type') == 'syntax_error']),
            'style_issues': len(results['python']['style'].get('style_errors', [])),
            'security_issues': len(results['python']['security'].get('security_issues', [])),
            'dependency_vulns': len([v for v in results['python']['dependencies']['vulnerabilities'] if v.get('type') != 'missing_dependency'])
        }

        return summary

    def _calculate_grade(self, summary: Dict) -> str:
        """Calculate code quality grade"""
        error_count = summary.get('total_errors', 0)

        if error_count == 0:
            return "A+ (Exceptional)"
        elif error_count < 10:
            return "A (Very Good)"
        elif error_count < 50:
            return "B (Good)"
        elif error_count < 100:
            return "C (Fair)"
        else:
            return "D (Poor)"

    def print_comprehensive_report(self, results: Dict[str, Any]):
        """Print the comprehensive report summary"""
        summary = results['summary']

        print("\n" + "="*70)
        print("🏆 SOPHIA AI - COMPREHENSIVE LINT REPORT")
        print("="*70)

        print(f"\n📊 OVERALL STATISTICS:")
        print(f"  Files Analyzed: {summary['total_files_checked']}")
        print(f"  Total Errors: {summary['total_errors']}")
        print(f"  Total Warnings: {summary['total_warnings']}")
        print(f"  Critical Issues: {summary['total_errors']}")

        print(f"\n📈 CATEGORY BREAKDOWN:")
        breakdown = summary['category_breakdown']
        print(f"  Syntax Errors: {breakdown['syntax_errors']}")
        print(f"  Style Issues: {breakdown['style_issues']}")
        print(f"  Security Issues: {breakdown['security_issues']}")
        print(f"  Dependency Vulnerabilities: {breakdown['dependency_vulns']}")

        # Grade the codebase
        if summary['total_errors'] == 0:
            print("\n🎉 GRADE: A+ (Exceptional)")
            print("   Code quality is excellent!")
        elif summary['total_errors'] < 10:
            print("\n✅ GRADE: A (Very Good)")
            print("   Minor issues found, overall good quality.")
        elif summary['total_errors'] < 50:
            print("\n⚠️  GRADE: B (Good)")
            print("   Some improvements needed.")
        elif summary['total_errors'] < 100:
            print("\n🟡 GRADE: C (Fair)")
            print("   Significant improvements needed.")
        else:
            print("\n🔴 GRADE: D (Poor)")
            print("   Code review recommended before production.")

        # Tool availability
        tools_status = results['tools_status']
        print("\n🔧 TOOL AVAILABILITY:")
        for category, tools in tools_status.items():
            installed = [t for t, avail in tools.items() if avail]
            if installed:
                print(f"  ✅ {category.title()}: Available - {', '.join(installed)}")

            missing = [t for t, avail in tools.items() if not avail]
            if missing:
                print(f"  ❌ {category.title()}: Install - {', '.join(missing)}")

def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Comprehensive linting for Sophia AI')
    parser.add_argument('--python-only', action='store_true', help='Run Python checks only')
    parser.add_argument('--typescript-only', action='store_true', help='Run TypeScript checks only')
    parser.add_argument('--config-only', action='store_true', help='Run configuration checks only')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save report to file')
    args = parser.parse_args()

    linter = ComprehensiveLinter()
    results = linter.generate_comprehensive_report()
    linter.print_comprehensive_report(results)

    if not args.no_save:
        # Save detailed report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_dir = Path('lint_reports')
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / f'comprehensive_lint_report_{timestamp}.json'

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Detailed report saved: {report_file}")

        # Save human-readable summary
        summary_file = report_dir / f'lint_summary_{timestamp}.txt'
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"Sophia AI Lint Report - {timestamp}\n")
            f.write("=" * 50)
            f.write(f"\nFiles Analyzed: {results['summary']['total_files_checked']}")
            f.write(f"\nErrors: {results['summary']['total_errors']}")
            f.write(f"\nWarnings: {results['summary']['total_warnings']}")
            f.write(f"\nGrade: {linter._calculate_grade(results['summary'])}")

        print(f"💾 Summary saved: {summary_file}")

    # Exit code based on errors
    if results['summary']['total_errors'] > 0:
        sys.exit(1)
    else:
        print("\n✅ All lint checks passed!")

if __name__ == "__main__":
    main()
