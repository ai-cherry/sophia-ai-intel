"""
Modular Render Service Components for Sophia AI Intel Platform
Supports both containerized and native builds
"""

import pulumi
import pulumi_render as render
from typing import Dict, Optional, List
import os

class RenderService(pulumi.ComponentResource):
    """Base component for Render services"""
    
    def __init__(self, name: str, opts: Optional[pulumi.ResourceOptions] = None, **kwargs):
        super().__init__("sophia:render:Service", name, None, opts)
        
        # Default values
        self.name = name
        self.env = kwargs.get('env', 'production')
        self.service_type = kwargs.get('type', 'web_service')
        self.plan = kwargs.get('plan', 'starter')
        
        # Build configuration
        self.is_containerized = kwargs.get('containerized', False)
        self.container_image = kwargs.get('container_image')
        self.build_command = kwargs.get('build_command')
        self.start_command = kwargs.get('start_command')
        
        # Service configuration
        self.env_vars = kwargs.get('env_vars', {})
        self.health_check_path = kwargs.get('health_check_path', '/healthz')
        self.auto_deploy = kwargs.get('auto_deploy', True)
        self.num_instances = kwargs.get('num_instances', 1)
        
        # Create the service
        self.service = self._create_service()
        
        # Register outputs
        self.register_outputs({
            'service_id': self.service.id,
            'service_url': getattr(self.service, 'service_url', None)
        })

    def _create_service(self):
        """Create the Render service with appropriate configuration"""
        
        if self.is_containerized and self.container_image:
            return self._create_container_service()
        else:
            return self._create_native_service()
    
    def _create_container_service(self):
        """Create a container-based service"""
        return render.Service(
            f"{self.name}-service",
            type=self.service_type,
            name=self.name,
            env_id=self.env,
            plan=self.plan,
            repo=os.environ.get('GITHUB_REPOSITORY', 'ai-cherry/sophia-ai-intel'),
            auto_deploy=self.auto_deploy,
            image={
                "owner_id": os.environ.get('RENDER_OWNER_ID'),
                "image_path": self.container_image
            },
            env_vars=[
                {"key": key, "value": str(value)} 
                for key, value in self.env_vars.items() 
                if value is not None
            ],
            health_check_path=self.health_check_path if self.service_type == 'web_service' else None,
            num_instances=self.num_instances,
            opts=pulumi.ResourceOptions(parent=self)
        )
    
    def _create_native_service(self):
        """Create a native build service"""
        return render.Service(
            f"{self.name}-service",
            type=self.service_type,
            name=self.name,
            env_id=self.env,
            plan=self.plan,
            repo=os.environ.get('GITHUB_REPOSITORY', 'ai-cherry/sophia-ai-intel'),
            auto_deploy=self.auto_deploy,
            build_command=self.build_command,
            start_command=self.start_command,
            env_vars=[
                {"key": key, "value": str(value)} 
                for key, value in self.env_vars.items() 
                if value is not None
            ],
            health_check_path=self.health_check_path if self.service_type == 'web_service' else None,
            num_instances=self.num_instances,
            opts=pulumi.ResourceOptions(parent=self)
        )


class DashboardService(RenderService):
    """Containerized React dashboard service"""
    
    def __init__(self, name: str = "sophia-dashboard", container_image: Optional[str] = None, 
                 opts: Optional[pulumi.ResourceOptions] = None):
        
        # Dashboard-specific configuration
        config = {
            'type': 'static_site',
            'containerized': True,
            'container_image': container_image or os.environ.get('CONTAINER_IMAGE'),
            'plan': 'starter',
            'env_vars': {
                'NODE_ENV': 'production',
                'VITE_BUILD_ID': os.environ.get('GITHUB_RUN_ID', 'local'),
            }
        }
        
        super().__init__(name, opts, **config)


class PythonMCPService(RenderService):
    """Python-based MCP service component"""
    
    def __init__(self, name: str, service_config: Dict, opts: Optional[pulumi.ResourceOptions] = None):
        
        # Python MCP service defaults
        config = {
            'type': 'web_service',
            'containerized': False,  # Use native Python builds for now
            'build_command': f'cd services/{name} && pip install --no-cache-dir -r requirements.txt',
            'start_command': f'cd services/{name} && uvicorn app:app --host 0.0.0.0 --port $PORT --workers 2',
            'plan': service_config.get('plan', 'starter'),
            'health_check_path': '/healthz',
            'env_vars': service_config.get('env_vars', {}),
            'num_instances': service_config.get('instances', 1)
        }
        
        super().__init__(name, opts, **config)


class BackgroundWorkerService(RenderService):
    """Background worker service component"""
    
    def __init__(self, name: str, service_config: Dict, opts: Optional[pulumi.ResourceOptions] = None):
        
        # Background worker defaults
        config = {
            'type': 'background_worker',
            'containerized': False,
            'build_command': f'cd {service_config.get("root_dir", "jobs")} && pip install --no-cache-dir -r requirements.txt',
            'start_command': f'cd {service_config.get("root_dir", "jobs")} && python {service_config.get("script", "reindex.py")}',
            'plan': 'starter',
            'env_vars': service_config.get('env_vars', {}),
            'health_check_path': None,  # Background workers don't have health checks
            'num_instances': 1
        }
        
        super().__init__(name, opts, **config)


class ServiceStack:
    """Complete service stack for staging or production"""
    
    def __init__(self, stack_name: str, container_image: Optional[str] = None):
        self.stack_name = stack_name
        self.container_image = container_image
        self.services = {}
        
        # External service configurations
        self.redis_url = self._construct_redis_url()
        self.neon_database_url = os.environ.get('NEON_DATABASE_URL')
        self.qdrant_url = os.environ.get('QDRANT_URL', 'https://your-cluster.qdrant.tech')
        
    def _construct_redis_url(self) -> str:
        """Construct Redis URL from environment components"""
        redis_key = os.environ.get('REDIS_API_KEY')
        redis_endpoint = os.environ.get('REDIS_DATABASE_ENDPOINT')
        
        if redis_key and redis_endpoint:
            return f"redis://:{redis_key}@{redis_endpoint}:6379"
        return ""
    
    def create_dashboard(self) -> DashboardService:
        """Create containerized dashboard service"""
        dashboard = DashboardService(
            name=f"sophia-dashboard-{self.stack_name}",
            container_image=self.container_image
        )
        self.services['dashboard'] = dashboard
        return dashboard
    
    def create_research_service(self) -> PythonMCPService:
        """Create research MCP service"""
        config = {
            'plan': 'standard',
            'instances': 2,
            'env_vars': {
                'PORT': '10000',
                'PYTHONUNBUFFERED': '1',
                'DEFAULT_LLM_MODEL': 'gpt-5',
                'ANTHROPIC_API_KEY': os.environ.get('ANTHROPIC_API_KEY'),
                'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
                'QDRANT_API_KEY': os.environ.get('QDRANT_API_KEY'),
                'QDRANT_URL': self.qdrant_url,
                'REDIS_URL': self.redis_url,
                'NEON_DATABASE_URL': self.neon_database_url,
                'TENANT': 'pay-ready'
            }
        }
        
        research = PythonMCPService('mcp-research', config)
        self.services['research'] = research
        return research
    
    def create_context_service(self) -> PythonMCPService:
        """Create context MCP service"""
        config = {
            'plan': 'standard',
            'env_vars': {
                'PORT': '10000',
                'PYTHONUNBUFFERED': '1',
                'NEON_DATABASE_URL': self.neon_database_url,
                'QDRANT_URL': self.qdrant_url,
                'QDRANT_API_KEY': os.environ.get('QDRANT_API_KEY'),
                'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY'),
                'TENANT': 'pay-ready'
            }
        }
        
        context = PythonMCPService('mcp-context', config)
        self.services['context'] = context
        return context
    
    def create_github_service(self) -> PythonMCPService:
        """Create GitHub MCP service"""
        config = {
            'plan': 'starter',
            'env_vars': {
                'PORT': '10000',
                'PYTHONUNBUFFERED': '1',
                'GITHUB_APP_ID': os.environ.get('GITHUB_APP_ID'),
                'GITHUB_INSTALLATION_ID': os.environ.get('GITHUB_INSTALLATION_ID'),
                'GITHUB_PRIVATE_KEY': os.environ.get('GITHUB_PRIVATE_KEY'),
                'GITHUB_REPO': 'ai-cherry/sophia-ai-intel',
                'DASHBOARD_ORIGIN': f'https://sophia-dashboard-{self.stack_name}.onrender.com',
                'TENANT': 'pay-ready'
            }
        }
        
        github = PythonMCPService('mcp-github', config)
        self.services['github'] = github
        return github
    
    def create_business_service(self) -> PythonMCPService:
        """Create business integrations MCP service"""
        config = {
            'plan': 'standard',
            'instances': 2,
            'env_vars': {
                'PORT': '10000',
                'PYTHONUNBUFFERED': '1',
                'HUBSPOT_API_TOKEN': os.environ.get('HUBSPOT_API_TOKEN'),
                'NEON_DATABASE_URL': self.neon_database_url,
                'REDIS_URL': self.redis_url,
                'QDRANT_URL': self.qdrant_url,
                'TENANT': 'pay-ready'
            }
        }
        
        business = PythonMCPService('mcp-business', config)
        self.services['business'] = business
        return business
    
    def create_lambda_service(self) -> PythonMCPService:
        """Create Lambda Labs GPU service"""
        config = {
            'plan': 'pro',  # Higher tier for GPU coordination
            'env_vars': {
                'PORT': '10000',
                'PYTHONUNBUFFERED': '1',
                'LAMBDA_API_KEY': os.environ.get('LAMBDA_API_KEY'),
                'LAMBDA_PRIVATE_SSH_KEY': os.environ.get('LAMBDA_PRIVATE_SSH_KEY'),
                'LAMBDA_PUBLIC_SSH_KEY': os.environ.get('LAMBDA_PUBLIC_SSH_KEY'),
                'LAMBDA_API_ENDPOINT': 'https://cloud.lambdalabs.com/api/v1',
                'DATABASE_URL': self.neon_database_url,
                'REDIS_URL': self.redis_url,
                'TENANT': 'pay-ready'
            }
        }
        
        lambda_service = PythonMCPService('mcp-lambda', config)
        self.services['lambda'] = lambda_service
        return lambda_service
    
    def create_hubspot_service(self) -> PythonMCPService:
        """Create HubSpot integration service"""
        config = {
            'plan': 'starter',
            'env_vars': {
                'PORT': '10000',
                'PYTHONUNBUFFERED': '1',
                'HUBSPOT_ACCESS_TOKEN': os.environ.get('HUBSPOT_API_TOKEN'),
                'HUBSPOT_CLIENT_SECRET': os.environ.get('HUBSPOT_CLIENT_SECRET'),
                'TENANT': 'pay-ready'
            }
        }
        
        hubspot = PythonMCPService('mcp-hubspot', config)
        self.services['hubspot'] = hubspot
        return hubspot
    
    def create_orchestrator_service(self) -> PythonMCPService:
        """Create service orchestrator"""
        config = {
            'plan': 'standard',
            'env_vars': {
                'PORT': '10000',
                'PYTHONUNBUFFERED': '1',
                'REDIS_URL': self.redis_url,
                'NEON_DATABASE_URL': self.neon_database_url,
                'TENANT': 'pay-ready'
            }
        }
        
        orchestrator = PythonMCPService('orchestrator', config)
        self.services['orchestrator'] = orchestrator
        return orchestrator
    
    def create_jobs_worker(self) -> BackgroundWorkerService:
        """Create background jobs worker"""
        config = {
            'root_dir': 'jobs',
            'script': 'reindex.py',
            'env_vars': {
                'PYTHONUNBUFFERED': '1',
                'NEON_DATABASE_URL': self.neon_database_url,
                'REDIS_URL': self.redis_url,
                'TENANT': 'pay-ready'
            }
        }
        
        jobs = BackgroundWorkerService('sophia-jobs', config)
        self.services['jobs'] = jobs
        return jobs
    
    def create_all_services(self):
        """Create all services for the stack"""
        pulumi.log.info(f"Creating {self.stack_name} stack services...")
        
        # Create all services
        self.create_dashboard()
        self.create_research_service()
        self.create_context_service()
        self.create_github_service()
        self.create_business_service()
        self.create_lambda_service()
        self.create_hubspot_service()
        self.create_orchestrator_service()
        self.create_jobs_worker()
        
        pulumi.log.info(f"Created {len(self.services)} services for {self.stack_name}")
        
        return self.services
