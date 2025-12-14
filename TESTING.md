# COBANA Testing Guide

## Overview

COBANA uses pytest for testing with custom markers to categorize and run different types of tests.

## Test Markers

Tests are categorized with the following markers:

- **`unit`** - Unit tests that test individual components in isolation
- **`integration`** - Integration tests that test multiple components working together
- **`ui`** - UI/CLI tests that test the command-line interface
- **`regression`** - Regression tests to ensure fixed bugs stay fixed
- **`slow`** - Tests that take significant time to run

## Running Tests

### Install Test Dependencies

```bash
# Install with dev dependencies
uv pip install -e ".[dev]"
```

### Run All Tests

```bash
# Run all tests
uv run pytest tests/

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=cobana --cov-report=html
```

### Run Tests by Marker

```bash
# Run only unit tests
uv run pytest tests/ -m unit

# Run only integration tests
uv run pytest tests/ -m integration

# Run UI/CLI tests
uv run pytest tests/ -m ui

# Run regression tests
uv run pytest tests/ -m regression

# Run all except slow tests
uv run pytest tests/ -m "not slow"
```

### Run Specific Test Files or Classes

```bash
# Run a specific test file
uv run pytest tests/test_utils/test_file_utils.py

# Run a specific test class
uv run pytest tests/test_utils/test_file_utils.py::TestFileScanner

# Run a specific test function
uv run pytest tests/test_utils/test_file_utils.py::TestFileScanner::test_max_depth_limit
```

### Combine Markers

```bash
# Run unit and integration tests, but not slow ones
uv run pytest tests/ -m "unit or integration and not slow"

# Run only fast unit tests
uv run pytest tests/ -m "unit and not slow"
```

## Test Structure

```
tests/
├── conftest.py                    # Shared fixtures and configuration
├── test_analyzers/
│   └── test_complexity.py         # Unit tests for complexity analyzer
├── test_report/
│   ├── test_json_generator.py     # Unit tests for JSON generator
│   └── test_md_generator.py       # Unit tests for Markdown generator
├── test_utils/
│   ├── test_file_utils.py         # Unit tests for file utilities
│   └── test_module_detector.py    # Unit tests for module detection
├── test_integration.py            # Integration tests
└── test_cli.py                    # CLI/UI tests
```

## Test Coverage

View coverage report after running tests:

```bash
# Generate HTML coverage report
uv run pytest tests/ --cov=cobana --cov-report=html

# Open in browser
open htmlcov/index.html
```

Current coverage: ~40% overall, with high coverage in utilities and report generators.

## Writing Tests

### Test Naming

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Using Fixtures

```python
import pytest

@pytest.mark.unit
def test_example(temp_dir, sample_python_file):
    """Test using shared fixtures."""
    # temp_dir provides a temporary directory
    # sample_python_file provides a sample Python file
    assert sample_python_file.exists()
```

### Marking Tests

```python
import pytest

@pytest.mark.unit
def test_unit_example():
    """A unit test."""
    pass

@pytest.mark.integration
def test_integration_example():
    """An integration test."""
    pass

@pytest.mark.slow
@pytest.mark.integration
def test_slow_integration():
    """A slow integration test."""
    pass

@pytest.mark.regression
def test_bug_fix():
    """Regression test for fixed bug."""
    pass
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Run tests
  run: |
    uv pip install -e ".[dev]"
    uv run pytest tests/ -m "not slow" --cov=cobana
```

## Troubleshooting

### Tests Failing Locally

1. Ensure dev dependencies are installed:
   ```bash
   uv pip install -e ".[dev]"
   ```

2. Check Python version (requires 3.11+):
   ```bash
   python --version
   ```

3. Run with verbose output:
   ```bash
   uv run pytest tests/ -v --tb=short
   ```

### Import Errors

Make sure COBANA is installed in editable mode:
```bash
uv pip install -e .
```

## Available Fixtures

See `tests/conftest.py` for all available fixtures:

- `temp_dir` - Temporary directory for test files
- `sample_python_file` - Pre-created sample Python file
- `sample_codebase` - Complete sample codebase structure
- `basic_config` - Basic configuration dictionary
- `db_coupling_config` - Configuration with table ownership
- `sample_analysis_results` - Mock analysis results for report testing
