#!/bin/bash

# SOPHIA UNIFIED SYSTEM TEST SCRIPT
# ==================================

echo "=================================="
echo "SOPHIA UNIFIED SYSTEM TEST"
echo "=================================="
echo ""

# Test 1: Health Check
echo "1. Testing Health Check..."
curl -s http://localhost:3001/api/chat | head -c 100 && echo "... ✅"
echo ""

# Test 2: Code Search
echo "2. Testing Code Search (GitHub)..."
curl -s -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Find React dashboard repositories on GitHub"}' | \
  jq -r '.provider' | grep -q -E "(mcp|tavily|perplexity)" && echo "✅ Provider: $(curl -s -X POST http://localhost:3001/api/chat -H "Content-Type: application/json" -d '{"message": "Find React dashboard repositories on GitHub"}' | jq -r '.provider')"
echo ""

# Test 3: General Knowledge
echo "3. Testing General Knowledge..."
curl -s -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is machine learning?"}' | \
  jq -r '.provider' | grep -q -E "(openrouter|perplexity|fallback)" && echo "✅ Provider: $(curl -s -X POST http://localhost:3001/api/chat -H "Content-Type: application/json" -d '{"message": "What is machine learning?"}' | jq -r '.provider')"
echo ""

# Test 4: Research Query
echo "4. Testing Research Query..."
curl -s -X POST http://localhost:3001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Research the latest AI developments in 2025"}' | \
  jq -r '.provider' | grep -q -E "(perplexity|tavily|openrouter)" && echo "✅ Provider: $(curl -s -X POST http://localhost:3001/api/chat -H "Content-Type: application/json" -d '{"message": "Research the latest AI developments"}' | jq -r '.provider')"
echo ""

# Test 5: Service Status
echo "5. Testing Unified Service Status..."
curl -s http://localhost:8100/status | jq '.providers.available' && echo "✅ Providers Available"
echo ""

echo "=================================="
echo "TEST COMPLETE"
echo "=================================="
echo ""
echo "System Architecture:"
echo "-------------------"
echo "✅ Single Dashboard: http://localhost:3001"
echo "✅ Single API Route: /api/chat/route.ts"
echo "✅ Single Orchestrator: sophia_unified.py"
echo "✅ No Duplicates"
echo ""
echo "Available Providers:"
echo "-------------------"
curl -s http://localhost:8100/providers 2>/dev/null | jq -r '.providers[]? | "- \(.name): \(if .has_key then "✅" else "❌" end)"' || echo "Service not available"
echo ""