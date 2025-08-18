#!/bin/bash

# Dinner First CI/CD Environment Setup Script
# Configures the complete CI/CD infrastructure for the dating platform

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CICD_ENV_FILE="$PROJECT_ROOT/.env.cicd"
GITLAB_URL="http://localhost:8090"
JENKINS_URL="http://localhost:8084"
SONARQUBE_URL="http://localhost:9000"
NEXUS_URL="http://localhost:8081"
VAULT_URL="http://localhost:8200"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if Docker and Docker Compose are installed
check_prerequisites() {
    log "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        error "Docker daemon is not running. Please start Docker first."
    fi
    
    log "Prerequisites check passed ✓"
}

# Generate environment variables
generate_env_file() {
    log "Generating CI/CD environment file..."
    
    cat > "$CICD_ENV_FILE" << EOF
# Dinner First CI/CD Environment Configuration
# Generated on $(date)

# Database Passwords
DB_PASSWORD=$(openssl rand -base64 32)
SONAR_DB_PASSWORD=$(openssl rand -base64 32)

# Redis Configuration
REDIS_PASSWORD=$(openssl rand -base64 32)

# MinIO Configuration
MINIO_ACCESS_KEY=dinner_first_minio
MINIO_SECRET_KEY=$(openssl rand -base64 32)

# Application Secrets
SECRET_KEY=$(openssl rand -base64 64)
JWT_SECRET=$(openssl rand -base64 64)

# GitLab Configuration
GITLAB_ROOT_PASSWORD=$(openssl rand -base64 32)
GITLAB_RUNNER_REGISTRATION_TOKEN=$(openssl rand -hex 16)

# Jenkins Configuration
JENKINS_ADMIN_PASSWORD=$(openssl rand -base64 32)

# SonarQube Configuration
SONAR_ADMIN_PASSWORD=$(openssl rand -base64 32)

# Nexus Configuration
NEXUS_ADMIN_PASSWORD=$(openssl rand -base64 32)

# Vault Configuration
VAULT_ROOT_TOKEN=$(openssl rand -hex 16)
VAULT_UNSEAL_KEY=$(openssl rand -hex 16)

# Grafana Configuration
GRAFANA_PASSWORD=$(openssl rand -base64 32)

# External API Keys (to be set manually)
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here
VAPID_PUBLIC_KEY=your_vapid_public_key_here
VAPID_PRIVATE_KEY=your_vapid_private_key_here

# Monitoring
SLACK_WEBHOOK_URL=your_slack_webhook_url_here
EOF

    log "Environment file generated at $CICD_ENV_FILE"
    warn "Please update the external API keys in $CICD_ENV_FILE"
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p "$PROJECT_ROOT/data/"{postgres,uploads,prometheus,grafana,nexus,vault,minio}
    mkdir -p "$PROJECT_ROOT/monitoring/"{prometheus/rules,grafana/provisioning,alertmanager}
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Set proper permissions
    chmod 755 "$PROJECT_ROOT/data"/*
    
    log "Directories created ✓"
}

# Start the CI/CD infrastructure
start_infrastructure() {
    log "Starting CI/CD infrastructure..."
    
    cd "$PROJECT_ROOT"
    
    # Start the base CI/CD environment
    docker-compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to start..."
    sleep 30
    
    # Start the Dinner First application with CI/CD integration
    docker-compose -f docker-compose.yml -f docker-compose.cicd.yml up -d
    
    log "Infrastructure started ✓"
}

# Wait for services to be healthy
wait_for_services() {
    log "Waiting for services to be healthy..."
    
    local services=(
        "$GITLAB_URL:GitLab"
        "$JENKINS_URL:Jenkins" 
        "$NEXUS_URL:Nexus"
        "$VAULT_URL:Vault"
    )
    
    for service in "${services[@]}"; do
        IFS=':' read -r url name <<< "$service"
        info "Waiting for $name to be ready..."
        
        local timeout=300
        local elapsed=0
        
        while ! curl -sf "$url/health" &> /dev/null && ! curl -sf "$url" &> /dev/null; do
            if [[ $elapsed -ge $timeout ]]; then
                warn "$name did not start within $timeout seconds"
                break
            fi
            sleep 10
            elapsed=$((elapsed + 10))
        done
        
        if curl -sf "$url" &> /dev/null; then
            log "$name is ready ✓"
        fi
    done
}

# Configure GitLab
configure_gitlab() {
    log "Configuring GitLab..."
    
    # Wait for GitLab to be fully ready
    info "Waiting for GitLab to be ready (this may take a few minutes)..."
    sleep 60
    
    # Register GitLab Runner
    if docker exec gitlab-runner gitlab-runner verify; then
        log "GitLab Runner already registered"
    else
        info "Registering GitLab Runner..."
        docker exec gitlab-runner gitlab-runner register \
            --non-interactive \
            --url "$GITLAB_URL" \
            --registration-token "$(grep GITLAB_RUNNER_REGISTRATION_TOKEN "$CICD_ENV_FILE" | cut -d'=' -f2)" \
            --executor docker \
            --docker-image "docker:latest" \
            --docker-privileged true \
            --docker-volumes "/var/run/docker.sock:/var/run/docker.sock" \
            --description "Dinner First Docker Runner" \
            --tag-list "docker,dinner_first" \
            --run-untagged true \
            --locked false
    fi
    
    log "GitLab configured ✓"
}

# Configure SonarQube
configure_sonarqube() {
    log "Configuring SonarQube..."
    
    if curl -sf "$SONARQUBE_URL/api/system/status" &> /dev/null; then
        # Create SonarQube project
        local auth="admin:$(grep SONAR_ADMIN_PASSWORD "$CICD_ENV_FILE" | cut -d'=' -f2)"
        
        curl -u "$auth" -X POST "$SONARQUBE_URL/api/projects/create" \
            -d "project=dinner_first-dating-platform" \
            -d "name=Dinner First Dating Platform" || warn "SonarQube project might already exist"
        
        # Generate token for CI/CD
        local sonar_token
        sonar_token=$(curl -u "$auth" -X POST "$SONARQUBE_URL/api/user_tokens/generate" \
            -d "name=cicd-token" | jq -r '.token' 2>/dev/null || echo "failed")
        
        if [[ "$sonar_token" != "failed" ]]; then
            echo "SONAR_TOKEN=$sonar_token" >> "$CICD_ENV_FILE"
            log "SonarQube token generated and saved"
        fi
        
        log "SonarQube configured ✓"
    else
        warn "SonarQube is not responding, skipping configuration"
    fi
}

# Configure Nexus Repository
configure_nexus() {
    log "Configuring Nexus Repository..."
    
    if curl -sf "$NEXUS_URL/service/rest/v1/status" &> /dev/null; then
        info "Nexus is ready for configuration"
        
        # Create Docker repositories
        local auth="admin:$(grep NEXUS_ADMIN_PASSWORD "$CICD_ENV_FILE" | cut -d'=' -f2)"
        
        # Create hosted Docker repository
        curl -u "$auth" -X POST "$NEXUS_URL/service/rest/v1/repositories/docker/hosted" \
            -H "Content-Type: application/json" \
            -d '{
                "name": "docker-hosted",
                "online": true,
                "storage": {
                    "blobStoreName": "default",
                    "strictContentTypeValidation": true,
                    "writePolicy": "ALLOW"
                },
                "docker": {
                    "v1Enabled": false,
                    "forceBasicAuth": true,
                    "httpPort": 8082
                }
            }' || warn "Docker repository might already exist"
        
        log "Nexus configured ✓"
    else
        warn "Nexus is not responding, skipping configuration"
    fi
}

# Configure Vault
configure_vault() {
    log "Configuring Vault..."
    
    if curl -sf "$VAULT_URL/v1/sys/health" &> /dev/null; then
        local root_token
        root_token=$(grep VAULT_ROOT_TOKEN "$CICD_ENV_FILE" | cut -d'=' -f2)
        
        # Initialize Vault (if not already done)
        if ! curl -sf -H "X-Vault-Token: $root_token" "$VAULT_URL/v1/sys/init" &> /dev/null; then
            info "Initializing Vault..."
            docker exec vault-secrets vault operator init -key-shares=1 -key-threshold=1
        fi
        
        # Enable KV secrets engine
        curl -H "X-Vault-Token: $root_token" -X POST "$VAULT_URL/v1/sys/mounts/secret" \
            -d '{"type":"kv-v2"}' || warn "KV engine might already be enabled"
        
        log "Vault configured ✓"
    else
        warn "Vault is not responding, skipping configuration"
    fi
}

# Import Grafana dashboards
configure_grafana() {
    log "Configuring Grafana..."
    
    # Copy dashboards to Grafana
    docker cp "$PROJECT_ROOT/monitoring/grafana-dashboards/." grafana-monitoring:/var/lib/grafana/dashboards/
    
    # Restart Grafana to load dashboards
    docker restart grafana-monitoring
    
    log "Grafana configured ✓"
}

# Display access information
show_access_info() {
    log "CI/CD Environment Setup Complete!"
    
    echo ""
    echo "======================================"
    echo "  🚀 DINNER1 CI/CD ACCESS INFORMATION"
    echo "======================================"
    echo ""
    echo "📊 GitLab CE:          http://localhost:8090"
    echo "🔧 Jenkins:           http://localhost:8084"
    echo "📈 SonarQube:         http://localhost:9000"
    echo "📦 Nexus Repository:  http://localhost:8081"
    echo "🔐 Vault:             http://localhost:8200"
    echo "📉 Prometheus:        http://localhost:9091"
    echo "📊 Grafana:           http://localhost:3000"
    echo "🔔 Alertmanager:      http://localhost:9093"
    echo "🐳 Portainer:         https://localhost:9443"
    echo "🌐 Traefik Dashboard: http://localhost:8083"
    echo ""
    echo "💝 Dinner First Application:"
    echo "   Frontend:          http://localhost:4200"
    echo "   Backend API:       http://localhost:8000"
    echo "   API Docs:          http://localhost:8000/docs"
    echo ""
    echo "🔑 Default Credentials:"
    echo "   Check $CICD_ENV_FILE for passwords"
    echo ""
    echo "📝 Next Steps:"
    echo "   1. Update external API keys in $CICD_ENV_FILE"
    echo "   2. Configure GitLab project and push your code"
    echo "   3. Set up CI/CD variables in GitLab"
    echo "   4. Run your first pipeline!"
    echo ""
    echo "📚 Documentation:"
    echo "   CI/CD Pipeline: .gitlab-ci.yml"
    echo "   Helm Charts:    helm/dinner_first/"
    echo "   Monitoring:     monitoring/"
    echo ""
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    docker-compose -f docker-compose.yml -f docker-compose.cicd.yml down
}

# Main execution
main() {
    log "Starting Dinner First CI/CD Environment Setup"
    
    check_prerequisites
    generate_env_file
    create_directories
    start_infrastructure
    wait_for_services
    configure_gitlab
    configure_sonarqube
    configure_nexus
    configure_vault
    configure_grafana
    show_access_info
    
    log "Setup completed successfully! 🎉"
}

# Handle script interruption
trap cleanup EXIT

# Parse command line arguments
case "${1:-setup}" in
    "setup")
        main
        ;;
    "start")
        log "Starting CI/CD environment..."
        start_infrastructure
        ;;
    "stop")
        log "Stopping CI/CD environment..."
        docker-compose -f docker-compose.yml -f docker-compose.cicd.yml down
        ;;
    "restart")
        log "Restarting CI/CD environment..."
        docker-compose -f docker-compose.yml -f docker-compose.cicd.yml restart
        ;;
    "logs")
        docker-compose -f docker-compose.yml -f docker-compose.cicd.yml logs -f "${2:-}"
        ;;
    "status")
        docker-compose -f docker-compose.yml -f docker-compose.cicd.yml ps
        ;;
    "clean")
        log "Cleaning up CI/CD environment..."
        docker-compose -f docker-compose.yml -f docker-compose.cicd.yml down -v
        docker system prune -f
        rm -rf "$PROJECT_ROOT/data"
        ;;
    *)
        echo "Usage: $0 {setup|start|stop|restart|logs|status|clean}"
        echo ""
        echo "Commands:"
        echo "  setup   - Full setup of CI/CD environment"
        echo "  start   - Start all services"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  logs    - Show logs (optionally for specific service)"
        echo "  status  - Show service status"
        echo "  clean   - Clean up everything"
        exit 1
        ;;
esac