# syntax=docker/dockerfile:1.4
# This template is designed for SOPHIA AI microservices to standardize builds,
# optimize image size, and enhance security through multi-stage builds and non-root user execution.

ARG PYTHON_VERSION=3.11-slim

# --- Builder Stage ---
# This stage is responsible for installing all build-time dependencies and Python packages.
# It uses `python:PYTHON_VERSION-buster` to ensure `apt-get` and build tools are available.
FROM python:${PYTHON_VERSION} AS builder

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

# Copy the common base Python requirements and install them.
# These packages are shared across all SOPHIA AI microservices.
COPY platform/common/base-requirements.txt ./platform/common/base-requirements.txt
RUN pip install --no-cache-dir -r ./platform/common/base-requirements.txt

# Copy service-specific requirements and install them.
# The `SERVICE_REQUIREMENTS_PATH` argument allows each microservice to specify its own `requirements.txt`.
# Example: ARG SERVICE_REQUIREMENTS_PATH=services/my-service/requirements.txt
ARG SERVICE_REQUIREMENTS_PATH=services/agno-teams/requirements.txt
COPY ${SERVICE_REQUIREMENTS_PATH} ./requirements.txt
RUN pip install --no-cache-dir -r ./requirements.txt

# Copy the application source code.
# The `SERVICE_SOURCE_PATH` argument allows each microservice to specify its own application directory.
# Example: ARG SERVICE_SOURCE_PATH=services/my-service/src
ARG SERVICE_SOURCE_PATH=services/agno-teams/src
COPY ${SERVICE_SOURCE_PATH} ./app


# --- Runtime Stage ---
# This stage creates a minimal production image, copying only essential artifacts from the builder stage.
# It uses the `python:PYTHON_VERSION-buster` image for a smaller footprint.
FROM python:${PYTHON_VERSION} AS runtime

# Set environment variables for runtime, including unbuffered Python output and application port.
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Create a dedicated non-root user (`appuser`) for enhanced security.
# The application will run as this user, limiting potential damage in case of a security breach.
RUN adduser --system --group appuser

# Set the working directory for the application.
WORKDIR /app

# Copy only the installed Python packages from the builder stage.
# This significantly reduces the final image size by excluding build dependents.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code from the builder stage.
COPY --from=builder /app /app

# Set ownership of /app to appuser after directory and files exist
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port on which the application will listen.
EXPOSE ${PORT}

# Define a standardized HEALTHCHECK instruction using `curl`.
# This ensures that Kubernetes and other orchestrators can reliably determine service health.
# It assumes an accessible /health endpoint on the application.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:${PORT}/health || exit 1

# Define the default command to run the application using uvicorn.
# This assumes the main FastAPI application instance is located at `app.main:app`.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "${PORT}"]