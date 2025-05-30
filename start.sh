#!/bin/bash

# Dinner App Startup Script
# This script starts all necessary services for the Dinner App

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for a service to be ready
wait_for_service() {
    local service_name=$1
    local port=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    print_step "Waiting for $service_name to be ready on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if check_port $port; then
            print_status "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to start after $((max_attempts * 2)) seconds"
    return 1
}

# Function to cleanup on exit
cleanup() {
    print_warning "Shutting down services..."
    
    # Kill background processes
    jobs -p | xargs -r kill 2>/dev/null || true
    
    # Stop Docker containers
    if command_exists docker-compose; then
        docker-compose down 2>/dev/null || true
    fi
    
    print_status "Cleanup completed"
}

# Set trap for cleanup on script exit
trap cleanup EXIT INT TERM

# Main script starts here
print_status "Starting Dinner App..."
print_status "======================================"

# Check prerequisites
print_step "Checking prerequisites..."

if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command_exists docker-compose; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

if ! command_exists node; then
    print_error "Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists npm; then
    print_error "npm is not installed. Please install npm first."
    exit 1
fi

if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

print_status "All prerequisites are met!"

# Check if services are already running
if check_port 5432; then
    print_warning "PostgreSQL is already running on port 5432"
else
    # Start PostgreSQL with Docker
    print_step "Starting PostgreSQL database..."
    docker-compose up -d postgres
    
    # Wait for PostgreSQL to be ready
    wait_for_service "PostgreSQL" 5432
fi

if check_port 8000; then
    print_warning "Backend is already running on port 8000"
else
    # Start Backend
    print_step "Starting Python FastAPI backend..."
    
    # Check if virtual environment exists
    if [ ! -d "backend_py/venv" ]; then
        print_step "Creating Python virtual environment..."
        cd backend_py
        python3 -m venv venv
        cd ..
    fi
    
    # Activate virtual environment and install dependencies
    cd backend_py
    source venv/bin/activate
    
    # Install requirements if needed
    if [ ! -f "venv/.deps_installed" ] || [ requirements.txt -nt venv/.deps_installed ]; then
        print_step "Installing Python dependencies..."
        pip install -r requirements.txt
        touch venv/.deps_installed
    fi
    
    # Run database migrations
    print_step "Running database migrations..."
    alembic upgrade head 2>/dev/null || print_warning "Migration might have failed, but continuing..."
    
    # Start the backend server in background
    print_step "Starting FastAPI server..."
    python run.py &
    BACKEND_PID=$!
    cd ..
    
    # Wait for backend to be ready
    wait_for_service "Backend API" 8000
fi

if check_port 4200; then
    print_warning "Frontend is already running on port 4200"
else
    # Start Frontend
    print_step "Starting Angular frontend..."
    
    cd interface/Angular
    
    # Install npm dependencies if needed
    if [ ! -d "node_modules" ] || [ package.json -nt node_modules/.package-lock.json ]; then
        print_step "Installing npm dependencies..."
        npm install
        touch node_modules/.package-lock.json 2>/dev/null || true
    fi
    
    # Start the frontend server in background
    print_step "Starting Angular development server..."
    npm start &
    FRONTEND_PID=$!
    cd ../..
    
    # Wait for frontend to be ready
    wait_for_service "Angular Frontend" 4200
fi

# Print success message with URLs
print_status "======================================"
print_status "🎉 Dinner App is now running!"
print_status "======================================"
echo ""
print_status "📱 Frontend (Angular): http://localhost:4200"
print_status "🔧 Backend API (FastAPI): http://localhost:8000"
print_status "📚 API Documentation: http://localhost:8000/api/docs"
print_status "🗄️  Database (PostgreSQL): localhost:5432"
echo ""
print_status "Press Ctrl+C to stop all services"
echo ""

# Keep script running and show logs
print_step "Monitoring services... (Press Ctrl+C to stop)"

# Function to check if services are still running
check_services() {
    while true; do
        # Check if any background job has failed
        for job in $(jobs -p); do
            if ! kill -0 $job 2>/dev/null; then
                print_error "A service has stopped unexpectedly"
                return 1
            fi
        done
        
        # Check if ports are still in use
        if ! check_port 5432; then
            print_error "PostgreSQL has stopped"
            return 1
        fi
        
        if ! check_port 8000; then
            print_error "Backend API has stopped"
            return 1
        fi
        
        if ! check_port 4200; then
            print_error "Frontend has stopped"
            return 1
        fi
        
        sleep 5
    done
}

# Monitor services
check_services || {
    print_error "One or more services have failed"
    exit 1
}