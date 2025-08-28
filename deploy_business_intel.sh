#!/bin/bash
export PATH=$PATH:/Applications/Docker.app/Contents/Resources/bin
echo "📊 Starting Sophia Business Intel Service..."
docker run -d --name sophia-business-intel --link redis --link postgres -p 8081:8081 --env-file .env.production.real -e NODE_ENV=production -e REDIS_URL=redis://redis:6379 -e DATABASE_URL=postgresql://sophia:sophia_secure_password_2024@postgres:5432/sophia sophia-registry/sophia-business-intel:latest
echo "✅ Sophia Business Intel started on http://localhost:8081"

