"""COBANA - Codebase Architecture Analysis Tool

A comprehensive Python codebase analysis tool that measures architectural health,
code quality, and technical debt with educational explanations for both technical
and non-technical stakeholders.
"""

__version__ = "1.0.0"
__author__ = "COBANA Team"

from cobana.analyzer import CodebaseAnalyzer

__all__ = ["CodebaseAnalyzer", "__version__"]
