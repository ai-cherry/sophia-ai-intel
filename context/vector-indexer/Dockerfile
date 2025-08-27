# Sophia AI Vector Indexer Worker
# ================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker.py .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Environment variables (can be overridden at runtime)
ENV SERVICE_NAME="vector-indexer" \
    LOG_LEVEL=INFO \
    PYTHONUNBUFFERED=1 \
    CONTINUOUS_MODE=false \
    RUN_INTERVAL=60 \
    BATCH_SIZE=10 \
    CHUNK_SIZE=1000 \
    CHUNK_OVERLAP=200

# No health check for worker process (runs periodically or once)

# Run the worker
CMD ["python", "-u", "worker.py"]