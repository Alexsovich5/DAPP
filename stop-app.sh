#!/bin/bash

# Dinner1 Application Stop Script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/python-backend"
FRONTEND_DIR="$PROJECT_ROOT/angular-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

log "Stopping Dinner1 Application services..."

# Kill backend
if [ -f "$BACKEND_DIR/backend.pid" ]; then
    BACKEND_PID=$(cat "$BACKEND_DIR/backend.pid")
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        kill $BACKEND_PID
        rm "$BACKEND_DIR/backend.pid"
        success "Backend stopped"
    fi
else
    # Try to find and kill uvicorn processes
    pkill -f "uvicorn.*app.main:app" && success "Backend stopped (via process name)"
fi

# Kill frontend
if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
    FRONTEND_PID=$(cat "$FRONTEND_DIR/frontend.pid")
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        kill $FRONTEND_PID
        rm "$FRONTEND_DIR/frontend.pid"
        success "Frontend stopped"
    fi
else
    # Try to find and kill ng serve processes
    pkill -f "ng serve" && success "Frontend stopped (via process name)"
fi

# Stop database container
if docker ps --format 'table {{.Names}}' | grep -q "dinner1-postgres" 2>/dev/null; then
    docker stop dinner1-postgres
    success "Database stopped"
fi

log "All services stopped"