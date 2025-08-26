#!/usr/bin/env python3
"""
Sophia AI - Generate Kubernetes manifests from Docker Compose
Converts MCP services to K8s deployments
"""

import os
import yaml
import json

# Service configurations based on docker-compose.yml
MCP_SERVICES = {
    "mcp-context": {
        "port": 8080,
        "gpu": True,
        "memory": "16Gi",
        "cpu": "4",
        "env_keys": [
            "OPENAI_API_KEY",
            "NEON_DATABASE_URL",
            "QDRANT_URL", 
            "QDRANT_API_KEY",
            "REDIS_URL"
        ]
    },
    "mcp-github": {
        "port": 8080,
        "memory": "1Gi",
        "cpu": "1",
        "env_keys": [
            "GITHUB_APP_ID",
            "GITHUB_INSTALLATION_ID",
            "GITHUB_PRIVATE_KEY",
            "NEON_DATABASE_URL"
        ],
        "env_values": {
            "GITHUB_REPO": "ai-cherry/sophia-ai-intel",
            "DASHBOARD_ORIGIN": "http://sophia-dashboard:3000"
        }
    },
    "mcp-business": {
        "port": 8080,
        "memory": "1Gi",
        "cpu": "1",
        "env_keys": [
            "APOLLO_API_KEY",
            "HUBSPOT_ACCESS_TOKEN",
            "NEON_DATABASE_URL",
            "QDRANT_URL",
            "REDIS_URL",
            "OPENROUTER_API_KEY"
        ]
    },
    "mcp-lambda": {
        "port": 8080,
        "memory": "1Gi",
        "cpu": "1",
        "env_keys": [
            "LAMBDA_API_KEY",
            "LAMBDA_PRIVATE_SSH_KEY",
            "LAMBDA_PUBLIC_SSH_KEY",
            "NEON_DATABASE_URL",
            "REDIS_URL"
        ],
        "env_values": {
            "LAMBDA_API_ENDPOINT": "https://cloud.lambdalabs.com/api/v1"
        }
    },
    "mcp-hubspot": {
        "port": 8080,
        "memory": "1Gi",
        "cpu": "1",
        "env_keys": [
            "HUBSPOT_ACCESS_TOKEN",
            "HUBSPOT_CLIENT_SECRET"
        ]
    },
    "mcp-agents": {
        "port": 8000,
        "gpu": True,
        "memory": "16Gi",
        "cpu": "4",
        "env_keys": [
            "GITHUB_APP_ID",
            "GITHUB_INSTALLATION_ID",
            "GITHUB_PRIVATE_KEY",
            "NEON_DATABASE_URL",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "QDRANT_URL",
            "QDRANT_API_KEY",
            "REDIS_URL"
        ],
        "env_values": {
            "PYTHONPATH": "/app/libs:/app",
            "DASHBOARD_ORIGIN": "http://sophia-dashboard:3000",
            "GITHUB_MCP_URL": "http://mcp-github:8080",
            "CONTEXT_MCP_URL": "http://mcp-context:8080",
            "RESEARCH_MCP_URL": "http://mcp-research:8080",
            "BUSINESS_MCP_URL": "http://mcp-business:8080"
        }
    }
}

def generate_deployment_manifest(service_name, config):
    """Generate Kubernetes deployment manifest for a service"""
    
    # Base deployment structure
    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": service_name,
            "namespace": "sophia",
            "labels": {
                "app": service_name,
                "component": "backend",
                "service": service_name.replace("mcp-", "")
            }
        },
        "spec": {
            "replicas": 1,
            "selector": {
                "matchLabels": {
                    "app": service_name
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": service_name,
                        "component": "backend",
                        "service": service_name.replace("mcp-", "")
                    }
                },
                "spec": {
                    "containers": [{
                        "name": service_name,
                        "image": f"sophia-ai-intel/{service_name}:latest",
                        "ports": [{
                            "containerPort": config["port"],
                            "name": "http"
                        }],
                        "env": [
                            {"name": "PORT", "value": str(config["port"])},
                            {"name": "PYTHONUNBUFFERED", "value": "1"},
                            {"name": "TENANT", "value": "pay-ready"}
                        ],
                        "resources": {
                            "limits": {
                                "cpu": config["cpu"],
                                "memory": config["memory"]
                            },
                            "requests": {
                                "cpu": str(int(config["cpu"]) // 2) if int(config["cpu"]) > 1 else config["cpu"],
                                "memory": "512Mi" if config["memory"] == "1Gi" else "8Gi"
                            }
                        },
                        "livenessProbe": {
                            "httpGet": {
                                "path": "/healthz",
                                "port": config["port"]
                            },
                            "initialDelaySeconds": 30,
                            "periodSeconds": 30
                        },
                        "readinessProbe": {
                            "httpGet": {
                                "path": "/healthz",
                                "port": config["port"]
                            },
                            "initialDelaySeconds": 10,
                            "periodSeconds": 10
                        },
                        "imagePullPolicy": "IfNotPresent"
                    }]
                }
            }
        }
    }
    
    # Add GPU if needed
    if config.get("gpu"):
        deployment["spec"]["template"]["spec"]["containers"][0]["resources"]["limits"]["nvidia.com/gpu"] = 1
    
    # Add environment variables from secrets
    container = deployment["spec"]["template"]["spec"]["containers"][0]
    for key in config.get("env_keys", []):
        container["env"].append({
            "name": key,
            "valueFrom": {
                "secretKeyRef": {
                    "name": "sophia-secrets",
                    "key": key
                }
            }
        })
    
    # Add static environment variables
    for key, value in config.get("env_values", {}).items():
        container["env"].append({
            "name": key,
            "value": value
        })
    
    # Service definition
    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": service_name,
            "namespace": "sophia",
            "labels": {
                "app": service_name,
                "component": "backend",
                "service": service_name.replace("mcp-", "")
            }
        },
        "spec": {
            "type": "ClusterIP",
            "selector": {
                "app": service_name
            },
            "ports": [{
                "port": config["port"],
                "targetPort": config["port"],
                "protocol": "TCP",
                "name": "http"
            }]
        }
    }
    
    return deployment, service

def main():
    """Generate all Kubernetes manifests"""
    
    # Create manifests directory if it doesn't exist
    os.makedirs("k8s-deploy/manifests", exist_ok=True)
    
    # Generate manifests for each service
    for service_name, config in MCP_SERVICES.items():
        try:
            print(f"Generating manifest for {service_name}...")
            
            deployment, service = generate_deployment_manifest(service_name, config)
            
            # Write to file
            manifest_path = f"k8s-deploy/manifests/{service_name}.yaml"
            with open(manifest_path, 'w') as f:
                # Write deployment
                yaml.dump(deployment, f, default_flow_style=False, sort_keys=False)
                f.write("---\n")
                # Write service
                yaml.dump(service, f, default_flow_style=False, sort_keys=False)
            
            print(f"✅ Generated {manifest_path}")
        except Exception as e:
            print(f"❌ Error generating manifest for {service_name}: {e}")
    
    # Generate persistent volume claim for mcp-context
    pvc = {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": "mcp-context-storage",
            "namespace": "sophia"
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": "10Gi"
                }
            },
            "storageClassName": "local-path"
        }
    }
    
    with open("k8s-deploy/manifests/mcp-context-pvc.yaml", 'w') as f:
        yaml.dump(pvc, f, default_flow_style=False, sort_keys=False)
    
    print("\n✅ All manifests generated successfully!")
    print("\nNext steps:")
    print("1. Review generated manifests in k8s-deploy/manifests/")
    print("2. Create secrets with: k8s-deploy/scripts/create-all-secrets.sh")
    print("3. Apply manifests with: kubectl apply -f k8s-deploy/manifests/")

if __name__ == "__main__":
    main()
