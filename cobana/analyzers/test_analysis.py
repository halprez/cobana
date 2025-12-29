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

    def __init__(self, config: dict[str, Any], tests_dir: Path | None = None):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
            tests_dir: Optional path to tests directory. If provided, files under
                      this directory will be treated as test files.
        """
        self.config = config
        self.tests_dir = tests_dir

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
            "edge_case_analysis": {
                "total_edge_case_tests": 0,
                "total_happy_path_tests": 0,
                "edge_case_percentage": 0.0,
                "exception_handling_tests": 0,
                "boundary_value_tests": 0,
                "negative_assertion_tests": 0,
                "error_condition_tests": 0,
                "regression_tests": 0,
                "parametrized_tests": 0,
                "edge_case_details": [],
            },
            "by_module": defaultdict(
                lambda: {
                    "test_files": 0,
                    "unit_tests": 0,
                    "integration_tests": 0,
                    "edge_case_tests": 0,
                    "happy_path_tests": 0,
                    "edge_case_percentage": 0.0,
                    "testability_score": 0.0,
                    "mixed_functions": 0,
                    "total_functions": 0,
                    "functions_with_tests": 0,
                    "function_coverage": 0.0,
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

        # Track test function names per module for coverage calculation
        self._test_functions_by_module: dict[str, set[str]] = defaultdict(set)
        # Track production function names per module
        self._production_functions_by_module: dict[str, set[str]] = defaultdict(set)

        # Patterns for test categorization
        self.db_import_pattern = re.compile(r"from\s+vf_db\s+import\s+db")
        self.db_fixture_pattern = re.compile(
            r"@pytest\.fixture.*\n\s*def\s+.*db.*\("
        )

        # Integration test indicators (external dependencies)
        self.integration_patterns = {
            # Database
            "database": [
                r"import\s+(?:psycopg2|pymongo|pymysql|sqlite3|sqlalchemy)",
                r"from\s+(?:psycopg2|pymongo|pymysql|sqlite3|sqlalchemy)",
                r"MongoClient|mysql\.connector|psycopg2\.connect",
                r"mongomock|fakeredis",
                r"@pytest\.fixture.*\(.*db.*\)",
            ],
            # Network/API
            "network": [
                r"import\s+(?:requests|httpx|urllib|aiohttp)",
                r"from\s+(?:requests|httpx|urllib|aiohttp)",
                r"requests\.(?:get|post|put|delete)",
                r"httpx\.(?:Client|AsyncClient)",
                r"responses\.mock",
            ],
            # File System
            "filesystem": [
                r"@pytest\.fixture.*\(.*tmp_path.*\)",
                r"tempfile\.(?:mkdtemp|NamedTemporaryFile)",
                r"shutil\.(?:copy|move|rmtree)",
                r"Path\(.*\)\.(?:write_text|read_text|mkdir)",
            ],
            # External Process
            "subprocess": [
                r"import\s+subprocess",
                r"subprocess\.(?:run|Popen|call|check_output)",
            ],
            # Time-dependent
            "time": [
                r"time\.sleep",
                r"@pytest\.mark\.slow",
                r"asyncio\.sleep",
            ],
        }

    def infer_test_module(
        self, file_path: Path, detected_module: str, content: str
    ) -> str:
        """Infer which module a test file belongs to by analyzing imports.

        Uses multiple strategies:
        1. Analyze relative imports (from ..module, from ...module)
        2. Look at absolute imports from the codebase
        3. Check file path structure (tests/module_name/test_*.py -> module_name)
        4. Fall back to detected module from path

        Args:
            file_path: Path to test file
            detected_module: Module detected from file path
            content: File content

        Returns:
            Best guess for module the test belongs to
        """
        # Common test/utility modules to ignore
        ignore_modules = {
            "typing", "pytest", "unittest", "mock", "mongomock", "fakeredis",
            "requests", "httpx", "pathlib", "os", "sys", "json", "re",
            "datetime", "time", "collections", "itertools", "functools",
            "asyncio", "logging", "conftest", "fixtures", "helpers",
        }

        # Pattern for relative imports: from ..module or from ...module
        relative_import_pattern = re.compile(
            r"from\s+(\.{1,3})(\w+)\s+import"
        )
        # Pattern for absolute imports
        absolute_import_pattern = re.compile(
            r"from\s+([a-zA-Z_]\w+(?:\.[a-zA-Z_]\w+)*)\s+import"
        )

        imported_modules = set()

        # Check relative imports (these are most likely to indicate the tested module)
        relative_matches = relative_import_pattern.findall(content)
        for dots, module in relative_matches:
            if module and module not in ignore_modules:
                imported_modules.add(module)

        # If we found relative imports, use those
        if imported_modules:
            # Prefer the most commonly imported module
            if len(imported_modules) == 1:
                return list(imported_modules)[0]
            # If multiple, prefer one matching detected module
            for mod in imported_modules:
                if mod in detected_module or detected_module in mod:
                    return mod
            return list(imported_modules)[0]

        # Check absolute imports
        absolute_matches = absolute_import_pattern.findall(content)
        for module_path in absolute_matches:
            # Get the first component (top-level module)
            top_module = module_path.split(".")[0]
            if top_module and top_module not in ignore_modules:
                # Avoid common standard library modules
                if not top_module.startswith("_") and top_module.islower():
                    imported_modules.add(top_module)

        # Filter to modules that might be from this codebase
        # (simple heuristic: short names are more likely to be local modules)
        local_modules = {m for m in imported_modules if len(m) < 20}

        if local_modules:
            if len(local_modules) == 1:
                return list(local_modules)[0]
            # Prefer module matching detected module
            for mod in local_modules:
                if mod in detected_module or detected_module in mod:
                    return mod
            return list(local_modules)[0]

        # Check file path structure for hints
        # e.g., tests/analyzers/test_db.py -> analyzers
        path_parts = file_path.parts
        test_dir_indices = [i for i, part in enumerate(path_parts)
                           if part in {"test", "tests", "testing", "__tests__"}]
        if test_dir_indices:
            # Get directory after test dir
            test_dir_idx = test_dir_indices[-1]
            if test_dir_idx + 1 < len(path_parts):
                next_dir = path_parts[test_dir_idx + 1]
                # If it's not a file and looks like a module name
                if not next_dir.endswith(".py") and next_dir not in ignore_modules:
                    return next_dir

        # Fall back to detected module from file path
        return detected_module

    def is_test_file(self, file_path: Path) -> bool:
        """Check if file is a test file.

        Uses multiple heuristics:
        1. If tests_dir is set, check if file is under that directory
        2. Filename patterns (test_*.py or *_test.py)
        3. Located in test directories (test/, tests/, testing/)
        4. Contains test classes or functions (checked via content)

        Args:
            file_path: Path to file

        Returns:
            True if file is a test file
        """
        # If tests_dir is set, check if file is under it
        if self.tests_dir:
            try:
                # Check if file is relative to tests_dir
                file_path.resolve().relative_to(self.tests_dir.resolve())
                # If no exception, file is under tests_dir
                logger.debug(f"File {file_path} is under tests_dir {self.tests_dir}")
                return True
            except ValueError:
                # File is not under tests_dir, continue with other checks
                pass

        name = file_path.name
        path_str = str(file_path)

        # Check filename patterns
        if name.startswith("test_") or name.endswith("_test.py"):
            return True

        # Check if in test directory
        path_parts = file_path.parts
        test_dir_names = {"test", "tests", "testing", "spec", "specs", "__tests__"}
        if any(part in test_dir_names for part in path_parts):
            # If in test directory and is a Python file, likely a test
            if name.endswith(".py") and not name.startswith("__"):
                return True

        # Check for conftest.py (pytest configuration, always in test dirs)
        if name == "conftest.py":
            return True

        return False

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

        # Count test functions and analyze edge cases
        parser = ASTParser(file_path, content)
        functions = parser.get_functions()

        test_functions = [
            (name, node) for name, node in functions if name.startswith("test_")
        ]

        # Track test function names for coverage calculation
        for test_func, _ in test_functions:
            self._test_functions_by_module[inferred_module].add(test_func)

        # Analyze edge case patterns in each test function
        edge_case_count = 0
        happy_path_count = 0
        edge_case_tests = []

        for func_name, func_node in test_functions:
            edge_indicators = self._detect_edge_case_patterns(
                func_name, func_node, content
            )

            if edge_indicators["is_edge_case"]:
                edge_case_count += 1
                edge_case_tests.append(
                    {
                        "function": func_name,
                        "file": str(file_path),
                        "module": inferred_module,
                        "line": func_node.lineno,
                        "patterns": edge_indicators["patterns"],
                        "boundary_values": edge_indicators["boundary_values"],
                        "is_regression": edge_indicators["is_regression"],
                    }
                )

                # Update specific edge case counters
                if edge_indicators["exception_handling"]:
                    self.results["edge_case_analysis"]["exception_handling_tests"] += 1
                if edge_indicators["boundary_values"]:
                    self.results["edge_case_analysis"]["boundary_value_tests"] += 1
                if edge_indicators["negative_assertions"]:
                    self.results["edge_case_analysis"]["negative_assertion_tests"] += 1
                if edge_indicators["error_condition"]:
                    self.results["edge_case_analysis"]["error_condition_tests"] += 1
                if edge_indicators["is_regression"]:
                    self.results["edge_case_analysis"]["regression_tests"] += 1
                if edge_indicators["is_parametrized"]:
                    self.results["edge_case_analysis"]["parametrized_tests"] += 1
            else:
                happy_path_count += 1

        # Update module-level edge case stats
        self.results["by_module"][inferred_module]["edge_case_tests"] += edge_case_count
        self.results["by_module"][inferred_module]["happy_path_tests"] += happy_path_count

        # Update overall edge case stats
        self.results["edge_case_analysis"]["total_edge_case_tests"] += edge_case_count
        self.results["edge_case_analysis"]["total_happy_path_tests"] += happy_path_count
        self.results["edge_case_analysis"]["edge_case_details"].extend(edge_case_tests)

        # Determine if integration or unit test
        is_integration = self._is_integration_test(content)

        test_type = "integration" if is_integration else "unit"
        test_lines = len(content.split("\n"))

        file_results = {
            "file": str(file_path),
            "module": inferred_module,  # Use inferred module for better accuracy
            "type": test_type,
            "test_count": len(test_functions),
            "edge_case_tests": edge_case_count,
            "happy_path_tests": happy_path_count,
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

        Integration tests interact with external resources like:
        - Databases
        - Network/APIs
        - File system
        - External processes
        - Time-dependent operations

        Args:
            content: File content

        Returns:
            True if integration test (has external dependencies)
        """
        # Check all integration pattern categories
        for category, patterns in self.integration_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    return True

        # Legacy patterns for backwards compatibility
        if self.db_import_pattern.search(content):
            return True
        if self.db_fixture_pattern.search(content):
            return True

        return False

    def _get_integration_indicators(self, content: str) -> list[str]:
        """Get indicators that make this an integration test.

        Args:
            content: File content

        Returns:
            List of indicator strings (e.g., ["database", "network"])
        """
        indicators = []

        # Check each integration category
        for category, patterns in self.integration_patterns.items():
            for pattern in patterns:
                if re.search(pattern, content):
                    if category not in indicators:
                        indicators.append(category)
                    break  # Found one pattern in this category, move to next

        # Legacy patterns
        if self.db_import_pattern.search(content) and "database" not in indicators:
            indicators.append("database")

        if self.db_fixture_pattern.search(content) and "database" not in indicators:
            indicators.append("database")

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

    def _detect_edge_case_patterns(
        self, func_name: str, func_node: Any, content: str
    ) -> dict[str, Any]:
        """Detect edge case testing patterns in a test function.

        Edge case tests are critical for production reliability but often overlooked.
        This method identifies various patterns that indicate edge case coverage:

        1. Exception handling: Tests that verify error conditions
        2. Boundary values: Tests with 0, None, empty collections, max values
        3. Negative assertions: Tests checking for false/None/not-equal conditions
        4. Error conditions: Tests for validation failures
        5. Regression tests: Tests for previously fixed bugs
        6. Parametrized tests: Tests covering multiple scenarios

        Args:
            func_name: Name of test function
            func_node: AST FunctionDef node
            content: Full file content as string

        Returns:
            Dictionary with edge case indicators and classification
        """
        import ast

        indicators = {
            "is_edge_case": False,
            "is_regression": False,
            "patterns": [],
            "boundary_values": [],
            "exception_handling": False,
            "negative_assertions": False,
            "error_condition": False,
            "is_parametrized": False,
        }

        # Get function source
        func_lines = content.split("\n")[
            func_node.lineno - 1 : func_node.end_lineno
        ]
        func_source = "\n".join(func_lines)

        # 1. Detect exception handling tests
        exception_patterns = [
            r"pytest\.raises",
            r"assertRaises",
            r"with\s+raises",
            r"except\s+\w+Error",
            r"@pytest\.mark\.xfail",
        ]
        for pattern in exception_patterns:
            if re.search(pattern, func_source):
                indicators["exception_handling"] = True
                indicators["patterns"].append("exception_handling")
                indicators["is_edge_case"] = True
                break

        # 2. Detect boundary value tests
        # Look for boundary values in assertions or function calls
        # More specific patterns to avoid false positives
        boundary_patterns = [
            (r"(?:==|!=|assert|,)\s*0\b", "zero"),
            (r"(?:==|!=|assert|,)\s*-1\b", "negative_one"),
            (r"(?:==|!=|assert|is|,)\s*None\b", "none"),
            (r'(?:==|!=|assert|,)\s*""', "empty_string"),
            (r"(?:==|!=|assert|,)\s*\[\]", "empty_list"),
            (r"(?:==|!=|assert|,)\s*\{\}", "empty_dict"),
            (r"float\(['\"]inf['\"]\)", "infinity"),
            (r"sys\.maxsize", "max_int"),
            (r"\.MIN\b", "minimum"),
            (r"\.MAX\b", "maximum"),
        ]
        for pattern, value_type in boundary_patterns:
            if re.search(pattern, func_source):
                indicators["boundary_values"].append(value_type)

        if indicators["boundary_values"]:
            indicators["patterns"].append("boundary_values")
            indicators["is_edge_case"] = True

        # 3. Detect negative assertions (checking for false/failure conditions)
        negative_patterns = [
            r"assertFalse",
            r"assertIsNone",
            r"assertNotEqual",
            r"assertNotIn",
            r"assert\s+not\s+",
            r"assert\s+.*\s+is\s+None",
            r"assert\s+.*\s+!=",
        ]
        for pattern in negative_patterns:
            if re.search(pattern, func_source):
                indicators["negative_assertions"] = True
                indicators["patterns"].append("negative_assertions")
                indicators["is_edge_case"] = True
                break

        # 4. Detect error condition tests (by naming and content)
        error_keywords = [
            r"invalid",
            r"error",
            r"fail",
            r"exception",
            r"wrong",
            r"bad",
            r"missing",
            r"empty",
            r"null",
            r"overflow",
            r"underflow",
        ]
        func_name_lower = func_name.lower()
        for keyword in error_keywords:
            if re.search(keyword, func_name_lower) or re.search(
                keyword, func_source, re.IGNORECASE
            ):
                indicators["error_condition"] = True
                indicators["patterns"].append("error_condition")
                indicators["is_edge_case"] = True
                break

        # 5. Detect regression tests
        regression_keywords = [r"regression", r"fix", r"bug", r"issue"]
        for keyword in regression_keywords:
            if re.search(keyword, func_name_lower):
                indicators["is_regression"] = True
                indicators["patterns"].append("regression")
                indicators["is_edge_case"] = True
                break

        # 6. Detect parametrized tests (multiple scenarios)
        parametrize_patterns = [
            r"@pytest\.mark\.parametrize",
            r"@parameterized",
        ]
        for pattern in parametrize_patterns:
            # Check decorators before function
            pre_func_lines = content.split("\n")[
                max(0, func_node.lineno - 10) : func_node.lineno - 1
            ]
            pre_func_source = "\n".join(pre_func_lines)
            if re.search(pattern, pre_func_source):
                indicators["is_parametrized"] = True
                indicators["patterns"].append("parametrized")
                # Parametrized tests often cover edge cases
                indicators["is_edge_case"] = True
                break

        return indicators

    def track_production_functions(
        self, file_path: Path, module_name: str, content: str
    ) -> None:
        """Track production function names for test coverage calculation.

        Args:
            file_path: Path to file
            module_name: Module name
            content: File content
        """
        parser = ASTParser(file_path, content)
        functions = parser.get_functions()

        # Count public functions (skip private/magic methods)
        for func_name, _ in functions:
            if not func_name.startswith("_"):
                self._production_functions_by_module[module_name].add(func_name)
                self.results["by_module"][module_name]["total_functions"] += 1

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

        # Calculate edge case coverage percentage
        total_edge = self.results["edge_case_analysis"]["total_edge_case_tests"]
        total_happy = self.results["edge_case_analysis"]["total_happy_path_tests"]
        total_all_tests = total_edge + total_happy

        if total_all_tests > 0:
            self.results["edge_case_analysis"]["edge_case_percentage"] = (
                total_edge / total_all_tests
            ) * 100
        else:
            self.results["edge_case_analysis"]["edge_case_percentage"] = 0.0

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

        # Calculate module testability scores and edge case percentages
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

            # Calculate module edge case percentage
            module_edge = module_stats["edge_case_tests"]
            module_happy = module_stats["happy_path_tests"]
            module_total = module_edge + module_happy

            if module_total > 0:
                module_stats["edge_case_percentage"] = (
                    module_edge / module_total
                ) * 100
            else:
                module_stats["edge_case_percentage"] = 0.0

        # Calculate function coverage (functions with corresponding tests)
        for module_name in self.results["by_module"].keys():
            production_funcs = self._production_functions_by_module.get(module_name, set())
            test_funcs = self._test_functions_by_module.get(module_name, set())

            if production_funcs:
                # Check which production functions have corresponding test_* functions
                tested_funcs = set()
                for prod_func in production_funcs:
                    test_name = f"test_{prod_func}"
                    if test_name in test_funcs:
                        tested_funcs.add(prod_func)

                self.results["by_module"][module_name]["functions_with_tests"] = len(tested_funcs)
                self.results["by_module"][module_name]["function_coverage"] = (
                    len(tested_funcs) / len(production_funcs)
                ) * 100
            else:
                self.results["by_module"][module_name]["function_coverage"] = 0.0

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
            "edge_case_percentage": round(
                self.results["edge_case_analysis"]["edge_case_percentage"], 1
            ),
            "total_edge_case_tests": self.results["edge_case_analysis"]["total_edge_case_tests"],
            "total_happy_path_tests": self.results["edge_case_analysis"]["total_happy_path_tests"],
        }
