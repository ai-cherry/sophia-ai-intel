#!/usr/bin/env python3
"""
Sophia AI Intel Platform - Modular Pulumi Infrastructure
Enterprise-grade IaC with containerization and staging/production support
"""

import os
import pulumi
import pulumi_render as render
from components.render_service import ServiceStack
from typing import Dict, Any, Optional

def get_stack_name() -> str:
    """Get current stack name from Pulumi context"""
    return pulumi.get_stack()

def get_environment() -> str:
    """Determine environment from stack name"""
    stack_name = get_stack_name()
    if 'staging' in stack_name.lower():
        return 'staging'
    elif 'production' in stack_name.lower():
        return 'production'
    else:
        # Default to production for main branch
        return 'production'

def validate_environment():
    """Validate required environment variables are present"""
    required_vars = [
        'RENDER_API_TOKEN',
        'NEON_DATABASE_URL',
        'REDIS_API_KEY',
        'REDIS_DATABASE_ENDPOINT',
        'QDRANT_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        pulumi.log.warn(f"Warning: Missing environment variables: {missing_vars}")
        # Don't fail - allow partial deployments for testing
    
    pulumi.log.info(f"Environment validation complete. Stack: {get_stack_name()}, Env: {get_environment()}")

def main():
    """Main Pulumi program with modular service deployment"""
    try:
        pulumi.log.info("Starting Sophia AI Intel platform deployment...")
        
        # Validate environment
        validate_environment()
        
        # Get deployment configuration
        stack_name = get_stack_name()
        environment = get_environment()
        container_image = os.environ.get('CONTAINER_IMAGE')
        
        pulumi.log.info(f"Deploying to {environment} environment (stack: {stack_name})")
        if container_image:
            pulumi.log.info(f"Using container image: {container_image}")
        
        # Create service stack
        service_stack = ServiceStack(
            stack_name=environment,
            container_image=container_image
        )
        
        # Deploy all services
        services = service_stack.create_all_services()
        
        # Export service information
        pulumi.export("environment", environment)
        pulumi.export("stack_name", stack_name)
        pulumi.export("container_image", container_image or "none")
        pulumi.export("services_count", len(services))
        pulumi.export("deployment_method", "pulumi_modular")
        
        # Export service URLs and IDs
        service_urls = {}
        service_ids = {}
        
        for name, service_component in services.items():
            service_urls[name] = f"https://sophia-{name}-{environment}.onrender.com"
            service_ids[name] = service_component.service.id
        
        pulumi.export("service_urls", service_urls)
        pulumi.export("service_ids", service_ids)
        
        # Export external service configurations
        external_config = {
            'redis_configured': bool(os.environ.get('REDIS_API_KEY')),
            'neon_configured': bool(os.environ.get('NEON_DATABASE_URL')),
            'qdrant_configured': bool(os.environ.get('QDRANT_API_KEY')),
            'mem0_configured': bool(os.environ.get('MEM0_API_KEY')),
            'lambda_configured': bool(os.environ.get('LAMBDA_API_KEY'))
        }
        pulumi.export("external_services", external_config)
        
        # Success status
        pulumi.export("deployment_status", "success")
        pulumi.export("deployed_at", pulumi.get_project())
        
        pulumi.log.info(f"Successfully deployed {len(services)} services to {environment}")
        
    except Exception as e:
        pulumi.log.error(f"Deployment failed: {e}")
        
        # Export error information
        pulumi.export("deployment_status", "failed")
        pulumi.export("error_message", str(e))
        pulumi.export("stack_name", get_stack_name())
        
        # Re-raise to fail the deployment
        raise

if __name__ == "__main__":
    main()
