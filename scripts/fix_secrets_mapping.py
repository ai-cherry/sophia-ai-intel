#!/usr/bin/env python3
"""
Secrets Mapping Fix Script
==========================
Maps your actual GitHub secrets to the expected workflow format.
Constructs proper Redis URL from individual components.
"""

import os
import json
from datetime import datetime

def create_secrets_mapping():
    """Create mapping between actual secrets and workflow expectations"""
    
    # Your actual secret names (based on what you mentioned you set)
    actual_secrets = {
        "FLY_ORG_API": "FLY_TOKEN_PAY_READY",  # Map your name to workflow expectation
        "REDIS_API_KEY": "REDIS_API_KEY", 
        "REDIS_DATABASE_ENDPOINT": "REDIS_DATABASE_ENDPOINT",
        "REDIS_ACCOUNT_KEY": "REDIS_ACCOUNT_KEY",
        "LAMBDA_API_KEY": "LAMBDA_API_KEY", 
        "LAMBDA_PRIVATE_SSH_KEY": "LAMBDA_PRIVATE_SSH_KEY",
        "LAMBDA_PUBLIC_SSH_KEY": "LAMBDA_PUBLIC_SSH_KEY",
        "NEON_API_TOKEN": "NEON_API_TOKEN",
        "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
        "GITHUB_PAT": "GITHUB_PAT"
    }
    
    # Generate Redis URL construction logic
    redis_config = {
        "note": "Redis URL must be constructed from individual components",
        "format": "redis://:{REDIS_API_KEY}@{REDIS_DATABASE_ENDPOINT}:6379",
        "components": ["REDIS_API_KEY", "REDIS_DATABASE_ENDPOINT", "REDIS_ACCOUNT_KEY"],
        "workflow_expects": "REDIS_URL"
    }
    
    mapping_report = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "secrets_mapping_analysis", 
        "actual_vs_expected": actual_secrets,
        "redis_special_handling": redis_config,
        "required_workflow_updates": [
            "Replace secrets.FLY_TOKEN_PAY_READY with secrets.FLY_ORG_API",
            "Add Redis URL construction step using individual components",
            "Add Lambda Labs secrets mapping",
            "Ensure NEON_DATABASE_URL is properly mapped"
        ]
    }
    
    # Save mapping analysis
    with open("proofs/secrets/mapping_analysis.json", "w") as f:
        json.dump(mapping_report, f, indent=2)
    
    print("✅ Secrets mapping analysis created")
    return mapping_report

def generate_workflow_fixes():
    """Generate the workflow fixes needed"""
    
    fixes = {
        "fly_token_fix": {
            "current": "FLY_API_TOKEN: ${{ secrets.FLY_TOKEN_PAY_READY }}",
            "fixed": "FLY_API_TOKEN: ${{ secrets.FLY_ORG_API }}"
        },
        "redis_url_construction": {
            "description": "Add step to construct Redis URL from components",
            "step_addition": """
      - name: Construct Redis URL
        env:
          REDIS_API_KEY: ${{ secrets.REDIS_API_KEY }}
          REDIS_DATABASE_ENDPOINT: ${{ secrets.REDIS_DATABASE_ENDPOINT }}
        run: |
          REDIS_URL="redis://:${REDIS_API_KEY}@${REDIS_DATABASE_ENDPOINT}:6379"
          echo "REDIS_URL=${REDIS_URL}" >> $GITHUB_ENV
          echo "::add-mask::${REDIS_URL}"
"""
        },
        "lambda_secrets_addition": {
            "description": "Add Lambda Labs secrets to workflow",
            "env_additions": [
                "LAMBDA_API_KEY: ${{ secrets.LAMBDA_API_KEY }}",
                "LAMBDA_PRIVATE_SSH_KEY: ${{ secrets.LAMBDA_PRIVATE_SSH_KEY }}",
                "LAMBDA_PUBLIC_SSH_KEY: ${{ secrets.LAMBDA_PUBLIC_SSH_KEY }}"
            ]
        }
    }
    
    with open("proofs/secrets/workflow_fixes.json", "w") as f:
        json.dump(fixes, f, indent=2)
    
    print("✅ Workflow fixes generated")
    return fixes

if __name__ == "__main__":
    os.makedirs("proofs/secrets", exist_ok=True)
    
    print("🔐 Analyzing secrets mapping conflicts...")
    mapping = create_secrets_mapping()
    fixes = generate_workflow_fixes()
    
    print("\n📋 Analysis Summary:")
    print(f"- Found {len(mapping['actual_vs_expected'])} secret mappings to fix")
    print(f"- Redis requires special URL construction")
    print(f"- {len(fixes)} workflow modifications needed")
    
    print("\n✅ Run this script to see the exact changes needed for deploy_all.yml")
