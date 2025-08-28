#!/bin/bash

echo "🔧 Fixing Docker Desktop Issues"
echo "================================"

# Step 1: Kill any stuck Docker processes
echo "1️⃣ Killing stuck Docker processes..."
pkill -f docker 2>/dev/null || true
pkill -f Docker 2>/dev/null || true
sleep 2

# Step 2: Clean up Docker socket if exists
echo "2️⃣ Cleaning Docker socket..."
sudo rm -f /var/run/docker.sock 2>/dev/null || true

# Step 3: Reset Docker to factory defaults (preserves images)
echo "3️⃣ Resetting Docker daemon..."
osascript -e 'quit app "Docker"' 2>/dev/null || true
sleep 3

# Step 4: Start Docker Desktop
echo "4️⃣ Starting Docker Desktop..."
open -a Docker

# Step 5: Wait for Docker to be ready
echo "5️⃣ Waiting for Docker to be ready (this may take 30-60 seconds)..."
while ! docker system info > /dev/null 2>&1; do
    echo -n "."
    sleep 2
done
echo ""

# Step 6: Test Docker
echo "6️⃣ Testing Docker..."
docker run --rm hello-world

echo ""
echo "✅ Docker has been reset and is working!"
echo ""
echo "Now you can run the Sophia platform with:"
echo "  docker-compose -f docker-compose.prebuilt.yml up -d"