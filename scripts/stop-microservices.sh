#!/bin/bash

# Dinner First Microservices Stop Script
# Phase 5: Advanced Features & Scale

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🛑 Stopping Dinner First Microservices Architecture"
echo "=================================================="

# Stop all services gracefully
echo "🔄 Stopping all microservices..."
docker-compose -f docker-compose.microservices.yml down --remove-orphans

# Optional: Remove volumes (uncomment to clean all data)
# echo "🗑️  Removing all data volumes..."
# docker-compose -f docker-compose.microservices.yml down -v

# Optional: Remove images (uncomment to clean all images)
# echo "🗑️  Removing all images..."
# docker-compose -f docker-compose.microservices.yml down --rmi all

echo ""
echo "✅ All microservices stopped successfully!"
echo ""
echo "💡 To restart: ./scripts/start-microservices.sh"
echo "💡 To remove all data: docker-compose -f docker-compose.microservices.yml down -v"
echo "💡 To remove all images: docker-compose -f docker-compose.microservices.yml down --rmi all"
