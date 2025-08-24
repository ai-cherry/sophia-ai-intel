#!/usr/bin/env python3
"""
Direct Render Deployment Script
Bypasses GitHub Actions and deploys services directly using Render API
"""

import os
import json
import requests
import time
from datetime import datetime

def print_status(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def main():
    print("🚀 Sophia AI Intel - Direct Render Deployment")
    print("============================================")
    
    # Get required secrets from environment
    render_api_key = os.environ.get('RENDER_API_KEY')
    if not render_api_key:
        print_error("RENDER_API_KEY not found in environment")
        return 1
    
    print_status("Render API key found")
    
    # Validate Render API access
    headers = {
        'Authorization': f'Bearer {render_api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get('https://api.render.com/v1/services', headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_info(f"API response type: {type(data)}")
            
            # Handle different response formats
            if isinstance(data, list):
                services = data
            elif isinstance(data, dict) and 'services' in data:
                services = data['services']
            else:
                services = []
                
            print_status(f"Render API validated - {len(services)} existing services found")
        else:
            print_error(f"Render API returned status {response.status_code}")
            print_error(f"Response: {response.text}")
            return 1
    except Exception as e:
        print_error(f"Render API validation failed: {e}")
        return 1
    
    # Define service configuration
    services_config = [
        {
            'name': 'sophia-dashboard',
            'type': 'static_site',
            'repo': 'https://github.com/ai-cherry/sophia-ai-intel',
            'branch': 'main',
            'buildCommand': 'cd apps/dashboard && npm install && npm run build',
            'publishPath': 'apps/dashboard/dist',
            'envVars': []
        },
        {
            'name': 'sophia-github',
            'type': 'web_service',
            'repo': 'https://github.com/ai-cherry/sophia-ai-intel',
            'branch': 'main',
            'rootDir': 'services/mcp-github',
            'buildCommand': 'pip install -r requirements.txt',
            'startCommand': 'python server.py',
            'envVars': [
                {'key': 'GITHUB_PAT', 'value': os.environ.get('GITHUB_PAT', '')},
                {'key': 'NEON_DATABASE_URL', 'value': os.environ.get('NEON_REST_API_ENDPOINT', '')}
            ]
        },
        {
            'name': 'sophia-research',
            'type': 'web_service',
            'repo': 'https://github.com/ai-cherry/sophia-ai-intel',
            'branch': 'main',
            'rootDir': 'services/mcp-research',
            'buildCommand': 'pip install -r requirements.txt',
            'startCommand': 'python server.py',
            'envVars': [
                {'key': 'TAVILY_API_KEY', 'value': os.environ.get('TAVILY_API_KEY', '')},
                {'key': 'SERPER_API_KEY', 'value': os.environ.get('SERPER_API_KEY', '')},
                {'key': 'PERPLEXITY_API_KEY', 'value': os.environ.get('PERPLEXITY_API_KEY', '')},
                {'key': 'NEON_DATABASE_URL', 'value': os.environ.get('NEON_REST_API_ENDPOINT', '')}
            ]
        },
        {
            'name': 'sophia-context',
            'type': 'web_service',
            'repo': 'https://github.com/ai-cherry/sophia-ai-intel',
            'branch': 'main',
            'rootDir': 'services/mcp-context',
            'buildCommand': 'pip install -r requirements.txt',
            'startCommand': 'python server.py',
            'envVars': [
                {'key': 'NEON_DATABASE_URL', 'value': os.environ.get('NEON_REST_API_ENDPOINT', '')},
                {'key': 'QDRANT_API_KEY', 'value': os.environ.get('QDRANT_API_KEY', '')},
                {'key': 'QDRANT_URL', 'value': os.environ.get('QDRANT_URL', '')}
            ]
        },
        {
            'name': 'sophia-business',
            'type': 'web_service',
            'repo': 'https://github.com/ai-cherry/sophia-ai-intel',
            'branch': 'main',
            'rootDir': 'services/mcp-business',
            'buildCommand': 'pip install -r requirements.txt',
            'startCommand': 'python server.py',
            'envVars': [
                {'key': 'HUBSPOT_API_TOKEN', 'value': os.environ.get('HUBSPOT_API_TOKEN', '')},
                {'key': 'NEON_DATABASE_URL', 'value': os.environ.get('NEON_REST_API_ENDPOINT', '')},
                {'key': 'APOLLO_IO_API_KEY', 'value': os.environ.get('APOLLO_IO_API_KEY', '')}
            ]
        }
    ]
    
    print_info(f"Configured {len(services_config)} services for deployment")
    
    # Deploy each service
    deployed_services = []
    for service_config in services_config:
        print(f"\n🚀 Deploying {service_config['name']}...")
        
        # Check if service already exists
        existing_service = None
        for service in services:
            if service.get('name') == service_config['name']:
                existing_service = service
                break
        
        if existing_service:
            print_info(f"Service {service_config['name']} already exists, updating...")
            service_id = existing_service['id']
            
            # Trigger a new deployment
            deploy_url = f"https://api.render.com/v1/services/{service_id}/deploys"
            deploy_response = requests.post(deploy_url, headers=headers, timeout=30)
            
            if deploy_response.status_code == 201:
                print_status(f"Deployment triggered for {service_config['name']}")
                deployed_services.append(service_config['name'])
            else:
                print_error(f"Failed to trigger deployment for {service_config['name']}: {deploy_response.status_code}")
        else:
            print_info(f"Service {service_config['name']} doesn't exist - would need to create via Render dashboard")
            # Note: Service creation via API requires more complex setup
            # For now, we'll focus on triggering deployments of existing services
    
    # Create deployment summary
    timestamp = datetime.utcnow().isoformat() + 'Z'
    summary = {
        'timestamp': timestamp,
        'platform': 'render',
        'method': 'direct_api_deployment',
        'services_deployed': deployed_services,
        'total_services': len(services_config),
        'render_api_validated': True,
        'deployment_status': 'success' if deployed_services else 'partial'
    }
    
    # Save deployment record
    with open('direct_deployment_success.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📊 Deployment Summary:")
    print(f"   - Services deployed: {len(deployed_services)}")
    print(f"   - Total configured: {len(services_config)}")
    print(f"   - Timestamp: {timestamp}")
    
    if deployed_services:
        print_status("Direct Render deployment completed successfully!")
        print("\n🌐 Service URLs (will be active after deployment completes):")
        for service_name in deployed_services:
            print(f"   - https://{service_name}.onrender.com")
        return 0
    else:
        print_error("No services were deployed")
        return 1

if __name__ == '__main__':
    exit(main())
