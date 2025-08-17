#!/bin/bash
# Test Environment Setup Script for CI/CD
# Configures testing environment with proper dependencies and database setup

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_VERSION=${PYTHON_VERSION:-"3.11"}
TEST_ENV=${TEST_ENV:-"ci"}
DATABASE_TYPE=${DATABASE_TYPE:-"sqlite"}
INSTALL_DEPS=${INSTALL_DEPS:-"true"}
RUN_MIGRATIONS=${RUN_MIGRATIONS:-"true"}
SETUP_COVERAGE=${SETUP_COVERAGE:-"true"}

echo -e "${BLUE}🚀 Setting up test environment...${NC}"
echo "Python Version: $PYTHON_VERSION"
echo "Test Environment: $TEST_ENV"
echo "Database Type: $DATABASE_TYPE"

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if running in CI
if [[ "${CI:-false}" == "true" ]]; then
    echo -e "${BLUE}🔧 Detected CI environment${NC}"
    export TESTING=1
    export CI=1
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating test directories...${NC}"
mkdir -p test_data
mkdir -p logs
mkdir -p coverage_reports
mkdir -p test_reports
print_status "Test directories created"

# Setup Python environment
if [[ "$INSTALL_DEPS" == "true" ]]; then
    echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install core dependencies
    pip install -r requirements.txt
    
    # Install test-specific dependencies
    if [[ -f "requirements-test.txt" ]]; then
        pip install -r requirements-test.txt
    fi
    
    # Install development dependencies for CI
    pip install pytest-xdist pytest-html pytest-json-report
    
    print_status "Python dependencies installed"
fi

# Database setup
echo -e "${BLUE}🗄️  Setting up test database...${NC}"

case $DATABASE_TYPE in
    "sqlite")
        export TEST_DATABASE_URL="sqlite:///./test_data/test.db"
        echo "Using SQLite database: $TEST_DATABASE_URL"
        ;;
    "postgresql")
        DB_HOST=${POSTGRES_HOST:-"localhost"}
        DB_PORT=${POSTGRES_PORT:-"5432"}
        DB_USER=${POSTGRES_USER:-"testuser"}
        DB_PASS=${POSTGRES_PASSWORD:-"testpass"}
        DB_NAME=${POSTGRES_DB:-"testdb"}
        export TEST_DATABASE_URL="postgresql://$DB_USER:$DB_PASS@$DB_HOST:$DB_PORT/$DB_NAME"
        export DATABASE_URL="$TEST_DATABASE_URL"
        export ALLOW_DB_DROP="1"
        
        echo "Using PostgreSQL database: $TEST_DATABASE_URL"
        
        # Wait for PostgreSQL to be ready
        if command -v pg_isready &> /dev/null; then
            echo "Waiting for PostgreSQL to be ready..."
            until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; do
                echo "PostgreSQL is unavailable - sleeping"
                sleep 2
            done
            print_status "PostgreSQL is ready"
        else
            print_warning "pg_isready not available, skipping connection check"
        fi
        ;;
    *)
        print_error "Unsupported database type: $DATABASE_TYPE"
        exit 1
        ;;
esac

# Run database migrations
if [[ "$RUN_MIGRATIONS" == "true" && "$DATABASE_TYPE" == "postgresql" ]]; then
    echo -e "${BLUE}🔄 Running database migrations...${NC}"
    alembic upgrade head
    print_status "Database migrations completed"
fi

# Setup Redis for caching tests (if available)
if [[ -n "${REDIS_URL:-}" ]]; then
    echo -e "${BLUE}🔴 Redis configuration detected${NC}"
    export REDIS_URL="$REDIS_URL"
    echo "Redis URL: $REDIS_URL"
fi

# Setup coverage configuration
if [[ "$SETUP_COVERAGE" == "true" ]]; then
    echo -e "${BLUE}📊 Setting up coverage configuration...${NC}"
    
    # Create .coveragerc if it doesn't exist
    if [[ ! -f ".coveragerc" ]]; then
        cat > .coveragerc << EOF
[run]
source = app
omit = 
    */tests/*
    */test_*
    */conftest.py
    */venv/*
    */__pycache__/*
    */migrations/*
    */alembic/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:

fail_under = 40
precision = 2
show_missing = true

[html]
directory = htmlcov

[xml]
output = coverage.xml
EOF
    fi
    print_status "Coverage configuration ready"
fi

# Validate test environment
echo -e "${BLUE}🔍 Validating test environment...${NC}"

# Check Python version
PYTHON_ACTUAL=$(python --version | cut -d' ' -f2)
echo "Python version: $PYTHON_ACTUAL"

# Check critical packages
echo "Checking critical packages..."
python -c "import pytest; print(f'pytest: {pytest.__version__}')"
python -c "import fastapi; print(f'fastapi: {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'sqlalchemy: {sqlalchemy.__version__}')"

# Test database connection
echo "Testing database connection..."
python -c "
import os
from sqlalchemy import create_engine, text
try:
    engine = create_engine(os.environ['TEST_DATABASE_URL'])
    with engine.connect() as conn:
        result = conn.execute(text('SELECT 1')).scalar()
        assert result == 1
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

# Test import of main application
echo "Testing application import..."
python -c "
try:
    from app.main import app
    print('✅ Application import successful')
except Exception as e:
    print(f'❌ Application import failed: {e}')
    exit(1)
"

print_status "Test environment validation completed"

# Environment summary
echo -e "${BLUE}📋 Environment Summary${NC}"
echo "=================================="
echo "Test Database URL: ${TEST_DATABASE_URL}"
echo "Python Path: $(which python)"
echo "Working Directory: $(pwd)"
echo "Test Data Directory: $(pwd)/test_data"
echo "Environment Variables:"
echo "  TESTING: ${TESTING:-'not set'}"
echo "  CI: ${CI:-'not set'}"
echo "  DATABASE_URL: ${DATABASE_URL:-'not set'}"
echo "  REDIS_URL: ${REDIS_URL:-'not set'}"

# Generate test execution commands
echo -e "${BLUE}🎯 Suggested Test Commands${NC}"
echo "=================================="
echo "# Run all tests:"
echo "pytest tests/"
echo ""
echo "# Run specific test categories:"
echo "pytest tests/ -m unit"
echo "pytest tests/ -m integration"
echo "pytest tests/ -m async_tests"
echo ""
echo "# Run with coverage:"
echo "pytest tests/ --cov=app --cov-report=html"
echo ""
echo "# Run performance tests:"
echo "pytest tests/ -m performance --benchmark-only"
echo ""
echo "# Run in parallel (if pytest-xdist installed):"
echo "pytest tests/ -n auto"

echo -e "${GREEN}🎉 Test environment setup completed successfully!${NC}"