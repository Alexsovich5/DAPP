#!/bin/bash

# Dinner First Microservices Startup Script
# Phase 5: Advanced Features & Scale

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Starting Dinner First Microservices Architecture"
echo "=================================================="

# Check if Docker and Docker Compose are installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if environment file exists
if [ ! -f ".env.microservices" ]; then
    echo "❌ .env.microservices file not found. Please create it with required environment variables."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs/{auth,matching,messaging,notifications,safety,analytics,profiles,gateway}
mkdir -p ml-models
mkdir -p cache/huggingface
mkdir -p microservices/{auth,matching,messaging,notifications,safety,analytics,profiles}/logs

# Pull latest images
echo "🐳 Pulling latest Docker images..."
docker-compose -f docker-compose.microservices.yml pull

# Build custom services
echo "🔨 Building custom microservices..."
docker-compose -f docker-compose.microservices.yml build

# Start infrastructure services first
echo "🗄️  Starting infrastructure services..."
docker-compose -f docker-compose.microservices.yml up -d \
    postgres-auth \
    postgres-matching \
    postgres-messaging \
    postgres-notifications \
    postgres-safety \
    postgres-profiles \
    redis \
    clickhouse \
    rabbitmq \
    consul

# Wait for databases to be ready
echo "⏳ Waiting for databases to initialize..."
sleep 30

# Check database health
echo "🔍 Checking database connectivity..."
for db in auth matching messaging notifications safety profiles; do
    echo "Checking postgres-$db..."
    docker-compose -f docker-compose.microservices.yml exec -T postgres-$db pg_isready -U postgres -d dinner_first_$db || {
        echo "❌ Database postgres-$db is not ready"
        exit 1
    }
done

# Start core services
echo "🏗️  Starting core microservices..."
docker-compose -f docker-compose.microservices.yml up -d \
    auth-service \
    profile-service \
    safety-service

# Wait for core services
echo "⏳ Waiting for core services to start..."
sleep 20

# Check core services health
echo "🔍 Checking core services health..."
for service in auth profile safety; do
    echo "Checking $service-service..."
    timeout 30 bash -c "until curl -f http://localhost:800$(case $service in auth) echo 1;; profile) echo 7;; safety) echo 5;; esac)/health; do sleep 1; done" || {
        echo "❌ Service $service-service is not healthy"
        exit 1
    }
done

# Start advanced services
echo "🤖 Starting advanced microservices..."
docker-compose -f docker-compose.microservices.yml up -d \
    matching-service \
    messaging-service \
    notification-service \
    analytics-service

# Wait for advanced services
echo "⏳ Waiting for advanced services to start..."
sleep 30

# Start gateway and monitoring
echo "🌐 Starting API Gateway and monitoring..."
docker-compose -f docker-compose.microservices.yml up -d \
    api-gateway \
    prometheus \
    grafana \
    elasticsearch \
    logstash \
    kibana

# Final health check
echo "🔍 Performing final health checks..."
sleep 20

# Check all services
services=("auth:8001" "matching:8002" "messaging:8003" "notifications:8004" "safety:8005" "analytics:8006" "profiles:8007")

for service_port in "${services[@]}"; do
    service=${service_port%:*}
    port=${service_port#*:}
    echo "Checking $service-service on port $port..."
    timeout 10 bash -c "until curl -f http://localhost:$port/health; do sleep 1; done" || {
        echo "⚠️  Warning: $service-service might not be fully ready yet"
    }
done

# Check gateway
echo "🌐 Checking API Gateway..."
timeout 10 bash -c "until curl -f http://localhost/health; do sleep 1; done" || {
    echo "⚠️  Warning: API Gateway might not be fully ready yet"
}

echo ""
echo "✅ Dinner First Microservices Started Successfully!"
echo "=================================================="
echo ""
echo "🌐 Service Endpoints:"
echo "   API Gateway:       http://localhost"
echo "   Auth Service:      http://localhost:8001"
echo "   Matching Service:  http://localhost:8002"
echo "   Messaging Service: http://localhost:8003"
echo "   Notification Svc:  http://localhost:8004"
echo "   Safety Service:    http://localhost:8005"
echo "   Analytics Service: http://localhost:8006"
echo "   Profile Service:   http://localhost:8007"
echo ""
echo "📊 Monitoring:"
echo "   Prometheus:        http://localhost:9090"
echo "   Grafana:           http://localhost:3000"
echo "   Kibana:           http://localhost:5601"
echo "   Consul:           http://localhost:8500"
echo "   RabbitMQ:         http://localhost:15672"
echo ""
echo "📚 API Documentation:"
echo "   Gateway Health:    http://localhost/health"
echo "   Service Docs:      http://localhost:800X/docs (replace X with service port)"
echo ""
echo "🛠️  Management Commands:"
echo "   Stop services:     ./scripts/stop-microservices.sh"
echo "   View logs:         docker-compose -f docker-compose.microservices.yml logs -f [service]"
echo "   Scale service:     docker-compose -f docker-compose.microservices.yml up -d --scale [service]=N"
echo ""

# Show running containers
echo "🐳 Running Containers:"
docker-compose -f docker-compose.microservices.yml ps