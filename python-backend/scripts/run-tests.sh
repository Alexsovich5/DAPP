#!/bin/bash
# Comprehensive Test Runner for CI/CD
# Executes different test suites with proper reporting and error handling

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_SUITE=${1:-"all"}
FAIL_FAST=${FAIL_FAST:-"false"}
PARALLEL=${PARALLEL:-"false"}
COVERAGE=${COVERAGE:-"true"}
REPORT_DIR=${REPORT_DIR:-"test_reports"}
MAX_WORKERS=${MAX_WORKERS:-"auto"}
TIMEOUT=${TIMEOUT:-"300"}

# Test configuration
UNIT_TIMEOUT=60
INTEGRATION_TIMEOUT=180
ASYNC_TIMEOUT=120
PERFORMANCE_TIMEOUT=300
E2E_TIMEOUT=600

echo -e "${BLUE}🧪 Running Test Suite: $TEST_SUITE${NC}"
echo "Configuration:"
echo "  Fail Fast: $FAIL_FAST"
echo "  Parallel: $PARALLEL"
echo "  Coverage: $COVERAGE"
echo "  Report Directory: $REPORT_DIR"
echo "  Max Workers: $MAX_WORKERS"

# Create report directory
mkdir -p "$REPORT_DIR"

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

# Function to run tests with timeout and error handling
run_test_suite() {
    local suite_name="$1"
    local test_command="$2"
    local timeout_seconds="$3"
    local marker="$4"
    
    echo -e "${BLUE}📝 Running $suite_name tests...${NC}"
    
    local start_time=$(date +%s)
    local junit_file="$REPORT_DIR/junit-$suite_name.xml"
    local coverage_file="$REPORT_DIR/coverage-$suite_name.xml"
    local log_file="$REPORT_DIR/log-$suite_name.txt"
    
    # Build pytest command
    local pytest_cmd="pytest tests/"
    
    if [[ -n "$marker" ]]; then
        pytest_cmd="$pytest_cmd -m \"$marker\""
    fi
    
    # Add common options
    pytest_cmd="$pytest_cmd --junit-xml=$junit_file"
    pytest_cmd="$pytest_cmd --tb=short"
    pytest_cmd="$pytest_cmd -v"
    
    # Add coverage if enabled
    if [[ "$COVERAGE" == "true" ]]; then
        pytest_cmd="$pytest_cmd --cov=app"
        pytest_cmd="$pytest_cmd --cov-report=xml:$coverage_file"
        pytest_cmd="$pytest_cmd --cov-report=html:$REPORT_DIR/htmlcov-$suite_name"
    fi
    
    # Add parallel execution if enabled
    if [[ "$PARALLEL" == "true" && "$suite_name" != "integration" ]]; then
        pytest_cmd="$pytest_cmd -n $MAX_WORKERS"
    fi
    
    # Add fail fast if enabled
    if [[ "$FAIL_FAST" == "true" ]]; then
        pytest_cmd="$pytest_cmd --maxfail=1"
    else
        pytest_cmd="$pytest_cmd --maxfail=10"
    fi
    
    # Execute with timeout (handle different platforms)
    if command -v timeout >/dev/null 2>&1; then
        # Linux timeout command
        if timeout "$timeout_seconds" bash -c "$pytest_cmd" > "$log_file" 2>&1; then
            timeout_success=true
        else
            timeout_success=false
        fi
    elif command -v gtimeout >/dev/null 2>&1; then
        # macOS with GNU coreutils
        if gtimeout "$timeout_seconds" bash -c "$pytest_cmd" > "$log_file" 2>&1; then
            timeout_success=true
        else
            timeout_success=false
        fi
    else
        # No timeout available, run without timeout
        print_warning "timeout command not available, running without timeout"
        if bash -c "$pytest_cmd" > "$log_file" 2>&1; then
            timeout_success=true
        else
            timeout_success=false
        fi
    fi
    
    if [[ "$timeout_success" == "true" ]]; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_status "$suite_name tests completed in ${duration}s"
        
        # Extract test summary
        if [[ -f "$junit_file" ]]; then
            local test_count=$(grep -o 'tests="[0-9]*"' "$junit_file" | grep -o '[0-9]*' || echo "0")
            local failures=$(grep -o 'failures="[0-9]*"' "$junit_file" | grep -o '[0-9]*' || echo "0")
            local errors=$(grep -o 'errors="[0-9]*"' "$junit_file" | grep -o '[0-9]*' || echo "0")
            echo "  Tests: $test_count, Failures: $failures, Errors: $errors"
        fi
        
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_error "$suite_name tests failed after ${duration}s (timeout: ${timeout_seconds}s)"
        
        # Show last few lines of log
        echo "Last 10 lines of output:"
        tail -n 10 "$log_file" || true
        
        return 1
    fi
}

# Test suite definitions
run_security_tests() {
    echo -e "${BLUE}🔒 Running security tests...${NC}"
    
    # Safety check for vulnerabilities
    echo "Checking for known vulnerabilities..."
    if command -v safety &> /dev/null; then
        safety check --json --output "$REPORT_DIR/safety-report.json" || print_warning "Safety check found issues"
    fi
    
    # Bandit security linter
    echo "Running security linter..."
    if command -v bandit &> /dev/null; then
        bandit -r app/ -f json -o "$REPORT_DIR/bandit-report.json" || print_warning "Bandit found security issues"
    fi
    
    print_status "Security tests completed"
}

run_lint_tests() {
    echo -e "${BLUE}📏 Running lint and format checks...${NC}"
    
    local lint_failed=false
    
    # Black formatting check
    if ! black --check --diff app/ tests/ > "$REPORT_DIR/black-output.txt" 2>&1; then
        print_error "Code formatting issues found"
        lint_failed=true
    fi
    
    # isort import sorting check
    if ! isort --check-only --diff app/ tests/ > "$REPORT_DIR/isort-output.txt" 2>&1; then
        print_error "Import sorting issues found"
        lint_failed=true
    fi
    
    # flake8 linting
    if ! flake8 app/ tests/ --max-line-length=100 --extend-ignore=E203,W503 > "$REPORT_DIR/flake8-output.txt" 2>&1; then
        print_error "Linting issues found"
        lint_failed=true
    fi
    
    if [[ "$lint_failed" == "true" ]]; then
        return 1
    fi
    
    print_status "Lint and format checks passed"
}

run_unit_tests() {
    run_test_suite "unit" "" "$UNIT_TIMEOUT" "unit"
}

run_integration_tests() {
    run_test_suite "integration" "" "$INTEGRATION_TIMEOUT" "integration"
}

run_async_tests() {
    # Run async infrastructure tests first
    if run_test_suite "async-infrastructure" "tests/test_async_infrastructure.py" "$ASYNC_TIMEOUT" ""; then
        print_status "Async infrastructure tests passed"
    else
        print_error "Async infrastructure tests failed"
        return 1
    fi
    
    # Run WebSocket tests
    run_test_suite "websocket" "" "$ASYNC_TIMEOUT" "websocket"
}

run_performance_tests() {
    echo -e "${BLUE}⚡ Running performance tests...${NC}"
    
    local start_time=$(date +%s)
    local benchmark_file="$REPORT_DIR/benchmark-results.json"
    local junit_file="$REPORT_DIR/junit-performance.xml"
    
    # Run with timeout handling
    local perf_success=false
    if command -v timeout >/dev/null 2>&1; then
        timeout "$PERFORMANCE_TIMEOUT" pytest tests/ -m "performance" \
            --benchmark-only \
            --benchmark-json="$benchmark_file" \
            --junit-xml="$junit_file" \
            -v > "$REPORT_DIR/log-performance.txt" 2>&1 && perf_success=true
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout "$PERFORMANCE_TIMEOUT" pytest tests/ -m "performance" \
            --benchmark-only \
            --benchmark-json="$benchmark_file" \
            --junit-xml="$junit_file" \
            -v > "$REPORT_DIR/log-performance.txt" 2>&1 && perf_success=true
    else
        pytest tests/ -m "performance" \
            --benchmark-only \
            --benchmark-json="$benchmark_file" \
            --junit-xml="$junit_file" \
            -v > "$REPORT_DIR/log-performance.txt" 2>&1 && perf_success=true
    fi
    
    if [[ "$perf_success" == "true" ]]; then
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        print_status "Performance tests completed in ${duration}s"
        
        # Show benchmark summary if available
        if [[ -f "$benchmark_file" ]]; then
            echo "Benchmark results saved to $benchmark_file"
        fi
        
        return 0
    else
        print_warning "Performance tests failed or timed out"
        return 1
    fi
}

run_e2e_tests() {
    echo -e "${BLUE}🌍 Running end-to-end tests...${NC}"
    
    # Start the application in background
    echo "Starting FastAPI server..."
    uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$REPORT_DIR/server.log" 2>&1 &
    local server_pid=$!
    
    # Wait for server to start
    echo "Waiting for server to be ready..."
    local retry_count=0
    while ! curl -s http://localhost:8000/health > /dev/null; do
        if [[ $retry_count -gt 30 ]]; then
            print_error "Server failed to start within 30 seconds"
            kill $server_pid || true
            return 1
        fi
        sleep 1
        ((retry_count++))
    done
    
    print_status "Server is ready"
    
    # Run E2E tests
    local e2e_result=0
    if ! run_test_suite "e2e" "tests/test_api_integration.py" "$E2E_TIMEOUT" ""; then
        e2e_result=1
    fi
    
    # Cleanup server
    echo "Stopping server..."
    kill $server_pid || true
    wait $server_pid 2>/dev/null || true
    
    return $e2e_result
}

# Generate test report
generate_report() {
    echo -e "${BLUE}📊 Generating test report...${NC}"
    
    local report_file="$REPORT_DIR/test-summary.md"
    local timestamp=$(date -u +"%Y-%m-%d %H:%M:%S UTC")
    
    cat > "$report_file" << EOF
# Test Suite Report

**Generated:** $timestamp  
**Test Suite:** $TEST_SUITE  
**Configuration:**
- Fail Fast: $FAIL_FAST
- Parallel: $PARALLEL
- Coverage: $COVERAGE
- Max Workers: $MAX_WORKERS

## Test Results Summary

EOF
    
    # Add results for each test type
    for test_type in unit integration async performance e2e; do
        local junit_file="$REPORT_DIR/junit-$test_type.xml"
        if [[ -f "$junit_file" ]]; then
            echo "### $test_type Tests" >> "$report_file"
            local test_count=$(grep -o 'tests="[0-9]*"' "$junit_file" | grep -o '[0-9]*' || echo "0")
            local failures=$(grep -o 'failures="[0-9]*"' "$junit_file" | grep -o '[0-9]*' || echo "0")
            local errors=$(grep -o 'errors="[0-9]*"' "$junit_file" | grep -o '[0-9]*' || echo "0")
            local time=$(grep -o 'time="[0-9.]*"' "$junit_file" | head -1 | grep -o '[0-9.]*' || echo "0")
            
            echo "- Tests: $test_count" >> "$report_file"
            echo "- Failures: $failures" >> "$report_file"
            echo "- Errors: $errors" >> "$report_file"
            echo "- Duration: ${time}s" >> "$report_file"
            echo "" >> "$report_file"
        fi
    done
    
    # Add coverage summary if available
    if [[ "$COVERAGE" == "true" ]]; then
        echo "## Coverage Summary" >> "$report_file"
        echo "" >> "$report_file"
        
        # Combine coverage reports if multiple exist
        if ls "$REPORT_DIR"/coverage-*.xml 1> /dev/null 2>&1; then
            echo "Coverage reports generated for individual test suites." >> "$report_file"
        fi
    fi
    
    # Add file listing
    echo "## Generated Files" >> "$report_file"
    echo "" >> "$report_file"
    ls -la "$REPORT_DIR" >> "$report_file"
    
    print_status "Test report generated: $report_file"
}

# Main execution logic
main() {
    local overall_result=0
    
    case "$TEST_SUITE" in
        "security")
            run_security_tests || overall_result=1
            ;;
        "lint")
            run_lint_tests || overall_result=1
            ;;
        "unit")
            run_unit_tests || overall_result=1
            ;;
        "integration")
            run_integration_tests || overall_result=1
            ;;
        "async")
            run_async_tests || overall_result=1
            ;;
        "performance")
            run_performance_tests || overall_result=1
            ;;
        "e2e")
            run_e2e_tests || overall_result=1
            ;;
        "all")
            echo -e "${BLUE}🚀 Running complete test suite...${NC}"
            
            run_security_tests || overall_result=1
            run_lint_tests || overall_result=1
            run_unit_tests || overall_result=1
            run_integration_tests || overall_result=1
            run_async_tests || overall_result=1
            
            # Only run performance and E2E on main/development branches
            if [[ "${GITHUB_REF:-}" == "refs/heads/main" || "${GITHUB_REF:-}" == "refs/heads/development" || "${CI_COMMIT_REF_NAME:-}" == "main" || "${CI_COMMIT_REF_NAME:-}" == "development" ]]; then
                run_performance_tests || print_warning "Performance tests failed but continuing"
                run_e2e_tests || print_warning "E2E tests failed but continuing"
            fi
            ;;
        "quick")
            echo -e "${BLUE}⚡ Running quick test suite...${NC}"
            run_lint_tests || overall_result=1
            run_unit_tests || overall_result=1
            ;;
        *)
            print_error "Unknown test suite: $TEST_SUITE"
            echo "Available options: security, lint, unit, integration, async, performance, e2e, all, quick"
            exit 1
            ;;
    esac
    
    # Generate report
    generate_report
    
    # Final status
    if [[ $overall_result -eq 0 ]]; then
        echo -e "${GREEN}🎉 Test suite '$TEST_SUITE' completed successfully!${NC}"
    else
        echo -e "${RED}💥 Test suite '$TEST_SUITE' failed!${NC}"
    fi
    
    return $overall_result
}

# Run main function
main "$@"