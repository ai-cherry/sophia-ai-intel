#!/usr/bin/env python3
"""
Fly.io Reference Cleanup Script
================================

Systematically removes all Fly.io references from the Sophia AI codebase
and replaces them with appropriate Lambda Labs/Kubernetes references.

This addresses the 226+ HIGH priority Fly.io references found during the audit.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

class ReplacementStrategy(Enum):
    REMOVE_LINE = "REMOVE_LINE"
    REPLACE_URL = "REPLACE_URL"
    REPLACE_TEXT = "REPLACE_TEXT"
    UPDATE_CONFIG = "UPDATE_CONFIG"

@dataclass
class FlyioReplacement:
    pattern: str
    replacement: str
    strategy: ReplacementStrategy
    description: str

class FlyioCleanupProcessor:
    def __init__(self, root_path: str = "."):
        self.root_path = Path(root_path)
        self.replacements_made = 0
        self.files_modified = 0

        # Define replacement patterns
        self.replacements = [
            # URL replacements
            FlyioReplacement(
                pattern=r'https://sophiaai-[a-zA-Z0-9-]+-v2\.fly\.dev',
                replacement='http://localhost:{port}',
                strategy=ReplacementStrategy.REPLACE_URL,
                description='Replace Fly.io service URLs with localhost references'
            ),

            # App name replacements
            FlyioReplacement(
                pattern=r'sophiaai-[a-zA-Z0-9-]+-v2',
                replacement='sophia-{service}',
                strategy=ReplacementStrategy.REPLACE_TEXT,
                description='Replace Fly.io app names with Docker service names'
            ),

            # Fly.io specific terms
            FlyioReplacement(
                pattern=r'fly\.io',
                replacement='lambda-labs',
                strategy=ReplacementStrategy.REPLACE_TEXT,
                description='Replace fly.io references with lambda-labs'
            ),

            # Flyctl commands
            FlyioReplacement(
                pattern=r'flyctl',
                replacement='docker-compose',
                strategy=ReplacementStrategy.REPLACE_TEXT,
                description='Replace flyctl commands with docker-compose'
            ),

            # Fly.toml references
            FlyioReplacement(
                pattern=r'fly\.toml',
                replacement='docker-compose.yml',
                strategy=ReplacementStrategy.REPLACE_TEXT,
                description='Replace fly.toml with docker-compose.yml'
            ),

            # Deployment commands
            FlyioReplacement(
                pattern=r'flyctl deploy',
                replacement='docker-compose up -d',
                strategy=ReplacementStrategy.REPLACE_TEXT,
                description='Replace flyctl deploy with docker-compose up'
            ),

            # Health check URLs
            FlyioReplacement(
                pattern=r'https://sophiaai-[a-zA-Z0-9-]+-v2\.fly\.dev/healthz',
                replacement='/healthz',
                strategy=ReplacementStrategy.REPLACE_URL,
                description='Replace Fly.io health URLs with relative paths'
            ),

            # API endpoint URLs
            FlyioReplacement(
                pattern=r'https://sophiaai-[a-zA-Z0-9-]+-v2\.fly\.dev/api/',
                replacement='/api/',
                strategy=ReplacementStrategy.REPLACE_URL,
                description='Replace Fly.io API URLs with relative paths'
            ),

            # Documentation references
            FlyioReplacement(
                pattern=r'Fly\.io.*platform',
                replacement='Lambda Labs GPU infrastructure',
                strategy=ReplacementStrategy.REPLACE_TEXT,
                description='Replace Fly.io platform references'
            ),

            # Configuration references
            FlyioReplacement(
                pattern=r'flyctl secrets set',
                replacement='docker-compose exec',
                strategy=ReplacementStrategy.REPLACE_TEXT,
                description='Replace flyctl secrets with docker-compose exec'
            ),
        ]

    def should_process_file(self, file_path: Path) -> bool:
        """Determine if a file should be processed for Fly.io cleanup."""

        # Skip certain files and directories
        skip_patterns = [
            '.git',
            '__pycache__',
            'node_modules',
            '.next',
            'backups',
            'proofs',
            'darwin-arm64',
            'flyio-cleanup.py',  # Don't modify this script itself
            'phase4-legacy-audit.py'  # Don't modify the audit script
        ]

        file_str = str(file_path)
        if any(skip in file_str for skip in skip_patterns):
            return False

        # Only process relevant file types
        relevant_extensions = ['.py', '.ts', '.js', '.yml', '.yaml', '.json', '.md', '.sh', '.conf']
        return file_path.suffix.lower() in relevant_extensions

    def process_file(self, file_path: Path) -> bool:
        """Process a single file for Fly.io references."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                original_content = f.read()

            modified_content = original_content
            replacements_in_file = 0

            for replacement in self.replacements:
                if replacement.strategy == ReplacementStrategy.REPLACE_TEXT:
                    # Use regex to find and replace
                    pattern = re.compile(re.escape(replacement.pattern), re.IGNORECASE)
                    if pattern.search(modified_content):
                        modified_content = pattern.sub(replacement.replacement, modified_content)
                        replacements_in_file += 1

                elif replacement.strategy == ReplacementStrategy.REPLACE_URL:
                    # Use regex for URL patterns
                    pattern = re.compile(replacement.pattern, re.IGNORECASE)
                    if pattern.search(modified_content):
                        modified_content = pattern.sub(replacement.replacement, modified_content)
                        replacements_in_file += 1

            # Write back if changes were made
            if replacements_in_file > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(modified_content)
                self.replacements_made += replacements_in_file
                self.files_modified += 1
                print(f"✅ Modified {file_path}: {replacements_in_file} replacements")
                return True

            return False

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False

    def cleanup_flyio_files(self) -> None:
        """Remove actual Fly.io configuration files."""
        flyio_files = [
            'fly.toml',
            'fly.toml.backup'
        ]

        files_removed = 0
        for flyio_file in flyio_files:
            file_path = self.root_path / flyio_file
            if file_path.exists():
                file_path.unlink()
                files_removed += 1
                print(f"🗑️  Removed {flyio_file}")

        # Also check for fly.toml files in service directories
        for service_dir in self.root_path.rglob('services/*/fly.toml'):
            service_dir.unlink()
            files_removed += 1
            print(f"🗑️  Removed {service_dir}")

        print(f"Removed {files_removed} Fly.io configuration files")

    def process_all_files(self) -> None:
        """Process all relevant files for Fly.io cleanup."""
        print("🔍 Starting Fly.io reference cleanup...")

        files_processed = 0
        for file_path in self.root_path.rglob('*'):
            if file_path.is_file() and self.should_process_file(file_path):
                self.process_file(file_path)
                files_processed += 1

        print(f"Processed {files_processed} files")
        print(f"Modified {self.files_modified} files")
        print(f"Made {self.replacements_made} total replacements")

    def generate_cleanup_report(self) -> str:
        """Generate a cleanup report."""
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("FLY.IO CLEANUP REPORT")
        report_lines.append("=" * 60)
        report_lines.append(f"Files processed: {self.files_modified}")
        report_lines.append(f"Replacements made: {self.replacements_made}")
        report_lines.append("")

        report_lines.append("REPLACEMENT PATTERNS APPLIED:")
        report_lines.append("-" * 40)
        for replacement in self.replacements:
            report_lines.append(f"• {replacement.pattern} → {replacement.replacement}")
            report_lines.append(f"  {replacement.description}")

        report_lines.append("")
        report_lines.append("FILES REMOVED:")
        report_lines.append("-" * 40)
        report_lines.append("• fly.toml files")
        report_lines.append("• fly.toml.backup files")
        report_lines.append("• Service-level fly.toml files")

        return "\n".join(report_lines)

    def save_report(self, output_path: str = "flyio-cleanup-report.txt") -> None:
        """Save the cleanup report."""
        report = self.generate_cleanup_report()
        with open(output_path, 'w') as f:
            f.write(report)
        print(f"Report saved to: {output_path}")

def main():
    """Main execution function."""
    print("🧹 Starting comprehensive Fly.io cleanup...")

    processor = FlyioCleanupProcessor()

    # First, remove Fly.io configuration files
    processor.cleanup_flyio_files()

    # Then, process all code files for references
    processor.process_all_files()

    # Generate and display report
    report = processor.generate_cleanup_report()
    print(report)

    # Save report
    processor.save_report()

    print("\n🎉 Fly.io cleanup completed!")
    print("Next steps:")
    print("1. Review the changes made")
    print("2. Test the application functionality")
    print("3. Update any hardcoded URLs in configuration")
    print("4. Run the legacy audit script again to verify")

if __name__ == "__main__":
    main()