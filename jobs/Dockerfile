FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the reindex agent script
COPY reindex.py .

# Make the script executable
RUN chmod +x reindex.py

# Create proofs directory for output
RUN mkdir -p /tmp/proofs

# Run the reindex agent
CMD ["python", "reindex.py"]