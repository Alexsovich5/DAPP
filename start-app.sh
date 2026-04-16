#!/bin/bash
# Dinner First — Docker development startup

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! docker info > /dev/null 2>&1; then
  echo "Docker is not running. Please start Docker Desktop and try again."
  exit 1
fi

case "${1:-up}" in
  up)
    echo "Starting Dinner First (Docker dev stack)..."
    docker compose -f "$PROJECT_ROOT/docker-compose.dev.yml" up --build
    ;;
  down)
    echo "Stopping all services..."
    docker compose -f "$PROJECT_ROOT/docker-compose.dev.yml" down
    ;;
  logs)
    docker compose -f "$PROJECT_ROOT/docker-compose.dev.yml" logs -f "${2:-}"
    ;;
  ps)
    docker compose -f "$PROJECT_ROOT/docker-compose.dev.yml" ps
    ;;
  reset)
    echo "Stopping services and removing volumes (database data will be deleted)..."
    docker compose -f "$PROJECT_ROOT/docker-compose.dev.yml" down -v
    ;;
  *)
    echo "Usage: $0 [up|down|logs [service]|ps|reset]"
    echo "  up           Start all services (default)"
    echo "  down         Stop all services"
    echo "  logs         Tail logs for all services"
    echo "  logs backend Tail logs for a specific service"
    echo "  ps           Show service status"
    echo "  reset        Stop and remove all volumes (wipes database)"
    exit 1
    ;;
esac
