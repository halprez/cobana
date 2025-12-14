"""Pytest configuration and shared fixtures for COBANA tests."""

import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests.

    Yields:
        Path: Temporary directory path
    """
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_python_file(temp_dir):
    """Create a sample Python file for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Path to sample file
    """
    file_path = temp_dir / "sample.py"
    content = '''"""Sample module for testing."""

def simple_function(x):
    """A simple function."""
    return x + 1

def complex_function(a, b, c):
    """A more complex function."""
    if a > 0:
        if b > 0:
            if c > 0:
                return a + b + c
            else:
                return a + b
        else:
            return a
    else:
        return 0

class SampleClass:
    """A sample class."""

    def __init__(self):
        self.value = 0

    def method_one(self):
        return self.value

    def method_two(self):
        self.value += 1
'''
    file_path.write_text(content)
    return file_path


@pytest.fixture
def sample_codebase(temp_dir):
    """Create a sample codebase structure for testing.

    Args:
        temp_dir: Temporary directory fixture

    Returns:
        Path: Root path of sample codebase
    """
    # Create directory structure
    (temp_dir / "module_a").mkdir()
    (temp_dir / "module_b").mkdir()
    (temp_dir / "module_a" / "submodule").mkdir()

    # Create Python files
    files = {
        "module_a/__init__.py": "# Module A",
        "module_a/file1.py": """
def function_a():
    return "a"
""",
        "module_a/submodule/__init__.py": "# Submodule",
        "module_a/submodule/file2.py": """
def function_b():
    return "b"
""",
        "module_b/__init__.py": "# Module B",
        "module_b/file3.py": """
def function_c():
    if True:
        if True:
            if True:
                return "c"
    return "nope"
""",
    }

    for file_path, content in files.items():
        full_path = temp_dir / file_path
        full_path.write_text(content)

    return temp_dir


@pytest.fixture
def basic_config():
    """Provide basic configuration for tests.

    Returns:
        dict: Basic configuration
    """
    return {
        'service_name': 'test_service',
        'module_detection': {
            'method': 'auto',
            'depth': 1,
        },
        'exclude_patterns': [
            '__pycache__/*',
            '*.pyc',
            '.git/*',
        ],
        'thresholds': {
            'complexity': 10,
            'maintainability': 20,
            'file_size': 500,
            'function_size': 50,
            'parameters': 5,
            'nesting': 4,
        },
    }


@pytest.fixture
def db_coupling_config(basic_config):
    """Provide configuration with table ownership for DB coupling tests.

    Args:
        basic_config: Basic configuration fixture

    Returns:
        dict: Configuration with table ownership
    """
    config = basic_config.copy()
    config['table_ownership'] = {
        'test_service': ['own_table_1', 'own_table_2'],
        'other_service': ['other_table_1', 'other_table_2'],
        'shared': ['shared_table'],
    }
    return config


@pytest.fixture
def sample_analysis_results():
    """Provide sample analysis results for report testing.

    Returns:
        dict: Sample analysis results
    """
    return {
        'metadata': {
            'service_name': 'test_service',
            'total_files_analyzed': 10,
            'module_count': 2,
        },
        'summary': {
            'overall_health': 75.5,
            'best_module': 'module_a',
            'best_score': 80.0,
            'worst_module': 'module_b',
            'worst_score': 70.0,
            'debt_ratio': 10.5,
            'sqale_rating': 'B',
            'total_remediation_hours': 25.5,
            'total_remediation_days': 3.2,
            'total_operations': 15,
            'severity_score': 10,
            'violation_count_write': 2,
            'violation_count_read': 5,
            'avg_complexity': 5.5,
            'high_complexity_count': 3,
            'max_complexity': 15,
            'avg_mi': 65.0,
            'low_mi_count': 1,
            'total_sloc': 1500,
            'avg_file_size': 150,
            'comment_ratio': 10.0,
            'large_files_count': 2,
            'total_test_files': 5,
            'unit_percentage': 60.0,
            'integration_percentage': 40.0,
            'testability_score': 75.0,
            'total_smells': 10,
            'long_methods': 5,
            'long_parameter_lists': 3,
            'deep_nesting': 2,
            'total_classes': 8,
            'god_classes_count': 1,
            'low_cohesion_count': 2,
            'avg_lcom': 1.5,
            'avg_wmc': 15.0,
        },
        'complexity': {
            'avg_complexity': 5.5,
            'max_complexity': 15,
            'high_complexity_functions': [
                {
                    'function': 'complex_func',
                    'file': '/test/file.py',
                    'line': 10,
                    'complexity': 15,
                    'category': 'complex',
                }
            ],
        },
        'db_coupling': {
            'violations': [],
        },
        'module_health': {
            'by_module': {
                'module_a': {'score': 80.0},
                'module_b': {'score': 70.0},
            },
            'module_rankings': [
                {'module': 'module_a', 'score': 80.0, 'category': 'good'},
                {'module': 'module_b', 'score': 70.0, 'category': 'good'},
            ],
        },
    }
