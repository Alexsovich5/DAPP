# Backend Directory Structure

This document outlines the organized structure of the Python backend codebase.

## Directory Structure

```
python-backend/
├── app/                          # Main application code
│   ├── api/                      # API routes and endpoints
│   ├── core/                     # Core functionality (auth, database, etc.)
│   ├── models/                   # Database models
│   ├── ai/                       # AI/ML components (Sprint 8)
│   └── middleware/               # Custom middleware
├── tests/                        # Test suite
│   ├── manual/                   # Manual test scripts
│   ├── integration/              # Integration tests
│   ├── validation/               # Feature validation tests
│   ├── data/                     # Test data files
│   └── databases/                # Test database configurations
├── alembic/                      # Database migrations
├── debug/                        # Debug and development tools
├── docs/                         # Documentation and reports
│   └── reports/                  # Generated reports (coverage, bandit, etc.)
├── logs/                         # Application logs
├── uploads/                      # File upload storage
├── venv/                         # Python virtual environment
├── .env                         # Environment configuration
├── .env.example                 # Environment template
├── .env.test.example            # Test environment template
├── .env.production.template     # Production environment template
├── requirements.txt             # Python dependencies
├── requirements-ai.txt          # AI/ML specific dependencies
├── run.py                       # Application entry point
├── pytest.ini                  # PyTest configuration
├── alembic.ini                  # Alembic configuration
└── Dockerfile                   # Docker configuration
```

## Key Reorganization Changes

### Files Moved:
- `debug_*.py` → `debug/`
- `test_imports.py`, `test_sprint8_imports.py` → `tests/manual/`
- `test_matching_validation.py`, `test_photo_reveal_system.py` → `tests/validation/`
- `test_security_headers.py` → `tests/integration/`
- `test_data/` → `tests/data/`
- `test_databases/` → `tests/databases/`
- `bandit-report.json`, `coverage.xml` → `docs/reports/`

### Cleaned Up:
- Removed temporary cache directories (`.benchmarks`, `.pytest_cache`, `htmlcov`)
- Removed duplicate nested `python-backend/python-backend/` structure
- Removed `.DS_Store` and other system files

## Test Organization

### tests/manual/
Manual test scripts for component validation and import testing.

### tests/integration/
Integration tests that test multiple components working together.

### tests/validation/
Feature-specific validation tests for complex functionality.

### tests/data/
Test data files and fixtures.

### tests/databases/
Database-related test configurations and schemas.

## Usage

All tests should be run from the `python-backend` directory:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/integration/
pytest tests/validation/

# Run manual validation
python tests/manual/test_sprint8_imports.py
```

## CI/CD Integration

The GitHub Actions pipeline has been updated to reference the new file locations:
- Sprint 8 import validation: `tests/manual/test_sprint8_imports.py`
- All other tests continue to use the standard `tests/` directory structure
