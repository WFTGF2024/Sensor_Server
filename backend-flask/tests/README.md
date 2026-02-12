# Sensor_Flask Tests

This directory contains test suites for the Sensor_Flask application.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── README.md                # This file
├── run_tests.sh             # Test runner script
├── unit/                    # Unit tests
│   ├── test_errors.py       # Error handling utilities tests
│   └── test_config.py       # Configuration management tests
└── integration/             # Integration tests
    └── test_auth_endpoints.py  # Authentication endpoint tests
```

## Running Tests

### Using Test Runner Script

```bash
# Run all tests
./run_tests.sh

# Run only unit tests
./run_tests.sh unit

# Run only integration tests
./run_tests.sh integration

# Run tests with coverage report
./run_tests.sh all coverage
```

### Using pytest Directly

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run integration tests only
pytest tests/integration/ -v

# Run specific test file
pytest tests/unit/test_errors.py -v

# Run specific test function
pytest tests/unit/test_errors.py::test_api_error_basic -v

# Run tests with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term
```

## Test Coverage

### Unit Tests
- **test_errors.py**: Tests for error handling utilities
  - API error classes
  - Error response creation
  - Field validation utilities
  
- **test_config.py**: Tests for configuration management
  - Default configuration values
  - Environment variable overrides
  - Configuration validation
  - Different environment configurations

### Integration Tests
- **test_auth_endpoints.py**: Tests for authentication endpoints
  - User registration
  - User login/logout
  - Profile management
  - Password changes
  - Account deletion

## Test Fixtures

The `conftest.py` file provides the following fixtures:

- `test_client`: Flask test client for making HTTP requests
- `test_db_config`: Test database configuration
- `mock_db_connection`: Mock database connection and cursor
- `test_user_data`: Sample user data for testing
- `test_file_data`: Sample file data for testing
- `temp_upload_dir`: Temporary upload directory
- `authenticated_session`: Client with authenticated session

## Writing New Tests

### Unit Test Example

```python
def test_my_function():
    """Test description."""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = my_function(input_data)
    
    # Assert
    assert result == expected_result
```

### Integration Test Example

```python
def test_my_endpoint(test_client):
    """Test endpoint description."""
    # Arrange
    request_data = {"key": "value"}
    
    # Act
    response = test_client.post(
        '/my-endpoint',
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # Assert
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
```

## Best Practices

1. **Use descriptive test names**: Each test should clearly describe what it's testing
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Test one thing**: Each test should focus on a single behavior
4. **Use fixtures**: Reuse fixtures for common setup
5. **Mock external dependencies**: Use mocks for database, file system, etc.
6. **Keep tests independent**: Tests should not depend on each other
7. **Test both success and failure cases**: Cover happy paths and error cases

## Environment Setup

Tests use the following environment variables:

```bash
FLASK_ENV=testing
FLASK_SECRET_KEY=test-secret-key-for-testing
DB_NAME=modality_test
```

These are automatically set by the test runner script.

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    ./run_tests.sh all coverage
```

## Troubleshooting

### Import Errors
If you encounter import errors, make sure you're running tests from the project root directory.

### Database Connection Errors
Tests use mock database connections, so no actual database is required.

### Fixture Not Found
Make sure `conftest.py` is in the `tests/` directory and fixtures are properly defined.