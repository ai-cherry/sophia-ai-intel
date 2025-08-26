#!/usr/bin/env python3
"""
Script to replace placeholder values in secrets files with dummy base64-encoded values.
This allows deployment testing without real credentials.
"""

import base64
import os
import re
import time
import random
from pathlib import Path

def generate_dummy_base64():
    """Generate a dummy base64-encoded value."""
    dummy_value = f"dummy_value_for_testing_{int(time.time())}_{random.randint(1000, 999999)}"
    return base64.b64encode(dummy_value.encode('utf-8')).decode('utf-8')

def fix_secrets_file(file_path):
    """Fix a single secrets file by replacing placeholders with dummy values."""
    if not os.path.exists(file_path):
        print(f"⚠️  File {file_path} not found, skipping...")
        return False

    print(f"📝 Processing {file_path}...")

    # Create a backup
    backup_path = f"{file_path}.backup"
    with open(file_path, 'r') as f:
        original_content = f.read()

    with open(backup_path, 'w') as f:
        f.write(original_content)

    # Replace all placeholder values
    pattern = r'<BASE64_ENCODED_[^>]*>'
    modified_content = re.sub(pattern, generate_dummy_base64(), original_content)

    # Write the modified content back
    with open(file_path, 'w') as f:
        f.write(modified_content)

    print(f"✅ Fixed {file_path}")
    return True

def main():
    """Main function to fix all secrets files."""
    print("🔧 Fixing secrets files for deployment testing...")

    # List of secrets files to fix
    secret_files = [
        "secrets/database-secrets.yaml",
        "secrets/llm-secrets.yaml",
        "secrets/infrastructure-secrets.yaml",
        "secrets/business-secrets.yaml"
    ]

    fixed_count = 0
    for file_path in secret_files:
        if fix_secrets_file(file_path):
            fixed_count += 1

    print(f"🎉 Fixed {fixed_count} secrets files with dummy values for testing")
    print("📋 Note: These are dummy values for deployment testing only")
    print("🔒 In production, replace with real base64-encoded credentials")

if __name__ == "__main__":
    main()