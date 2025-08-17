# Testing Guide - Dinner First Backend

This document provides comprehensive testing guidelines, patterns, and standards for the Dinner First dating platform backend.

## Table of Contents

1. [Overview](#overview)
2. [Test Categories](#test-categories)
3. [Testing Standards](#testing-standards)
4. [Test Environment Setup](#test-environment-setup)
5. [Writing Tests](#writing-tests)
6. [Test Fixtures](#test-fixtures)
7. [Async Testing](#async-testing)
8. [CI/CD Integration](#cicd-integration)
9. [Performance Testing](#performance-testing)
10. [Security Testing](#security-testing)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

## Overview

The Dinner First backend uses a comprehensive testing strategy with multiple test categories, fixtures, and CI/CD integration to ensure code quality and reliability.

### Testing Philosophy

- **Soul Before Skin**: Tests should validate the core functionality before UI concerns
- **Comprehensive Coverage**: Aim for high test coverage with meaningful tests
- **Fast Feedback**: Unit tests should be fast, integration tests thorough
- **Realistic Testing**: Use real databases and services for integration tests
- **Async-First**: Properly test async/await patterns and WebSocket functionality

### Test Coverage Goals

- **Overall Coverage**: ≥50% (current requirement)
- **Core Services**: ≥80% coverage
- **API Endpoints**: ≥70% coverage
- **Critical Paths**: 100% coverage (auth, matching, safety)

## Test Categories

### 1. Unit Tests (`@pytest.mark.unit`)

**Purpose**: Test individual functions, classes, and modules in isolation.

**Characteristics**:
- Fast execution (< 1 second per test)
- No external dependencies (database, network, files)
- Use mocks and stubs for dependencies
- High coverage of business logic

**Example**:
```python
@pytest.mark.unit
def test_calculate_age_compatibility():
    """Test age compatibility calculation algorithm"""
    calculator = CompatibilityCalculator()
    
    # Same age should be perfect match
    assert calculator.calculate_age_compatibility(25, 25) == 1.0
    
    # Small difference should be high compatibility
    assert calculator.calculate_age_compatibility(25, 27) == 0.9
    
    # Large difference should be low compatibility
    assert calculator.calculate_age_compatibility(25, 45) == 0.2
```

### 2. Integration Tests (`@pytest.mark.integration`)

**Purpose**: Test interactions between components, including database operations.

**Characteristics**:
- Use real database (PostgreSQL in CI, SQLite locally)
- Test API endpoints end-to-end
- Validate data persistence and retrieval
- Test service interactions

**Example**:
```python
@pytest.mark.integration
def test_soul_connection_creation_workflow(client, authenticated_user, db_session):
    """Test complete soul connection creation workflow"""
    # Create potential match
    other_user = UserFactory()
    
    # Create connection
    response = client.post(
        "/api/v1/connections/initiate",
        json={"target_user_id": other_user.id},
        headers=authenticated_user["headers"]
    )
    
    assert response.status_code == 201
    connection_data = response.json()
    
    # Verify database state
    connection = db_session.query(SoulConnection).filter_by(
        id=connection_data["id"]
    ).first()
    assert connection is not None
    assert connection.connection_stage == "soul_discovery"
```

### 3. Async Tests (`@pytest.mark.async_tests`)

**Purpose**: Test asynchronous operations, WebSocket connections, and concurrent processing.

**Characteristics**:
- Use `@pytest.mark.asyncio` decorator
- Test async/await patterns
- Validate WebSocket functionality
- Test concurrent operations

**Example**:
```python
@pytest.mark.asyncio
@pytest.mark.async_tests
async def test_websocket_message_broadcast(websocket_test_client, async_realtime_service):
    """Test WebSocket message broadcasting"""
    # Connect to WebSocket
    await websocket_test_client.connect("/ws/connection/123")
    
    # Send message through service
    result = await async_realtime_service.broadcast_to_connection(
        123, {"type": "message", "content": "Hello"}
    )
    
    assert result["broadcasted"] is True
    assert result["connection_id"] == 123
```

### 4. Performance Tests (`@pytest.mark.performance`)

**Purpose**: Validate system performance and identify bottlenecks.

**Characteristics**:
- Use `pytest-benchmark` for timing
- Test algorithm performance
- Validate concurrent load handling
- Monitor resource usage

**Example**:
```python
@pytest.mark.performance
def test_compatibility_calculation_performance(benchmark, sample_users):
    """Test compatibility calculation performance"""
    calculator = CompatibilityCalculator()
    
    def calculate_compatibility():
        return calculator.calculate_overall_compatibility(
            sample_users[0], sample_users[1]
        )
    
    result = benchmark(calculate_compatibility)
    assert result["total_compatibility"] > 0
```

### 5. Security Tests (`@pytest.mark.security`)

**Purpose**: Validate security measures and identify vulnerabilities.

**Characteristics**:
- Test authentication and authorization
- Validate input sanitization
- Test for common vulnerabilities (XSS, SQL injection)
- Verify data privacy

**Example**:
```python
@pytest.mark.security
def test_sql_injection_protection(client, test_user):
    """Test SQL injection protection in search endpoints"""
    malicious_input = "'; DROP TABLE users; --"
    
    response = client.get(
        f"/api/v1/users/search?query={malicious_input}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    # Should not cause server error
    assert response.status_code in [200, 400, 422]
    
    # Database should still be intact
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {test_user['token']}"})
    assert response.status_code == 200
```

## Testing Standards

### File Naming Conventions

```
tests/
├── test_<module>_unit.py           # Unit tests for specific modules
├── test_<module>_integration.py    # Integration tests
├── test_<feature>_comprehensive.py # Full feature testing
├── test_api_<router>.py            # API endpoint tests
├── test_async_<component>.py       # Async-specific tests
└── test_<service>_performance.py   # Performance tests
```

### Test Class Organization

```python
class TestFeatureName:
    """Test suite for FeatureName functionality"""
    
    def test_basic_functionality(self):
        """Test basic feature operation"""
        pass
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        pass
    
    def test_error_handling(self):
        """Test error conditions and exception handling"""
        pass
    
    @pytest.mark.integration
    def test_database_operations(self):
        """Test database interactions"""
        pass
    
    @pytest.mark.security
    def test_security_requirements(self):
        """Test security and authorization"""
        pass
```

### Test Method Naming

- Use descriptive names that explain what is being tested
- Include the expected outcome in the name
- Use `test_` prefix for pytest discovery

**Good Examples**:
```python
def test_user_registration_with_valid_email_creates_user()
def test_password_validation_rejects_weak_passwords()
def test_soul_connection_calculation_with_high_compatibility_users()
def test_websocket_connection_handles_authentication_failure()
```

**Bad Examples**:
```python
def test_user()  # Too vague
def test_1()     # No meaning
def test_something_works()  # Not specific
```

## Test Environment Setup

### Local Development Setup

1. **Install Dependencies**:
```bash
# Install test dependencies
pip install -r requirements.txt

# Install additional test tools
pip install pytest-xdist pytest-html safety bandit
```

2. **Setup Test Environment**:
```bash
# Run environment setup script
./scripts/setup-test-env.sh

# Or manually set environment variables
export TESTING=1
export TEST_DATABASE_URL="sqlite:///./test_data/test.db"
```

3. **Run Tests**:
```bash
# Run all tests
pytest tests/

# Run specific categories
pytest tests/ -m unit
pytest tests/ -m integration
pytest tests/ -m async_tests

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### CI/CD Environment

Tests run automatically in CI/CD with different configurations:

- **GitHub Actions**: Multi-platform testing with PostgreSQL and Redis
- **GitLab CI**: Parallel execution with service containers
- **Docker**: Isolated test environments with docker-compose

## Writing Tests

### Basic Test Structure

```python
import pytest
from app.models.user import User
from app.services.compatibility import CompatibilityCalculator
from tests.factories import UserFactory, ProfileFactory


class TestCompatibilityCalculation:
    """Test compatibility calculation algorithms"""
    
    @pytest.fixture
    def calculator(self):
        """Create compatibility calculator instance"""
        return CompatibilityCalculator()
    
    @pytest.fixture
    def sample_users(self, db_session):
        """Create sample users for testing"""
        setup_factories(db_session)
        user1 = UserFactory(interests=["cooking", "reading"])
        user2 = UserFactory(interests=["cooking", "hiking"])
        return user1, user2
    
    def test_interest_similarity_calculation(self, calculator, sample_users):
        """Test interest similarity calculation"""
        user1, user2 = sample_users
        
        similarity = calculator.calculate_interest_similarity(
            user1.interests, user2.interests
        )
        
        # Should have some similarity (cooking overlap)
        assert 0.0 < similarity < 1.0
        
    def test_compatibility_with_empty_interests(self, calculator):
        """Test compatibility calculation with empty interest lists"""
        similarity = calculator.calculate_interest_similarity([], [])
        assert similarity == 0.0
        
    @pytest.mark.parametrize("interests1,interests2,expected", [
        (["cooking"], ["cooking"], 1.0),
        (["cooking"], ["hiking"], 0.0),
        (["cooking", "reading"], ["cooking", "hiking"], 0.33),
    ])
    def test_interest_similarity_parametrized(self, calculator, interests1, interests2, expected):
        """Test interest similarity with various input combinations"""
        result = calculator.calculate_interest_similarity(interests1, interests2)
        assert abs(result - expected) < 0.01
```

### Using Test Fixtures

Test fixtures provide reusable test data and setup. See `tests/conftest.py` for available fixtures:

#### Common Fixtures

```python
def test_with_authenticated_user(authenticated_user, client):
    """Test using authenticated user fixture"""
    response = client.get(
        "/api/v1/users/me",
        headers=authenticated_user["headers"]
    )
    assert response.status_code == 200

def test_with_soul_connection_data(soul_connection_data):
    """Test using soul connection fixture"""
    connection = soul_connection_data["connection"]
    users = soul_connection_data["users"]
    
    assert connection.user1_id == users[0].id
    assert connection.user2_id == users[1].id

def test_with_performance_monitoring(async_performance_monitor):
    """Test using performance monitoring fixture"""
    async def slow_operation():
        await asyncio.sleep(0.01)
        return "result"
    
    result, duration = await async_performance_monitor.measure_async_operation(
        slow_operation(), "test_operation"
    )
    
    assert result == "result"
    assert duration >= 0.01
```

#### Custom Fixtures

Create custom fixtures for specific test needs:

```python
@pytest.fixture
def high_compatibility_pair(db_session):
    """Create a pair of users with high compatibility"""
    setup_factories(db_session)
    
    user1 = UserFactory(
        interests=["cooking", "hiking", "reading", "music"],
        core_values={
            "relationship_goals": "I want deep emotional connection",
            "life_values": "Family and personal growth"
        }
    )
    
    user2 = UserFactory(
        interests=["cooking", "travel", "reading", "art"],
        core_values={
            "relationship_goals": "Looking for meaningful connection",
            "life_values": "Family is important to me"
        }
    )
    
    return user1, user2
```

## Async Testing

### Basic Async Test Structure

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test async function"""
    result = await some_async_function()
    assert result is not None
```

### WebSocket Testing

```python
@pytest.mark.asyncio
async def test_websocket_connection(websocket_test_client):
    """Test WebSocket connection and messaging"""
    # Connect
    await websocket_test_client.connect("/ws/test")
    assert websocket_test_client.connected
    
    # Send message
    await websocket_test_client.send_json({
        "type": "message",
        "content": "Hello WebSocket"
    })
    
    # Verify message was sent
    assert len(websocket_test_client.messages_sent) == 1
    
    # Simulate receiving message
    websocket_test_client.simulate_incoming_message("Reply message")
    received = await websocket_test_client.receive_text()
    assert received == "Reply message"
```

### Async Service Testing

```python
@pytest.mark.asyncio
async def test_async_ai_service(async_ai_service):
    """Test async AI service functionality"""
    user_data1 = {"interests": ["cooking"], "values": {"growth": True}}
    user_data2 = {"interests": ["cooking"], "values": {"growth": True}}
    
    insights = await async_ai_service.generate_compatibility_insights(
        user_data1, user_data2
    )
    
    assert "insights" in insights
    assert insights["confidence"] > 0.5
```

## CI/CD Integration

### Running Tests in CI

Tests are automatically executed in CI/CD pipelines:

#### GitHub Actions
```yaml
- name: Run unit tests
  run: pytest tests/ -m unit --cov=app --cov-report=xml

- name: Run integration tests
  env:
    DATABASE_URL: postgresql://testuser:testpass@localhost:5432/testdb
  run: pytest tests/ -m integration
```

#### GitLab CI
```yaml
unit-tests:
  script:
    - pytest tests/ -m unit --junit-xml=junit-unit.xml
  artifacts:
    reports:
      junit: junit-unit.xml
```

### Test Reports

CI generates comprehensive test reports:

- **JUnit XML**: For CI integration and test result tracking
- **Coverage Reports**: HTML and XML coverage reports
- **Performance Reports**: Benchmark results in JSON format
- **Security Reports**: Vulnerability scanning results

### Viewing Test Results

Access test results through:

1. **CI/CD Interface**: View results directly in GitHub/GitLab
2. **Test Report Server**: `http://localhost:8080` when using Docker
3. **Local Coverage**: Open `htmlcov/index.html` after running tests with coverage

## Performance Testing

### Benchmark Tests

Use `pytest-benchmark` for performance testing:

```python
@pytest.mark.performance
def test_algorithm_performance(benchmark):
    """Test algorithm performance with benchmark"""
    def algorithm_to_test():
        # Your algorithm here
        return calculate_complex_compatibility()
    
    result = benchmark(algorithm_to_test)
    
    # Verify result is correct
    assert result > 0
```

### Load Testing

Test concurrent operations:

```python
@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_requests(async_performance_monitor):
    """Test handling concurrent requests"""
    async def simulate_request():
        # Simulate API request
        await asyncio.sleep(0.01)
        return "success"
    
    results = await async_performance_monitor.simulate_concurrent_load(
        simulate_request, concurrent_users=50, iterations=5
    )
    
    assert results["successful"] == 250
    assert results["operations_per_second"] > 100
```

## Security Testing

### Authentication Testing

```python
@pytest.mark.security
def test_unauthorized_access_blocked(client):
    """Test that unauthorized access is properly blocked"""
    response = client.get("/api/v1/users/me")
    assert response.status_code == 401

@pytest.mark.security
def test_invalid_token_rejected(client):
    """Test that invalid tokens are rejected"""
    response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
```

### Input Validation Testing

```python
@pytest.mark.security
def test_input_sanitization(client, authenticated_user):
    """Test that malicious input is properly sanitized"""
    malicious_inputs = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE users; --",
        "../../../etc/passwd",
    ]
    
    for malicious_input in malicious_inputs:
        response = client.post(
            "/api/v1/profiles",
            json={"bio": malicious_input},
            headers=authenticated_user["headers"]
        )
        
        # Should not cause server error
        assert response.status_code in [200, 201, 400, 422]
```

## Best Practices

### 1. Test Organization

- **Group related tests** in classes
- **Use descriptive test names** that explain the scenario
- **Keep tests focused** on a single behavior
- **Use parametrized tests** for multiple input scenarios

### 2. Test Data Management

- **Use factories** for creating test data
- **Isolate test data** between tests
- **Use realistic data** that matches production scenarios
- **Clean up after tests** to prevent interference

### 3. Mocking and Stubbing

- **Mock external dependencies** (APIs, file system, network)
- **Use real databases** for integration tests
- **Mock time-dependent operations** for consistency
- **Verify mock interactions** when testing integration points

### 4. Error Testing

- **Test error conditions** explicitly
- **Verify error messages** are appropriate
- **Test edge cases** and boundary conditions
- **Ensure graceful degradation** under failure conditions

### 5. Performance Considerations

- **Keep unit tests fast** (< 1 second each)
- **Use parallel execution** for test suites
- **Profile slow tests** and optimize if needed
- **Separate performance tests** from regular test runs

## Troubleshooting

### Common Issues

#### 1. Database Connection Errors

**Problem**: Tests fail with database connection errors.

**Solution**:
```bash
# Check database status
pg_isready -h localhost -p 5432 -U testuser

# Reset test database
export ALLOW_DB_DROP=1
alembic upgrade head

# Use SQLite for local testing
export TEST_DATABASE_URL="sqlite:///./test.db"
```

#### 2. Async Test Failures

**Problem**: Async tests hang or fail unexpectedly.

**Solution**:
```python
# Ensure proper async test decoration
@pytest.mark.asyncio
async def test_async_function():
    pass

# Check event loop configuration
pytest tests/test_async.py -v --tb=long
```

#### 3. Import Errors

**Problem**: Tests fail with import errors.

**Solution**:
```bash
# Set PYTHONPATH
export PYTHONPATH=.

# Install dependencies
pip install -r requirements.txt

# Check for circular imports
python -c "import app.main"
```

#### 4. Fixture Conflicts

**Problem**: Fixtures interfere with each other.

**Solution**:
- Use unique fixture names
- Properly scope fixtures (function, class, module, session)
- Clean up fixture state between tests

### Debug Mode

Run tests in debug mode for detailed output:

```bash
# Verbose output
pytest tests/ -v

# Show all output (including prints)
pytest tests/ -s

# Stop on first failure
pytest tests/ -x

# Debug specific test
pytest tests/test_specific.py::test_method -v -s
```

### Performance Debugging

Identify slow tests:

```bash
# Show test durations
pytest tests/ --durations=10

# Profile test execution
pytest tests/ --profile

# Run only fast tests
pytest tests/ -m "not slow"
```

## Conclusion

This testing guide provides comprehensive patterns and standards for testing the Dinner First backend. Follow these guidelines to ensure:

- **High code quality** through comprehensive testing
- **Reliable CI/CD** through consistent test execution
- **Fast feedback** through efficient test organization
- **Security assurance** through targeted security testing
- **Performance validation** through benchmark testing

For questions or improvements to this guide, please refer to the team leads or create an issue in the project repository.

---

**Last Updated**: August 2025  
**Version**: 1.0  
**Authors**: Development Team  
**Review**: Required for any changes to testing standards