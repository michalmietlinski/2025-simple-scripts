# DALL-E Image Generator Tests

This directory contains test files for the DALL-E Image Generator application.

## Test Files

- **test_image_display.py**: Tests for the image display functionality, including full resolution viewing and output directory access
- **test_database.py**: Tests for the database implementation, including CRUD operations for prompts, generations, and usage statistics
- **test_image_generation.py**: Tests for the image generation functionality using the OpenAI API
- **test_openai_api.py**: Tests for the OpenAI API connection and authentication

## Running Tests

### Running All Tests

To run all tests, use the `run_tests.py` script:

```bash
python run_tests.py
```

### Running Individual Tests

To run a specific test file:

```bash
python test_image_display.py
```

## Test Structure

Each test file follows a similar structure:

1. Import necessary modules
2. Add the parent directory to the Python path to ensure imports work correctly
3. Define test functions or classes
4. Include a main block to allow running the test file directly

## Adding New Tests

When adding new tests:

1. Create a new file with the naming pattern `test_*.py`
2. Add the parent directory to the Python path using:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```
3. Import the modules you want to test
4. Write your test functions or classes
5. Add a main block to allow running the test file directly 
