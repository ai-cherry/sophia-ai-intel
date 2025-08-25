# Sophia AI Monitoring Stack

This directory contains the monitoring infrastructure for the Sophia AI system, including Prometheus, Grafana, and supporting exporters.

## Components

### Prometheus
- **Port**: 9090
- **Purpose**: Metrics collection and storage
- **Configuration**: `prometheus.yml`
- **Retention**: 200 hours of metrics data

### Grafana
- **Port**: 3000
- **Purpose**: Metrics visualization and dashboards
- **Default Credentials**: admin/admin (change in production)
- **Provisioning**: Automatic datasource and dashboard setup

### cAdvisor
- **Port**: 8080
- **Purpose**: Container metrics collection
- **Scope**: All Docker containers on the host

### Node Exporter
- **Port**: 9100
- **Purpose**: Host system metrics (CPU, memory, disk, network)

## Quick Start

1. **Start the monitoring stack:**
   ```bash
   cd monitoring
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

2. **Access Grafana:**
   - URL: http://localhost:3000
   - Username: admin
   - Password: admin

3. **Access Prometheus:**
   - URL: http://localhost:9090
   - Use for debugging metrics and queries

## Integration with Main Application

To integrate monitoring with the main Sophia AI application:

1. **Update main docker-compose.yml:**
   ```yaml
   networks:
     default:
       external:
         name: monitoring_monitoring
   ```

2. **Add monitoring labels to services:**
   ```yaml
   services:
     your-service:
       labels:
         - "prometheus.io/scrape=true"
         - "prometheus.io/port=8000"
         - "prometheus.io/path=/metrics"
   ```

## Dashboards

### Available Dashboards
- **Sophia AI System Overview**: General system metrics and health status
- **Container Metrics**: Detailed container performance metrics
- **Host Metrics**: System-level resource utilization

### Custom Dashboards
Add custom dashboards by placing JSON files in `grafana/dashboards/` directory. They will be automatically provisioned.

## Metrics Endpoints

The following services expose metrics endpoints:

- **Dashboard**: `http://dashboard:3000/metrics`
- **Orchestrator**: `http://orchestrator:8000/metrics`
- **MCP Agents**: `http://mcp-agents:8001/metrics`
- **MCP Business**: `http://mcp-business:8002/metrics`
- **MCP Research**: `http://mcp-research:8003/metrics`
- **MCP GitHub**: `http://mcp-github:8004/metrics`
- **MCP Context**: `http://mcp-context:8005/metrics`

## Alerting

To set up alerting:

1. Configure Alertmanager in `prometheus.yml`
2. Create alerting rules in Prometheus
3. Set up notification channels in Grafana

## Production Considerations

- Change default Grafana credentials
- Configure persistent storage for Prometheus data
- Set up proper authentication and authorization
- Configure SSL/TLS for external access
- Set up log aggregation (ELK stack or similar)
- Configure backup strategies for metrics data

## Troubleshooting

### Common Issues

1. **Grafana not loading dashboards:**
   - Check provisioning configuration
   - Verify file permissions
   - Check Grafana logs: `docker logs sophia-grafana`

2. **Prometheus not scraping targets:**
   - Verify network connectivity
   - Check scrape configuration
   - Check target service logs

3. **Metrics not appearing:**
   - Ensure services expose `/metrics` endpoint
   - Check Prometheus targets page
   - Verify service labels in docker-compose

## Phase 2 Implementation - COMPLETED ✅

Phase 2 monitoring and observability enhancements have been successfully implemented:

### ✅ Completed Features

- **Complete Monitoring Stack**: Prometheus, Grafana, cAdvisor, Node Exporter, Loki, Promtail
- **Automated Service Discovery**: Docker service discovery for all 8 microservices
- **Comprehensive Dashboards**: System overview, service-specific metrics, and logs dashboards
- **Advanced Alerting**: 10+ alerting rules for service health, resource usage, and system issues
- **Centralized Logging**: Loki + Promtail for log aggregation and analysis
- **Network Integration**: All services connected to monitoring network with proper labels

### 📊 Available Dashboards

1. **Sophia AI System Overview** - General system metrics and health status
2. **Sophia AI Services** - Detailed per-service metrics (CPU, memory, network)
3. **Sophia AI Logs** - Centralized log aggregation with error tracking

### 🔧 Access Information

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Loki**: http://localhost:3100
- **cAdvisor**: http://localhost:8080
- **Node Exporter**: http://localhost:9100

### 🚀 Production Deployment

To deploy to production:

1. Update docker-compose.yml with proper environment variables
2. Start main application: `docker-compose up -d`
3. Start monitoring: `cd monitoring && docker-compose -f docker-compose.monitoring.yml up -d`
4. Access Grafana at your domain/grafana

### 📈 Monitoring Coverage

- **8 Microservices**: Dashboard, Research, Context, GitHub, Business, Lambda, HubSpot, Agents
- **System Metrics**: CPU, memory, disk, network usage
- **Application Metrics**: Service health, response times, error rates
- **Log Aggregation**: Structured logging with service-specific parsing
- **Alerting**: Critical service failures, resource thresholds, error spikes

### 🔒 Security Considerations

- Change default Grafana credentials in production
- Configure SSL/TLS for external access
- Set up proper authentication and authorization
- Implement data retention policies
- Configure backup strategies for metrics data

### 📋 Next Steps

- Configure production environment variables
- Set up SSL certificates for monitoring endpoints
- Implement log retention policies
- Configure additional alerting channels (Slack, email)
- Set up monitoring for additional infrastructure components