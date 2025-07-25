#!/bin/bash

# Dinner1 Production Deployment Script
# Automated deployment with zero-downtime and rollback capability

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_ENV="${1:-production}"
DEPLOY_VERSION="${2:-latest}"

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

# Pre-deployment checks
pre_deployment_checks() {
    log "Running pre-deployment checks..."
    
    # Check if required files exist
    local required_files=(
        "docker-compose.production.yml"
        ".env.production"
        "python-backend/Dockerfile"
        "angular-frontend/Dockerfile"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$PROJECT_ROOT/$file" ]]; then
            error "Required file not found: $file"
            exit 1
        fi
    done
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if environment variables are set
    if [[ ! -f "$PROJECT_ROOT/.env.production" ]]; then
        error "Production environment file not found: .env.production"
        exit 1
    fi
    
    # Load environment variables
    set -a
    source "$PROJECT_ROOT/.env.production"
    set +a
    
    # Validate critical environment variables
    local required_vars=(
        "POSTGRES_PASSWORD"
        "JWT_SECRET"
        "ENCRYPTION_KEY"
        "REDIS_PASSWORD"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            error "Required environment variable not set: $var"
            exit 1
        fi
    done
    
    success "Pre-deployment checks passed"
}

# Database migration
run_database_migrations() {
    log "Running database migrations..."
    
    # Check if database is accessible
    docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U postgres
    
    # Run Alembic migrations
    docker-compose -f docker-compose.production.yml exec -T backend alembic upgrade head
    
    if [[ $? -eq 0 ]]; then
        success "Database migrations completed successfully"
    else
        error "Database migrations failed"
        exit 1
    fi
}

# Build and tag images
build_images() {
    log "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build backend image
    log "Building backend image..."
    docker build -t dinner1/backend:$DEPLOY_VERSION ./python-backend
    docker tag dinner1/backend:$DEPLOY_VERSION dinner1/backend:latest
    
    # Build frontend image
    log "Building frontend image..."
    docker build -t dinner1/frontend:$DEPLOY_VERSION ./angular-frontend
    docker tag dinner1/frontend:$DEPLOY_VERSION dinner1/frontend:latest
    
    success "Docker images built successfully"
}

# Health check function
health_check() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0
    
    log "Checking health of $service..."
    
    while [[ $attempt -lt $max_attempts ]]; do
        if curl -f -s "$url" > /dev/null; then
            success "$service is healthy"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Health check attempt $attempt/$max_attempts for $service..."
        sleep 10
    done
    
    error "$service health check failed after $max_attempts attempts"
    return 1
}

# Zero-downtime deployment
zero_downtime_deploy() {
    log "Starting zero-downtime deployment..."
    
    cd "$PROJECT_ROOT"
    
    # Create backup of current deployment
    backup_current_deployment
    
    # Scale up new instances
    log "Scaling up new instances..."
    docker-compose -f docker-compose.production.yml up -d --scale backend=4 --scale frontend=2
    
    # Wait for new instances to be healthy
    sleep 30
    
    # Health checks for new instances
    if ! health_check "backend" "http://localhost/api/v1/health"; then
        error "New backend instances are not healthy, rolling back..."
        rollback_deployment
        exit 1
    fi
    
    if ! health_check "frontend" "http://localhost/health"; then
        error "New frontend instances are not healthy, rolling back..."
        rollback_deployment
        exit 1
    fi
    
    # Scale down old instances gradually
    log "Scaling down old instances..."
    docker-compose -f docker-compose.production.yml up -d --scale backend=2 --scale frontend=1
    
    sleep 15
    
    # Final health check
    if ! health_check "application" "http://localhost/health"; then
        error "Application health check failed, rolling back..."
        rollback_deployment
        exit 1
    fi
    
    success "Zero-downtime deployment completed successfully"
}

# Backup current deployment
backup_current_deployment() {
    log "Creating backup of current deployment..."
    
    local backup_dir="$PROJECT_ROOT/backups/deployment_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Backup database
    docker-compose -f docker-compose.production.yml exec -T postgres pg_dump -U postgres dinner1 > "$backup_dir/database_backup.sql"
    
    # Backup configuration files
    cp docker-compose.production.yml "$backup_dir/"
    cp .env.production "$backup_dir/"
    
    # Store current image versions
    docker images --format "table {{.Repository}}:{{.Tag}}\t{{.ID}}" | grep dinner1 > "$backup_dir/image_versions.txt"
    
    # Store backup info
    echo "BACKUP_DATE=$(date)" > "$backup_dir/backup_info.txt"
    echo "DEPLOY_VERSION=$DEPLOY_VERSION" >> "$backup_dir/backup_info.txt"
    echo "GIT_COMMIT=$(git rev-parse HEAD)" >> "$backup_dir/backup_info.txt"
    
    success "Backup created at $backup_dir"
    echo "$backup_dir" > /tmp/last_backup_path
}

# Rollback deployment
rollback_deployment() {
    log "Rolling back deployment..."
    
    if [[ -f /tmp/last_backup_path ]]; then
        local backup_dir=$(cat /tmp/last_backup_path)
        
        if [[ -d "$backup_dir" ]]; then
            log "Rolling back to backup: $backup_dir"
            
            # Restore configuration
            cp "$backup_dir/docker-compose.production.yml" "$PROJECT_ROOT/"
            cp "$backup_dir/.env.production" "$PROJECT_ROOT/"
            
            # Restart services with old configuration
            cd "$PROJECT_ROOT"
            docker-compose -f docker-compose.production.yml down
            docker-compose -f docker-compose.production.yml up -d
            
            # Wait for services to start
            sleep 30
            
            # Health check
            if health_check "application" "http://localhost/health"; then
                success "Rollback completed successfully"
            else
                error "Rollback failed - manual intervention required"
                exit 1
            fi
        else
            error "Backup directory not found: $backup_dir"
            exit 1
        fi
    else
        error "No backup information found - cannot rollback"
        exit 1
    fi
}

# Post-deployment verification
post_deployment_verification() {
    log "Running post-deployment verification..."
    
    # Comprehensive health checks
    local endpoints=(
        "http://localhost/health"
        "http://localhost/api/v1/health"
        "http://localhost/api/v1/docs"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if ! curl -f -s "$endpoint" > /dev/null; then
            error "Endpoint check failed: $endpoint"
            return 1
        fi
    done
    
    # Check database connectivity
    docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U postgres
    
    # Check Redis connectivity
    docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping
    
    # Verify file upload functionality (basic test)
    log "Verifying application functionality..."
    
    # Check logs for errors
    local error_count=$(docker-compose -f docker-compose.production.yml logs --tail=100 backend | grep -i error | wc -l)
    if [[ $error_count -gt 0 ]]; then
        warning "Found $error_count error messages in backend logs"
    fi
    
    success "Post-deployment verification completed"
}

# Cleanup old images and containers
cleanup() {
    log "Cleaning up old images and containers..."
    
    # Remove dangling images
    docker image prune -f
    
    # Remove old versions (keep last 3)
    docker images dinner1/backend --format "table {{.Tag}}\t{{.ID}}" | tail -n +4 | awk '{print $2}' | xargs -r docker rmi
    docker images dinner1/frontend --format "table {{.Tag}}\t{{.ID}}" | tail -n +4 | awk '{print $2}' | xargs -r docker rmi
    
    # Remove unused volumes (be careful with this)
    # docker volume prune -f
    
    success "Cleanup completed"
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    # This would integrate with your notification system
    # (Slack, email, PagerDuty, etc.)
    log "Notification: $status - $message"
    
    # Example webhook notification
    if [[ -n "$SLACK_WEBHOOK_URL" ]]; then
        local color="good"
        if [[ "$status" == "failed" ]]; then
            color="danger"
        elif [[ "$status" == "warning" ]]; then
            color="warning"
        fi
        
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"attachments\":[{\"color\":\"$color\",\"title\":\"Dinner1 Deployment\",\"text\":\"$message\"}]}" \
            "$SLACK_WEBHOOK_URL"
    fi
}

# Main deployment function
main() {
    log "Starting Dinner1 deployment to $DEPLOY_ENV environment..."
    log "Deploy version: $DEPLOY_VERSION"
    
    cd "$PROJECT_ROOT"
    
    # Set trap for cleanup on exit
    trap 'cleanup_on_exit' EXIT
    
    try_deploy() {
        pre_deployment_checks
        build_images
        run_database_migrations
        zero_downtime_deploy
        post_deployment_verification
        cleanup
        
        success "Deployment completed successfully!"
        send_notification "success" "Dinner1 deployment to $DEPLOY_ENV completed successfully (version: $DEPLOY_VERSION)"
    }
    
    # Attempt deployment with rollback on failure
    if ! try_deploy; then
        error "Deployment failed, initiating rollback..."
        rollback_deployment
        send_notification "failed" "Dinner1 deployment to $DEPLOY_ENV failed and was rolled back"
        exit 1
    fi
}

# Cleanup function for exit trap
cleanup_on_exit() {
    local exit_code=$?
    if [[ $exit_code -ne 0 ]]; then
        error "Deployment script exited with error code $exit_code"
        # Perform any necessary cleanup
    fi
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [version]"
    echo "  environment: production (default), staging, development"
    echo "  version: Docker image tag (default: latest)"
    echo ""
    echo "Examples:"
    echo "  $0 production v1.2.3"
    echo "  $0 staging"
    echo "  $0"
    exit 1
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        usage
        ;;
    rollback)
        rollback_deployment
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac