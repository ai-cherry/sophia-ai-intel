"""
Sophia AI Intel Platform - Render Migration Infrastructure
Pulumi script for automated migration from Fly.io to Render
Integrates Qdrant, Mem0, n8n, Airbyte, and Lambda Labs
"""

import pulumi
import requests
import os
from typing import Dict, List
from urllib.parse import urlparse

# Pulumi configuration
config = pulumi.Config()

# Get secrets from environment (GitHub Actions will populate these)
RENDER_API_TOKEN = os.getenv("RENDER_API_TOKEN")
GITHUB_PAT = os.getenv("GITHUB_PAT") 
NEON_API_TOKEN = os.getenv("NEON_API_TOKEN")
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")

# New service API keys (to be added to GitHub secrets)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
MEM0_API_KEY = os.getenv("MEM0_API_KEY")
AIRBYTE_API_TOKEN = os.getenv("AIRBYTE_API_TOKEN")

# Redis Cloud components (existing)
REDIS_API_KEY = os.getenv("REDIS_API_KEY")
REDIS_DATABASE_ENDPOINT = os.getenv("REDIS_DATABASE_ENDPOINT")
REDIS_ACCOUNT_KEY = os.getenv("REDIS_ACCOUNT_KEY")

# Lambda Labs (existing)
LAMBDA_API_KEY = os.getenv("LAMBDA_API_KEY")

class RenderService:
    """Helper class for Render API operations"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.render.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_service_from_yaml(self, service_config: Dict) -> Dict:
        """Create a Render service from YAML configuration"""
        endpoint = f"{self.base_url}/services"
        
        # Convert render.yaml format to Render API format
        payload = self._convert_yaml_to_api_format(service_config)
        
        response = requests.post(endpoint, json=payload, headers=self.headers)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create service: {response.text}")
    
    def update_service_env_vars(self, service_id: str, env_vars: Dict[str, str]) -> Dict:
        """Update environment variables for a service"""
        endpoint = f"{self.base_url}/services/{service_id}/env-vars"
        
        # Convert to Render API format
        env_var_updates = [
            {"key": key, "value": value}
            for key, value in env_vars.items()
        ]
        
        response = requests.put(endpoint, json=env_var_updates, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to update env vars: {response.text}")
    
    def _convert_yaml_to_api_format(self, yaml_config: Dict) -> Dict:
        """Convert render.yaml service config to Render API format"""
        service_type = yaml_config.get("type")
        
        if service_type == "static_site":
            return self._convert_static_site(yaml_config)
        elif service_type == "web_service":
            return self._convert_web_service(yaml_config)
        elif service_type == "background_worker":
            return self._convert_background_worker(yaml_config)
        else:
            raise ValueError(f"Unsupported service type: {service_type}")
    
    def _convert_static_site(self, config: Dict) -> Dict:
        """Convert static site configuration"""
        return {
            "type": "static_site",
            "name": config["name"],
            "repo": config["repo"],
            "branch": config.get("branch", "main"),
            "rootDir": config.get("rootDir", "./"),
            "buildCommand": config.get("buildCommand", ""),
            "publishPath": config.get("publishPath", "./"),
            "pullRequestPreviewsEnabled": config.get("pullRequestPreviewsEnabled", False),
            "headers": config.get("headers", []),
            "envVars": self._convert_env_vars(config.get("envVars", []))
        }
    
    def _convert_web_service(self, config: Dict) -> Dict:
        """Convert web service configuration"""
        return {
            "type": "web_service", 
            "name": config["name"],
            "repo": config["repo"],
            "branch": config.get("branch", "main"),
            "rootDir": config.get("rootDir", "./"),
            "runtime": config.get("runtime", "python"),
            "buildCommand": config.get("buildCommand", ""),
            "startCommand": config.get("startCommand", ""),
            "plan": config.get("plan", "starter"),
            "region": config.get("region", "oregon"),
            "healthCheckPath": config.get("healthCheckPath", "/healthz"),
            "pullRequestPreviewsEnabled": config.get("pullRequestPreviewsEnabled", False),
            "envVars": self._convert_env_vars(config.get("envVars", [])),
            "scaling": config.get("scaling", {})
        }
    
    def _convert_background_worker(self, config: Dict) -> Dict:
        """Convert background worker configuration"""
        return {
            "type": "background_worker",
            "name": config["name"],
            "repo": config["repo"], 
            "branch": config.get("branch", "main"),
            "rootDir": config.get("rootDir", "./"),
            "runtime": config.get("runtime", "python"),
            "buildCommand": config.get("buildCommand", ""),
            "startCommand": config.get("startCommand", ""),
            "plan": config.get("plan", "starter"),
            "region": config.get("region", "oregon"),
            "envVars": self._convert_env_vars(config.get("envVars", [])),
            "scaling": config.get("scaling", {})
        }
    
    def _convert_env_vars(self, env_vars: List[Dict]) -> List[Dict]:
        """Convert environment variables to Render API format"""
        converted = []
        for var in env_vars:
            if var.get("sync", True):  # sync: false means it's a secret
                # This is a regular environment variable
                converted.append({
                    "key": var["key"],
                    "value": var.get("value", "")
                })
        return converted

class QdrantCluster:
    """Qdrant Cloud cluster management"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.qdrant.io/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_cluster(self, name: str, region: str = "us-west") -> Dict:
        """Create a Qdrant cluster"""
        payload = {
            "name": name,
            "region": region,
            "plan": "free",  # Start with free tier
            "size": "1x-small"
        }
        
        response = requests.post(f"{self.base_url}/clusters", json=payload, headers=self.headers)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create Qdrant cluster: {response.text}")
    
    def get_cluster_url(self, cluster_id: str) -> str:
        """Get the connection URL for a cluster"""
        response = requests.get(f"{self.base_url}/clusters/{cluster_id}", headers=self.headers)
        if response.status_code == 200:
            cluster_info = response.json()
            return cluster_info.get("endpoint_url", "")
        else:
            raise Exception(f"Failed to get cluster info: {response.text}")

class Mem0Client:
    """Mem0 API client for memory management"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.mem0.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def create_memory_store(self, name: str, config: Dict) -> Dict:
        """Create a memory store"""
        payload = {
            "name": name,
            "config": config
        }
        
        response = requests.post(f"{self.base_url}/stores", json=payload, headers=self.headers)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create memory store: {response.text}")

class AirbyteClient:
    """Airbyte Cloud API client"""
    
    def __init__(self, api_token: str):
        self.api_token = api_token
        self.base_url = "https://api.airbyte.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }
    
    def create_source(self, source_config: Dict) -> Dict:
        """Create an Airbyte source"""
        response = requests.post(f"{self.base_url}/sources", json=source_config, headers=self.headers)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create Airbyte source: {response.text}")
    
    def create_destination(self, dest_config: Dict) -> Dict:
        """Create an Airbyte destination"""
        response = requests.post(f"{self.base_url}/destinations", json=dest_config, headers=self.headers)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            raise Exception(f"Failed to create Airbyte destination: {response.text}")

def construct_redis_url() -> str:
    """Construct Redis URL from individual components"""
    if REDIS_API_KEY and REDIS_DATABASE_ENDPOINT:
        return f"redis://:{REDIS_API_KEY}@{REDIS_DATABASE_ENDPOINT}:6379"
    else:
        pulumi.log.warn("Redis components missing, using localhost fallback")
        return "redis://localhost:6379"

def extract_neon_db_components() -> Dict[str, str]:
    """Extract database components from Neon URL for n8n configuration"""
    if not NEON_DATABASE_URL:
        return {}
    
    parsed = urlparse(NEON_DATABASE_URL)
    return {
        "host": parsed.hostname or "",
        "database": parsed.path.lstrip('/') if parsed.path else "",
        "user": parsed.username or "",
        "password": parsed.password or "",
        "port": str(parsed.port) if parsed.port else "5432"
    }

def create_external_services():
    """Create and configure external services"""
    services_info = {}
    
    # 1. Create Qdrant Cluster
    if QDRANT_API_KEY:
        try:
            qdrant = QdrantCluster(QDRANT_API_KEY)
            cluster = qdrant.create_cluster("sophia-vector-db")
            cluster_url = qdrant.get_cluster_url(cluster["id"])
            services_info["qdrant"] = {
                "cluster_id": cluster["id"],
                "url": cluster_url,
                "api_key": QDRANT_API_KEY
            }
            pulumi.log.info(f"Created Qdrant cluster: {cluster['id']}")
        except Exception as e:
            pulumi.log.warn(f"Failed to create Qdrant cluster: {e}")
    
    # 2. Setup Mem0 Memory Store
    if MEM0_API_KEY:
        try:
            mem0 = Mem0Client(MEM0_API_KEY)
            memory_store = mem0.create_memory_store("sophia-memory", {
                "vector_store": "qdrant",
                "embedding_model": "text-embedding-3-small"
            })
            services_info["mem0"] = {
                "store_id": memory_store["id"],
                "api_key": MEM0_API_KEY
            }
            pulumi.log.info(f"Created Mem0 memory store: {memory_store['id']}")
        except Exception as e:
            pulumi.log.warn(f"Failed to create Mem0 memory store: {e}")
    
    # 3. Setup Airbyte Data Pipelines
    if AIRBYTE_API_TOKEN:
        try:
            airbyte = AirbyteClient(AIRBYTE_API_TOKEN)
            
            # Create Neon destination
            neon_dest = airbyte.create_destination({
                "name": "sophia-neon-db",
                "destinationDefinitionId": "25c5221d-dce2-4163-ade9-739ef790f503",  # Postgres
                "connectionConfiguration": {
                    "host": extract_neon_db_components().get("host"),
                    "port": 5432,
                    "database": extract_neon_db_components().get("database"),
                    "username": extract_neon_db_components().get("user"),
                    "password": extract_neon_db_components().get("password"),
                    "ssl": True
                }
            })
            
            services_info["airbyte"] = {
                "destination_id": neon_dest["destinationId"],
                "api_token": AIRBYTE_API_TOKEN
            }
            pulumi.log.info(f"Created Airbyte destination: {neon_dest['destinationId']}")
        except Exception as e:
            pulumi.log.warn(f"Failed to create Airbyte destination: {e}")
    
    # 4. Redis URL construction (existing service)
    redis_url = construct_redis_url()
    services_info["redis"] = {
        "url": redis_url,
        "api_key": REDIS_API_KEY,
        "endpoint": REDIS_DATABASE_ENDPOINT
    }
    
    # 5. Lambda Labs (existing service)
    if LAMBDA_API_KEY:
        services_info["lambda_labs"] = {
            "api_key": LAMBDA_API_KEY,
            "endpoint": "https://cloud.lambdalabs.com/api/v1"
        }
    
    return services_info

def deploy_render_services(services_info: Dict):
    """Deploy services to Render using the render.yaml configuration"""
    if not RENDER_API_TOKEN:
        pulumi.log.error("RENDER_API_TOKEN is required")
        return
    
    render_client = RenderService(RENDER_API_TOKEN)
    
    # Load render.yaml configuration
    with open("render.yaml", "r") as f:
        import yaml
        render_config = yaml.safe_load(f)
    
    deployed_services = {}
    
    for service_config in render_config.get("services", []):
        try:
            service_name = service_config["name"]
            pulumi.log.info(f"Deploying service: {service_name}")
            
            # Create the service
            service = render_client.create_service_from_yaml(service_config)
            service_id = service["service"]["id"]
            
            # Prepare environment variables with secrets
            env_vars = prepare_env_vars_for_service(service_name, services_info)
            
            # Update environment variables
            if env_vars:
                render_client.update_service_env_vars(service_id, env_vars)
            
            deployed_services[service_name] = {
                "id": service_id,
                "url": service.get("service", {}).get("serviceDetails", {}).get("url", ""),
                "status": "deployed"
            }
            
            pulumi.log.info(f"Successfully deployed: {service_name}")
            
        except Exception as e:
            pulumi.log.error(f"Failed to deploy {service_config['name']}: {e}")
            deployed_services[service_config["name"]] = {
                "status": "failed",
                "error": str(e)
            }
    
    return deployed_services

def prepare_env_vars_for_service(service_name: str, services_info: Dict) -> Dict[str, str]:
    """Prepare environment variables for a specific service"""
    env_vars = {}
    
    # Common variables for all services
    env_vars["TENANT"] = "pay-ready"
    
    # Service-specific environment variables
    if service_name == "sophia-research":
        env_vars.update({
            "SERPAPI_API_KEY": os.getenv("TAVILY_API_KEY", ""),
            "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY", ""),
            "TOGETHER_API_KEY": os.getenv("OPENROUTER_API_KEY", ""),
            "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", ""),
            "PORTKEY_API_KEY": os.getenv("PORTKEY_API_KEY", ""),
            "REDIS_URL": services_info.get("redis", {}).get("url", ""),
            "NEON_DATABASE_URL": NEON_DATABASE_URL or "",
            "QDRANT_URL": services_info.get("qdrant", {}).get("url", ""),
            "QDRANT_API_KEY": services_info.get("qdrant", {}).get("api_key", "")
        })
    
    elif service_name == "sophia-context":
        env_vars.update({
            "NEON_DATABASE_URL": NEON_DATABASE_URL or "",
            "QDRANT_URL": services_info.get("qdrant", {}).get("url", ""),
            "QDRANT_API_KEY": services_info.get("qdrant", {}).get("api_key", ""),
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "")
        })
    
    elif service_name == "sophia-github":
        env_vars.update({
            "GITHUB_APP_ID": os.getenv("GITHUB_APP_ID", ""),
            "GITHUB_INSTALLATION_ID": os.getenv("GITHUB_INSTALLATION_ID", ""),
            "GITHUB_PRIVATE_KEY": os.getenv("GITHUB_PRIVATE_KEY", "")
        })
    
    elif service_name == "sophia-business":
        env_vars.update({
            "APOLLO_API_KEY": os.getenv("APOLLO_API_KEY", ""),
            "HUBSPOT_ACCESS_TOKEN": os.getenv("HUBSPOT_ACCESS_TOKEN", ""),
            "SALESFORCE_CLIENT_ID": os.getenv("SALESFORCE_CLIENT_ID", ""),
            "SALESFORCE_CLIENT_SECRET": os.getenv("SALESFORCE_CLIENT_SECRET", ""),
            "SLACK_BOT_TOKEN": os.getenv("SLACK_BOT_TOKEN", ""),
            "SLACK_SIGNING_SECRET": os.getenv("SLACK_SIGNING_SECRET", ""),
            "NEON_DATABASE_URL": NEON_DATABASE_URL or "",
            "REDIS_URL": services_info.get("redis", {}).get("url", "")
        })
    
    elif service_name == "sophia-lambda":
        env_vars.update({
            "LAMBDA_API_KEY": LAMBDA_API_KEY or "",
            "LAMBDA_PRIVATE_SSH_KEY": os.getenv("LAMBDA_PRIVATE_SSH_KEY", ""),
            "LAMBDA_PUBLIC_SSH_KEY": os.getenv("LAMBDA_PUBLIC_SSH_KEY", ""),
            "DATABASE_URL": NEON_DATABASE_URL or "",
            "REDIS_URL": services_info.get("redis", {}).get("url", "")
        })
    
    elif service_name == "sophia-n8n":
        db_components = extract_neon_db_components()
        env_vars.update({
            "DB_POSTGRESDB_HOST": db_components.get("host", ""),
            "DB_POSTGRESDB_DATABASE": db_components.get("database", ""),
            "DB_POSTGRESDB_USER": db_components.get("user", ""),
            "DB_POSTGRESDB_PASSWORD": db_components.get("password", "")
        })
    
    # Remove empty values
    return {k: v for k, v in env_vars.items() if v}

def main():
    """Main Pulumi program"""
    pulumi.log.info("Starting Sophia AI Intel migration to Render...")
    
    # Step 1: Create external services
    pulumi.log.info("Creating external services...")
    services_info = create_external_services()
    
    # Step 2: Deploy Render services
    pulumi.log.info("Deploying Render services...")
    deployed_services = deploy_render_services(services_info)
    
    # Export important information
    pulumi.export("services_info", services_info)
    pulumi.export("deployed_services", deployed_services)
    pulumi.export("redis_url", services_info.get("redis", {}).get("url", ""))
    pulumi.export("qdrant_cluster_id", services_info.get("qdrant", {}).get("cluster_id", ""))
    pulumi.export("mem0_store_id", services_info.get("mem0", {}).get("store_id", ""))
    
    pulumi.log.info("Migration completed!")

if __name__ == "__main__":
    main()
