"""Analyzer base classes and protocols.

This module defines the common interface and utilities for all code analyzers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, Any, runtime_checkable


@runtime_checkable
class Analyzer(Protocol):
    """Protocol defining the interface for all analyzers.

    This emerged naturally after implementing multiple concrete analyzers.
    Each analyzer follows this pattern:
    1. Analyze individual files
    2. Accumulate results
    3. Finalize aggregated metrics
    4. Provide summary statistics
    """

    def analyze_file(self, file_path: Path, module_name: str) -> dict[str, Any]:
        """Analyze a single file.

        Args:
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            File-level analysis results
        """
        ...

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return complete analysis results.

        Called after all files have been analyzed.
        Performs aggregation, calculations, and cleanup.

        Returns:
            Complete analysis results
        """
        ...

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            High-level summary suitable for dashboards
        """
        ...


@dataclass
class FileLocation:
    """Represents a location in a file."""
    file: str
    module: str
    line: int

    def __str__(self) -> str:
        return f"{self.file}:{self.line}"


@dataclass
class FunctionInfo:
    """Information about a function."""
    name: str
    module: str
    file: str
    line: int
    class_name: str | None = None

    def full_name(self) -> str:
        """Get fully qualified function name."""
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name


@dataclass
class ModuleStats:
    """Statistics for a single module."""
    name: str
    file_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'file_count': self.file_count,
        }


# Utility functions for common aggregation patterns

def calculate_average(total: float, count: int) -> float:
    """Calculate average safely.

    Args:
        total: Sum total
        count: Count of items

    Returns:
        Average, or 0 if count is 0
    """
    return total / count if count > 0 else 0.0


def categorize_by_threshold(
    value: int | float,
    thresholds: list[tuple[int | float, str]]
) -> str:
    """Categorize a value by thresholds.

    Args:
        value: Value to categorize
        thresholds: List of (threshold, category) tuples, in ascending order

    Returns:
        Category name

    Example:
        >>> categorize_by_threshold(7, [(5, 'low'), (10, 'medium'), (20, 'high')])
        'medium'
    """
    for threshold, category in thresholds:
        if value <= threshold:
            return category
    return thresholds[-1][1] if thresholds else 'unknown'


__all__ = [
    'Analyzer',
    'FileLocation',
    'FunctionInfo',
    'ModuleStats',
    'calculate_average',
    'categorize_by_threshold',
]
