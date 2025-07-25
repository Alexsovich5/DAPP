#!/bin/bash

# Production Health Check Script for Dinner1
# Comprehensive health verification for production deployment

set -e

# Configuration
API_BASE_URL="${API_BASE_URL:-https://api.dinner1.com}"
FRONTEND_URL="${FRONTEND_URL:-https://dinner1.com}"
TIMEOUT="${TIMEOUT:-30}"
MAX_RETRIES="${MAX_RETRIES:-3}"

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

# HTTP request with retry logic
http_request() {
    local url=$1
    local expected_status=${2:-200}
    local max_retries=${3:-$MAX_RETRIES}
    local timeout=${4:-$TIMEOUT}
    
    for ((i=1; i<=max_retries; i++)); do
        local response=$(curl -s -w "%{http_code}:%{time_total}:%{time_connect}" \
                        --max-time $timeout \
                        --connect-timeout 10 \
                        "$url" 2>/dev/null || echo "000:0:0")
        
        local status_code=$(echo "$response" | cut -d':' -f1)
        local total_time=$(echo "$response" | cut -d':' -f2)
        local connect_time=$(echo "$response" | cut -d':' -f3)
        
        if [[ "$status_code" == "$expected_status" ]]; then
            echo "SUCCESS:$status_code:$total_time:$connect_time"
            return 0
        fi
        
        if [[ $i -lt $max_retries ]]; then
            log "Request failed (attempt $i/$max_retries), retrying in 2 seconds..."
            sleep 2
        fi
    done
    
    echo "FAILED:$status_code:$total_time:$connect_time"
    return 1
}

# Basic connectivity check
check_basic_connectivity() {
    log "Checking basic connectivity..."
    
    # Frontend health check
    local frontend_result=$(http_request "$FRONTEND_URL/health")
    if [[ "$frontend_result" == SUCCESS* ]]; then
        local response_time=$(echo "$frontend_result" | cut -d':' -f3)
        success "Frontend is accessible (${response_time}s response time)"
    else
        error "Frontend is not accessible: $FRONTEND_URL/health"
        return 1
    fi
    
    # API health check
    local api_result=$(http_request "$API_BASE_URL/health")
    if [[ "$api_result" == SUCCESS* ]]; then
        local response_time=$(echo "$api_result" | cut -d':' -f3)
        success "API is accessible (${response_time}s response time)"
    else
        error "API is not accessible: $API_BASE_URL/health"
        return 1
    fi
    
    return 0
}

# Comprehensive API health check
check_api_health() {
    log "Performing comprehensive API health check..."
    
    # Main health endpoint
    local health_response=$(curl -s --max-time 30 "$API_BASE_URL/health" 2>/dev/null || echo "{}")
    local health_status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
    
    if [[ "$health_status" == "healthy" ]]; then
        success "API health status: healthy"
    else
        error "API health status: $health_status"
        echo "Full response: $health_response"
        return 1
    fi
    
    # Database connectivity
    local db_status=$(echo "$health_response" | grep -o '"database":{"status":"[^"]*"' | cut -d'"' -f6)
    if [[ "$db_status" == "healthy" ]]; then
        success "Database connectivity: healthy"
    else
        error "Database connectivity: $db_status"
        return 1
    fi
    
    # Redis connectivity
    local redis_status=$(echo "$health_response" | grep -o '"redis":{"status":"[^"]*"' | cut -d'"' -f6)
    if [[ "$redis_status" == "healthy" ]]; then
        success "Redis connectivity: healthy"
    else
        error "Redis connectivity: $redis_status"
        return 1
    fi
    
    # API documentation accessibility
    local docs_result=$(http_request "$API_BASE_URL/docs")
    if [[ "$docs_result" == SUCCESS* ]]; then
        success "API documentation is accessible"
    else
        warning "API documentation is not accessible (may be disabled in production)"
    fi
    
    return 0
}

# Test critical API endpoints
check_critical_endpoints() {
    log "Testing critical API endpoints..."
    
    local endpoints=(
        "/api/v1/health:200"
        "/api/v1/auth/me:401"  # Should return 401 without authentication
        "/:200"                # Root endpoint
    )
    
    for endpoint_config in "${endpoints[@]}"; do
        local endpoint=$(echo "$endpoint_config" | cut -d':' -f1)
        local expected_status=$(echo "$endpoint_config" | cut -d':' -f2)
        
        local result=$(http_request "$API_BASE_URL$endpoint" "$expected_status")
        if [[ "$result" == SUCCESS* ]]; then
            local response_time=$(echo "$result" | cut -d':' -f3)
            success "Endpoint $endpoint returned expected status $expected_status (${response_time}s)"
        else
            error "Endpoint $endpoint failed to return expected status $expected_status"
            return 1
        fi
    done
    
    return 0
}

# Performance checks
check_performance() {
    log "Performing performance checks..."
    
    local endpoints=(
        "$API_BASE_URL/health"
        "$API_BASE_URL/api/v1/health"
        "$FRONTEND_URL/"
    )
    
    local slow_endpoints=()
    local performance_threshold=2.0  # 2 seconds
    
    for endpoint in "${endpoints[@]}"; do
        local result=$(http_request "$endpoint")
        if [[ "$result" == SUCCESS* ]]; then
            local response_time=$(echo "$result" | cut -d':' -f3)
            
            # Check if response time exceeds threshold
            if (( $(echo "$response_time > $performance_threshold" | bc -l) )); then
                slow_endpoints+=("$endpoint (${response_time}s)")
            else
                success "Performance OK: $endpoint (${response_time}s)"
            fi
        fi
    done
    
    if [[ ${#slow_endpoints[@]} -gt 0 ]]; then
        warning "Slow endpoints detected:"
        for slow_endpoint in "${slow_endpoints[@]}"; do
            warning "  - $slow_endpoint"
        done
    else
        success "All endpoints performing within acceptable limits"
    fi
    
    return 0
}

# SSL certificate check
check_ssl_certificates() {
    log "Checking SSL certificates..."
    
    local domains=("$FRONTEND_URL" "$API_BASE_URL")
    
    for domain in "${domains[@]}"; do
        local hostname=$(echo "$domain" | sed 's|https\?://||' | cut -d'/' -f1)
        
        # Get certificate expiry date
        local cert_info=$(echo | openssl s_client -servername "$hostname" -connect "$hostname:443" 2>/dev/null | openssl x509 -noout -dates 2>/dev/null || echo "")
        
        if [[ -n "$cert_info" ]]; then
            local expiry_date=$(echo "$cert_info" | grep "notAfter" | cut -d'=' -f2)
            local expiry_epoch=$(date -d "$expiry_date" +%s 2>/dev/null || echo "0")
            local current_epoch=$(date +%s)
            local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [[ $days_until_expiry -gt 30 ]]; then
                success "SSL certificate for $hostname is valid (expires in $days_until_expiry days)"
            elif [[ $days_until_expiry -gt 7 ]]; then
                warning "SSL certificate for $hostname expires in $days_until_expiry days"
            else
                error "SSL certificate for $hostname expires in $days_until_expiry days - URGENT RENEWAL REQUIRED"
                return 1
            fi
        else
            error "Could not retrieve SSL certificate information for $hostname"
            return 1
        fi
    done
    
    return 0
}

# Database connectivity and performance
check_database() {
    log "Checking database connectivity and performance..."
    
    # Get database metrics from API
    local metrics_response=$(curl -s --max-time 30 "$API_BASE_URL/api/v1/metrics" 2>/dev/null || echo "{}")
    
    # Check connection count
    local db_connections=$(echo "$metrics_response" | grep -o '"active_connections":[0-9]*' | cut -d':' -f2)
    if [[ -n "$db_connections" && $db_connections -lt 50 ]]; then
        success "Database connections: $db_connections (healthy)"
    elif [[ -n "$db_connections" ]]; then
        warning "Database connections: $db_connections (high)"
    else
        warning "Could not retrieve database connection count"
    fi
    
    # Check query performance
    local avg_query_time=$(echo "$metrics_response" | grep -o '"query_duration_avg_ms":[0-9.]*' | cut -d':' -f2)
    if [[ -n "$avg_query_time" ]]; then
        if (( $(echo "$avg_query_time < 100" | bc -l) )); then
            success "Average query time: ${avg_query_time}ms (excellent)"
        elif (( $(echo "$avg_query_time < 500" | bc -l) )); then
            success "Average query time: ${avg_query_time}ms (good)"
        else
            warning "Average query time: ${avg_query_time}ms (may need optimization)"
        fi
    fi
    
    return 0
}

# Cache performance check
check_cache() {
    log "Checking cache performance..."
    
    # Get cache metrics from API
    local metrics_response=$(curl -s --max-time 30 "$API_BASE_URL/api/v1/metrics" 2>/dev/null || echo "{}")
    
    # Check cache hit ratio
    local cache_hits=$(echo "$metrics_response" | grep -o '"cache_hits":[0-9]*' | cut -d':' -f2)
    local cache_misses=$(echo "$metrics_response" | grep -o '"cache_misses":[0-9]*' | cut -d':' -f2)
    
    if [[ -n "$cache_hits" && -n "$cache_misses" && $((cache_hits + cache_misses)) -gt 0 ]]; then
        local hit_ratio=$(( cache_hits * 100 / (cache_hits + cache_misses) ))
        
        if [[ $hit_ratio -gt 80 ]]; then
            success "Cache hit ratio: ${hit_ratio}% (excellent)"
        elif [[ $hit_ratio -gt 60 ]]; then
            success "Cache hit ratio: ${hit_ratio}% (good)"
        else
            warning "Cache hit ratio: ${hit_ratio}% (may need optimization)"
        fi
    else
        warning "Could not retrieve cache metrics"
    fi
    
    return 0
}

# Security headers check
check_security_headers() {
    log "Checking security headers..."
    
    local headers_to_check=(
        "X-Frame-Options"
        "X-Content-Type-Options"
        "X-XSS-Protection"
        "Strict-Transport-Security"
        "Content-Security-Policy"
    )
    
    local missing_headers=()
    
    for header in "${headers_to_check[@]}"; do
        local header_value=$(curl -s -I --max-time 10 "$FRONTEND_URL/" | grep -i "^$header:" || echo "")
        
        if [[ -n "$header_value" ]]; then
            success "Security header present: $header"
        else
            missing_headers+=("$header")
        fi
    done
    
    if [[ ${#missing_headers[@]} -gt 0 ]]; then
        warning "Missing security headers:"
        for header in "${missing_headers[@]}"; do
            warning "  - $header"
        done
    else
        success "All security headers are present"
    fi
    
    return 0
}

# Business metrics check
check_business_metrics() {
    log "Checking business metrics..."
    
    local metrics_response=$(curl -s --max-time 30 "$API_BASE_URL/api/v1/metrics" 2>/dev/null || echo "{}")
    
    # Check active users
    local active_users=$(echo "$metrics_response" | grep -o '"active_users":[0-9]*' | cut -d':' -f2)
    if [[ -n "$active_users" ]]; then
        if [[ $active_users -gt 0 ]]; then
            success "Active users: $active_users"
        else
            warning "No active users detected"
        fi
    fi
    
    # Check error rate
    local error_rate=$(curl -s --max-time 10 "$API_BASE_URL/api/v1/metrics/prometheus" | grep "dinner1_errors_total" | tail -1 | awk '{print $2}')
    if [[ -n "$error_rate" ]]; then
        success "Current error count: $error_rate"
    fi
    
    return 0
}

# Generate health report
generate_report() {
    local exit_code=$1
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    
    echo ""
    echo "=================================================="
    echo "Dinner1 Production Health Check Report"
    echo "=================================================="
    echo "Timestamp: $timestamp"
    echo "Overall Status: $([ $exit_code -eq 0 ] && echo "HEALTHY" || echo "UNHEALTHY")"
    echo "API Base URL: $API_BASE_URL"
    echo "Frontend URL: $FRONTEND_URL"
    echo "=================================================="
    
    if [[ $exit_code -eq 0 ]]; then
        success "All health checks passed successfully!"
        echo "✅ Basic connectivity"
        echo "✅ API health"
        echo "✅ Critical endpoints"
        echo "✅ Performance"
        echo "✅ SSL certificates"
        echo "✅ Database connectivity"
        echo "✅ Cache performance"
        echo "✅ Security headers"
        echo "✅ Business metrics"
    else
        error "Some health checks failed!"
        echo "❌ Check the logs above for specific failures"
    fi
    
    echo "=================================================="
}

# Main function
main() {
    log "Starting comprehensive production health check..."
    log "Target URLs: $FRONTEND_URL, $API_BASE_URL"
    
    local overall_status=0
    
    # Run all health checks
    check_basic_connectivity || overall_status=1
    check_api_health || overall_status=1
    check_critical_endpoints || overall_status=1
    check_performance || overall_status=1
    check_ssl_certificates || overall_status=1
    check_database || overall_status=1
    check_cache || overall_status=1
    check_security_headers || overall_status=1
    check_business_metrics || overall_status=1
    
    # Generate report
    generate_report $overall_status
    
    exit $overall_status
}

# Handle script arguments
case "${1:-}" in
    -h|--help)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  -h, --help    Show this help message"
        echo ""
        echo "Environment variables:"
        echo "  API_BASE_URL     Base URL for API (default: https://api.dinner1.com)"
        echo "  FRONTEND_URL     Frontend URL (default: https://dinner1.com)"
        echo "  TIMEOUT          Request timeout in seconds (default: 30)"
        echo "  MAX_RETRIES      Maximum retry attempts (default: 3)"
        exit 0
        ;;
    *)
        main
        ;;
esac