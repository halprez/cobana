"""Code Smells Analyzer

Detects common code smells like long methods, deep nesting, and long parameter lists.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict
import logging

from cobana.utils.file_utils import read_file_safely
from cobana.utils.ast_utils import (
    ASTParser,
    count_lines,
    get_function_params,
    get_nesting_depth,
)

logger = logging.getLogger(__name__)


class CodeSmellsAnalyzer:
    """Detects code smells in Python codebases."""

    def __init__(self, config: dict[str, Any]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.function_size_threshold = config.get("thresholds", {}).get(
            "function_size", 50
        )
        self.parameters_threshold = config.get("thresholds", {}).get(
            "parameters", 5
        )
        self.nesting_threshold = config.get("thresholds", {}).get("nesting", 4)

        # Results storage
        self.results: dict[str, Any] = {
            "total_smells": 0,
            "by_module": defaultdict(
                lambda: {
                    "long_methods": 0,
                    "long_parameter_lists": 0,
                    "deep_nesting": 0,
                    "total_smells": 0,
                }
            ),
            "long_methods": [],
            "long_parameter_lists": [],
            "deep_nesting": [],
            "duplicate_code": [],  # Placeholder for future implementation
        }

    def analyze_file(self, file_path: Path, module_name: str) -> dict[str, Any]:
        """Analyze code smells in a single file.

        Args:
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            Dictionary with file analysis results
        """
        content = read_file_safely(file_path)
        if content is None:
            return {}
        return self.analyze_file_content(content, file_path, module_name)

    def analyze_file_content(
        self, content: str, file_path: Path, module_name: str
    ) -> dict[str, Any]:
        """Analyze code smells from file content (optimization: uses pre-read content).

        Args:
            content: File content as string
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            Dictionary with file analysis results
        """
        parser = ASTParser(file_path, content)
        if not parser.parse():
            return {}

        functions = parser.get_functions()

        if not functions:
            return {}

        file_smells = {
            "file": str(file_path),
            "module": module_name,
            "smells": [],
        }

        # Analyze each function
        for func_name, func_node in functions:
            # Check for long methods
            func_lines = count_lines(func_node)
            if func_lines > self.function_size_threshold:
                smell = {
                    "type": "long_method",
                    "function": func_name,
                    "sloc": func_lines,
                    "line": func_node.lineno,
                }
                file_smells["smells"].append(smell)
                self._track_smell("long_methods", smell, module_name)

            # Check for long parameter lists
            params = get_function_params(func_node)
            param_count = len(params)
            if param_count > self.parameters_threshold:
                smell = {
                    "type": "long_parameter_list",
                    "function": func_name,
                    "parameters": param_count,
                    "param_names": params,
                    "line": func_node.lineno,
                }
                file_smells["smells"].append(smell)
                self._track_smell("long_parameter_lists", smell, module_name)

            # Check for deep nesting
            max_depth = get_nesting_depth(func_node)
            if max_depth > self.nesting_threshold:
                smell = {
                    "type": "deep_nesting",
                    "function": func_name,
                    "max_depth": max_depth,
                    "line": func_node.lineno,
                }
                file_smells["smells"].append(smell)
                self._track_smell("deep_nesting", smell, module_name)

        return file_smells

    def _track_smell(
        self, smell_type: str, smell: dict[str, Any], module_name: str
    ) -> None:
        """Track a detected code smell.

        Args:
            smell_type: Type of smell
            smell: Smell details
            module_name: Module name
        """
        # Add to overall results
        self.results[smell_type].append(
            {
                **smell,
                "module": module_name,
            }
        )

        # Update counts
        self.results["total_smells"] += 1
        self.results["by_module"][module_name][smell_type] += 1
        self.results["by_module"][module_name]["total_smells"] += 1

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return analysis results.

        Returns:
            Complete analysis results
        """
        # Sort smells by severity (largest/deepest first)
        self.results["long_methods"].sort(
            key=lambda x: x.get("sloc", 0), reverse=True
        )

        self.results["long_parameter_lists"].sort(
            key=lambda x: x.get("parameters", 0), reverse=True
        )

        self.results["deep_nesting"].sort(
            key=lambda x: x.get("max_depth", 0), reverse=True
        )

        # Convert by_module from defaultdict to regular dict
        self.results["by_module"] = dict(self.results["by_module"])

        return self.results

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        return {
            "total_smells": self.results["total_smells"],
            "long_methods": len(self.results["long_methods"]),
            "long_parameter_lists": len(self.results["long_parameter_lists"]),
            "deep_nesting": len(self.results["deep_nesting"]),
            "duplicate_code": len(self.results["duplicate_code"]),
        }
