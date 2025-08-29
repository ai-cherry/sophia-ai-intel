# Sophia AI Intel Platform

## Overview

Sophia AI Intel is an advanced AI orchestration platform that provides a unified interface for research, coding, business intelligence, and multi-agent swarm coordination. Built with a microservices architecture, it integrates seamlessly with major business tools and provides enterprise-grade security and scalability.

## Key Features

### 🤖 Unified AI Interface
- Single chat interface for all AI interactions
- Natural language processing for complex requests
- Multi-modal responses with code, research, and analysis

### 🧠 Context-Aware Intelligence
- Advanced memory management with Qdrant and pgvector
- Incremental indexing with GitHub webhook integration
- Real-time context updates and semantic search

### 🔍 Multi-Provider Research
- Aggregated research from Tavily, Serper, Perplexity, Exa, and Portkey
- Automated deduplication and summarization
- Redis caching for performance optimization

### 🏭 Business Integrations
- **HubSpot**: CRM data access and automation
- **Salesforce**: Account and opportunity management
- **Gong**: Call analytics and sentiment analysis
- **GitHub**: Code repository integration
- **Slack**: Team communication
- **Looker**: Business intelligence
- **UserGems**: Sales intelligence

### 🐝 Multi-Agent Swarms
- AI code planning swarm with debating agents
- Optimistic Planner and Cautious Critic roles
- Mediator agent for balanced decision making
- WebSocket-based real-time orchestration

### 🚀 Smart LLM Routing
- Multi-provider support (OpenAI, Anthropic, Perplexity, Portkey)
- Cost and performance optimization
- Response caching and streaming

## Architecture

### Frontend
- Next.js dashboard with React Server Components
- Real-time WebSocket connections
- Responsive design with Tailwind CSS
- Dark/light mode support

### Backend Services
- **MCP Services**: Business integration microservices
- **Context Service**: Memory and vector database management
- **Research Service**: Multi-provider search orchestration
- **Agents Service**: Multi-agent swarm coordination
- **LLM Router**: Intelligent provider selection

### Infrastructure
- Docker containerization
- Redis caching
- PostgreSQL database
- Qdrant vector database
- Prometheus monitoring
- Grafana dashboards

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11+
- Node.js 18+
- GitHub CLI (for secrets management)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ai-cherry/sophia-ai-intel.git
cd sophia-ai-intel
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

3. **Start the platform:**
```bash
docker-compose up -d
```

4. **Access the dashboard:**
Open `http://localhost:3000` in your browser

### Development Setup

1. **Install dependencies:**
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd apps/sophia-dashboard
npm install
```

2. **Run development servers:**
```bash
# Backend services
docker-compose -f docker-compose.local.yml up

# Frontend
cd apps/sophia-dashboard
npm run dev
```

## Configuration

### Environment Variables

Configure your environment using the `.env` file. Key variables include:

- **LLM Providers**: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **Search Providers**: `TAVILY_API_KEY`, `SERPER_API_KEY`
- **Business Integrations**: `HUBSPOT_API_KEY`, `SALESFORCE_*`
- **Database**: `NEON_DATABASE_URL`, `QDRANT_API_KEY`
- **Security**: `JWT_SECRET`, `ENCRYPTION_KEY`

### Secrets Management

The platform supports multiple secret backends:
1. **GitHub Actions Secrets** - CI/CD pipeline
2. **Pulumi ESC** - Infrastructure configuration
3. **Fly.io Secrets** - Production deployment
4. **Environment Variables** - Development

See [SECRETS.md](docs/SECRETS.md) for detailed configuration.

## API Endpoints

### Chat Interface
- `POST /api/chat` - Main chat endpoint
- `GET /api/health` - System health check
- `GET /api/metrics` - Performance metrics

### Agent Services
- `POST /api/agents/swarm` - Create new agent swarm
- `GET /api/agents/swarms` - List active swarms
- `GET /api/agents/swarms/{id}` - Get swarm status

### Research Services
- `POST /api/research/search` - Multi-provider search
- `POST /api/research/deep` - Comprehensive research
- `GET /api/research/cache` - Cached results

## Deployment

### Local Development
```bash
docker-compose -f docker-compose.local.yml up -d
```

### Production Deployment
```bash
docker-compose up -d
```

### Cloud Deployment
The platform supports deployment to Fly.io with automated scripts:
```bash
./scripts/fly-deploy.sh
```

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

## Testing

### Unit Tests
```bash
# Python services
pytest tests/

# Frontend
cd apps/sophia-dashboard
npm test
```

### Integration Tests
```bash
./scripts/run-integration-tests.sh
```

### End-to-End Tests
```bash
./scripts/run-e2e-tests.sh
```

## Monitoring

### Health Checks
- Service health: `/healthz`
- Detailed metrics: `/metrics`
- System status: Dashboard health panel

### Logging
- Structured JSON logging
- Loki log aggregation
- Grafana visualization

### Performance Metrics
- Response times
- Error rates
- Resource utilization
- Throughput monitoring

## Security

### Authentication
- JWT-based authentication
- Role-based access control
- Session management

### Data Protection
- Encryption at rest and in transit
- Secure secret management
- Regular security scanning

### Compliance
- GDPR compliant data handling
- SOC 2 controls
- Regular audit logging

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Implement changes
4. Add tests
5. Submit pull request

### Code Standards
- Python: PEP 8 compliance
- TypeScript: ESLint with strict rules
- Docker: Multi-stage builds
- Security: Bandit and CodeQL scanning

### Testing Requirements
- Unit test coverage > 80%
- Integration tests for service interactions
- End-to-end tests for user workflows

## Support

### Documentation
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Secrets Management](docs/SECRETS.md)
- [API Documentation](docs/API.md)

### Community
- GitHub Issues for bug reports
- Discussions for feature requests
- Pull requests for contributions

### Enterprise Support
- SLA guarantees
- Dedicated support team
- Custom development services

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- OpenAI for GPT models
- Anthropic for Claude models
- Qdrant for vector database
- PostgreSQL community
- All open source contributors
