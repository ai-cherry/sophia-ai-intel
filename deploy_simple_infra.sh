#!/bin/bash
export PATH=$PATH:/Applications/Docker.app/Contents/Resources/bin
echo "🚀 Starting Sophia AI Local Deployment..."
echo "1️⃣ Starting Redis..."
docker run -d --name redis --network-alias redis -p 6380:6379 redis:7-alpine
echo "2️⃣ Starting PostgreSQL..."  
docker run -d --name postgres --network-alias postgres -p 5433:5432 -e POSTGRES_DB=sophia -e POSTGRES_USER=sophia -e POSTGRES_PASSWORD=sophia_secure_password_2024 postgres:15-alpine
echo "✅ Core infrastructure started!"
echo "💾 Access: PostgreSQL=localhost:5433, Redis=localhost:6380"

