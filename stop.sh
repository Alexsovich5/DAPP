#!/bin/bash

# Dinner App Stop Script
# This script stops all services for the Dinner App

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

print_status "Stopping Dinner App services..."
print_status "======================================"

# Stop processes on specific ports
print_step "Stopping services on known ports..."

# Stop Angular (port 4200)
if lsof -Pi :4200 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_step "Stopping Angular frontend (port 4200)..."
    lsof -ti:4200 | xargs kill -15 2>/dev/null || true
else
    print_warning "No service found on port 4200"
fi

# Stop FastAPI (port 8000)
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_step "Stopping FastAPI backend (port 8000)..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
else
    print_warning "No service found on port 8000"
fi

# Stop any remaining node/python processes from this project
print_step "Stopping any remaining project processes..."

# Kill any node processes running in the Angular directory
pkill -f "interface/Angular" 2>/dev/null || true

# Kill any python processes running from backend_py
pkill -f "backend_py" 2>/dev/null || true

# Stop Docker containers
if command_exists docker-compose; then
    print_step "Stopping Docker containers..."
    docker-compose down 2>/dev/null || print_warning "No Docker containers to stop"
else
    print_warning "Docker Compose not found, skipping container shutdown"
fi

# Optional: Stop PostgreSQL container specifically (if running)
if command_exists docker && docker ps -q -f name=dinner1-postgres >/dev/null 2>&1; then
    print_step "Stopping PostgreSQL container..."
    docker stop dinner1-postgres 2>/dev/null || true
fi

print_status "======================================"
print_status "🛑 All Dinner App services have been stopped!"
print_status "======================================"