#!/bin/bash
# Build script for consolidated services

set -e

SERVICE_NAME=${1:-"all"}
REGISTRY=${REGISTRY:-"sophia-registry"}

build_service() {
    local service=$1
    echo "Building $service..."
    
    docker build \
        --build-arg SERVICE_NAME=$service \
        -f dockerfiles/Dockerfile.python-ml \
        -t $REGISTRY/$service:latest \
        --progress=plain \
        .
}

case $SERVICE_NAME in
    "sophia-ai-core")
        build_service "sophia-ai-core"
        ;;
    "sophia-business-intel")
        build_service "sophia-business-intel"
        ;;
    "sophia-communications")
        build_service "sophia-communications"
        ;;
    "sophia-development")
        build_service "sophia-development"
        ;;
    "sophia-orchestration")
        build_service "sophia-orchestration"
        ;;
    "sophia-infrastructure")
        build_service "sophia-infrastructure"
        ;;
    "all")
        for service in sophia-ai-core sophia-business-intel sophia-communications sophia-development sophia-orchestration sophia-infrastructure; do
            build_service $service
        done
        ;;
    *)
        echo "Unknown service: $SERVICE_NAME"
        echo "Available: sophia-ai-core, sophia-business-intel, sophia-communications, sophia-development, sophia-orchestration, sophia-infrastructure, all"
        exit 1
        ;;
esac

echo "Build completed for $SERVICE_NAME"