#!/bin/bash
# Frontend User Data Script for Dinner1 Auto Scaling
# Optimized setup for high-performance Angular frontend with SSR

set -e

# Variables from Terraform
ENVIRONMENT="${environment}"
API_ENDPOINT="${api_endpoint}"

# Logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "Starting frontend setup for environment: $ENVIRONMENT"

# System updates and essential packages
yum update -y
yum install -y \
    docker \
    git \
    htop \
    amazon-cloudwatch-agent \
    aws-cli \
    nginx \
    nodejs \
    npm

# Start and enable Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Configure CloudWatch Agent for frontend
cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << 'EOF'
{
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "root"
    },
    "metrics": {
        "namespace": "Dinner1/Frontend",
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
            }
        }
    },
    "logs": {
        "logs_collected": {
            "files": {
                "collect_list": [
                    {
                        "file_path": "/var/log/nginx/access.log",
                        "log_group_name": "dinner1-frontend-nginx-access",
                        "log_stream_name": "{instance_id}-nginx-access",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/nginx/error.log",
                        "log_group_name": "dinner1-frontend-nginx-error",
                        "log_stream_name": "{instance_id}-nginx-error",
                        "timezone": "UTC"
                    },
                    {
                        "file_path": "/var/log/dinner1/frontend.log",
                        "log_group_name": "dinner1-frontend-app",
                        "log_stream_name": "{instance_id}-frontend",
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
mkdir -p /opt/dinner1-frontend
cd /opt/dinner1-frontend

# Create log directory
mkdir -p /var/log/dinner1
chown ec2-user:ec2-user /var/log/dinner1

# Get frontend application from ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

# Pull latest frontend image
docker pull <account>.dkr.ecr.us-east-1.amazonaws.com/dinner1-frontend:latest

# Create environment file for frontend
cat > /opt/dinner1-frontend/.env << EOF
ENVIRONMENT=$ENVIRONMENT
API_ENDPOINT=https://$API_ENDPOINT
WS_ENDPOINT=wss://$API_ENDPOINT

# CDN and Assets
CDN_URL=https://d1234567890.cloudfront.net
STATIC_URL=https://d1234567890.cloudfront.net/static

# Analytics
GOOGLE_ANALYTICS_ID=G-XXXXXXXXXX
MIXPANEL_TOKEN=your_mixpanel_token

# Error tracking
SENTRY_DSN=your_frontend_sentry_dsn

# Performance monitoring
NEW_RELIC_BROWSER_LICENSE_KEY=your_browser_key

# Feature flags
ENABLE_ANALYTICS=true
ENABLE_AB_TESTING=true
ENABLE_PWA=true

# Security
CSP_NONCE=auto-generated
EOF

# Create Docker Compose file for frontend
cat > /opt/dinner1-frontend/docker-compose.yml << 'EOF'
version: '3.8'

services:
  frontend:
    image: <account>.dkr.ecr.us-east-1.amazonaws.com/dinner1-frontend:latest
    ports:
      - "4000:4000"
    env_file:
      - .env
    volumes:
      - /var/log/dinner1:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./cache:/var/cache/nginx
      - /var/log/nginx:/var/log/nginx
    depends_on:
      - frontend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3
EOF

# Create cache directory
mkdir -p /opt/dinner1-frontend/cache
chown -R ec2-user:ec2-user /opt/dinner1-frontend/cache

# Create optimized Nginx configuration for frontend
cat > /opt/dinner1-frontend/nginx.conf << 'EOF'
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

    # Logging with additional performance metrics
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time uct="$upstream_connect_time" '
                    'uht="$upstream_header_time" urt="$upstream_response_time" '
                    'cache_status="$upstream_cache_status"';

    access_log /var/log/nginx/access.log main;

    # Performance optimizations
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;
    server_tokens off;

    # Client settings
    client_max_body_size 10M;
    client_body_buffer_size 128k;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;

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
        image/svg+xml
        application/font-woff
        application/font-woff2;

    # Browser caching
    map $sent_http_content_type $expires {
        default                    off;
        text/html                  1h;
        text/css                   1y;
        application/javascript     1y;
        application/font-woff      1y;
        application/font-woff2     1y;
        ~image/                    1M;
        application/json           1h;
    }

    expires $expires;

    # Rate limiting for frontend
    limit_req_zone $binary_remote_addr zone=frontend:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=assets:10m rate=100r/s;

    # Proxy cache configuration
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=dinner1_cache:10m max_size=1g 
                     inactive=60m use_temp_path=off;

    # Frontend upstream
    upstream frontend {
        server frontend:4000;
        keepalive 16;
    }

    server {
        listen 80 default_server;
        server_name _;
        
        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        
        # CSP header for dating platform
        add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' *.googletagmanager.com *.google-analytics.com; style-src 'self' 'unsafe-inline' fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: *.cloudfront.net; connect-src 'self' *.dinner1.com wss://*.dinner1.com *.google-analytics.com; frame-src 'none';" always;

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }

        # Static assets with aggressive caching
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            limit_req zone=assets burst=50 nodelay;
            
            proxy_pass http://frontend;
            proxy_cache dinner1_cache;
            proxy_cache_valid 200 1y;
            proxy_cache_valid 404 1m;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            proxy_cache_background_update on;
            proxy_cache_lock on;
            
            # Cache headers
            add_header X-Cache-Status $upstream_cache_status;
            expires 1y;
            add_header Cache-Control "public, immutable";
            
            # Compression
            gzip_static on;
        }

        # Angular routes (for client-side routing)
        location / {
            limit_req zone=frontend burst=20 nodelay;
            
            # Try file first, then proxy to Angular app
            try_files $uri $uri/ @angular;
            
            # Security headers for HTML
            add_header X-Frame-Options "SAMEORIGIN" always;
            add_header X-Content-Type-Options "nosniff" always;
        }

        # Angular fallback
        location @angular {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # SSR optimization
            proxy_cache dinner1_cache;
            proxy_cache_valid 200 1h;
            proxy_cache_valid 404 1m;
            proxy_cache_key "$scheme$request_method$host$request_uri$http_user_agent";
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            
            # Cache headers
            add_header X-Cache-Status $upstream_cache_status;
            
            # Timeouts
            proxy_connect_timeout 5s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            
            # Buffering
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
            
            # Keep alive
            proxy_http_version 1.1;
            proxy_set_header Connection "";
        }

        # API proxy (fallback if not handled by ALB)
        location /api/ {
            proxy_pass https://$API_ENDPOINT/api/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket proxy for real-time features
        location /ws/ {
            proxy_pass http://frontend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket timeouts
            proxy_read_timeout 86400;
            proxy_send_timeout 86400;
        }

        # Block access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
        
        location ~ \.(htaccess|htpasswd|ini|log|sh|sql|conf)$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
EOF

# Set permissions
chown -R ec2-user:ec2-user /opt/dinner1-frontend

# Start services
cd /opt/dinner1-frontend
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for frontend services to start..."
sleep 30

# Verify frontend is responding
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -f http://localhost:4000/health > /dev/null 2>&1; then
        echo "Frontend application is healthy!"
        break
    fi
    
    attempt=$((attempt + 1))
    echo "Attempt $attempt/$max_attempts - waiting for frontend..."
    sleep 10
done

if [ $attempt -eq $max_attempts ]; then
    echo "ERROR: Frontend failed to become healthy"
    docker-compose logs
    exit 1
fi

# Verify nginx is responding
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "Nginx is healthy!"
else
    echo "ERROR: Nginx is not responding"
    exit 1
fi

# Setup log rotation
cat > /etc/logrotate.d/dinner1-frontend << 'EOF'
/var/log/dinner1/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}

/var/log/nginx/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    sharedscripts
    postrotate
        if [ -f /var/run/nginx.pid ]; then
            kill -USR1 `cat /var/run/nginx.pid`
        fi
    endscript
}
EOF

# Setup cron jobs for maintenance
cat > /tmp/crontab << 'EOF'
# Cache cleanup (every hour)
0 * * * * find /opt/dinner1-frontend/cache -type f -mtime +1 -delete

# Log cleanup (daily)
0 3 * * * find /var/log/nginx -name "*.log" -mtime +14 -delete
0 3 * * * find /var/log/dinner1 -name "*.log" -mtime +7 -delete

# Health check and auto-restart if needed
*/5 * * * * /opt/dinner1-frontend/health_check.sh

# Update SSL certificates (if using Let's Encrypt)
0 2 * * * certbot renew --quiet

# Preload popular content (warm cache)
*/15 * * * * /opt/dinner1-frontend/cache_warmer.sh
EOF

crontab /tmp/crontab

# Create health check script
cat > /opt/dinner1-frontend/health_check.sh << 'EOF'
#!/bin/bash
# Frontend health check script with auto-restart

HEALTH_ENDPOINT="http://localhost/health"
APP_HEALTH_ENDPOINT="http://localhost:4000/health"
MAX_FAILURES=3
FAILURE_FILE="/tmp/dinner1_frontend_failures"

# Check if nginx is healthy
if ! curl -f $HEALTH_ENDPOINT > /dev/null 2>&1; then
    echo "$(date): Nginx health check failed" >> /var/log/dinner1/health_check.log
    systemctl restart nginx
    sleep 5
fi

# Check if frontend app is healthy
if curl -f $APP_HEALTH_ENDPOINT > /dev/null 2>&1; then
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
    echo "$(date): Frontend unhealthy for $FAILURES checks, restarting..." >> /var/log/dinner1/auto_restart.log
    cd /opt/dinner1-frontend
    docker-compose restart frontend
    rm -f $FAILURE_FILE
fi
EOF

chmod +x /opt/dinner1-frontend/health_check.sh

# Create cache warming script
cat > /opt/dinner1-frontend/cache_warmer.sh << 'EOF'
#!/bin/bash
# Cache warming script for popular pages

BASE_URL="http://localhost"
POPULAR_PAGES=(
    "/"
    "/discover"
    "/matches"
    "/profile"
    "/how-it-works"
    "/pricing"
)

for page in "${POPULAR_PAGES[@]}"; do
    curl -s "$BASE_URL$page" > /dev/null 2>&1
done

echo "$(date): Cache warming completed" >> /var/log/dinner1/cache_warmer.log
EOF

chmod +x /opt/dinner1-frontend/cache_warmer.sh

# Create performance monitoring script
cat > /opt/dinner1-frontend/performance_monitor.sh << 'EOF'
#!/bin/bash
# Performance monitoring for frontend

LOG_FILE="/var/log/dinner1/performance.log"

# Check response times
RESPONSE_TIME=$(curl -o /dev/null -s -w "%{time_total}" http://localhost/)
echo "$(date): Homepage response time: ${RESPONSE_TIME}s" >> $LOG_FILE

# Check cache hit ratio
CACHE_HITS=$(grep -c "HIT" /var/log/nginx/access.log | tail -1000 || echo 0)
CACHE_TOTAL=$(wc -l < /var/log/nginx/access.log | tail -1000 || echo 1)
CACHE_RATIO=$(echo "scale=2; $CACHE_HITS / $CACHE_TOTAL * 100" | bc -l 2>/dev/null || echo 0)
echo "$(date): Cache hit ratio: ${CACHE_RATIO}%" >> $LOG_FILE

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
echo "$(date): Memory usage: ${MEM_USAGE}%" >> $LOG_FILE

# Check disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}')
echo "$(date): Disk usage: ${DISK_USAGE}" >> $LOG_FILE
EOF

chmod +x /opt/dinner1-frontend/performance_monitor.sh

# Add performance monitoring to cron
echo "*/5 * * * * /opt/dinner1-frontend/performance_monitor.sh" | crontab -

# Setup SSL certificate renewal (if using Let's Encrypt)
if command -v certbot &> /dev/null; then
    echo "Setting up SSL certificate auto-renewal..."
    cat > /etc/nginx/snippets/ssl-params.conf << 'EOF'
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384;
ssl_ecdh_curve secp384r1;
ssl_session_timeout 10m;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
EOF
fi

# Final verification
echo "Frontend setup completed successfully!"
echo "Services status:"
cd /opt/dinner1-frontend
docker-compose ps

# Test endpoints
echo "Testing health endpoints:"
curl -s http://localhost/health
echo ""
curl -s http://localhost:4000/health

# Test main page
echo "Testing main page load time:"
curl -o /dev/null -s -w "Response time: %{time_total}s\n" http://localhost/

echo "Frontend setup completed at $(date)"