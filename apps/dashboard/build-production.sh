#!/bin/bash
# Production build script that bypasses workspace dependencies

echo "🔨 Starting production build for dashboard..."

# Clean any existing builds
rm -rf dist/ node_modules/

# Install dependencies directly (not using workspace)
npm install --no-optional --no-fund

# Check for TypeScript
if ! command -v tsc &> /dev/null; then
    echo "Installing TypeScript..."
    npm install -g typescript@latest
fi

# Build TypeScript
echo "📦 Building TypeScript..."
tsc

# Build with Vite
echo "🚀 Building with Vite..."
npx vite build

# Verify dist directory exists
if [ -d "dist" ]; then
    echo "✅ Build successful - dist directory created"
    ls -la dist/
    echo "📊 Build size:"
    du -sh dist/
else
    echo "❌ Build failed - no dist directory"
    exit 1
fi

echo "🎉 Production build complete!"
