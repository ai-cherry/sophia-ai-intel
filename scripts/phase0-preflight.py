#!/usr/bin/env python3
"""
Phase 0: Pre-flight checks and environment validation
"""

import os
import sys
from pathlib import Path
from datetime import datetime

def validate_environment():
    """Validate environment and secrets"""
    
    print("=" * 80)
    print("SOPHIA AI REPOSITORY UPGRADE - PHASE 0: PRE-FLIGHT CHECKS")
    print("=" * 80)
    print(f"\nTimestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {os.getcwd()}")
    
    # 1. Verify repository root
    repo_root = Path("/Users/lynnmusil/sophia-ai-intel-1")
    current_dir = Path.cwd()
    
    print("\n1. Repository Root Validation")
    print("-" * 40)
    if current_dir == repo_root:
        print(f"✅ Confirmed at repository root: {repo_root}")
    else:
        print(f"❌ Not at repository root. Current: {current_dir}, Expected: {repo_root}")
        return False
    
    # 2. Check .env file
    env_file = repo_root / ".env"
    print("\n2. Environment File Check")
    print("-" * 40)
    
    if env_file.exists():
        print(f"✅ .env file exists at: {env_file}")
        file_size = env_file.stat().st_size
        print(f"   File size: {file_size} bytes")
    else:
        print(f"❌ .env file not found at: {env_file}")
        return False
    
    # 3. Read and validate environment variables
    print("\n3. Environment Variables Validation")
    print("-" * 40)
    
    env_vars = {}
    critical_vars = []
    optional_vars = []
    
    try:
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    try:
                        key = line.split('=', 1)[0].strip()
                        if key and key.isidentifier():
                            env_vars[key] = True
                    except:
                        # Skip malformed lines
                        pass
        
        # Critical environment variables
        critical_keys = [
            'OPENAI_API_KEY',
            'POSTGRES_URL',
            'NEON_API_KEY',
            'GITHUB_TOKEN',
            'LAMBDA_API_KEY'
        ]
        
        # Check for Fly token (either FLY_API_TOKEN or FLY_ORG_TOKEN or FLY_ORG_API)
        fly_keys = ['FLY_API_TOKEN', 'FLY_ORG_TOKEN', 'FLY_ORG_API']
        
        print("\nCritical Variables:")
        for key in critical_keys:
            if key in env_vars:
                critical_vars.append(key)
                print(f"  ✅ {key} - Present")
            else:
                print(f"  ❌ {key} - Missing")
        
        print("\nFly.io Token Status:")
        fly_found = False
        for key in fly_keys:
            if key in env_vars:
                print(f"  ✅ {key} - Present")
                fly_found = True
                break
        if not fly_found:
            print(f"  ⚠️  No Fly token found (checked: {', '.join(fly_keys)})")
        
        # Other important variables
        other_keys = [
            'ANTHROPIC_API_KEY',
            'REDIS_URL',
            'QDRANT_URL',
            'PORTKEY_API_KEY',
            'HUBSPOT_API_KEY',
            'SLACK_BOT_TOKEN'
        ]
        
        print("\nOther Important Variables:")
        for key in other_keys:
            if key in env_vars:
                optional_vars.append(key)
                print(f"  ✅ {key} - Present")
            else:
                print(f"  ⚠️  {key} - Not found")
        
        # Summary statistics
        print(f"\nSummary:")
        print(f"  Total environment variables found: {len(env_vars)}")
        print(f"  Critical variables present: {len(critical_vars)}/{len(critical_keys)}")
        print(f"  Fly.io token available: {'Yes' if fly_found else 'No'}")
        print(f"  Other variables present: {len(optional_vars)}/{len(other_keys)}")
        
    except Exception as e:
        print(f"❌ Error reading .env file: {e}")
        return False
    
    # 4. List all available environment variable keys
    print("\n4. All Available Environment Variables")
    print("-" * 40)
    
    if env_vars:
        sorted_keys = sorted(env_vars.keys())
        # Display in columns for better readability
        cols = 3
        keys_per_col = len(sorted_keys) // cols + (1 if len(sorted_keys) % cols else 0)
        
        for i in range(keys_per_col):
            row = []
            for j in range(cols):
                idx = i + j * keys_per_col
                if idx < len(sorted_keys):
                    row.append(f"{sorted_keys[idx]:25}")
            print("  " + "".join(row))
    
    # 5. Validation Report
    print("\n" + "=" * 80)
    print("VALIDATION REPORT")
    print("=" * 80)
    
    validation_passed = True
    
    print("\n✅ PASSED:")
    print("  - Repository root confirmed")
    print("  - .env file accessible")
    print(f"  - {len(env_vars)} environment variables loaded")
    
    if len(critical_vars) < len(critical_keys):
        validation_passed = False
        missing = set(critical_keys) - set(critical_vars)
        print("\n⚠️  WARNINGS:")
        print(f"  - Missing critical variables: {', '.join(missing)}")
    
    if not fly_found:
        print("\n⚠️  NOTES:")
        print("  - Fly.io token not found (may not be needed if migrated)")
    
    print("\n" + "=" * 80)
    print("PHASE 0 PRE-FLIGHT CHECK COMPLETE")
    print("=" * 80)
    
    if validation_passed:
        print("\n✅ Pre-flight checks PASSED - Environment ready for Phase 1")
    else:
        print("\n⚠️  Pre-flight checks completed with warnings")
    
    return validation_passed

if __name__ == "__main__":
    success = validate_environment()
    sys.exit(0 if success else 1)