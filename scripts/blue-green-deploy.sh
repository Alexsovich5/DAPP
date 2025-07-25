#!/bin/bash

# Blue-Green Deployment Script for Dinner1
# Zero-downtime production deployment with automatic rollback

set -e

# Configuration
NAMESPACE="dinner1-production"
APP_NAME="dinner1"
IMAGE_TAG="${1:-latest}"
HEALTH_CHECK_TIMEOUT=300
HEALTH_CHECK_INTERVAL=10

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

# Get current deployment color
get_current_color() {
    local current_color=$(kubectl get service ${APP_NAME} -n ${NAMESPACE} -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "")
    if [[ "$current_color" == "blue" ]]; then
        echo "blue"
    else
        echo "green"
    fi
}

# Get target deployment color
get_target_color() {
    local current_color=$(get_current_color)
    if [[ "$current_color" == "blue" ]]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Health check function
health_check() {
    local service_name=$1
    local timeout=$2
    local interval=$3
    
    log "Performing health check for $service_name..."
    
    local end_time=$((SECONDS + timeout))
    
    while [ $SECONDS -lt $end_time ]; do
        # Check if pods are ready
        local ready_pods=$(kubectl get pods -l app=${APP_NAME},color=${service_name} -n ${NAMESPACE} -o jsonpath='{.items[*].status.conditions[?(@.type=="Ready")].status}' 2>/dev/null)
        
        if [[ "$ready_pods" == *"False"* ]] || [[ -z "$ready_pods" ]]; then
            log "Waiting for pods to be ready... (${SECONDS}s elapsed)"
            sleep $interval
            continue
        fi
        
        # Check application health endpoint
        local service_ip=$(kubectl get service ${APP_NAME}-${service_name} -n ${NAMESPACE} -o jsonpath='{.spec.clusterIP}' 2>/dev/null)
        
        if [[ -n "$service_ip" ]]; then
            if kubectl run health-check-${service_name} --rm -i --restart=Never --image=curlimages/curl -- curl -f http://${service_ip}/health > /dev/null 2>&1; then
                success "Health check passed for $service_name"
                return 0
            fi
        fi
        
        log "Health check failed, retrying... (${SECONDS}s elapsed)"
        sleep $interval
    done
    
    error "Health check failed for $service_name after ${timeout}s"
    return 1
}

# Deploy to target environment
deploy_target() {
    local target_color=$1
    local image_tag=$2
    
    log "Deploying to $target_color environment with image tag: $image_tag"
    
    # Create temporary deployment manifests
    cat > /tmp/${APP_NAME}-${target_color}-backend.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}-backend-${target_color}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
    component: backend
    color: ${target_color}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${APP_NAME}
      component: backend
      color: ${target_color}
  template:
    metadata:
      labels:
        app: ${APP_NAME}
        component: backend
        color: ${target_color}
    spec:
      containers:
      - name: backend
        image: ghcr.io/dinner1/backend:${image_tag}
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: COLOR
          value: "${target_color}"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ${APP_NAME}-backend-${target_color}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
    component: backend
    color: ${target_color}
spec:
  selector:
    app: ${APP_NAME}
    component: backend
    color: ${target_color}
  ports:
  - port: 8000
    targetPort: 8000
EOF

    cat > /tmp/${APP_NAME}-${target_color}-frontend.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}-frontend-${target_color}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
    component: frontend
    color: ${target_color}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ${APP_NAME}
      component: frontend
      color: ${target_color}
  template:
    metadata:
      labels:
        app: ${APP_NAME}
        component: frontend
        color: ${target_color}
    spec:
      containers:
      - name: frontend
        image: ghcr.io/dinner1/frontend:${image_tag}
        ports:
        - containerPort: 80
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: COLOR
          value: "${target_color}"
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "250m"
        livenessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ${APP_NAME}-frontend-${target_color}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
    component: frontend
    color: ${target_color}
spec:
  selector:
    app: ${APP_NAME}
    component: frontend
    color: ${target_color}
  ports:
  - port: 80
    targetPort: 80
EOF

    # Apply the deployments
    kubectl apply -f /tmp/${APP_NAME}-${target_color}-backend.yaml
    kubectl apply -f /tmp/${APP_NAME}-${target_color}-frontend.yaml
    
    # Wait for rollout to complete
    log "Waiting for backend rollout to complete..."
    kubectl rollout status deployment/${APP_NAME}-backend-${target_color} -n ${NAMESPACE} --timeout=600s
    
    log "Waiting for frontend rollout to complete..."
    kubectl rollout status deployment/${APP_NAME}-frontend-${target_color} -n ${NAMESPACE} --timeout=600s
    
    # Clean up temporary files
    rm -f /tmp/${APP_NAME}-${target_color}-*.yaml
    
    success "Deployment to $target_color completed"
}

# Switch traffic to target environment
switch_traffic() {
    local target_color=$1
    
    log "Switching traffic to $target_color environment..."
    
    # Update main services to point to target color
    kubectl patch service ${APP_NAME}-backend -n ${NAMESPACE} -p '{"spec":{"selector":{"color":"'${target_color}'"}}}'
    kubectl patch service ${APP_NAME}-frontend -n ${NAMESPACE} -p '{"spec":{"selector":{"color":"'${target_color}'"}}}'
    
    success "Traffic switched to $target_color environment"
}

# Cleanup old environment
cleanup_old() {
    local old_color=$1
    
    log "Cleaning up old $old_color environment..."
    
    # Scale down old deployments
    kubectl scale deployment ${APP_NAME}-backend-${old_color} --replicas=0 -n ${NAMESPACE} 2>/dev/null || true
    kubectl scale deployment ${APP_NAME}-frontend-${old_color} --replicas=0 -n ${NAMESPACE} 2>/dev/null || true
    
    # Wait a bit before complete cleanup
    sleep 30
    
    # Delete old deployments and services
    kubectl delete deployment ${APP_NAME}-backend-${old_color} -n ${NAMESPACE} 2>/dev/null || true
    kubectl delete deployment ${APP_NAME}-frontend-${old_color} -n ${NAMESPACE} 2>/dev/null || true
    kubectl delete service ${APP_NAME}-backend-${old_color} -n ${NAMESPACE} 2>/dev/null || true
    kubectl delete service ${APP_NAME}-frontend-${old_color} -n ${NAMESPACE} 2>/dev/null || true
    
    success "Cleanup of $old_color environment completed"
}

# Rollback to previous environment
rollback() {
    local current_color=$1
    local previous_color=$2
    
    warning "Rolling back from $current_color to $previous_color..."
    
    # Check if previous environment still exists
    if kubectl get deployment ${APP_NAME}-backend-${previous_color} -n ${NAMESPACE} > /dev/null 2>&1; then
        # Scale up previous environment
        kubectl scale deployment ${APP_NAME}-backend-${previous_color} --replicas=3 -n ${NAMESPACE}
        kubectl scale deployment ${APP_NAME}-frontend-${previous_color} --replicas=2 -n ${NAMESPACE}
        
        # Wait for previous environment to be ready
        kubectl rollout status deployment/${APP_NAME}-backend-${previous_color} -n ${NAMESPACE} --timeout=300s
        kubectl rollout status deployment/${APP_NAME}-frontend-${previous_color} -n ${NAMESPACE} --timeout=300s
        
        # Switch traffic back
        switch_traffic $previous_color
        
        # Scale down current environment
        kubectl scale deployment ${APP_NAME}-backend-${current_color} --replicas=0 -n ${NAMESPACE}
        kubectl scale deployment ${APP_NAME}-frontend-${current_color} --replicas=0 -n ${NAMESPACE}
        
        success "Rollback to $previous_color completed"
    else
        error "Previous environment $previous_color not found. Manual intervention required."
        return 1
    fi
}

# Main deployment function
main() {
    log "Starting blue-green deployment with image tag: $IMAGE_TAG"
    
    # Validate kubectl access
    if ! kubectl get namespace ${NAMESPACE} > /dev/null 2>&1; then
        error "Cannot access namespace ${NAMESPACE}. Check kubectl configuration."
        exit 1
    fi
    
    # Get current and target colors
    local current_color=$(get_current_color)
    local target_color=$(get_target_color)
    
    log "Current environment: $current_color"
    log "Target environment: $target_color"
    
    # Deploy to target environment
    if ! deploy_target $target_color $IMAGE_TAG; then
        error "Deployment to $target_color failed"
        exit 1
    fi
    
    # Health check target environment
    if ! health_check $target_color $HEALTH_CHECK_TIMEOUT $HEALTH_CHECK_INTERVAL; then
        error "Health check failed for $target_color environment"
        
        # Cleanup failed deployment
        log "Cleaning up failed deployment..."
        kubectl delete deployment ${APP_NAME}-backend-${target_color} -n ${NAMESPACE} 2>/dev/null || true
        kubectl delete deployment ${APP_NAME}-frontend-${target_color} -n ${NAMESPACE} 2>/dev/null || true
        kubectl delete service ${APP_NAME}-backend-${target_color} -n ${NAMESPACE} 2>/dev/null || true
        kubectl delete service ${APP_NAME}-frontend-${target_color} -n ${NAMESPACE} 2>/dev/null || true
        
        exit 1
    fi
    
    # Switch traffic to target environment
    switch_traffic $target_color
    
    # Final health check after traffic switch
    log "Performing final health check after traffic switch..."
    sleep 10
    
    if ! health_check $target_color 60 5; then
        error "Final health check failed. Rolling back..."
        rollback $target_color $current_color
        exit 1
    fi
    
    # Cleanup old environment
    cleanup_old $current_color
    
    success "Blue-green deployment completed successfully!"
    log "New active environment: $target_color"
    log "Application is now running with image tag: $IMAGE_TAG"
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [IMAGE_TAG]"
        echo "  IMAGE_TAG    Docker image tag to deploy (default: latest)"
        echo ""
        echo "Environment variables:"
        echo "  NAMESPACE               Kubernetes namespace (default: dinner1-production)"
        echo "  HEALTH_CHECK_TIMEOUT    Health check timeout in seconds (default: 300)"
        echo "  HEALTH_CHECK_INTERVAL   Health check interval in seconds (default: 10)"
        exit 0
        ;;
    rollback)
        current_color=$(get_current_color)
        if [[ "$current_color" == "blue" ]]; then
            previous_color="green"
        else
            previous_color="blue"
        fi
        rollback $current_color $previous_color
        exit 0
        ;;
    *)
        main
        ;;
esac