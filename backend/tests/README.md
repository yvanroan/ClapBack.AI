# ChatMatch Backend Tests

This directory contains tests for the ChatMatch backend application.

## Running Tests

To run all tests:

```bash
# From the project root
pytest backend/tests/

# With verbose output
pytest -v backend/tests/
```

To run specific test files:

```bash
# Run scenario tests
pytest backend/tests/test_scenarios.py

# Run data module tests
pytest backend/tests/test_data.py

# Run API tests
pytest backend/tests/test_api.py
```

To run tests with specific markers:

```bash
# Run integration tests only
pytest -m integration backend/tests/

# Run non-slow tests
pytest -m "not slow" backend/tests/
```

## Test Structure

The test suite is organized as follows:

- `conftest.py` - Contains pytest fixtures shared across test files
- `test_api.py` - Tests for API endpoints
- `test_data.py` - Tests for the data module
- `test_scenarios.py` - Tests for scenario services
- `data/` - Test data files

## Adding New Tests

### Adding a New Test File

1. Create a new Python file in the `tests` directory with the naming convention `test_*.py`
2. Import the necessary modules and fixtures
3. Write test functions with the naming convention `test_*`

Example:

```python
"""
Tests for the chat service functionality.
"""
import pytest
from backend.app.services import process_chat
from backend.tests import SAMPLE_SCENARIO, SAMPLE_MESSAGES

def test_chat_processing():
    """Test that chat processing works correctly."""
    # Test implementation
    pass
```

### Adding New Fixtures

Add common fixtures to `conftest.py` to make them available to all test files.

### Using Test Markers

To mark a test with a custom marker:

```python
@pytest.mark.integration
def test_with_external_service():
    """This is an integration test that interacts with external services."""
    pass

@pytest.mark.slow
def test_performance_intensive():
    """This is a slow test that takes more time to run."""
    pass
``` 