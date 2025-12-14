"""Code Size Analyzer

Analyzes code size metrics using the Radon library.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict
import logging

from radon.raw import analyze
from cobana.utils.file_utils import read_file_safely  # type: ignore
from cobana.utils.ast_utils import ASTParser, count_lines

logger = logging.getLogger(__name__)


class CodeSizeAnalyzer:
    """Analyzes code size metrics in Python codebases."""

    def __init__(self, config: dict[str, Any]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.file_size_threshold = config.get("thresholds", {}).get(
            "file_size", 500
        )
        self.function_size_threshold = config.get("thresholds", {}).get(
            "function_size", 50
        )
        self.comment_ratio_threshold = config.get("thresholds", {}).get(
            "comment_ratio", 5
        )

        # Results storage
        self.results: dict[str, Any] = {
            "total_sloc": 0,
            "total_comments": 0,
            "total_blank": 0,
            "total_loc": 0,
            "comment_ratio": 0.0,
            "file_count": 0,
            "file_size_distribution": {
                "small_0_100": 0,
                "medium_101_500": 0,
                "large_501_plus": 0,
            },
            "by_module": defaultdict(
                lambda: {
                    "total_sloc": 0,
                    "file_count": 0,
                    "avg_file_size": 0.0,
                    "comment_ratio": 0.0,
                    "total_comments": 0,
                    "total_loc": 0,
                }
            ),
            "large_files": [],
            "large_functions": [],
            "low_documentation": [],
            "per_file": [],
        }

    def analyze_file(self, file_path: Path, module_name: str) -> dict[str, Any]:
        """Analyze code size of a single file.

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
        """Analyze code size from file content (optimization: uses pre-read content).

        Args:
            content: File content as string
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            Dictionary with file analysis results
        """
        try:
            # Use Radon to analyze raw metrics
            raw_metrics = analyze(content)
        except Exception as e:
            logger.warning(f"Failed to analyze code size in {file_path}: {e}")
            return {}

        # Calculate comment ratio
        total_lines = raw_metrics.loc
        comment_ratio = 0.0
        if total_lines > 0:
            comment_ratio = (raw_metrics.comments / total_lines) * 100

        file_results = {
            "file": str(file_path),
            "module": module_name,
            "sloc": raw_metrics.sloc,
            "comments": raw_metrics.comments,
            "blank": raw_metrics.blank,
            "loc": raw_metrics.loc,
            "comment_ratio": comment_ratio,
        }

        # Analyze functions and classes for size and count
        parser = ASTParser(file_path, content)
        functions = parser.get_functions()
        classes = parser.get_classes()

        file_results["function_count"] = len(functions)
        file_results["class_count"] = len(classes)

        self._analyze_function_sizes(file_path, module_name, functions)

        # Update overall results
        self._update_results(file_results, module_name)

        return file_results

    def _analyze_function_sizes(
        self,
        file_path: Path,
        module_name: str,
        functions: list[tuple[str, Any]],
    ) -> None:
        """Analyze function sizes in file.

        Args:
            file_path: Path to file
            module_name: Module name
            functions: List of (name, node) tuples from parser
        """

        for func_name, func_node in functions:
            func_lines = count_lines(func_node)

            if func_lines > self.function_size_threshold:
                self.results["large_functions"].append(
                    {
                        "function": func_name,
                        "module": module_name,
                        "file": str(file_path),
                        "sloc": func_lines,
                        "line": func_node.lineno,
                    }
                )

    def _update_results(
        self, file_results: dict[str, Any], module_name: str
    ) -> None:
        """Update overall results with file results.

        Args:
            file_results: Results from analyzing a single file
            module_name: Module the file belongs to
        """
        sloc = file_results["sloc"]
        comments = file_results["comments"]
        blank = file_results["blank"]
        loc = file_results["loc"]
        comment_ratio = file_results["comment_ratio"]

        # Update overall stats
        self.results["total_sloc"] += sloc
        self.results["total_comments"] += comments
        self.results["total_blank"] += blank
        self.results["total_loc"] += loc
        self.results["file_count"] += 1

        # Update file size distribution
        match sloc:
            case s if s <= 100:
                self.results["file_size_distribution"]["small_0_100"] += 1
            case s if s <= 500:
                self.results["file_size_distribution"]["medium_101_500"] += 1
            case _:
                self.results["file_size_distribution"]["large_501_plus"] += 1

        # Track large files
        if sloc > self.file_size_threshold:
            self.results["large_files"].append(
                {
                    "file": file_results["file"],
                    "module": module_name,
                    "sloc": sloc,
                    "comments": comments,
                    "comment_ratio": comment_ratio,
                }
            )

        # Track low documentation files
        if comment_ratio < self.comment_ratio_threshold and sloc > 50:
            self.results["low_documentation"].append(
                {
                    "file": file_results["file"],
                    "module": module_name,
                    "comment_ratio": comment_ratio,
                    "sloc": sloc,
                }
            )

        # Update module stats
        module_stats = self.results["by_module"][module_name]
        module_stats["total_sloc"] += sloc
        module_stats["file_count"] += 1
        module_stats["total_comments"] += comments
        module_stats["total_loc"] += loc

        # Add to per-file results
        self.results["per_file"].append(
            {
                "file": file_results["file"],
                "module": module_name,
                "sloc": sloc,
                "comment_ratio": comment_ratio,
                "function_count": file_results.get("function_count", 0),
                "class_count": file_results.get("class_count", 0),
            }
        )

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return analysis results.

        Returns:
            Complete analysis results
        """
        # Calculate overall comment ratio
        if self.results["total_loc"] > 0:
            self.results["comment_ratio"] = (
                self.results["total_comments"] / self.results["total_loc"]
            ) * 100

        # Calculate module averages and comment ratios
        for module_name, module_stats in self.results["by_module"].items():
            if module_stats["file_count"] > 0:
                module_stats["avg_file_size"] = (
                    module_stats["total_sloc"] / module_stats["file_count"]
                )

            if module_stats["total_loc"] > 0:
                module_stats["comment_ratio"] = (
                    module_stats["total_comments"] / module_stats["total_loc"]
                ) * 100

        # Sort large files by SLOC
        self.results["large_files"].sort(key=lambda x: x["sloc"], reverse=True)

        # Sort large functions by SLOC
        self.results["large_functions"].sort(
            key=lambda x: x["sloc"], reverse=True
        )

        # Sort low documentation by comment ratio
        self.results["low_documentation"].sort(key=lambda x: x["comment_ratio"])

        # Convert by_module from defaultdict to regular dict
        self.results["by_module"] = dict(self.results["by_module"])

        # Store threshold in results for template use
        self.results["file_size_threshold"] = self.file_size_threshold

        return self.results

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        avg_file_size = 0
        if self.results["file_count"] > 0:
            avg_file_size = (
                self.results["total_sloc"] / self.results["file_count"]
            )

        return {
            "total_sloc": self.results["total_sloc"],
            "file_count": self.results["file_count"],
            "avg_file_size": round(avg_file_size, 1),
            "comment_ratio": round(self.results["comment_ratio"], 2),
            "large_files_count": len(self.results["large_files"]),
            "large_functions_count": len(self.results["large_functions"]),
        }
