#!/usr/bin/env python3
"""
Phase 4 Legacy Reference Audit Script
=====================================

Systematically identifies and reports all legacy references, conflicts,
and inconsistencies in the Sophia AI codebase that need to be resolved
before production deployment.

This script addresses the critical first task of Phase 4:
"Verify complete elimination of all legacy references and conflicts"
"""

import os
import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class IssueSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class AuditIssue:
    file_path: str
    line_number: int
    issue_type: str
    severity: IssueSeverity
    description: str
    recommendation: str
    context: str = ""

class LegacyReferenceAuditor:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.issues: List[AuditIssue] = []

        # Patterns for legacy references
        self.legacy_patterns = {
            'fly_io': [
                re.compile(r'fly\.toml', re.IGNORECASE),
                re.compile(r'flyctl', re.IGNORECASE),
                re.compile(r'fly\.io', re.IGNORECASE),
                re.compile(r'sophiaai-.*-v2', re.IGNORECASE),  # Old Fly.io naming
            ],
            'deprecated_services': [
                re.compile(r'fly\.io.*platform', re.IGNORECASE),
                re.compile(r'legacy.*deployment', re.IGNORECASE),
                re.compile(r'deprecated', re.IGNORECASE),
            ],
            'conflicting_configs': [
                re.compile(r'multiple.*deployment.*method', re.IGNORECASE),
                re.compile(r'conflicting.*configuration', re.IGNORECASE),
            ],
            'missing_files': [
                re.compile(r'docker-compose\.yml.*missing', re.IGNORECASE),
                re.compile(r'file.*not.*found', re.IGNORECASE),
            ]
        }

    def audit_file(self, file_path: Path) -> None:
        """Audit a single file for legacy references and issues."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                self._check_line_for_issues(file_path, line_num, line)

        except Exception as e:
            self.issues.append(AuditIssue(
                file_path=str(file_path),
                line_number=0,
                issue_type="FILE_READ_ERROR",
                severity=IssueSeverity.MEDIUM,
                description=f"Could not read file: {e}",
                recommendation="Check file permissions and encoding"
            ))

    def _check_line_for_issues(self, file_path: Path, line_num: int, line: str) -> None:
        """Check a line for various types of issues."""

        # Check for Fly.io references
        for pattern in self.legacy_patterns['fly_io']:
            if pattern.search(line):
                self.issues.append(AuditIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="FLY_IO_REFERENCE",
                    severity=IssueSeverity.HIGH,
                    description="Found Fly.io reference in current codebase",
                    recommendation="Remove Fly.io references and update to Lambda Labs/Kubernetes",
                    context=line.strip()
                ))

        # Check for deprecated service references
        for pattern in self.legacy_patterns['deprecated_services']:
            if pattern.search(line):
                self.issues.append(AuditIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="DEPRECATED_SERVICE",
                    severity=IssueSeverity.MEDIUM,
                    description="Found reference to deprecated service or deployment method",
                    recommendation="Update to current deployment architecture",
                    context=line.strip()
                ))

        # Check for conflicting configurations
        for pattern in self.legacy_patterns['conflicting_configs']:
            if pattern.search(line):
                self.issues.append(AuditIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="CONFLICTING_CONFIG",
                    severity=IssueSeverity.CRITICAL,
                    description="Found reference to conflicting deployment configurations",
                    recommendation="Resolve configuration conflicts",
                    context=line.strip()
                ))

    def check_missing_critical_files(self) -> None:
        """Check for missing critical files that should exist."""

        # Check for main docker-compose.yml
        docker_compose_path = self.root_path / "docker-compose.yml"
        if not docker_compose_path.exists():
            self.issues.append(AuditIssue(
                file_path="docker-compose.yml",
                line_number=0,
                issue_type="MISSING_CRITICAL_FILE",
                severity=IssueSeverity.CRITICAL,
                description="Main docker-compose.yml file is missing",
                recommendation="Create unified docker-compose.yml for all services"
            ))

        # Check for nginx configuration
        nginx_conf_path = self.root_path / "nginx.conf"
        if not nginx_conf_path.exists():
            self.issues.append(AuditIssue(
                file_path="nginx.conf",
                line_number=0,
                issue_type="MISSING_CRITICAL_FILE",
                severity=IssueSeverity.HIGH,
                description="nginx.conf file is missing",
                recommendation="Create production nginx configuration"
            ))

    def check_service_consistency(self) -> None:
        """Check for service definition consistency across configurations."""

        # Check if all MCP services have consistent configurations
        mcp_services = ['mcp-agents', 'mcp-context', 'mcp-github', 'mcp-hubspot',
                       'mcp-lambda', 'mcp-research', 'mcp-business']

        for service in mcp_services:
            service_path = self.root_path / "services" / service
            if service_path.exists():
                # Check for fly.toml (should not exist)
                fly_toml = service_path / "fly.toml"
                if fly_toml.exists():
                    self.issues.append(AuditIssue(
                        file_path=str(fly_toml),
                        line_number=0,
                        issue_type="LEGACY_FILE_EXISTS",
                        severity=IssueSeverity.CRITICAL,
                        description=f"Legacy fly.toml found in {service} service",
                        recommendation="Remove fly.toml and migrate to Docker/Kubernetes"
                    ))

    def audit_all_files(self) -> None:
        """Audit all relevant files in the project."""

        # File extensions to check
        extensions = ['*.py', '*.ts', '*.js', '*.yml', '*.yaml', '*.json', '*.md', '*.sh', '*.conf']

        for ext in extensions:
            for file_path in self.root_path.rglob(ext):
                # Skip certain directories
                if any(skip in str(file_path) for skip in [
                    '.git', '__pycache__', 'node_modules', '.next',
                    'backups', 'proofs', 'darwin-arm64'
                ]):
                    continue

                self.audit_file(file_path)

        # Check for missing critical files
        self.check_missing_critical_files()

        # Check service consistency
        self.check_service_consistency()

    def generate_report(self) -> str:
        """Generate a comprehensive audit report."""

        # Group issues by severity
        issues_by_severity = {}
        for issue in self.issues:
            severity = issue.severity.value
            if severity not in issues_by_severity:
                issues_by_severity[severity] = []
            issues_by_severity[severity].append(issue)

        # Generate report
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("SOPHIA AI PHASE 4 - LEGACY REFERENCE AUDIT REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {Path(__file__).name}")
        report_lines.append("")

        # Summary
        total_issues = len(self.issues)
        report_lines.append(f"TOTAL ISSUES FOUND: {total_issues}")
        report_lines.append("")

        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = len(issues_by_severity.get(severity, []))
            report_lines.append(f"{severity}: {count} issues")
        report_lines.append("")

        # Detailed issues
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            issues = issues_by_severity.get(severity, [])
            if issues:
                report_lines.append(f"{severity} ISSUES:")
                report_lines.append("-" * 40)

                for issue in issues:
                    report_lines.append(f"File: {issue.file_path}:{issue.line_number}")
                    report_lines.append(f"Type: {issue.issue_type}")
                    report_lines.append(f"Description: {issue.description}")
                    report_lines.append(f"Recommendation: {issue.recommendation}")
                    if issue.context:
                        report_lines.append(f"Context: {issue.context}")
                    report_lines.append("")

        # Recommendations summary
        report_lines.append("=" * 80)
        report_lines.append("RECOMMENDATIONS SUMMARY")
        report_lines.append("=" * 80)

        if total_issues == 0:
            report_lines.append("✅ No legacy references or conflicts found!")
            report_lines.append("✅ System is ready for Phase 4 verification.")
        else:
            report_lines.append("1. Address CRITICAL issues immediately")
            report_lines.append("2. Review HIGH priority issues before deployment")
            report_lines.append("3. Clean up MEDIUM and LOW priority issues")
            report_lines.append("4. Re-run this audit after fixes")

        return "\n".join(report_lines)

    def save_report(self, output_path: str = "phase4-legacy-audit-report.txt") -> None:
        """Save the audit report to a file."""
        report = self.generate_report()
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_path}")

def main():
    """Main execution function."""
    print("🔍 Starting Phase 4 Legacy Reference Audit...")
    print("This may take a few minutes...")

    auditor = LegacyReferenceAuditor()

    # Run comprehensive audit
    auditor.audit_all_files()

    # Generate and display report
    report = auditor.generate_report()
    print(report)

    # Save report
    auditor.save_report()

    # Exit with appropriate code
    critical_issues = [i for i in auditor.issues if i.severity == IssueSeverity.CRITICAL]
    if critical_issues:
        print(f"\n❌ Found {len(critical_issues)} CRITICAL issues that must be resolved!")
        exit(1)
    else:
        print("\n✅ No critical legacy issues found!")
        exit(0)

if __name__ == "__main__":
    main()