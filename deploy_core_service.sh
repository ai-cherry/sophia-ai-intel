#!/bin/bash
export PATH=$PATH:/Applications/Docker.app/Contents/Resources/bin
echo "🤖 Starting Sophia AI Core Service..."
docker run -d --name sophia-ai-core --link redis --link postgres -p 8080:8080 --env-file .env.production.real -e NODE_ENV=production -e REDIS_URL=redis://redis:6379 -e DATABASE_URL=postgresql://sophia:sophia_secure_password_2024@postgres:5432/sophia sophia-registry/sophia-ai-core:latest
echo "✅ Sophia AI Core started on http://localhost:8080"

