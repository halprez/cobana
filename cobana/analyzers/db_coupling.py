"""Database Coupling Analyzer - PRIMARY ANALYZER

Analyzes database coupling by detecting database operations and categorizing
them by ownership to identify architectural violations.
"""

import re
from pathlib import Path
from typing import Any
from collections import defaultdict
import logging

from cobana.utils.file_utils import read_file_safely

logger = logging.getLogger(__name__)


# Database operation patterns
READ_OPERATIONS = [
    "find",
    "find_one",
    "aggregate",
    "count",
    "count_documents",
    "distinct",
    "find_one_and_update",
    "find_one_and_replace",
    "find_one_and_delete",
    "select",
    "query",
    "get",
]

WRITE_OPERATIONS = [
    "insert",
    "insert_one",
    "insert_many",
    "update",
    "update_one",
    "update_many",
    "replace_one",
    "delete",
    "delete_one",
    "delete_many",
    "create_index",
    "drop",
    "drop_index",
    "save",
    "remove",
    "insert_update",
]

# NoSQL patterns
NOSQL_PATTERNS = {
    "mongodb": {
        "imports": [
            r"from\s+pymongo\s+import",
            r"import\s+pymongo",
            r"from\s+mongomock\s+import",
        ],
        "operations": r"(\w+_collection|\w+_db|client\[[\'\"][\w]+[\'\"]]\[)\.([a-zA-Z_]\w*)\(",
    },
    "dynamodb": {
        "imports": [r"from\s+boto3\s+import", r"import\s+boto3"],
        "operations": r"table\.(get_item|put_item|update_item|delete_item|query|scan)\(",
    },
}


class DatabaseCouplingAnalyzer:
    """Analyzes database coupling in Python codebases."""

    def __init__(self, config: dict[str, Any]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.service_name = config.get("service_name", "unknown")
        self.table_ownership = config.get("table_ownership", {})

        # Results storage
        self.results: dict[str, Any] = {
            "total_operations": 0,
            "total_files": 0,
            "total_files_with_db": 0,
            "severity_score": 0,
            "collections_accessed": {},
            "mixed_logic_files": [],  # Files with business logic + DB operations
            "by_module": defaultdict(
                lambda: {
                    "total_operations": 0,
                    "severity_score": 0,
                    "violations_write": 0,
                    "violations_read": 0,
                    "own_operations": 0,
                    "other_operations": 0,
                    "mixed_logic_count": 0,
                }
            ),
            "top_coupled_files": [],
            "violations": [],
        }

        # Build regex pattern for DB operations
        all_operations = READ_OPERATIONS + WRITE_OPERATIONS
        operations_pattern = "|".join(all_operations)
        # Pattern: db.{collection_name}.{operation}(
        self.db_pattern = re.compile(
            r"db\.([a-zA-Z_][a-zA-Z0-9_]*)\.({})\(".format(operations_pattern)
        )

        # Pattern for imports
        self.import_pattern = re.compile(r"from\s+vf_db\s+import\s+db")

        # Business logic patterns (control flow, calculations, validations)
        self.business_logic_patterns = [
            r"if\s+",  # Conditional logic
            r"for\s+",  # Loops
            r"while\s+",  # While loops
            r"\s+and\s+",  # Logical AND
            r"\s+or\s+",  # Logical OR
            r"assert\s+",  # Assertions
            r"raise\s+",  # Exception raising
            r"[+\-*/]\s*=",  # Arithmetic operations
            r"==|!=|<=|>=|<|>",  # Comparisons
        ]

    def analyze_file(self, file_path: Path, module_name: str) -> dict[str, Any]:
        """Analyze a single file for database coupling.

        Args:
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            Dictionary with file analysis results
        """
        content = read_file_safely(file_path)
        if content is None:
            return {}

        # Check for db import
        has_db_import = bool(self.import_pattern.search(content))

        # Find all DB operations
        operations = self._extract_operations(content, file_path)

        if not operations:
            return {}

        # Count this file
        self.results["total_files_with_db"] += 1

        # Categorize operations
        file_results = self._categorize_operations(operations, module_name)
        file_results["file"] = str(file_path)

        # Detect mixed logic (business logic + database operations)
        has_mixed_logic = self._detect_mixed_logic(content)
        file_results["has_mixed_logic"] = has_mixed_logic
        if has_mixed_logic:
            self.results["mixed_logic_files"].append(
                {
                    "file": str(file_path),
                    "module": module_name,
                    "operations_count": len(operations),
                }
            )
            self.results["by_module"][module_name]["mixed_logic_count"] += 1
        file_results["module"] = module_name
        file_results["has_db_import"] = has_db_import

        # Update overall results
        self._update_results(file_results, module_name)

        return file_results

    def _extract_operations(
        self, content: str, file_path: Path
    ) -> list[dict[str, Any]]:
        """Extract database operations from file content.

        Args:
            content: File content
            file_path: Path to file (for line numbers)

        Returns:
            List of operation dictionaries
        """
        operations = []
        lines = content.splitlines()

        for line_num, line in enumerate(lines, start=1):
            # Find all matches in this line
            for match in self.db_pattern.finditer(line):
                collection = match.group(1)
                operation = match.group(2)

                # Determine operation type
                op_type = "read" if operation in READ_OPERATIONS else "write"

                operations.append(
                    {
                        "collection": collection,
                        "operation": operation,
                        "type": op_type,
                        "line": line_num,
                        "code_snippet": line.strip()[:100],  # First 100 chars
                    }
                )

        return operations

    def _categorize_operations(
        self, operations: list[dict[str, Any]], module_name: str
    ) -> dict[str, Any]:
        """Categorize operations by ownership.

        Args:
            operations: List of operations to categorize
            module_name: Module name

        Returns:
            Categorized results
        """
        results = {
            "total_operations": len(operations),
            "reads": 0,
            "writes": 0,
            "collections": set(),
            "own_operations": 0,
            "shared_operations": 0,
            "other_reads": 0,
            "other_writes": 0,
            "operations_by_collection": defaultdict(
                lambda: {"reads": 0, "writes": 0}
            ),
            "violations": [],
        }

        for op in operations:
            collection = op["collection"]
            op_type = op["type"]

            results["collections"].add(collection)

            # Count by type
            if op_type == "read":
                results["reads"] += 1
            else:
                results["writes"] += 1

            # Update collection stats
            results["operations_by_collection"][collection][op_type + "s"] += 1

            # Determine ownership
            ownership = self._get_ownership(collection)

            match ownership:
                case "own":
                    results["own_operations"] += 1
                case "shared":
                    results["shared_operations"] += 1
                case "other":
                    if op_type == "read":
                        results["other_reads"] += 1
                        # Violation: reading from other service's table
                        results["violations"].append(
                            {
                                "type": "read",
                                "severity": "warning",
                                "collection": collection,
                                "operation": op["operation"],
                                "line": op["line"],
                                "code_snippet": op["code_snippet"],
                            }
                        )
                    else:
                        results["other_writes"] += 1
                        # Violation: writing to other service's table
                        results["violations"].append(
                            {
                                "type": "write",
                                "severity": "critical",
                                "collection": collection,
                                "operation": op["operation"],
                                "line": op["line"],
                                "code_snippet": op["code_snippet"],
                            }
                        )

        # Calculate severity score for this file
        results["severity_score"] = (
            results["other_reads"] * 1 + results["other_writes"] * 5
        )

        # Convert set to list for JSON serialization
        results["collections"] = list(results["collections"])

        return results

    def _get_ownership(self, collection: str) -> str:
        """Determine ownership of a collection.

        Args:
            collection: Collection name

        Returns:
            'own', 'shared', or 'other'
        """
        # Check if it's owned by this service
        own_tables = self.table_ownership.get(self.service_name, [])
        if collection in own_tables:
            return "own"

        # Check if it's shared
        shared_tables = self.table_ownership.get("shared", [])
        if collection in shared_tables:
            return "shared"

        # Otherwise, it's owned by another service
        return "other"

    def _update_results(
        self, file_results: dict[str, Any], module_name: str
    ) -> None:
        """Update overall results with file results.

        Args:
            file_results: Results from analyzing a single file
            module_name: Module the file belongs to
        """
        # Update overall stats
        self.results["total_operations"] += file_results["total_operations"]
        self.results["severity_score"] += file_results["severity_score"]

        # Update module stats
        module_stats = self.results["by_module"][module_name]
        module_stats["total_operations"] += file_results["total_operations"]
        module_stats["severity_score"] += file_results["severity_score"]
        module_stats["violations_write"] += file_results["other_writes"]
        module_stats["violations_read"] += file_results["other_reads"]
        module_stats["own_operations"] += file_results["own_operations"]
        module_stats["other_operations"] += (
            file_results["other_reads"] + file_results["other_writes"]
        )

        # Update collections accessed
        for collection in file_results["collections"]:
            if collection not in self.results["collections_accessed"]:
                self.results["collections_accessed"][collection] = {
                    "reads": 0,
                    "writes": 0,
                    "ownership": self._get_ownership(collection),
                    "accessed_by_modules": set(),
                }

            coll_stats = self.results["collections_accessed"][collection]
            coll_ops = file_results["operations_by_collection"][collection]
            coll_stats["reads"] += coll_ops["reads"]
            coll_stats["writes"] += coll_ops["writes"]
            coll_stats["accessed_by_modules"].add(module_name)

        # Add to top coupled files (we'll sort later)
        self.results["top_coupled_files"].append(
            {
                "file": file_results["file"],
                "module": module_name,
                "total_operations": file_results["total_operations"],
                "reads": file_results["reads"],
                "writes": file_results["writes"],
                "collections": file_results["collections"],
                "severity_score": file_results["severity_score"],
                "violations": len(file_results["violations"]),
            }
        )

        # Add violations
        for violation in file_results["violations"]:
            self.results["violations"].append(
                {
                    **violation,
                    "file": file_results["file"],
                    "module": module_name,
                }
            )

    def _detect_mixed_logic(self, content: str) -> bool:
        """Detect if file mixes business logic with database operations.

        Looks for patterns indicating control flow, calculations, or validations
        that happen alongside database operations.

        Args:
            content: File content

        Returns:
            True if mixed logic detected
        """
        # Count business logic indicators
        logic_count = 0
        for pattern in self.business_logic_patterns:
            if re.search(pattern, content):
                logic_count += 1

        # If file has at least 2 business logic indicators, consider it mixed
        # (this avoids false positives from imports with control flow)
        return logic_count >= 2

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return analysis results.

        Returns:
            Complete analysis results
        """
        # Convert sets to lists for JSON serialization
        for coll_data in self.results["collections_accessed"].values():
            coll_data["accessed_by_modules"] = list(
                coll_data["accessed_by_modules"]
            )

        # Sort top coupled files by severity score
        self.results["top_coupled_files"].sort(
            key=lambda x: x["severity_score"], reverse=True
        )

        # Keep only top 20
        self.results["top_coupled_files"] = self.results["top_coupled_files"][
            :20
        ]

        # Convert by_module from defaultdict to regular dict
        self.results["by_module"] = dict(self.results["by_module"])

        return self.results

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        return {
            "total_operations": self.results["total_operations"],
            "total_files_with_db": self.results["total_files_with_db"],
            "severity_score": self.results["severity_score"],
            "violation_count_read": len(
                [v for v in self.results["violations"] if v["type"] == "read"]
            ),
            "violation_count_write": len(
                [v for v in self.results["violations"] if v["type"] == "write"]
            ),
            "collections_count": len(self.results["collections_accessed"]),
        }
