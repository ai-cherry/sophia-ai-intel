# syntax=docker/dockerfile:1.4
# This template is designed for SOPHIA AI microservices to standardize builds,
# optimize image size, and enhance security through multi-stage builds and non-root user execution.

ARG PYTHON_VERSION=3.11-slim
ARG PYTHON_VERSION_MAJOR_MINOR=3.11

# --- Builder Stage ---
# This stage is responsible for installing all build-time dependencies and Python packages.
# It uses `python:PYTHON_VERSION-buster` to ensure `apt-get` and build tools are available.
FROM python:${PYTHON_VERSION}-bullseye AS builder

# Set environment variables for non-interactive installation and immediate output for Python applications.
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install common build-time system dependencies required for various Python packages.
# These include build tools, SSL libraries, and curl for health checks.
# `rm -rf /var/lib/apt/lists/*` cleans up apt cache to save space.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        openssh-client \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory for the application inside the container.
WORKDIR /app

# Copy `common/base-requirements.txt` to a well-known location within the build context first.
COPY platform/common/base-requirements.txt /tmp/base-requirements.txt

# Copy service-specific requirements, relative to the current service directory.
# The `SERVICE_REQUIREMENTS_PATH` argument allows each microservice to specify its own `requirements.txt`.
# Example: ARG SERVICE_REQUIREMENTS_PATH=services/my-service/requirements.txt
ARG SERVICE_REQUIREMENTS_PATH=mcp/enrichment-mcp/requirements.txt
COPY ${SERVICE_REQUIREMENTS_PATH} ./service-requirements.txt

# Install all requirements using the base and service-specific requirements.
# The local service requirements file should reference the base requirements using its /tmp path.
RUN pip install --no-cache-dir -r /tmp/base-requirements.txt -r ./service-requirements.txt && \
    echo "--- Builder Stage /usr/local/lib/ contents ---" && \
    ls -l /usr/local/lib/ && \
    echo "--- Builder Stage /usr/local/bin/ contents ---" && \
    ls -l /usr/local/bin/

# Copy the application source code, and also the platform directory for common modules.
# The `SERVICE_SOURCE_PATH` argument allows each microservice to specify its own application directory.
# Example: ARG SERVICE_SOURCE_PATH=services/my-service/src
ARG SERVICE_SOURCE_PATH=mcp/enrichment-mcp
COPY ${SERVICE_SOURCE_PATH} ./app
COPY platform ./platform


# --- Runtime Stage ---
# This stage creates a minimal production image, copying only essential artifacts from the builder stage.
# It uses the `python:PYTHON_VERSION-buster` image for a smaller footprint.
FROM python:${PYTHON_VERSION}-bullseye AS runtime

# Set environment variables for runtime, including unbuffered Python output and application port.
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Create a dedicated non-root user (`appuser`) for enhanced security.
# Also create the /app directory and set appropriate ownership.
RUN mkdir -p /app && \
    adduser --system --group appuser && \
    chown -R appuser:appuser /app
USER appuser

# Set the working directory for the non-root user.
WORKDIR /app

# Copy only the installed Python packages from the builder stage.
# This significantly reduces the final image size by excluding build dependents.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

RUN echo "--- Runtime Stage /usr/local/lib/ contents ---" && \
    ls -l /usr/local/lib/ && \
    echo "--- Runtime Stage /usr/local/bin/ contents ---" && \
    ls -l /usr/local/bin/

# Copy the application code and platform from the builder stage.
COPY --from=builder --chown=appuser:appuser /app /app
COPY --from=builder --chown=appuser:appuser /platform /platform

# Expose the port on which the application will listen.
EXPOSE ${PORT}

# Define a standardized HEALTHCHECK instruction using `curl`.
# This ensures that Kubernetes and other orchestrators can reliably determine service health.
# It assumes an accessible /health endpoint on the application.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Define the default command to run the application using uvicorn.
# This assumes the main FastAPI application instance is located at `app.main:app`.
CMD ["/bin/sh", "-c", "uvicorn app.app:app --host 0.0.0.0 --port ${PORT}"]