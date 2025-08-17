# Testing Quick Reference

Fast reference for common testing tasks and commands.

## Quick Commands

### Setup
```bash
# Setup test environment
./scripts/setup-test-env.sh

# Install test dependencies
pip install -r requirements.txt
```

### Running Tests
```bash
# All tests
pytest tests/

# By category
pytest tests/ -m unit          # Unit tests only
pytest tests/ -m integration   # Integration tests only
pytest tests/ -m async_tests   # Async/WebSocket tests
pytest tests/ -m performance   # Performance tests
pytest tests/ -m security      # Security tests

# With coverage
pytest tests/ --cov=app --cov-report=html

# Parallel execution
pytest tests/ -n auto

# Stop on first failure
pytest tests/ -x

# Verbose output
pytest tests/ -v

# Show test durations
pytest tests/ --durations=10
```

### CI/CD Scripts
```bash
# Run specific test suite
./scripts/run-tests.sh unit
./scripts/run-tests.sh integration
./scripts/run-tests.sh async
./scripts/run-tests.sh performance
./scripts/run-tests.sh all

# Quick tests (lint + unit)
./scripts/run-tests.sh quick

# Security scan
./scripts/run-tests.sh security
```

## Test Markers

```python
@pytest.mark.unit           # Fast unit tests
@pytest.mark.integration    # Database integration tests
@pytest.mark.async_tests    # Async/WebSocket tests
@pytest.mark.performance    # Performance benchmarks
@pytest.mark.security       # Security tests
@pytest.mark.slow           # Slow tests (run separately)
@pytest.mark.flaky          # Tests that may need retries
```

## Common Fixtures

```python
# Basic fixtures
authenticated_user           # User with auth headers
test_user                   # Basic test user
client                      # FastAPI test client
db_session                  # Database session

# Advanced fixtures
soul_connection_data        # Complete soul connection
high_compatibility_users    # Users with high compatibility
websocket_test_client       # WebSocket testing client
async_performance_monitor   # Performance monitoring

# Service fixtures
soul_compatibility_service  # Compatibility calculation
revelation_service         # Revelation management
async_ai_service           # AI service mocking
realtime_service           # WebSocket real-time service
```

## Test Templates

### Unit Test
```python
@pytest.mark.unit
def test_function_name():
    """Test description"""
    # Arrange
    input_data = "test_input"
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result == expected_output
```

### Integration Test
```python
@pytest.mark.integration
def test_api_endpoint(client, authenticated_user):
    """Test API endpoint integration"""
    response = client.post(
        "/api/v1/endpoint",
        json={"data": "test"},
        headers=authenticated_user["headers"]
    )
    
    assert response.status_code == 201
    assert response.json()["field"] == "expected_value"
```

### Async Test
```python
@pytest.mark.asyncio
@pytest.mark.async_tests
async def test_async_function(async_fixture):
    """Test async functionality"""
    result = await async_function()
    assert result is not None
```

### Performance Test
```python
@pytest.mark.performance
def test_performance(benchmark):
    """Test performance benchmark"""
    result = benchmark(function_to_benchmark)
    assert result > 0
```

## Environment Variables

```bash
# Testing mode
export TESTING=1

# Database URLs
export TEST_DATABASE_URL="sqlite:///./test.db"
export TEST_DATABASE_URL="postgresql://user:pass@localhost:5432/testdb"

# CI mode
export CI=1

# Allow database operations
export ALLOW_DB_DROP=1

# Redis URL for cache testing
export REDIS_URL="redis://localhost:6379"
```

## Debugging Tests

```bash
# Debug specific test
pytest tests/test_file.py::test_function -v -s

# Show all output
pytest tests/ -s

# Drop into debugger on failure
pytest tests/ --pdb

# Run with coverage debug
pytest tests/ --cov=app --cov-report=term-missing

# Profile test execution
python -m cProfile -s cumtime -m pytest tests/
```

## Docker Testing

```bash
# Run all tests in Docker
docker-compose -f docker-compose.test.yml up test-runner

# Run specific test suite
docker-compose -f docker-compose.test.yml up unit-test-runner
docker-compose -f docker-compose.test.yml up async-test-runner

# View test reports
docker-compose -f docker-compose.test.yml up test-reports
# Open http://localhost:8080 to view reports
```

## Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Generate XML coverage report (for CI)
pytest tests/ --cov=app --cov-report=xml

# Check coverage percentage
coverage report

# Show missing lines
coverage report --show-missing
```

## Common Patterns

### Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("valid_input", True),
    ("invalid_input", False),
])
def test_validation(input, expected):
    assert validate(input) == expected
```

### Exception Testing
```python
def test_function_raises_exception():
    with pytest.raises(ValueError, match="Expected error message"):
        function_that_should_raise()
```

### Mock Usage
```python
from unittest.mock import Mock, patch

def test_with_mock():
    with patch('app.services.external_service') as mock_service:
        mock_service.return_value = "mocked_result"
        result = function_using_service()
        assert result == "expected_result"
        mock_service.assert_called_once()
```

### Fixture Creation
```python
@pytest.fixture
def custom_data():
    """Create custom test data"""
    return {"key": "value"}

@pytest.fixture
def sample_user(db_session):
    """Create sample user for testing"""
    user = UserFactory(email="test@example.com")
    return user
```

## Troubleshooting

### Database Issues
```bash
# Reset test database
rm test.db
alembic upgrade head

# Check PostgreSQL connection
pg_isready -h localhost -p 5432 -U testuser
```

### Import Issues
```bash
# Set Python path
export PYTHONPATH=.

# Check imports
python -c "import app.main"
```

### Async Issues
```bash
# Check async test configuration
pytest tests/test_async.py -v --tb=long

# Verify asyncio mode
grep asyncio_mode pytest.ini
```

### Performance Issues
```bash
# Find slow tests
pytest tests/ --durations=0

# Run only fast tests
pytest tests/ -m "not slow"

# Profile specific test
python -c "import cProfile; cProfile.run('pytest tests/test_slow.py')"
```

## File Locations

- **Main test config**: `pytest.ini`
- **CI test config**: `pytest-ci.ini`
- **Test fixtures**: `tests/conftest.py`
- **Test factories**: `tests/factories.py`
- **Environment setup**: `scripts/setup-test-env.sh`
- **Test runner**: `scripts/run-tests.sh`
- **Coverage config**: `.coveragerc`
- **Docker tests**: `docker-compose.test.yml`