"""Test Analyzer

Analyzes test files and calculates testability scores.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict
import re
import logging

from cobana.utils.file_utils import read_file_safely
from cobana.utils.ast_utils import ASTParser

logger = logging.getLogger(__name__)


class TestAnalyzer:
    """Analyzes test coverage and testability in Python codebases."""

    def __init__(self, config: dict[str, Any]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config

        # Results storage
        self.results: dict[str, Any] = {
            "total_test_files": 0,
            "unit_test_files": 0,
            "integration_test_files": 0,
            "total_test_functions": 0,
            "unit_test_functions": 0,
            "integration_test_functions": 0,
            "test_ratio": {
                "unit_percentage": 0.0,
                "integration_percentage": 0.0,
            },
            "by_module": defaultdict(
                lambda: {
                    "test_files": 0,
                    "unit_tests": 0,
                    "integration_tests": 0,
                    "testability_score": 0.0,
                    "mixed_functions": 0,
                }
            ),
            "testability": {
                "total_functions": 0,
                "functions_with_db_access": 0,
                "functions_with_business_logic": 0,
                "functions_mixing_both": 0,
                "testability_score": 0.0,
                "untestable_functions": [],
            },
            "test_details": [],
        }

        # Patterns for detection
        self.db_import_pattern = re.compile(r"from\s+vf_db\s+import\s+db")
        self.db_fixture_pattern = re.compile(
            r"@pytest\.fixture.*\n\s*def\s+.*db.*\("
        )

    def infer_test_module(
        self, file_path: Path, detected_module: str, content: str
    ) -> str:
        """Infer which module a test file belongs to by analyzing imports.

        Args:
            file_path: Path to test file
            detected_module: Module detected from file path
            content: File content

        Returns:
            Best guess for module the test belongs to
        """
        # Look for imports from sibling modules
        # Pattern: from ../module_name import ... or from module_name import ...
        import_pattern = re.compile(
            r"from\s+\.\.?(\w+)\s+import|from\s+(\w+)\s+import"
        )
        matches = import_pattern.findall(content)

        if matches:
            # Get unique module names from imports
            imported_modules = set()
            for match in matches:
                module = match[0] or match[1]
                if module and module not in [
                    "typing",
                    "pytest",
                    "unittest",
                    "mock",
                    "mongomock",
                ]:
                    imported_modules.add(module)

            # If only one module imported, that's likely the module being tested
            if len(imported_modules) == 1:
                return list(imported_modules)[0]

            # If multiple modules, prefer the one that appears in the detected module
            for mod in imported_modules:
                if mod in detected_module or detected_module in mod:
                    return mod

            # Otherwise use the first imported module
            if imported_modules:
                return list(imported_modules)[0]

        # Fall back to detected module from file path
        return detected_module

    def is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file.

        Args:
            file_path: Path to file

        Returns:
            True if file is a test file
        """
        name = file_path.name
        return name.startswith("test_") or name.endswith("_test.py")

    def analyze_test_file(
        self, file_path: Path, module_name: str
    ) -> dict[str, Any]:
        """Analyze a test file.

        Args:
            file_path: Path to test file
            module_name: Module the file belongs to

        Returns:
            Dictionary with test file analysis results
        """
        content = read_file_safely(file_path)
        if content is None:
            return {}
        return self.analyze_test_file_content(content, file_path, module_name)

    def analyze_test_file_content(
        self, content: str, file_path: Path, module_name: str
    ) -> dict[str, Any]:
        """Analyze a test file from file content (optimization: uses pre-read content).

        Args:
            content: File content as string
            file_path: Path to test file
            module_name: Module the file belongs to

        Returns:
            Dictionary with test file analysis results
        """
        # Infer actual module from test imports for smarter association
        inferred_module = self.infer_test_module(
            file_path, module_name, content
        )

        # Count test functions
        parser = ASTParser(file_path, content)
        functions = parser.get_functions()

        test_functions = [
            name for name, _ in functions if name.startswith("test_")
        ]

        # Determine if integration or unit test
        is_integration = self._is_integration_test(content)

        test_type = "integration" if is_integration else "unit"
        test_lines = len(content.split("\n"))

        file_results = {
            "file": str(file_path),
            "module": inferred_module,  # Use inferred module for better accuracy
            "type": test_type,
            "test_count": len(test_functions),
            "lines": test_lines,
            "indicators": self._get_integration_indicators(content)
            if is_integration
            else [],
        }

        # Update overall results with inferred module
        self._update_test_results(file_results, inferred_module)

        return file_results

    def _is_integration_test(self, content: str) -> bool:
        """Check if test file is integration test.

        Args:
            content: File content

        Returns:
            True if integration test
        """
        # Has database import
        if self.db_import_pattern.search(content):
            return True

        # Has database fixture
        if self.db_fixture_pattern.search(content):
            return True

        # Check for MongoClient or other DB clients
        if "MongoClient" in content or "mongomock" in content:
            return True

        return False

    def _get_integration_indicators(self, content: str) -> list[str]:
        """Get indicators that make this an integration test.

        Args:
            content: File content

        Returns:
            List of indicator strings
        """
        indicators = []

        if self.db_import_pattern.search(content):
            indicators.append("from vf_db import db")

        if "MongoClient" in content:
            indicators.append("MongoClient usage")

        if "mongomock" in content:
            indicators.append("mongomock usage")

        if self.db_fixture_pattern.search(content):
            indicators.append("database fixtures")

        return indicators

    def _update_test_results(
        self, file_results: dict[str, Any], module_name: str
    ) -> None:
        """Update test results.

        Args:
            file_results: Test file results
            module_name: Module name
        """
        test_count = file_results["test_count"]
        test_type = file_results["type"]

        # Update overall stats
        self.results["total_test_files"] += 1
        self.results["total_test_functions"] += test_count

        if test_type == "integration":
            self.results["integration_test_files"] += 1
            self.results["integration_test_functions"] += test_count
        else:
            self.results["unit_test_files"] += 1
            self.results["unit_test_functions"] += test_count

        # Update module stats
        module_stats = self.results["by_module"][module_name]
        module_stats["test_files"] += 1

        if test_type == "integration":
            module_stats["integration_tests"] += test_count
        else:
            module_stats["unit_tests"] += test_count

        # Add to test details
        self.results["test_details"].append(file_results)

    def analyze_testability(self, file_path: Path, module_name: str) -> None:
        """Analyze testability of a non-test file.

        Args:
            file_path: Path to file
            module_name: Module name
        """
        content = read_file_safely(file_path)
        if content is None:
            return
        self.analyze_testability_content(content, file_path, module_name)

    def analyze_testability_content(
        self, content: str, file_path: Path, module_name: str
    ) -> None:
        """Analyze testability from file content (optimization: uses pre-read content).

        Args:
            content: File content as string
            file_path: Path to file
            module_name: Module name
        """
        parser = ASTParser(file_path, content)
        functions = parser.get_functions()

        for func_name, func_node in functions:
            # Skip private and magic methods
            if func_name.startswith("_"):
                continue

            self.results["testability"]["total_functions"] += 1

            # Check if function has DB access
            func_source = content.split("\n")[
                func_node.lineno - 1 : func_node.end_lineno
            ]
            func_text = "\n".join(func_source)

            has_db = "db." in func_text
            has_business_logic = self._has_business_logic(func_node)

            if has_db:
                self.results["testability"]["functions_with_db_access"] += 1

            if has_business_logic:
                self.results["testability"][
                    "functions_with_business_logic"
                ] += 1

            # Mixed = both DB and business logic
            if has_db and has_business_logic:
                self.results["testability"]["functions_mixing_both"] += 1
                self.results["by_module"][module_name]["mixed_functions"] += 1

                # Track as untestable
                self.results["testability"]["untestable_functions"].append(
                    {
                        "function": func_name,
                        "module": module_name,
                        "file": str(file_path),
                        "line": func_node.lineno,
                        "reason": "mixes_business_logic_and_db",
                    }
                )

    def _has_business_logic(self, func_node: Any) -> bool:
        """Check if function has business logic.

        Args:
            func_node: AST FunctionDef node

        Returns:
            True if has business logic
        """
        import ast

        # Look for control flow and operations
        for node in ast.walk(func_node):
            # Control flow
            if isinstance(node, (ast.If, ast.For, ast.While)):
                return True
            # Comparisons
            if isinstance(node, ast.Compare):
                return True
            # Binary operations
            if isinstance(node, ast.BinOp):
                return True

        return False

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return analysis results.

        Returns:
            Complete analysis results
        """
        # Calculate test ratios
        total_tests = self.results["total_test_functions"]
        if total_tests > 0:
            self.results["test_ratio"]["unit_percentage"] = (
                self.results["unit_test_functions"] / total_tests
            ) * 100
            self.results["test_ratio"]["integration_percentage"] = (
                self.results["integration_test_functions"] / total_tests
            ) * 100

        # Calculate testability score
        total_with_logic = self.results["testability"][
            "functions_with_business_logic"
        ]
        mixed = self.results["testability"]["functions_mixing_both"]

        if total_with_logic > 0:
            # Score = percentage of business logic functions that are NOT mixed with DB
            pure_logic = total_with_logic - mixed
            self.results["testability"]["testability_score"] = (
                pure_logic / total_with_logic
            ) * 100
        else:
            self.results["testability"]["testability_score"] = 100.0

        # Calculate module testability scores
        for module_name, module_stats in self.results["by_module"].items():
            # Simple score based on test presence and type
            unit_tests = module_stats["unit_tests"]
            integration_tests = module_stats["integration_tests"]
            total_module_tests = unit_tests + integration_tests

            if total_module_tests > 0:
                module_stats["testability_score"] = (
                    unit_tests / total_module_tests
                ) * 100
            else:
                module_stats["testability_score"] = 0.0

        # Convert by_module from defaultdict to regular dict
        self.results["by_module"] = dict(self.results["by_module"])

        return self.results

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        return {
            "total_test_files": self.results["total_test_files"],
            "unit_percentage": round(
                self.results["test_ratio"]["unit_percentage"], 1
            ),
            "integration_percentage": round(
                self.results["test_ratio"]["integration_percentage"], 1
            ),
            "testability_score": round(
                self.results["testability"]["testability_score"], 1
            ),
            "untestable_functions": len(
                self.results["testability"]["untestable_functions"]
            ),
        }
