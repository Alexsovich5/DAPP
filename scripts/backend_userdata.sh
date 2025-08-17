#!/bin/bash
# Backend User Data Script for Dinner1 Auto Scaling
# Optimized setup for high-performance dating platform backend

set -e

# Variables from Terraform
ENVIRONMENT="${environment}"
REDIS_ENDPOINT="${redis_endpoint}"
DB_ENDPOINT="${db_endpoint}"

# Logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting backend setup for environment: $ENVIRONMENT"

# System updates and essential packages
yum update -y
yum install -y \
    docker \
    git \
    htop \
    amazon-cloudwatch-agent \
    aws-cli \
    python3 \
    python3-pip \
    nginx \
    postgresql-client \
    redis-cli

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure CloudWatch Agent
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "root"
    },
    "metrics": {
        "namespace": "Dinner1/Backend",
        "metrics_collected": {
            "cpu": {
                "measurement": [
                    "cpu_usage_idle",
                    "cpu_usage_iowait",
                    "cpu_usage_user",
                    "cpu_usage_system"
                ],
                "metrics_collection_interval": 60,
                "totalcpu": false
            },
            "disk": {
                "measurement": [
                    "used_percent"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "diskio": {
                "measurement": [
                    "io_time",
                    "read_bytes",
                    "write_bytes",
                    "reads",
                    "writes"
                ],
                "metrics_collection_interval": 60,
                "resources": [
                    "*"
                ]
            },
            "mem": {
                "measurement": [
                    "mem_used_percent"
                ],
                "metrics_collection_interval": 60
            },
            "netstat": {
                "measurement": [
                    "tcp_established",
                    "tcp_time_wait"
                ],
                "metrics_collection_interval": 60
            },
            "swap": {
                "measurement": [
                    "swap_used_percent"
                ],
                "metrics_collection_interval": 60
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/dinner1/backend.log",
                        "log_group_name": "dinner1-backend-logs",
                        "log_stream_name": "{instance_id}-backend",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/nginx/access.log",
                        "log_group_name": "dinner1-nginx-access",
                        "log_stream_name": "{instance_id}-nginx-access",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/nginx/error.log",
                        "log_group_name": "dinner1-nginx-error",
                        "log_stream_name": "{instance_id}-nginx-error",
                        "timezone": "UTC"
                    }
                ]
            }
        }
    }
}
EOF

# Start CloudWatch Agent
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config \
    -m ec2 \
    -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

# Create application directory
mkdir -p /opt/dinner1
cd /opt/dinner1

# Create log directory
mkdir -p /var/log/dinner1
chown ec2-user:ec2-user /var/log/dinner1

# Get application from ECR or build from source
# For production, this would pull from ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Pull latest backend image
docker pull <account>.dkr.ecr.us-east-1.amazonaws.com/dinner1-backend:latest

# Create environment file
cat > /opt/dinner1/.env << EOF
ENVIRONMENT=$ENVIRONMENT
DATABASE_URL=postgresql://dinner1_user:secure_password@$DB_ENDPOINT:5432/dinner1
REDIS_URL=redis://$REDIS_ENDPOINT:6379/0

# Security
SECRET_KEY=$(openssl rand -base64 32)
JWT_SECRET_KEY=$(openssl rand -base64 32)

# CORS
CORS_ORIGINS=https://dinner1.com,https://www.dinner1.com

# Cache
REDIS_CACHE_URL=redis://$REDIS_ENDPOINT:6379/1

# Analytics
CLICKHOUSE_HOST=clickhouse.dinner1.internal
CLICKHOUSE_USER=analytics_user
CLICKHOUSE_PASSWORD=secure_analytics_password

# Email
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=smtp_user
SMTP_PASSWORD=smtp_password

# File uploads
S3_BUCKET=dinner1-uploads-production
AWS_REGION=us-east-1

# Performance
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_MAX_REQUESTS=1000
GUNICORN_MAX_REQUESTS_JITTER=100

# Monitoring
NEW_RELIC_LICENSE_KEY=your_new_relic_key
SENTRY_DSN=your_sentry_dsn
EOF

# Create Docker Compose file for backend
cat > /opt/dinner1/docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    image: <account>.dkr.ecr.us-east-1.amazonaws.com/dinner1-backend:latest
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - /var/log/dinner1:/app/logs
      - /tmp:/tmp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /var/log/nginx:/var/log/nginx
    depends_on:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

# Create optimized Nginx configuration
cat > /opt/dinner1/nginx.conf << 'EOF'
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 2048;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    client_max_body_size 50M;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1000;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    # Backend upstream
    upstream backend {
        server backend:8000;
        keepalive 32;
    }

    server {
        listen 80;
        server_name _;

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffering
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
            
            # Keep alive
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        # Authentication endpoints with stricter rate limiting
        location ~ ^/api/v1/auth/(login|register) {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Admin endpoints
        location /admin/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Default response for load balancer health checks
        location / {
            return 200 "Backend ready\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

# Set permissions
chown -R ec2-user:ec2-user /opt/dinner1

# Start services
cd /opt/dinner1
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to start..."
sleep 30

# Verify backend is responding
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "Backend is healthy!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - waiting for backend..."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Backend failed to become healthy"
    docker-compose logs
    exit 1
fi

# Setup log rotation
cat > /etc/logrotate.d/dinner1 << 'EOF'
/var/log/dinner1/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF

# Setup cron jobs for maintenance
cat > /tmp/crontab << 'EOF'
# Database optimization (daily at 2 AM)
0 2 * * * /usr/bin/docker exec dinner1_backend_1 python -c "from app.core.database_optimized import get_database_optimizer; get_database_optimizer().vacuum_analyze_tables()"

# Cache cleanup (every 6 hours)
0 */6 * * * /usr/bin/docker exec dinner1_backend_1 python -c "from app.services.cache_service import get_cache_service; get_cache_service().cleanup_expired_l1_cache()"

# Log cleanup (weekly)
0 3 * * 0 find /var/log/dinner1 -name "*.log" -mtime +7 -delete

# Health check and auto-restart if needed
*/5 * * * * /opt/dinner1/health_check.sh
EOF

crontab /tmp/crontab

# Create health check script
cat > /opt/dinner1/health_check.sh << 'EOF'
#!/bin/bash
# Health check script with auto-restart

HEALTH_ENDPOINT="http://localhost:8000/health"
MAX_FAILURES=3
FAILURE_FILE="/tmp/dinner1_failures"

# Check if backend is healthy
if curl -f $HEALTH_ENDPOINT > /dev/null 2>&1; then
    # Reset failure counter on success
    rm -f $FAILURE_FILE
    exit 0
fi

# Increment failure counter
if [ -f $FAILURE_FILE ]; then
    FAILURES=$(cat $FAILURE_FILE)
    FAILURES=$((FAILURES + 1))
else
    FAILURES=1
fi

echo $FAILURES > $FAILURE_FILE

# Restart if max failures reached
if [ $FAILURES -ge $MAX_FAILURES ]; then
    echo "$(date): Backend unhealthy for $FAILURES checks, restarting..." >> /var/log/dinner1/auto_restart.log
    cd /opt/dinner1
    docker-compose restart backend
    rm -f $FAILURE_FILE
fi
EOF

chmod +x /opt/dinner1/health_check.sh

# Setup system monitoring
cat > /opt/dinner1/system_monitor.sh << 'EOF'
#!/bin/bash
# System monitoring script

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): High disk usage: $DISK_USAGE%" >> /var/log/dinner1/alerts.log
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
if [ $MEM_USAGE -gt 90 ]; then
    echo "$(date): High memory usage: $MEM_USAGE%" >> /var/log/dinner1/alerts.log
fi

# Check load average
LOAD_AVG=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
LOAD_THRESHOLD=$(nproc | awk '{print $1 * 2}')
if (( $(echo "$LOAD_AVG > $LOAD_THRESHOLD" | bc -l) )); then
    echo "$(date): High load average: $LOAD_AVG" >> /var/log/dinner1/alerts.log
fi
EOF

chmod +x /opt/dinner1/system_monitor.sh

# Add system monitoring to cron
echo "*/5 * * * * /opt/dinner1/system_monitor.sh" | crontab -

# Final verification
echo "Backend setup completed successfully!"
echo "Services status:"
docker-compose ps

# Test endpoints
echo "Testing health endpoint:"
curl -s http://localhost:8000/health

echo "Setup completed at $(date)"