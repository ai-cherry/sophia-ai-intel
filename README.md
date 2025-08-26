# Sophia AI Intel

An autonomous AI intelligence platform built with a microservices architecture using Model Context Protocol (MCP) for seamless integration across business systems.

## Architecture Overview

Sophia AI Intel is designed as a monorepo with the following structure:

```
sophia-ai-intel/
├── apps/
│   └── dashboard/                 # CEO chat UI (React + TypeScript)
├── services/
│   ├── mcp-research/              # Web research meta-aggregator
│   ├── mcp-context/               # Neon-backed index registry
│   ├── mcp-github/                # GitHub App integration (READ-ONLY)
│   ├── mcp-business/              # Business intelligence & CRM integrations
│   ├── mcp-lambda/                # Lambda Labs infrastructure management
│   ├── mcp-hubspot/               # HubSpot CRM integration
│   ├── mcp-agents/                # AI Agent Swarm orchestration
│   └── orchestrator/              # Cross-service coordination
├── jobs/                          # Background processing tasks
├── libs/
│   ├── contracts/                 # Zod/JSON Schema definitions
│   ├── clients/                   # TypeScript clients
│   ├── agents/                    # AI agent implementations
│   └── memory/                    # Memory architecture components
├── ops/
│   ├── workflows/                 # GitHub Actions
│   ├── infra/                     # Infrastructure manifests
│   ├── pulumi/                    # Pulumi Infrastructure as Code
│   └── playbooks/                 # Runbooks and guides
└── proofs/                        # CI/Actions proof artifacts
```

## Default LLM Configuration

**Primary Model**: ChatGPT-5 (GPT-5)
- Used as the default model for all AI operations
- Configured through Portkey router for optimal performance
- Fallback models: Claude 3.5 Sonnet, GPT-4o

## Technology Stack

### Infrastructure & Orchestration
- **Kubernetes + Lambda Labs**: Multi-region Docker deployments with GPU acceleration
- **Pulumi**: Infrastructure as Code
- **Docker**: Containerized services
- **Neon PostgreSQL**: Primary database
- **Redis**: Caching and rate limiting

### AI & LLM Stack
- **Portkey**: Primary LLM router with ChatGPT-5 default
- **OpenAI API**: ChatGPT-5, GPT-4o access
- **Anthropic**: Claude 3.5 Sonnet backup
- **DeepSeek**: Code assistance
- **Groq**: Low-latency inference

### Research & Data
- **Tavily API**: Web search and research
- **Serper API**: Search results aggregation
- **Exa API**: Semantic search
- **Perplexity API**: AI-powered search

### Business Integrations
- **GitHub App**: Repository access (read-only)
- **Slack API**: Team communication
- **Salesforce API**: CRM integration
- **Notion API**: Knowledge management

## Quick Start

### Prerequisites
- Node.js 20+
- Docker
- kubectl (for Kubernetes deployment)
- GitHub CLI (optional)

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/ai-cherry/sophia-ai-intel.git
cd sophia-ai-intel
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Required Environment Variables

```bash
# LLM Configuration (ChatGPT-5 Default)
PORTKEY_API_KEY=your_portkey_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Research APIs
TAVILY_API_KEY=your_tavily_key
SERPER_API_KEY=your_serper_key

# Database
NEON_DATABASE_URL=your_neon_url

# GitHub Integration
GITHUB_APP_ID=your_app_id
GITHUB_INSTALLATION_ID=your_installation_id
GITHUB_PRIVATE_KEY=your_private_key

# Lambda Labs Configuration
LAMBDA_API_KEY=your_lambda_api_key
LAMBDA_PRIVATE_SSH_KEY=your_lambda_private_ssh_key
LAMBDA_PUBLIC_SSH_KEY=your_lambda_public_ssh_key
```

## Development

### Local Development
```bash
# Start all services
npm run dev

# Start specific service
npm run dev:dashboard
npm run dev:mcp-research
```

### Testing
```bash
# Run all tests
npm test

# Run specific service tests
npm run test:dashboard
```

## Deployment

### Kubernetes + Lambda Labs Deployment
```bash
# Deploy all services
npm run deploy

# Deploy specific service
npm run deploy:dashboard

# Deploy to Lambda Labs GPU instances
npm run deploy:lambda-labs
```

### Health Checks
All services expose health check endpoints:
- `/healthz` - Basic health status
- `/__build` - Build information (dashboard only)

## Security & Compliance

- All secrets managed via GitHub Organization Secrets → Pulumi ESC
- Read-only access for external integrations by default
- Write operations require explicit approval workflows
- Comprehensive audit logging for all operations

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Make your changes and add tests
4. Submit a pull request

All pull requests require:
- CODEOWNERS approval
- Passing CI/CD checks
- Security scan approval

## License

MIT License - see [LICENSE](LICENSE) for details.

## Support

For questions or issues, please:
1. Check the [documentation](docs/)
2. Search existing [issues](https://github.com/ai-cherry/sophia-ai-intel/issues)
3. Create a new issue if needed

---

Built with ❤️ by the AI Cherry team
