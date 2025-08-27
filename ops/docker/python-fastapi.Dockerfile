# syntax=docker/dockerfile:1.4
# ops/docker/python-fastapi.Dockerfile
# Enhanced SOPHIA AI microservices template with advanced security, multi-stage builds,
# vulnerability scanning integration, and build optimizations.

ARG PYTHON_VERSION=3.11-slim
ARG BASE_REQUIREMENTS_PATH=platform/common/base-requirements.txt
ARG SERVICE_REQUIREMENTS_PATH=requirements.txt
ARG SERVICE_SOURCE_PATH=.
ARG SERVICE_APP_MODULE=app:app
ARG PORT=8080
ARG SERVICE_NAME=sophia-service
ARG BUILD_SECURITY_SCAN=true

# --- Security Scanner Stage ---
# This stage runs security scanning tools on the source code and dependencies
FROM python:${PYTHON_VERSION}-buster AS security_scanner

# Install security scanning tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        gnupg \
        lsb-release \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Trivy for vulnerability scanning
RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | apt-key add - && \
    echo deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main | tee -a /etc/apt/sources.list.d/trivy.list && \
    apt-get update && \
    apt-get install -y trivy

# Install Safety for Python dependency vulnerability scanning
RUN pip install --no-cache-dir safety

# Copy source for scanning
WORKDIR /scan
COPY ${SERVICE_REQUIREMENTS_PATH} ./requirements.txt
COPY ${BASE_REQUIREMENTS_PATH} ./base-requirements.txt

# Run security scans if enabled
RUN if [ "${BUILD_SECURITY_SCAN}" = "true" ]; then \
        echo "Running Safety scan on Python dependencies..." && \
        safety check --file ./base-requirements.txt --json > /scan/safety-base-report.json || true && \
        safety check --file ./requirements.txt --json > /scan/safety-service-report.json || true; \
    fi

# --- Builder Stage ---
# Enhanced builder stage with security hardening and optimization
FROM python:${PYTHON_VERSION}-buster AS builder

# Set environment variables for non-interactive installation and immediate output
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        openssh-client \
        curl \
        wget \
        git \
        # Security hardening packages
        libcap2-bin \
        procps \
    && rm -rf /var/lib/apt/lists/* && \
    # Remove unnecessary packages and clear caches
    apt-get autoremove -y && \
    apt-get clean

# Create app user early for better layer caching
RUN groupadd -r appuser && useradd -r -g appuser -s /bin/bash -m appuser

# Set working directory
WORKDIR /app

# Copy and install base requirements first (better caching)
COPY ${BASE_REQUIREMENTS_PATH} ./base-requirements.txt
RUN pip install --no-cache-dir --user -r ./base-requirements.txt

# Copy and install service requirements
COPY ${SERVICE_REQUIREMENTS_PATH} ./requirements.txt
RUN pip install --no-cache-dir --user -r ./requirements.txt

# Copy source code with proper permissions
COPY --chown=appuser:appuser ${SERVICE_SOURCE_PATH} ./app

# Copy security scan results for runtime reference
COPY --from=security_scanner /scan /security-scans

# --- Runtime Stage ---
# Production-optimized runtime with advanced security hardening
FROM python:${PYTHON_VERSION}-buster AS runtime

# Set metadata labels for better container management
LABEL org.opencontainers.image.title="${SERVICE_NAME}" \
      org.opencontainers.image.description="SOPHIA AI Microservice - ${SERVICE_NAME}" \
      org.opencontainers.image.vendor="SOPHIA AI" \
      org.opencontainers.image.version="latest"

# Set environment variables for production runtime
ENV PYTHONUNBUFFERED=1 \
    PORT=${PORT} \
    PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    # Security hardening
    USER=appuser \
    HOME=/home/appuser

# Install minimal runtime dependencies with security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        wget \
        # Security monitoring tools
        libcap2-bin \
        procps \
        net-tools \
        # Required for health checks and monitoring
        dnsutils \
    && rm -rf /var/lib/apt/lists/* && \
    apt-get autoremove -y && \
    apt-get clean && \
    # Create non-root user with minimal privileges
    groupadd -r appuser && \
    useradd -r -g appuser -s /bin/bash -d /home/appuser -m appuser && \
    # Security hardening: remove unnecessary files and set permissions
    rm -rf /var/cache/* /tmp/* && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

# Switch to non-root user
USER appuser

# Set working directory
WORKDIR /app

# Copy Python packages from builder stage
COPY --from=builder --chown=appuser:appuser /root/.local/lib/python3.11/site-packages /home/appuser/.local/lib/python3.11/site-packages
COPY --from=builder --chown=appuser:appuser /root/.local/bin /home/appuser/.local/bin

# Update PATH to include user-installed packages
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy application code
COPY --from=builder --chown=appuser:appuser /app/app ./app

# Copy security scan results for auditing
COPY --from=builder --chown=appuser:appuser /security-scans /security-scans

# Create necessary directories with proper permissions
RUN mkdir -p /tmp && \
    chmod 1777 /tmp

# Health check with enhanced monitoring
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f -s --max-time 5 http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Create startup script
RUN mkdir -p /usr/local/bin && \
    echo 'Starting service...' > /usr/local/bin/startup.sh && \
    chmod +x /usr/local/bin/startup.sh

# Default command with security hardening
CMD ["uvicorn", "${SERVICE_APP_MODULE}", \
     "--host", "0.0.0.0", \
     "--port", "${PORT}", \
     "--workers", "1", \
     "--loop", "uvloop", \
     "--http", "httptools", \
     "--access-log", \
     "--log-level", "info"]

# --- Security Audit Stage (Optional) ---
# This stage can be used to generate security reports
FROM security_scanner AS security_audit

# Copy final image for scanning
COPY --from=runtime / /

# Run comprehensive security audit
RUN echo "Running comprehensive security audit..." && \
    trivy filesystem --format json --output /audit-results.json / || true && \
    echo "Security audit completed. Results available at /audit-results.json"