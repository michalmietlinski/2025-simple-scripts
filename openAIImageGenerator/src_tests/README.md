# OpenAI Image Generator Tests

This directory contains test files for the migrated OpenAI Image Generator application.

## Test Structure

The tests are organized to match the structure of the `src` directory:

- **core/**: Tests for core components (OpenAI client, database, file manager)
- **ui/**: Tests for UI components (main window, tabs, dialogs)
- **utils/**: Tests for utility modules (error handler, settings manager, template utils, usage tracker)

## Running Tests

### Prerequisites

Make sure you have the required dependencies installed:

```bash
pip install pytest pytest-mock pytest-cov
```

### Running All Tests

To run all tests with coverage report:

```bash
pytest src_tests/ --cov=src
```

### Running Specific Test Categories

To run tests for a specific module:

```bash
# Run core tests
pytest src_tests/core/

# Run UI tests
pytest src_tests/ui/

# Run utils tests
pytest src_tests/utils/
```

## Test Guidelines

When writing tests for the migrated codebase, follow these guidelines:

1. **Unit Tests**: Test individual components in isolation, using mocks for dependencies
2. **Integration Tests**: Test interactions between components
3. **UI Tests**: Test UI components with mock events

### Example Test Structure

```python
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path to allow imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from src.core.module_to_test import ClassToTest

class TestClassName:
    def setup_method(self):
        # Setup code that runs before each test
        self.mock_dependency = MagicMock()
        self.test_instance = ClassToTest(self.mock_dependency)
    
    def test_specific_functionality(self):
        # Arrange
        expected_result = "expected value"
        self.mock_dependency.some_method.return_value = "mock value"
        
        # Act
        result = self.test_instance.method_to_test("test input")
        
        # Assert
        assert result == expected_result
        self.mock_dependency.some_method.assert_called_once_with("test input")
```

## Test Coverage Goals

- Aim for at least 80% code coverage for core and utils modules
- Focus on testing critical functionality and error handling
- For UI components, test key interactions and state changes

## Continuous Integration

Tests will be run automatically on each commit to ensure code quality and prevent regressions. 
