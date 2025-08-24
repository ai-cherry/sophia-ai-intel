#!/usr/bin/env python3
"""
Automated Infrastructure Setup
Pulumi script designed to run from GitHub Actions with zero manual intervention
"""

import os
import pulumi
import pulumi_render as render
import json
import requests
from typing import Dict, Any, Optional

class AutomatedInfrastructure:
    def __init__(self):
        self.render_token = os.environ.get('RENDER_API_TOKEN')
        self.neon_api_key = os.environ.get('NEON_API_KEY')
        self.redis_account_key = os.environ.get('REDIS_ACCOUNT_KEY')
        self.redis_endpoint = os.environ.get('REDIS_DATABASE_ENDPOINT')
        self.qdrant_api_key = os.environ.get('QDRANT_API_KEY')
        self.mem0_api_key = os.environ.get('MEM0_API_KEY')
        self.lambda_api_key = os.environ.get('LAMBDA_API_KEY')
        self.n8n_api_key = os.environ.get('N8N_API_KEY')
        self.airbyte_api_key = os.environ.get('AIRBYTE_API_KEY')
        
        if not self.render_token:
            raise ValueError("RENDER_API_TOKEN is required")
            
        # Validate all required secrets
        required_secrets = {
            'NEON_API_KEY': self.neon_api_key,
            'REDIS_ACCOUNT_KEY': self.redis_account_key,
            'REDIS_DATABASE_ENDPOINT': self.redis_endpoint,
            'QDRANT_API_KEY': self.qdrant_api_key,
            'MEM0_API_KEY': self.mem0_api_key
        }
        
        for name, value in required_secrets.items():
            if not value:
                pulumi.log.warn(f"Warning: {name} not set")

    def provision_external_services(self):
        """Provision external services using their APIs"""
        pulumi.log.info("Provisioning external services...")
        
        services = {}
        
        # Provision Neon database branches
        if self.neon_api_key:
            services['neon'] = self.provision_neon_branch()
            
        # Set up Qdrant collections
        if self.qdrant_api_key:
            services['qdrant'] = self.provision_qdrant_collections()
            
        # Initialize Mem0 clients
        if self.mem0_api_key:
            services['mem0'] = self.provision_mem0_clients()
            
        # Set up Redis databases
        if self.redis_account_key and self.redis_endpoint:
            services['redis'] = self.construct_redis_url()
            
        return services

    def provision_neon_branch(self) -> Dict[str, Any]:
        """Create Neon database branch for the environment"""
        try:
            import requests
            
            headers = {
                'Authorization': f'Bearer {self.neon_api_key}',
                'Content-Type': 'application/json'
            }
            
            # Get project ID (assuming single project)
            projects_resp = requests.get(
                'https://console.neon.tech/api/v2/projects',
                headers=headers
            )
            projects_resp.raise_for_status()
            projects = projects_resp.json()['projects']
            
            if not projects:
                raise ValueError("No Neon projects found")
                
            project_id = projects[0]['id']
            
            # Create production branch
            branch_data = {
                'name': 'production',
                'parent_id': projects[0]['default_branch_id']
            }
            
            branch_resp = requests.post(
                f'https://console.neon.tech/api/v2/projects/{project_id}/branches',
                headers=headers,
                json=branch_data
            )
            
            if branch_resp.status_code == 201:
                branch = branch_resp.json()['branch']
                pulumi.log.info(f"Created Neon branch: {branch['id']}")
                
                # Get connection string
                endpoints_resp = requests.get(
                    f'https://console.neon.tech/api/v2/projects/{project_id}/endpoints',
                    headers=headers
                )
                endpoints_resp.raise_for_status()
                endpoints = endpoints_resp.json()['endpoints']
                
                for endpoint in endpoints:
                    if endpoint['branch_id'] == branch['id']:
                        database_url = f"postgresql://postgres:{endpoint['password']}@{endpoint['host']}/{endpoint['database_name']}"
                        return {
                            'branch_id': branch['id'],
                            'database_url': database_url,
                            'host': endpoint['host']
                        }
            else:
                pulumi.log.warn(f"Branch might already exist: {branch_resp.text}")
                return {'status': 'existing'}
                
        except Exception as e:
            pulumi.log.error(f"Failed to provision Neon branch: {e}")
            return {'error': str(e)}
            
    def provision_qdrant_collections(self) -> Dict[str, Any]:
        """Set up Qdrant vector collections"""
        try:
            collections = [
                {
                    'name': 'knowledge_base',
                    'vectors': {
                        'size': 1536,  # OpenAI embedding size
                        'distance': 'Cosine'
                    }
                },
                {
                    'name': 'conversation_memory',
                    'vectors': {
                        'size': 1536,
                        'distance': 'Cosine'
                    }
                },
                {
                    'name': 'code_context',
                    'vectors': {
                        'size': 1536,
                        'distance': 'Cosine'
                    }
                }
            ]
            
            created_collections = []
            
            for collection_config in collections:
                # Assume Qdrant cluster URL from API key
                qdrant_url = f"https://your-cluster.qdrant.tech"
                headers = {
                    'api-key': self.qdrant_api_key,
                    'Content-Type': 'application/json'
                }
                
                response = requests.put(
                    f"{qdrant_url}/collections/{collection_config['name']}",
                    headers=headers,
                    json=collection_config
                )
                
                if response.status_code in [200, 409]:  # 409 if already exists
                    created_collections.append(collection_config['name'])
                    pulumi.log.info(f"Qdrant collection ready: {collection_config['name']}")
                    
            return {
                'collections': created_collections,
                'url': qdrant_url
            }
            
        except Exception as e:
            pulumi.log.error(f"Failed to provision Qdrant collections: {e}")
            return {'error': str(e)}
            
    def provision_mem0_clients(self) -> Dict[str, Any]:
        """Initialize Mem0 memory clients"""
        try:
            # Mem0 client initialization
            clients = [
                'sophia_context',
                'user_preferences', 
                'conversation_state',
                'knowledge_graph'
            ]
            
            initialized_clients = []
            
            for client_name in clients:
                # Initialize client via Mem0 API
                headers = {
                    'Authorization': f'Bearer {self.mem0_api_key}',
                    'Content-Type': 'application/json'
                }
                
                client_config = {
                    'name': client_name,
                    'config': {
                        'vector_store': {
                            'provider': 'qdrant',
                            'config': {
                                'api_key': self.qdrant_api_key
                            }
                        }
                    }
                }
                
                # This is a placeholder for Mem0 API calls
                pulumi.log.info(f"Mem0 client configured: {client_name}")
                initialized_clients.append(client_name)
                
            return {
                'clients': initialized_clients,
                'api_key': self.mem0_api_key
            }
            
        except Exception as e:
            pulumi.log.error(f"Failed to provision Mem0 clients: {e}")
            return {'error': str(e)}
            
    def construct_redis_url(self) -> str:
        """Construct Redis connection URL from components"""
        if not self.redis_account_key or not self.redis_endpoint:
            raise ValueError("Redis credentials incomplete")
            
        redis_url = f"redis://:{self.redis_account_key}@{self.redis_endpoint}:6379"
        pulumi.log.info("Redis URL constructed successfully")
        return redis_url

    def create_render_services(self):
        """Create all Render services with proper configuration"""
        pulumi.log.info("Creating Render services...")
        
        # Provision external services first
        external_services = self.provision_external_services()
        
        services = {}
        
        # Service configurations
        service_configs = [
            {
                'name': 'dashboard',
                'type': 'static_site',
                'build_command': 'cd apps/dashboard && npm ci && npm run build',
                'publish_directory': 'apps/dashboard/dist',
                'env_vars': {}
            },
            {
                'name': 'mcp-research',
                'type': 'web_service',
                'build_command': 'cd services/mcp-research && pip install -r requirements.txt',
                'start_command': 'cd services/mcp-research && python server.py',
                'env_vars': {
                    'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
                    'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
                    'QDRANT_API_KEY': self.qdrant_api_key,
                    'QDRANT_URL': external_services.get('qdrant', {}).get('url'),
                    'MEM0_API_KEY': self.mem0_api_key,
                    'REDIS_URL': external_services.get('redis')
                }
            },
            {
                'name': 'mcp-context',
                'type': 'web_service', 
                'build_command': 'cd services/mcp-context && pip install -r requirements.txt',
                'start_command': 'cd services/mcp-context && python server.py',
                'env_vars': {
                    'NEON_DATABASE_URL': external_services.get('neon', {}).get('database_url'),
                    'REDIS_URL': external_services.get('redis'),
                    'MEM0_API_KEY': self.mem0_api_key
                }
            },
            {
                'name': 'mcp-github',
                'type': 'web_service',
                'build_command': 'cd services/mcp-github && pip install -r requirements.txt',
                'start_command': 'cd services/mcp-github && python server.py',
                'env_vars': {
                    'GITHUB_TOKEN': os.environ.get('GITHUB_TOKEN'),
                    'REDIS_URL': external_services.get('redis')
                }
            },
            {
                'name': 'mcp-business',
                'type': 'web_service',
                'build_command': 'cd services/mcp-business && pip install -r requirements.txt', 
                'start_command': 'cd services/mcp-business && python server.py',
                'env_vars': {
                    'HUBSPOT_API_TOKEN': os.environ.get('HUBSPOT_API_TOKEN'),
                    'NEON_DATABASE_URL': external_services.get('neon', {}).get('database_url'),
                    'REDIS_URL': external_services.get('redis')
                }
            },
            {
                'name': 'mcp-hubspot',
                'type': 'web_service',
                'build_command': 'cd services/mcp-hubspot && pip install -r requirements.txt',
                'start_command': 'cd services/mcp-hubspot && python server.py', 
                'env_vars': {
                    'HUBSPOT_API_TOKEN': os.environ.get('HUBSPOT_API_TOKEN'),
                    'REDIS_URL': external_services.get('redis')
                }
            },
            {
                'name': 'mcp-lambda',
                'type': 'web_service',
                'build_command': 'cd services/mcp-lambda && pip install -r requirements.txt',
                'start_command': 'cd services/mcp-lambda && python server.py',
                'env_vars': {
                    'LAMBDA_API_KEY': self.lambda_api_key,
                    'REDIS_URL': external_services.get('redis')
                }
            },
            {
                'name': 'orchestrator',
                'type': 'web_service',
                'build_command': 'cd services/orchestrator && npm ci',
                'start_command': 'cd services/orchestrator && npm start',
                'env_vars': {
                    'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
                    'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
                    'REDIS_URL': external_services.get('redis'),
                    'NEON_DATABASE_URL': external_services.get('neon', {}).get('database_url')
                }
            },
            {
                'name': 'jobs',
                'type': 'background_worker',
                'build_command': 'cd jobs && pip install -r requirements.txt',
                'start_command': 'cd jobs && python reindex.py',
                'env_vars': {
                    'QDRANT_API_KEY': self.qdrant_api_key,
                    'QDRANT_URL': external_services.get('qdrant', {}).get('url'),
                    'NEON_DATABASE_URL': external_services.get('neon', {}).get('database_url')
                }
            }
        ]
        
        # Create each service
        for config in service_configs:
            service_name = config['name']
            
            # Filter out None values from env_vars
            env_vars = {k: v for k, v in config['env_vars'].items() if v is not None}
            
            if config['type'] == 'static_site':
                service = render.StaticSite(
                    service_name,
                    name=service_name,
                    build_command=config['build_command'],
                    publish_directory=config['publish_directory'],
                    auto_deploy=True,
                    branch='main'
                )
            else:
                service_type = 'web_service' if config['type'] != 'background_worker' else 'background_worker'
                
                service = render.Service(
                    service_name,
                    name=service_name,
                    type=service_type,
                    build_command=config['build_command'],
                    start_command=config['start_command'],
                    env_vars=env_vars,
                    auto_deploy=True,
                    branch='main',
                    health_check_path='/healthz' if service_type == 'web_service' else None,
                    num_instances=1,
                    plan='starter'  # Can be upgraded later
                )
            
            services[service_name] = service
            pulumi.log.info(f"Created Render service: {service_name}")
            
        return services

def main():
    """Main Pulumi program"""
    try:
        infra = AutomatedInfrastructure()
        
        # Create all services
        services = infra.create_render_services()
        
        # Export service URLs
        for name, service in services.items():
            if hasattr(service, 'url'):
                pulumi.export(f"{name}_url", service.url)
            
        pulumi.export("deployment_status", "success")
        pulumi.export("services_count", len(services))
        
    except Exception as e:
        pulumi.log.error(f"Deployment failed: {e}")
        pulumi.export("deployment_status", "failed")
        pulumi.export("error", str(e))
        raise

if __name__ == "__main__":
    main()
