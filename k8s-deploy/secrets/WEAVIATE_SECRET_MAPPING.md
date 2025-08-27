# Weaviate Cloud Secret Configuration

## Overview
This document describes the Weaviate Cloud secret configuration for the Sophia AI Kubernetes deployment.

## Secret Files
- **Primary**: [`k8s-deploy/secrets/weaviate-cloud-secrets.yaml`](weaviate-cloud-secrets.yaml)
- **Updated**: [`k8s-deploy/secrets/database-secrets.yaml`](database-secrets.yaml) - `sophia-vector-secrets` section

## Environment Variable Mapping

### Weaviate Cloud Credentials
| Environment Variable | Secret Key | Description | Example Value |
|---------------------|------------|-------------|---------------|
| `WEAVIATE_URL` | `WEAVIATE_URL` | REST endpoint for HTTP operations | `https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud` |
| `WEAVIATE_API_KEY` | `WEAVIATE_API_KEY` | Authentication bearer token | `VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf` |
| `WEAVIATE_GRPC_URL` | `WEAVIATE_GRPC_URL` | gRPC endpoint for high-performance operations | `grpc-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud:443` |

## Secret Structure

### weaviate-cloud-config Secret
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: weaviate-cloud-config
  namespace: sophia
  labels:
    app: sophia-ai
    component: vector-database
type: Opaque
data:
  WEAVIATE_URL: aHR0cHM6Ly93NmJpZ3BveHNyd3ZxN3dsZ21tZHZhLmMwLnVzLXdlc3QzLmdjcC53ZWF2aWF0ZS5jbG91ZA==
  WEAVIATE_API_KEY: Vk1LakdNUVVuWFFJRGlGT2NpWlpPaHI3YW1CZkNITWg3aE5m
  WEAVIATE_GRPC_URL: Z3JwYy13NmJpZ3BveHNyd3ZxN3dsZ21tZHZhLmMwLnVzLXdlc3QzLmdjcC53ZWF2aWF0ZS5jbG91ZDo0NDM=
```

### sophia-vector-secrets Secret (Updated)
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: sophia-vector-secrets
  namespace: sophia
  labels:
    app: sophia-ai
    component: vector-db
type: Opaque
data:
  WEAVIATE_URL: aHR0cHM6Ly93NmJpZ3BveHNyd3ZxN3dsZ21tZHZhLmMwLnVzLXdlc3QzLmdjcC53ZWF2aWF0ZS5jbG91ZA==
  WEAVIATE_API_KEY: Vk1LakdNUVVuWFFJRGlGT2NpWlpPaHI3YW1CZkNITWg3aE5m
  WEAVIATE_GRPC_URL: Z3JwYy13NmJpZ3BveHNyd3ZxN3dsZ21tZHZhLmMwLnVzLXdlc3QzLmdjcC53ZWF2aWF0ZS5jbG91ZDo0NDM=
```

## Usage in Deployments

Services can reference these secrets using `valueFrom`:

```yaml
env:
- name: WEAVIATE_URL
  valueFrom:
    secretKeyRef:
      name: sophia-vector-secrets  # or weaviate-cloud-config
      key: WEAVIATE_URL
- name: WEAVIATE_API_KEY
  valueFrom:
    secretKeyRef:
      name: sophia-vector-secrets  # or weaviate-cloud-config
      key: WEAVIATE_API_KEY
- name: WEAVIATE_GRPC_URL
  valueFrom:
    secretKeyRef:
      name: sophia-vector-secrets  # or weaviate-cloud-config
      key: WEAVIATE_GRPC_URL
```

## Migration from Qdrant

### Replaced Environment Variables
| Old Qdrant Variable | New Weaviate Variable | Status |
|-------------------|---------------------|--------|
| `QDRANT_URL` | `WEAVIATE_URL` | ✅ Replaced |
| `QDRANT_API_KEY` | `WEAVIATE_API_KEY` | ✅ Replaced |
| `QDRANT_CLUSTER_ID` | N/A | ❌ Removed (not needed for Weaviate) |
| `QDRANT_MANAGEMENT_KEY` | N/A | ❌ Removed (not needed for Weaviate) |
| `QDRANT_ACCOUNT_ID` | N/A | ❌ Removed (not needed for Weaviate) |

### Files Updated
- ✅ `k8s-deploy/secrets/database-secrets.yaml` - sophia-vector-secrets section
- ✅ `k8s-deploy/secrets/weaviate-cloud-secrets.yaml` - New dedicated secret

### Files Requiring Application Updates
The following manifest files reference Qdrant environment variables and will need updates when services are migrated:
- `k8s-deploy/manifests/mcp-context.yaml`
- `k8s-deploy/manifests/mcp-research.yaml`
- `k8s-deploy/manifests/external-secrets.yaml`
- Network policies in `k8s-deploy/manifests/network-policies.yaml` and `k8s-deploy/manifests/mtls-network-policies.yaml`

## Validation

### Base64 Encoding Verified
All base64 encoded values have been verified to decode to the correct credential values:

```bash
# Verify URL
echo "aHR0cHM6Ly93NmJpZ3BveHNyd3ZxN3dsZ21tZHZhLmMwLnVzLXdlc3QzLmdjcC53ZWF2aWF0ZS5jbG91ZA==" | base64 -d
# Returns: https://w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud

# Verify API Key
echo "Vk1LakdNUVVuWFFJRGlGT2NpWlpPaHI3YW1CZkNITWg3aE5m" | base64 -d  
# Returns: VMKjGMQUnXQIDiFOciZZOhr7amBfCHMh7hNf

# Verify gRPC URL
echo "Z3JwYy13NmJpZ3BveHNyd3ZxN3dsZ21tZHZhLmMwLnVzLXdlc3QzLmdjcC53ZWF2aWF0ZS5jbG91ZDo0NDM=" | base64 -d
# Returns: grpc-w6bigpoxsrwvq7wlgmmdva.c0.us-west3.gcp.weaviate.cloud:443
```

## Security Notes
- All secrets use `type: Opaque` for secure storage
- Secrets are properly namespaced to `sophia`
- Labels follow consistent `app: sophia-ai` pattern
- Base64 encoding follows Kubernetes secret standards