"""Configuration utilities for COBANA.

Handles loading, merging, and validating configuration files.
"""

from pathlib import Path
from typing import Any
import yaml


# Default configuration
DEFAULT_CONFIG: dict[str, Any] = {
    "service_name": "unknown",
    "module_detection": {
        "method": "auto",  # "auto" or "manual"
        "depth": 1,  # Folder depth to treat as modules
        "manual_modules": [],
    },
    "table_ownership": {},
    "thresholds": {
        "complexity": 10,
        "maintainability": 20,
        "file_size": 500,
        "function_size": 50,
        "parameters": 5,
        "nesting": 4,
        "class_methods": 20,
        "class_wmc": 50,
        "class_lcom": 2,
        "comment_ratio": 5,
        "module_fan_out": 10,
    },
    "exclude_patterns": [
        "*/test_*",
        "*_test.py",
        "*/__pycache__/*",
        "*/migrations/*",
        "*.pyc",
        ".git/*",
        "venv/*",
        "env/*",
        ".venv/*",
        "node_modules/*",
    ],
    "options": {
        "analyze_tests": True,
        "detect_duplicates": True,
        "detect_dead_code": False,
        "generate_charts": True,
        "module_dependency_graph": True,
    },
    "remediation_costs": {
        "very_high_complexity": 1.0,
        "high_complexity": 0.5,
        "low_maintainability": 2.0,
        "god_class": 4.0,
        "god_method": 2.0,
        "long_method": 0.5,
        "long_parameter_list": 0.25,
        "deep_nesting": 0.5,
        "duplicate_code": 1.0,
        "ownership_violation_write": 2.0,
        "ownership_violation_read": 0.5,
        "low_cohesion": 3.0,
        "high_fan_out": 1.0,
    },
}


def load_config(config_path: Path | str | None = None) -> dict[str, Any]:
    """Load configuration from YAML file and merge with defaults.

    Args:
        config_path: Path to YAML configuration file. If None, uses defaults.

    Returns:
        Complete configuration dictionary with defaults merged.

    Raises:
        FileNotFoundError: If config_path is specified but doesn't exist.
        yaml.YAMLError: If config file has invalid YAML syntax.
    """
    config = DEFAULT_CONFIG.copy()

    if config_path is None:
        return config

    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML in config file: {e}") from e

    # Deep merge user config into default config
    config = _deep_merge(config, user_config)

    # Validate configuration
    _validate_config(config)

    return config


def _deep_merge(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries.

    Args:
        base: Base dictionary
        update: Dictionary with updates to merge

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in update.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value

    return result


def _validate_config(config: dict[str, Any]) -> None:
    """Validate configuration structure and values.

    Args:
        config: Configuration dictionary to validate

    Raises:
        ValueError: If configuration is invalid
    """
    # Validate module detection method
    method = config.get("module_detection", {}).get("method")
    if method not in ["auto", "manual"]:
        raise ValueError(f"Invalid module_detection.method: {method}. Must be 'auto' or 'manual'")

    # Validate depth is positive integer
    depth = config.get("module_detection", {}).get("depth")
    if not isinstance(depth, int) or depth < 1:
        raise ValueError(f"Invalid module_detection.depth: {depth}. Must be positive integer")

    # Validate thresholds are positive numbers
    thresholds = config.get("thresholds", {})
    for key, value in thresholds.items():
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"Invalid threshold {key}: {value}. Must be non-negative number")

    # Validate remediation costs are positive numbers
    costs = config.get("remediation_costs", {})
    for key, value in costs.items():
        if not isinstance(value, (int, float)) or value < 0:
            raise ValueError(f"Invalid remediation cost {key}: {value}. Must be non-negative number")


def save_default_config(output_path: Path | str) -> None:
    """Save the default configuration to a YAML file.

    Useful for generating config.yaml.example files.

    Args:
        output_path: Path where to save the default config
    """
    path = Path(output_path)

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, sort_keys=False)
