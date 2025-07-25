#!/bin/bash

# Dinner1 Production Secrets Setup Script
# Generates secure secrets and configures environment variables

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env.production"
SECRETS_DIR="$PROJECT_ROOT/secrets"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

# Generate secure random string
generate_secret() {
    local length=${1:-32}
    openssl rand -hex $length 2>/dev/null || python3 -c "import secrets; print(secrets.token_hex($length))"
}

# Generate JWT secret
generate_jwt_secret() {
    openssl rand -base64 64 | tr -d "=+/" | cut -c1-64
}

# Generate Fernet encryption key
generate_encryption_key() {
    python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
}

# Generate PostgreSQL password
generate_postgres_password() {
    generate_secret 16
}

# Generate Redis password
generate_redis_password() {
    generate_secret 16
}

# Check if required tools are installed
check_dependencies() {
    log "Checking dependencies..."
    
    local missing_tools=()
    
    if ! command -v openssl &> /dev/null; then
        missing_tools+=("openssl")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_tools+=("python3")
    fi
    
    if ! python3 -c "import cryptography" &> /dev/null; then
        missing_tools+=("python3-cryptography")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        error "Missing required tools: ${missing_tools[*]}"
        echo "Please install missing dependencies:"
        echo "  Ubuntu/Debian: sudo apt-get install openssl python3 python3-pip && pip3 install cryptography"
        echo "  macOS: brew install openssl python3 && pip3 install cryptography"
        exit 1
    fi
    
    success "All dependencies are installed"
}

# Create secrets directory
create_secrets_directory() {
    log "Creating secrets directory..."
    
    mkdir -p "$SECRETS_DIR"
    chmod 700 "$SECRETS_DIR"
    
    success "Secrets directory created at $SECRETS_DIR"
}

# Generate database encryption key
generate_database_encryption() {
    log "Generating database encryption configuration..."
    
    local key=$(generate_secret 32)
    echo "$key" > "$SECRETS_DIR/db_encryption_key"
    chmod 600 "$SECRETS_DIR/db_encryption_key"
    
    success "Database encryption key generated"
}

# Generate SSL certificate (self-signed for development/staging)
generate_ssl_certificate() {
    local domain=${1:-dinner1.local}
    
    log "Generating SSL certificate for $domain..."
    
    mkdir -p "$SECRETS_DIR/ssl"
    
    # Generate private key
    openssl genrsa -out "$SECRETS_DIR/ssl/dinner1.key" 2048
    
    # Generate certificate signing request
    openssl req -new -key "$SECRETS_DIR/ssl/dinner1.key" -out "$SECRETS_DIR/ssl/dinner1.csr" -subj "/C=US/ST=CA/L=San Francisco/O=Dinner1/CN=$domain"
    
    # Generate self-signed certificate
    openssl x509 -req -days 365 -in "$SECRETS_DIR/ssl/dinner1.csr" -signkey "$SECRETS_DIR/ssl/dinner1.key" -out "$SECRETS_DIR/ssl/dinner1.crt"
    
    # Set proper permissions
    chmod 600 "$SECRETS_DIR/ssl/dinner1.key"
    chmod 644 "$SECRETS_DIR/ssl/dinner1.crt"
    
    # Clean up CSR
    rm "$SECRETS_DIR/ssl/dinner1.csr"
    
    success "SSL certificate generated for $domain"
    warning "This is a self-signed certificate. Use a proper CA certificate in production."
}

# Generate environment file with secrets
generate_environment_file() {
    log "Generating production environment file..."
    
    if [[ -f "$ENV_FILE" ]]; then
        warning "Environment file already exists. Creating backup..."
        cp "$ENV_FILE" "$ENV_FILE.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Copy example file as base
    cp "$PROJECT_ROOT/.env.production.example" "$ENV_FILE"
    
    # Generate secrets
    local jwt_secret=$(generate_jwt_secret)
    local encryption_key=$(generate_encryption_key)
    local postgres_password=$(generate_postgres_password)
    local redis_password=$(generate_redis_password)
    local app_secret=$(generate_secret 32)
    
    # Replace placeholders in environment file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/your_jwt_secret_key_here_32_characters_minimum/$jwt_secret/g" "$ENV_FILE"
        sed -i '' "s/your_encryption_key_here_for_sensitive_data/$encryption_key/g" "$ENV_FILE"
        sed -i '' "s/your_secure_password/$postgres_password/g" "$ENV_FILE"
        sed -i '' "s/your_secure_redis_password/$redis_password/g" "$ENV_FILE"
    else
        # Linux
        sed -i "s/your_jwt_secret_key_here_32_characters_minimum/$jwt_secret/g" "$ENV_FILE"
        sed -i "s/your_encryption_key_here_for_sensitive_data/$encryption_key/g" "$ENV_FILE"
        sed -i "s/your_secure_password/$postgres_password/g" "$ENV_FILE"
        sed -i "s/your_secure_redis_password/$redis_password/g" "$ENV_FILE"
    fi
    
    # Set proper permissions
    chmod 600 "$ENV_FILE"
    
    # Store secrets separately for reference
    cat > "$SECRETS_DIR/generated_secrets.txt" << EOF
# Generated Secrets for Dinner1 Production
# Generated on: $(date)
# WARNING: Keep this file secure and never commit to version control

JWT_SECRET=$jwt_secret
ENCRYPTION_KEY=$encryption_key
POSTGRES_PASSWORD=$postgres_password
REDIS_PASSWORD=$redis_password
APP_SECRET=$app_secret

# SSL Certificate paths
SSL_CERT_PATH=$SECRETS_DIR/ssl/dinner1.crt
SSL_KEY_PATH=$SECRETS_DIR/ssl/dinner1.key

EOF
    
    chmod 600 "$SECRETS_DIR/generated_secrets.txt"
    
    success "Environment file generated with secure secrets"
}

# Generate Docker secrets
generate_docker_secrets() {
    log "Generating Docker secrets..."
    
    mkdir -p "$SECRETS_DIR/docker"
    
    # JWT Secret
    echo "$(generate_jwt_secret)" > "$SECRETS_DIR/docker/jwt_secret"
    
    # Database password
    echo "$(generate_postgres_password)" > "$SECRETS_DIR/docker/postgres_password"
    
    # Redis password
    echo "$(generate_redis_password)" > "$SECRETS_DIR/docker/redis_password"
    
    # Encryption key
    echo "$(generate_encryption_key)" > "$SECRETS_DIR/docker/encryption_key"
    
    # Set proper permissions
    chmod 600 "$SECRETS_DIR/docker/"*
    
    success "Docker secrets generated"
}

# Generate Kubernetes secrets manifest
generate_k8s_secrets() {
    log "Generating Kubernetes secrets manifest..."
    
    local jwt_secret_b64=$(echo -n "$(generate_jwt_secret)" | base64)
    local postgres_password_b64=$(echo -n "$(generate_postgres_password)" | base64)
    local redis_password_b64=$(echo -n "$(generate_redis_password)" | base64)
    local encryption_key_b64=$(echo -n "$(generate_encryption_key)" | base64)
    
    cat > "$SECRETS_DIR/k8s-secrets.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: dinner1-secrets
  namespace: dinner1-production
type: Opaque
data:
  jwt-secret: $jwt_secret_b64
  postgres-password: $postgres_password_b64
  redis-password: $redis_password_b64
  encryption-key: $encryption_key_b64
---
apiVersion: v1
kind: Secret
metadata:
  name: dinner1-ssl
  namespace: dinner1-production
type: kubernetes.io/tls
data:
  tls.crt: $(base64 -i "$SECRETS_DIR/ssl/dinner1.crt" 2>/dev/null || base64 < "$SECRETS_DIR/ssl/dinner1.crt")
  tls.key: $(base64 -i "$SECRETS_DIR/ssl/dinner1.key" 2>/dev/null || base64 < "$SECRETS_DIR/ssl/dinner1.key")
EOF
    
    chmod 600 "$SECRETS_DIR/k8s-secrets.yaml"
    
    success "Kubernetes secrets manifest generated"
}

# Generate AWS Secrets Manager commands
generate_aws_secrets() {
    log "Generating AWS Secrets Manager commands..."
    
    cat > "$SECRETS_DIR/aws-secrets.sh" << 'EOF'
#!/bin/bash
# AWS Secrets Manager setup commands for Dinner1

# Read secrets from generated file
source generated_secrets.txt

# Create secrets in AWS Secrets Manager
aws secretsmanager create-secret \
    --name "dinner1/production/jwt-secret" \
    --description "JWT secret for Dinner1 production" \
    --secret-string "$JWT_SECRET"

aws secretsmanager create-secret \
    --name "dinner1/production/database-password" \
    --description "Database password for Dinner1 production" \
    --secret-string "$POSTGRES_PASSWORD"

aws secretsmanager create-secret \
    --name "dinner1/production/redis-password" \
    --description "Redis password for Dinner1 production" \
    --secret-string "$REDIS_PASSWORD"

aws secretsmanager create-secret \
    --name "dinner1/production/encryption-key" \
    --description "Encryption key for Dinner1 production" \
    --secret-string "$ENCRYPTION_KEY"

echo "AWS Secrets Manager secrets created successfully"
EOF
    
    chmod +x "$SECRETS_DIR/aws-secrets.sh"
    
    success "AWS Secrets Manager commands generated"
}

# Validate environment file
validate_environment_file() {
    log "Validating environment file..."
    
    local required_vars=(
        "JWT_SECRET"
        "ENCRYPTION_KEY"
        "DATABASE_URL"
        "REDIS_URL"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "your_.*_here" "$ENV_FILE"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        error "Missing or incomplete environment variables: ${missing_vars[*]}"
        return 1
    fi
    
    success "Environment file validation passed"
}

# Generate security audit checklist
generate_security_checklist() {
    log "Generating security checklist..."
    
    cat > "$SECRETS_DIR/security-checklist.md" << EOF
# Dinner1 Production Security Checklist

## Pre-Deployment Security Review

### Secrets Management
- [ ] All secrets have been generated using cryptographically secure methods
- [ ] No secrets are hardcoded in source code
- [ ] Environment files have proper permissions (600)
- [ ] Secrets are stored in a secure secrets management system
- [ ] Secrets rotation schedule is defined

### Database Security
- [ ] Database password is strong and unique
- [ ] Database access is restricted to application servers only
- [ ] Database encryption at rest is enabled
- [ ] Database backups are encrypted
- [ ] Database connection uses SSL/TLS

### Application Security
- [ ] JWT secrets are unique and strong
- [ ] Password hashing uses strong algorithms (bcrypt)
- [ ] All sensitive data is encrypted with proper keys
- [ ] Rate limiting is configured for all endpoints
- [ ] CORS is properly configured
- [ ] Security headers are implemented

### Infrastructure Security
- [ ] SSL/TLS certificates are valid and properly configured
- [ ] Firewall rules restrict access to necessary ports only
- [ ] Server access is restricted to authorized personnel
- [ ] Regular security updates are scheduled
- [ ] Monitoring and alerting is configured

### Compliance
- [ ] GDPR compliance measures are implemented
- [ ] Data retention policies are configured
- [ ] User consent management is functional
- [ ] Privacy policy is up to date
- [ ] Terms of service are current

### Monitoring
- [ ] Security event logging is enabled
- [ ] Anomaly detection is configured
- [ ] Incident response procedures are documented
- [ ] Regular security audits are scheduled

## Post-Deployment Verification
- [ ] All services are running with expected configurations
- [ ] Security scans show no critical vulnerabilities
- [ ] Monitoring alerts are functioning
- [ ] Backup and recovery procedures are tested

Generated on: $(date)
EOF
    
    success "Security checklist generated"
}

# Generate .gitignore for secrets
update_gitignore() {
    log "Updating .gitignore for secrets..."
    
    local gitignore_file="$PROJECT_ROOT/.gitignore"
    
    # Add secrets-related patterns to .gitignore
    cat >> "$gitignore_file" << EOF

# Secrets and environment files
.env.production
.env.staging
.env.local
secrets/
*.key
*.crt
*.pem
*_secret*
*_password*
*_token*

# AWS credentials
.aws/
aws-config/

# Certificate files
ssl/
certificates/

# Backup files
*.backup
*.bak
EOF
    
    success "Updated .gitignore with secrets patterns"
}

# Main setup function
main() {
    log "Starting Dinner1 production secrets setup..."
    
    # Check if running as root (not recommended)
    if [[ $EUID -eq 0 ]]; then
        warning "Running as root is not recommended for security reasons"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Run setup steps
    check_dependencies
    create_secrets_directory
    generate_database_encryption
    generate_ssl_certificate
    generate_environment_file
    generate_docker_secrets
    generate_k8s_secrets
    generate_aws_secrets
    validate_environment_file
    generate_security_checklist
    update_gitignore
    
    success "Secrets setup completed successfully!"
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Review the generated environment file: $ENV_FILE"
    echo "2. Update placeholder values for AWS, domain names, etc."
    echo "3. Store secrets securely using your chosen secrets management system"
    echo "4. Review and complete the security checklist: $SECRETS_DIR/security-checklist.md"
    echo "5. Test the application with the new configuration"
    echo ""
    echo "⚠️  Important reminders:"
    echo "- Never commit the .env.production file to version control"
    echo "- Keep the secrets directory secure and backed up"
    echo "- Rotate secrets regularly according to your security policy"
    echo "- Use a proper CA certificate for production SSL"
    
    warning "The generated SSL certificate is self-signed. Obtain a proper certificate from a CA for production use."
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [options]"
        echo "  --domain DOMAIN    Specify domain for SSL certificate (default: dinner1.local)"
        echo "  --env-only         Only generate environment file"
        echo "  --secrets-only     Only generate secrets files"
        echo "  -h, --help         Show this help message"
        exit 0
        ;;
    --domain)
        DOMAIN="$2"
        shift 2
        ;;
    --env-only)
        check_dependencies
        create_secrets_directory
        generate_environment_file
        validate_environment_file
        exit 0
        ;;
    --secrets-only)
        check_dependencies
        create_secrets_directory
        generate_docker_secrets
        generate_k8s_secrets
        generate_aws_secrets
        exit 0
        ;;
    *)
        main
        ;;
esac