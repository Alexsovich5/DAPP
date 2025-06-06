#!/bin/bash

# Dinner1 Application Startup Script
# Starts PostgreSQL database, Python backend, and Angular frontend

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/python-backend"
FRONTEND_DIR="$PROJECT_ROOT/angular-frontend"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    success "Docker is running"
}

# Start PostgreSQL database in Docker
start_database() {
    log "Starting PostgreSQL database..."
    
    # Check if container already exists
    if docker ps -a --format 'table {{.Names}}' | grep -q "dinner1-postgres"; then
        log "PostgreSQL container already exists. Starting it..."
        docker start dinner1-postgres
    else
        log "Creating new PostgreSQL container..."
        docker run -d \
            --name dinner1-postgres \
            -e POSTGRES_DB=dinner1 \
            -e POSTGRES_USER=postgres \
            -e POSTGRES_PASSWORD=postgres \
            -p 5432:5432 \
            postgres:15
    fi
    
    # Wait for database to be ready
    log "Waiting for database to be ready..."
    sleep 5
    
    # Test database connection
    for i in {1..30}; do
        if docker exec dinner1-postgres pg_isready -U postgres > /dev/null 2>&1; then
            success "PostgreSQL is ready"
            break
        fi
        if [ $i -eq 30 ]; then
            error "Database failed to start after 30 seconds"
            exit 1
        fi
        sleep 1
    done
}

# Start Python backend
start_backend() {
    log "Starting Python backend..."
    
    cd "$BACKEND_DIR"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        warning "Virtual environment not found. Creating it..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    
    log "Installing Python dependencies..."
    pip install -r requirements.txt > /dev/null 2>&1
    
    # Handle database migrations with error handling
    log "Running database migrations..."
    
    # Check for multiple heads and merge if necessary
    if alembic heads 2>/dev/null | wc -l | grep -q "2"; then
        warning "Multiple migration heads detected. Merging..."
        alembic merge heads -m "Auto-merge migration heads" 2>/dev/null || true
    fi
    
    # Run migrations with retry logic
    for i in {1..3}; do
        if alembic upgrade head 2>/dev/null; then
            success "Database migrations completed"
            break
        elif [ $i -eq 3 ]; then
            warning "Migration failed, but continuing with startup..."
            break
        else
            warning "Migration attempt $i failed, retrying..."
            sleep 2
        fi
    done
    
    # Start the backend server in background
    log "Starting FastAPI server on port 3001..."
    nohup python run.py > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > backend.pid
    
    # Wait for backend to start
    sleep 5
    
    # Test backend health with extended timeout
    for i in {1..60}; do
        if curl -s http://localhost:3001/health > /dev/null 2>&1; then
            success "Backend is running on http://localhost:3001"
            break
        elif curl -s http://localhost:3001/docs > /dev/null 2>&1; then
            success "Backend is running on http://localhost:3001 (docs available)"
            break
        fi
        if [ $i -eq 60 ]; then
            warning "Backend health check failed, but process may still be starting"
            log "Check backend.log for details: tail -f $BACKEND_DIR/backend.log"
        fi
        sleep 1
    done
}

# Start Angular frontend
start_frontend() {
    log "Starting Angular frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        log "Installing Angular dependencies..."
        npm install
    fi
    
    # Start the frontend server in background
    log "Starting Angular development server on port 4200..."
    nohup npm run start > frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > frontend.pid
    
    # Wait for frontend to start
    sleep 10
    
    # Test frontend
    for i in {1..60}; do
        if curl -s http://localhost:4200 > /dev/null; then
            success "Frontend is running on http://localhost:4200"
            break
        fi
        if [ $i -eq 60 ]; then
            error "Frontend failed to start after 60 seconds"
            exit 1
        fi
        sleep 1
    done
}

# Cleanup function
cleanup() {
    log "Shutting down services..."
    
    # Kill backend
    if [ -f "$BACKEND_DIR/backend.pid" ]; then
        BACKEND_PID=$(cat "$BACKEND_DIR/backend.pid")
        if ps -p $BACKEND_PID > /dev/null; then
            kill $BACKEND_PID
            rm "$BACKEND_DIR/backend.pid"
            success "Backend stopped"
        fi
    fi
    
    # Kill frontend
    if [ -f "$FRONTEND_DIR/frontend.pid" ]; then
        FRONTEND_PID=$(cat "$FRONTEND_DIR/frontend.pid")
        if ps -p $FRONTEND_PID > /dev/null; then
            kill $FRONTEND_PID
            rm "$FRONTEND_DIR/frontend.pid"
            success "Frontend stopped"
        fi
    fi
    
    # Stop database container
    if docker ps --format 'table {{.Names}}' | grep -q "dinner1-postgres"; then
        docker stop dinner1-postgres
        success "Database stopped"
    fi
    
    log "All services stopped"
}

# Trap cleanup on script exit
trap cleanup EXIT

# Main execution
main() {
    log "Starting Dinner1 Application..."
    
    check_docker
    start_database
    start_backend
    start_frontend
    
    success "All services are running!"
    echo ""
    echo "🚀 Application URLs:"
    echo "   Frontend: http://localhost:4200"
    echo "   Backend API: http://localhost:3001"
    echo "   API Docs: http://localhost:3001/docs"
    echo "   Database: localhost:5432 (dinner1)"
    echo ""
    echo "📝 Logs:"
    echo "   Backend: $BACKEND_DIR/backend.log"
    echo "   Frontend: $FRONTEND_DIR/frontend.log"
    echo ""
    echo "Press Ctrl+C to stop all services"
    
    # Keep script running
    while true; do
        sleep 1
    done
}

# Handle command line arguments
case "${1:-}" in
    "stop")
        cleanup
        exit 0
        ;;
    "logs")
        if [ -f "$BACKEND_DIR/backend.log" ]; then
            echo "=== Backend Logs ==="
            tail -f "$BACKEND_DIR/backend.log" &
        fi
        if [ -f "$FRONTEND_DIR/frontend.log" ]; then
            echo "=== Frontend Logs ==="
            tail -f "$FRONTEND_DIR/frontend.log" &
        fi
        wait
        ;;
    "")
        main
        ;;
    *)
        echo "Usage: $0 [stop|logs]"
        echo "  (no args) - Start all services"
        echo "  stop      - Stop all services"
        echo "  logs      - Show service logs"
        exit 1
        ;;
esac