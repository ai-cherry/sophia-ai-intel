# Shared Python base image for Sophia AI services
# Multi-stage build with BuildKit optimization
FROM python:3.11-slim as base

# Set build arguments for BuildKit
ARG BUILDKIT_CONTEXT_KEEP_GIT_DIR=1

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 sophia

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
# This layer will be cached unless requirements change
COPY requirements*.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Create runtime stage
FROM base as runtime

# Copy application code
COPY --chown=sophia:sophia . .

# Switch to non-root user
USER sophia

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8080

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/healthz || exit 1

# Default command
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]