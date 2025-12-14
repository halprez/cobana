"""Maintainability Analyzer

Analyzes maintainability index of files using the Radon library.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict
import logging

from radon.metrics import mi_visit, mi_rank
from cobana.utils.file_utils import read_file_safely

logger = logging.getLogger(__name__)


class MaintainabilityAnalyzer:
    """Analyzes maintainability index in Python codebases."""

    def __init__(self, config: dict[str, Any]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.threshold = config.get("thresholds", {}).get("maintainability", 20)

        # Results storage
        self.results: dict[str, Any] = {
            "avg_mi": 0.0,
            "total_files": 0,
            "mi_sum": 0.0,
            "distribution": {
                "high_65_100": 0,
                "moderate_20_64": 0,
                "low_0_19": 0,
            },
            "by_module": defaultdict(
                lambda: {
                    "avg_mi": 0.0,
                    "file_count": 0,
                    "mi_sum": 0.0,
                    "low_mi_count": 0,
                }
            ),
            "low_maintainability_files": [],
            "per_file": [],
        }

    def analyze_file(self, file_path: Path, module_name: str) -> dict[str, Any]:
        """Analyze maintainability of a single file.

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
        """Analyze maintainability from file content (optimization: uses pre-read content).

        Args:
            content: File content as string
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            Dictionary with file analysis results
        """
        try:
            # Use Radon to calculate maintainability index
            mi_score = mi_visit(content, multi=True)
        except Exception as e:
            logger.warning(
                f"Failed to analyze maintainability in {file_path}: {e}"
            )
            return {}

        # mi_score is the average MI for the file
        if mi_score is None or mi_score < 0:
            return {}

        # Get rank (A, B, C)
        rank = mi_rank(mi_score)

        # Categorize
        category = self._categorize_mi(mi_score)

        file_results = {
            "file": str(file_path),
            "module": module_name,
            "mi_score": mi_score,
            "rank": rank,
            "category": category,
        }

        # Update overall results
        self._update_results(file_results, module_name)

        return file_results

    def _categorize_mi(self, mi_score: float) -> str:
        """Categorize maintainability index.

        Args:
            mi_score: Maintainability index score

        Returns:
            Category string
        """
        match mi_score:
            case score if score >= 65:
                return "high"
            case score if score >= 20:
                return "moderate"
            case _:
                return "low"

    def _update_results(
        self, file_results: dict[str, Any], module_name: str
    ) -> None:
        """Update overall results with file results.

        Args:
            file_results: Results from analyzing a single file
            module_name: Module the file belongs to
        """
        mi_score = file_results["mi_score"]

        # Update overall stats
        self.results["total_files"] += 1
        self.results["mi_sum"] += mi_score

        # Update distribution
        category = file_results["category"]
        match category:
            case "high":
                self.results["distribution"]["high_65_100"] += 1
            case "moderate":
                self.results["distribution"]["moderate_20_64"] += 1
            case "low":
                self.results["distribution"]["low_0_19"] += 1

        # Track low maintainability files
        if mi_score < self.threshold:
            self.results["low_maintainability_files"].append(
                {
                    "file": file_results["file"],
                    "module": module_name,
                    "mi_score": mi_score,
                    "rank": file_results["rank"],
                    "category": category,
                }
            )

        # Update module stats
        module_stats = self.results["by_module"][module_name]
        module_stats["file_count"] += 1
        module_stats["mi_sum"] += mi_score

        if mi_score < self.threshold:
            module_stats["low_mi_count"] += 1

        # Add to per-file results
        self.results["per_file"].append(
            {
                "file": file_results["file"],
                "module": module_name,
                "mi_score": mi_score,
                "rank": file_results["rank"],
            }
        )

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return analysis results.

        Returns:
            Complete analysis results
        """
        # Calculate average MI
        if self.results["total_files"] > 0:
            self.results["avg_mi"] = (
                self.results["mi_sum"] / self.results["total_files"]
            )

        # Remove mi_sum (internal use only)
        del self.results["mi_sum"]

        # Calculate module averages
        for module_name, module_stats in self.results["by_module"].items():
            if module_stats["file_count"] > 0:
                module_stats["avg_mi"] = (
                    module_stats["mi_sum"] / module_stats["file_count"]
                )
            # Remove mi_sum (internal use only)
            del module_stats["mi_sum"]

        # Sort low maintainability files by MI score
        self.results["low_maintainability_files"].sort(
            key=lambda x: x["mi_score"]
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
            "avg_mi": round(self.results["avg_mi"], 2),
            "total_files": self.results["total_files"],
            "high_maintainability": self.results["distribution"]["high_65_100"],
            "low_maintainability": self.results["distribution"]["low_0_19"],
            "low_mi_count": len(self.results["low_maintainability_files"]),
        }
