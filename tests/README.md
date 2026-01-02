# PDFChat Test Suite

Comprehensive test suite for the PDFChat application with 90%+ code coverage.

## Overview

The test suite uses:
- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **pytest-sugar**: Pretty test output
- **pytest-xdist**: Parallel test execution
- **pytest-mock**: Mocking utilities

## Test Structure

```
tests/
├── __init__.py           # Package marker
├── conftest.py           # Shared fixtures
├── test_config.py        # Configuration tests
├── test_models.py        # Database model tests
├── test_api.py           # Flask API endpoint tests
├── test_agents.py        # QA agent tests
├── test_build_index.py   # Indexing pipeline tests
└── README.md             # This file
```

## Running Tests

### Run All Tests

```bash
uv run pytest
```

### Run with Coverage Report

```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Run with HTML Coverage Report

```bash
uv run pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Tests in Parallel

```bash
uv run pytest -n auto
```

### Run Specific Test File

```bash
uv run pytest tests/test_api.py
```

### Run Specific Test Class

```bash
uv run pytest tests/test_api.py::TestConversationEndpoints
```

### Run Specific Test

```bash
uv run pytest tests/test_api.py::TestConversationEndpoints::test_create_conversation
```

### Run Tests by Marker

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

## Test Markers

Tests are marked with the following categories:

- `@pytest.mark.unit` - Unit tests (fast, isolated)
- `@pytest.mark.integration` - Integration tests (slower, test component interaction)
- `@pytest.mark.slow` - Slow running tests (requires external services)

## Coverage Requirements

The test suite maintains a minimum of **80% code coverage** as enforced by pytest configuration.

Current coverage: **90.60%**

### Coverage by Module

- `src/agents/qa_agent.py`: 100%
- `src/config.py`: 100%
- `src/models.py`: 100%
- `src/indexing/build_index.py`: 98.33%
- `src/api/app.py`: 82.08%

## Fixtures

Shared fixtures are defined in `conftest.py`:

- `temp_dir` - Temporary directory for tests
- `test_db_path` - Path to test database
- `conversation_db` - Test database instance
- `app` - Flask test application
- `client` - Flask test client
- `mock_llm` - Mock LLM for testing
- `mock_embed_model` - Mock embedding model
- `mock_vector_store` - Mock vector store
- `sample_conversation_data` - Sample conversation data

## Writing New Tests

### Example Unit Test

```python
import pytest
from src.models import ConversationDB


@pytest.mark.unit
class TestMyFeature:
    """Test my new feature."""

    def test_feature_works(self, conversation_db):
        """Test that feature works correctly."""
        result = conversation_db.some_method()
        assert result is not None
```

### Example Integration Test

```python
@pytest.mark.integration
class TestEndToEndFlow:
    """Test complete user flows."""

    def test_full_flow(self, client):
        """Test complete workflow."""
        # Create resource
        response = client.post("/api/resource", json={"data": "test"})
        assert response.status_code == 200
```

### Using Mocks

```python
from unittest.mock import Mock, patch


def test_with_mock(monkeypatch):
    """Test using mocks."""
    mock_service = Mock()
    mock_service.method.return_value = "mocked"

    monkeypatch.setattr("module.service", mock_service)

    # Test code that uses the mocked service
    result = some_function()
    assert result == "mocked"
```

## Continuous Integration

The test suite is configured to fail if:
- Any test fails
- Coverage drops below 80%
- Type checking fails (if enabled)

## Best Practices

1. **Isolate Tests**: Each test should be independent and not rely on other tests
2. **Use Fixtures**: Leverage fixtures for common test setup
3. **Mock External Services**: Mock LLMs, APIs, and file system operations
4. **Test Edge Cases**: Include tests for error conditions and edge cases
5. **Descriptive Names**: Use clear, descriptive test names that explain what is being tested
6. **Fast Tests**: Keep tests fast by mocking slow operations
7. **Clean Up**: Use fixtures and context managers to ensure proper cleanup

## Troubleshooting

### Tests Fail with Database Errors

Make sure temporary directories are being used. Check that `conversation_db` fixture is being used instead of the default database path.

### Coverage is Lower Than Expected

Run with `--cov-report=term-missing` to see which lines are not covered:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

### Tests Are Slow

Run tests in parallel:

```bash
uv run pytest -n auto
```

Or skip slow tests:

```bash
uv run pytest -m "not slow"
```

## Contributing

When adding new features:

1. Write tests first (TDD approach)
2. Ensure tests pass: `uv run pytest`
3. Check coverage: `uv run pytest --cov=src`
4. Maintain 80%+ coverage
5. Add appropriate test markers (`@pytest.mark.unit`, etc.)
