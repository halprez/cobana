"""Class Metrics Analyzer

Analyzes class-level metrics including LCOM and WMC.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict
import ast
import logging

from radon.complexity import cc_visit
from cobana.utils.file_utils import read_file_safely
from cobana.utils.ast_utils import ASTParser

logger = logging.getLogger(__name__)


class ClassMetricsAnalyzer:
    """Analyzes class-level metrics in Python codebases."""

    def __init__(self, config: dict[str, Any]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.class_methods_threshold = config.get("thresholds", {}).get(
            "class_methods", 20
        )
        self.class_wmc_threshold = config.get("thresholds", {}).get(
            "class_wmc", 50
        )
        self.class_lcom_threshold = config.get("thresholds", {}).get(
            "class_lcom", 2
        )

        # Results storage
        self.results: dict[str, Any] = {
            "total_classes": 0,
            "avg_lcom": 0.0,
            "avg_wmc": 0.0,
            "avg_methods_per_class": 0.0,
            "lcom_sum": 0.0,
            "wmc_sum": 0.0,
            "methods_sum": 0,
            "by_module": defaultdict(
                lambda: {
                    "total_classes": 0,
                    "avg_lcom": 0.0,
                    "avg_wmc": 0.0,
                    "god_classes_count": 0,
                    "lcom_sum": 0.0,
                    "wmc_sum": 0.0,
                }
            ),
            "per_class": [],
            "god_classes": [],
            "low_cohesion_classes": [],
        }

    def analyze_file(self, file_path: Path, module_name: str) -> dict[str, Any]:
        """Analyze class metrics in a single file.

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
        """Analyze class metrics from file content (optimization: uses pre-read content).

        Args:
            content: File content as string
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            Dictionary with file analysis results
        """
        parser = ASTParser(file_path, content)
        classes = parser.get_classes()

        if not classes:
            return {}

        file_results = {
            "file": str(file_path),
            "module": module_name,
            "classes": [],
        }

        # Analyze each class
        for class_name, class_node in classes:
            class_info = self._analyze_class(
                class_name, class_node, content, file_path, module_name
            )
            if class_info:
                file_results["classes"].append(class_info)
                self._update_results(class_info, module_name)

        return file_results

    def _analyze_class(
        self,
        class_name: str,
        class_node: ast.ClassDef,
        content: str,
        file_path: Path,
        module_name: str,
    ) -> dict[str, Any] | None:
        """Analyze a single class.

        Args:
            class_name: Name of the class
            class_node: AST ClassDef node
            content: Full file content
            file_path: Path to file
            module_name: Module name

        Returns:
            Class analysis results or None
        """
        # Get methods
        methods = [
            node
            for node in class_node.body
            if isinstance(node, ast.FunctionDef)
        ]
        method_count = len(methods)

        if method_count == 0:
            return None

        # Get instance variables (attributes)
        attributes = self._get_class_attributes(class_node)

        # Calculate LCOM (simplified version)
        lcom = self._calculate_lcom(methods, attributes)

        # Calculate WMC (Weighted Methods per Class)
        wmc = self._calculate_wmc(class_name, content)

        # Determine cohesion level
        cohesion_level = (
            "high" if lcom <= 1 else "moderate" if lcom == 2 else "low"
        )

        class_info = {
            "class": class_name,
            "module": module_name,
            "file": str(file_path),
            "line": class_node.lineno,
            "methods": method_count,
            "attributes": len(attributes),
            "lcom": lcom,
            "wmc": wmc,
            "cohesion_level": cohesion_level,
        }

        # Check if god class
        is_god_class = (
            method_count > self.class_methods_threshold
            or wmc > self.class_wmc_threshold
            or lcom > self.class_lcom_threshold
        )

        if is_god_class:
            reasons = []
            if method_count > self.class_methods_threshold:
                reasons.append(f"{method_count} methods")
            if wmc > self.class_wmc_threshold:
                reasons.append(f"WMC {wmc}")
            if lcom > self.class_lcom_threshold:
                reasons.append(f"LCOM {lcom}")

            self.results["god_classes"].append(
                {
                    "class": class_name,
                    "module": module_name,
                    "file": str(file_path),
                    "line": class_node.lineno,
                    "reasons": reasons,
                    "severity": "high",
                    "methods": method_count,
                    "wmc": wmc,
                    "lcom": lcom,
                }
            )

        # Check low cohesion
        if lcom > self.class_lcom_threshold:
            self.results["low_cohesion_classes"].append(
                {
                    "class": class_name,
                    "module": module_name,
                    "file": str(file_path),
                    "lcom": lcom,
                    "methods": method_count,
                }
            )

        return class_info

    def _get_class_attributes(self, class_node: ast.ClassDef) -> set[str]:
        """Get instance attributes from a class.

        Args:
            class_node: AST ClassDef node

        Returns:
            Set of attribute names
        """
        attributes = set()

        # Look for self.attr assignments in __init__ and other methods
        for node in ast.walk(class_node):
            if isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name) and node.value.id == "self":
                    attributes.add(node.attr)

        return attributes

    def _calculate_lcom(
        self, methods: list[ast.FunctionDef], attributes: set[str]
    ) -> int:
        """Calculate LCOM (Lack of Cohesion of Methods).

        Uses simplified approach: count methods that don't share any attributes.

        Args:
            methods: List of method nodes
            attributes: Set of class attributes

        Returns:
            LCOM value (higher = less cohesive)
        """
        if not methods or not attributes:
            return 1

        # Track which attributes each method uses
        method_attributes: list[set[str]] = []

        for method in methods:
            method_attrs = set()
            for node in ast.walk(method):
                if isinstance(node, ast.Attribute):
                    if (
                        isinstance(node.value, ast.Name)
                        and node.value.id == "self"
                    ):
                        if node.attr in attributes:
                            method_attrs.add(node.attr)
            method_attributes.append(method_attrs)

        # Count connected components (methods sharing attributes)
        # Simplified: if most methods share attributes, LCOM = 1
        # If methods are disconnected, LCOM increases

        if not any(method_attributes):
            return 1

        # Count methods that share at least one attribute with others
        isolated_count = sum(1 for attrs in method_attributes if not attrs)

        # Simple LCOM: number of isolated method groups
        if isolated_count == len(methods):
            return len(methods)
        elif isolated_count > len(methods) / 2:
            return 3  # Low cohesion
        elif isolated_count > 0:
            return 2  # Moderate cohesion
        else:
            return 1  # High cohesion

    def _calculate_wmc(self, class_name: str, content: str) -> int:
        """Calculate WMC (Weighted Methods per Class).

        Sum of cyclomatic complexity of all methods.

        Args:
            class_name: Name of the class
            content: File content

        Returns:
            WMC value
        """
        try:
            complexity_blocks = cc_visit(content)
            wmc = sum(
                block.complexity
                for block in complexity_blocks
                if getattr(block, "classname", None) == class_name
            )
            return wmc
        except Exception as e:
            logger.warning(f"Failed to calculate WMC for {class_name}: {e}")
            return 0

    def _update_results(
        self, class_info: dict[str, Any], module_name: str
    ) -> None:
        """Update overall results with class results.

        Args:
            class_info: Class analysis results
            module_name: Module name
        """
        # Update overall stats
        self.results["total_classes"] += 1
        self.results["lcom_sum"] += class_info["lcom"]
        self.results["wmc_sum"] += class_info["wmc"]
        self.results["methods_sum"] += class_info["methods"]

        # Update module stats
        module_stats = self.results["by_module"][module_name]
        module_stats["total_classes"] += 1
        module_stats["lcom_sum"] += class_info["lcom"]
        module_stats["wmc_sum"] += class_info["wmc"]

        if any(
            gc["class"] == class_info["class"]
            and gc["file"] == class_info["file"]
            for gc in self.results["god_classes"]
        ):
            module_stats["god_classes_count"] += 1

        # Add to per-class results
        self.results["per_class"].append(class_info)

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return analysis results.

        Returns:
            Complete analysis results
        """
        # Calculate averages
        if self.results["total_classes"] > 0:
            self.results["avg_lcom"] = (
                self.results["lcom_sum"] / self.results["total_classes"]
            )
            self.results["avg_wmc"] = (
                self.results["wmc_sum"] / self.results["total_classes"]
            )
            self.results["avg_methods_per_class"] = (
                self.results["methods_sum"] / self.results["total_classes"]
            )

        # Remove internal sums
        del self.results["lcom_sum"]
        del self.results["wmc_sum"]
        del self.results["methods_sum"]

        # Calculate module averages
        for module_name, module_stats in self.results["by_module"].items():
            if module_stats["total_classes"] > 0:
                module_stats["avg_lcom"] = (
                    module_stats["lcom_sum"] / module_stats["total_classes"]
                )
                module_stats["avg_wmc"] = (
                    module_stats["wmc_sum"] / module_stats["total_classes"]
                )
            # Remove internal sums
            del module_stats["lcom_sum"]
            del module_stats["wmc_sum"]

        # Sort god classes by severity (highest WMC first)
        self.results["god_classes"].sort(key=lambda x: x["wmc"], reverse=True)

        # Sort low cohesion classes
        self.results["low_cohesion_classes"].sort(
            key=lambda x: x["lcom"], reverse=True
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
            "total_classes": self.results["total_classes"],
            "avg_lcom": round(self.results["avg_lcom"], 2),
            "avg_wmc": round(self.results["avg_wmc"], 1),
            "god_classes_count": len(self.results["god_classes"]),
            "low_cohesion_count": len(self.results["low_cohesion_classes"]),
        }
