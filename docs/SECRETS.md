# Sophia AI Secrets Management

## Overview

Sophia AI uses a multi-backend secrets management system that supports secure storage and retrieval of sensitive configuration values across different deployment environments. The system provides graceful degradation and fallback mechanisms to ensure availability while maintaining security.

## Supported Backends

### 1. GitHub Actions Secrets
- **Primary for CI/CD pipelines**
- Set secrets using GitHub CLI or web interface
- Secrets automatically available as environment variables in workflows

### 2. Pulumi ESC (Environment and Stack Configuration)
- **Primary for infrastructure and deployment configuration**
- Secure secret storage integrated with Pulumi IaC
- Environment-specific secret management

### 3. Fly.io Secrets
- **Primary for production deployment secrets**
- Runtime secret injection for Fly.io applications
- Automatic environment variable exposure

### 4. Environment Variables (Fallback)
- **Development and local testing**
- Direct environment variable access
- Lowest priority in secret resolution chain

## Secret Resolution Priority

Secrets are resolved in the following order:
1. GitHub Actions
2. Pulumi ESC
3. Fly.io
4. Environment Variables

## Configuration

### Environment Variables Required

```bash
# GitHub Actions (optional)
GITHUB_REPOSITORY=your-org/your-repo
GITHUB_TOKEN=your-github-token

# Pulumi ESC (optional)
PULUMI_PROJECT=your-project
PULUMI_STACK=production
PULUMI_ENVIRONMENT=production

# Fly.io (optional)
FLY_APP_NAME=your-app-name
```

## Usage Examples

### Getting a Secret
```python
from libs.secrets.manager import get_secret

# Get a secret with caching (default)
api_key = await get_secret("OPENAI_API_KEY")

# Get a secret without caching
api_key = await get_secret("OPENAI_API_KEY", use_cache=False)
```

### Setting a Secret
```python
from libs.secrets.manager import set_secret

# Set a secret in the preferred backend
success = await set_secret("NEW_API_KEY", "your-secret-value", backend="github")
```

### Listing Secrets
```python
from libs.secrets.manager import list_secrets

# List all available secrets
secret_names = await list_secrets()
```

## Secret Naming Convention

Use consistent, descriptive names for secrets:
- `SERVICE_PROVIDER_KEY` (e.g., `OPENAI_API_KEY`)
- `SERVICE_CONFIG_VALUE` (e.g., `NEON_DATABASE_URL`)
- Use underscores and uppercase letters
- Group related secrets with common prefixes

## Security Best Practices

### 1. Secret Rotation
- Regularly rotate API keys and credentials
- Use the secrets manager's metadata tracking
- Implement automated rotation where possible

### 2. Access Control
- Principle of least privilege for each backend
- Audit secret access logs regularly
- Remove unused secrets promptly

### 3. Development vs Production
- Use different secret backends for different environments
- Never commit actual secrets to version control
- Use `.env.example` for documentation only

## Backend-Specific Configuration

### GitHub Actions Setup
```bash
# Install GitHub CLI
brew install gh

# Authenticate
gh auth login

# Set a secret
gh secret set OPENAI_API_KEY --repo your-org/your-repo --body "your-key"
```

### Pulumi ESC Setup
```bash
# Install Pulumi CLI
brew install pulumi

# Set a secret
pulumi config set --secret OPENAI_API_KEY your-key
```

### Fly.io Setup
```bash
# Install Fly CLI
brew install flyctl

# Set a secret
fly secrets set OPENAI_API_KEY=your-key --app your-app-name
```

## Error Handling and Fallbacks

The secrets manager automatically handles:
- Backend connection failures
- Secret not found scenarios
- Graceful degradation to lower-priority backends
- Caching for performance optimization

## Monitoring and Auditing

### Secret Metadata Tracking
Each secret maintains metadata including:
- Last accessed timestamp
- Last rotated timestamp
- Version tracking
- Access frequency

### Logging
- All secret access attempts are logged
- Failed access attempts are logged as warnings
- Backend connection issues are logged

## Troubleshooting

### Common Issues

1. **Secret Not Found**
   - Check all backends in priority order
   - Verify secret name spelling and case
   - Ensure proper backend configuration

2. **Backend Connection Failures**
   - Verify required environment variables
   - Check CLI tool installation and authentication
   - Review backend-specific configuration

3. **Permission Errors**
   - Verify backend access permissions
   - Check repository/app access rights
   - Review IAM/service account configuration

### Debugging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed backend operations
from libs.secrets.manager import secrets_manager
await secrets_manager.initialize()
```

## Integration with Configuration System

The secrets manager integrates seamlessly with the configuration system:

```python
from libs.config.config import load_config

# Automatically loads secrets into typed configuration objects
config = await load_config()

# Access configured values
openai_key = config.llm.openai_api_key
database_url = config.database.neon_database_url
```

## Future Enhancements

Planned improvements:
- Automatic secret rotation policies
- Enhanced audit logging and reporting
- Integration with additional secret backends
- Secret validation and health checks
- Improved caching strategies
