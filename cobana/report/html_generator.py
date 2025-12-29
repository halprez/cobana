"""HTML report generator for COBANA."""

from pathlib import Path
from datetime import datetime
from typing import Any
import logging

try:
    from jinja2 import Environment, BaseLoader, TemplateNotFound
except ImportError:
    raise ImportError(
        "jinja2 is required for HTML report generation. Install with: pip install jinja2"
    )

from cobana.report.html_template import HTML_TEMPLATE
from cobana.utils.file_utils import read_file_safely

logger = logging.getLogger(__name__)


class MemoryLoader(BaseLoader):
    """Loads templates from memory (strings)."""

    def __init__(self, templates: dict[str, str]):
        self.templates = templates

    def get_source(
        self, environment: Environment, template: str
    ) -> tuple[str, str | None, Any]:
        """Get template source from memory."""
        if template in self.templates:
            source = self.templates[template]
            return source, None, lambda: True
        raise TemplateNotFound(template)


class HtmlReportGenerator:
    """Generates HTML reports from analysis results."""

    def __init__(self, results: dict[str, Any], max_items: int = 0):
        """Initialize HTML report generator.

        Args:
            results: Analysis results dictionary
            max_items: Maximum number of items to display in lists (0 = unlimited)
        """
        self.results = results
        self.max_items = max_items
        self.templates = self._create_templates()
        self.env = Environment(loader=MemoryLoader(self.templates))
        # Add custom filters
        self.env.filters["highlight_module"] = self._highlight_module_filter

    def _create_templates(self) -> dict[str, str]:
        """Create all template strings."""
        templates = {
            "main.html": HTML_TEMPLATE,
            "module_overview_section.html": self._create_module_overview_template(),
            "db_coupling_section.html": self._create_db_coupling_template(),
            "complexity_section.html": self._create_complexity_template(),
            "maintainability_section.html": self._create_maintainability_template(),
            "code_size_section.html": self._create_code_size_template(),
            "tests_section.html": self._create_tests_template(),
            "code_smells_section.html": self._create_code_smells_template(),
            "technical_debt_section.html": self._create_technical_debt_template(),
        }
        return templates

    def generate(self, output_path: Path | str) -> None:
        """Generate HTML report to file.

        Args:
            output_path: Path to output HTML file
        """
        output_path = Path(output_path)
        html_content = self.get_html_string()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        logger.info(f"HTML report generated: {output_path}")

    def get_html_string(self) -> str:
        """Get HTML report as string.

        Returns:
            Complete HTML report as string
        """
        template = self.env.get_template("main.html")

        # Prepare data for template
        module_health_raw = self.results.get("module_health", {})

        # Extract by_module if it exists, otherwise use the raw dict
        if "by_module" in module_health_raw:
            module_health_dict = module_health_raw["by_module"]
        else:
            # Filter out non-module keys like 'module_rankings'
            module_health_dict = {
                k: v
                for k, v in module_health_raw.items()
                if isinstance(v, dict)
                and k not in ["by_module", "module_rankings"]
            }

        context = {
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": self.results.get("metadata", {}),
            "summary": self.results.get("summary", {}),
            "complexity": self._prepare_complexity_data(),
            "maintainability": self._prepare_maintainability_data(),
            "code_size": self._prepare_code_size_data(),
            "tests": self._prepare_test_data(),
            "code_smells": self._prepare_code_smells_data(),
            "db_coupling": self._prepare_db_coupling_data(),
            "technical_debt": self._prepare_technical_debt_data(),
            "module_health": module_health_dict,
            "module_rankings": self._prepare_module_rankings(),
            "available_modules": self._get_available_modules(),
            "max_items": self.max_items,
        }

        return template.render(**context)

    def _prepare_module_rankings(self) -> list[dict[str, Any]]:
        """Prepare module rankings for chart.

        Returns:
            List of module rankings with scores
        """
        module_health = self.results.get("module_health", {})

        # Check if rankings are already provided
        if "module_rankings" in module_health:
            return module_health["module_rankings"]

        # Otherwise build from by_module or raw module_health dict
        if "by_module" in module_health:
            by_module = module_health["by_module"]
        else:
            by_module = module_health

        rankings = []
        for module_name, data in by_module.items():
            if isinstance(data, dict):
                rankings.append(
                    {
                        "module": module_name,
                        "score": data.get("health_score", data.get("score", 0)),
                    }
                )

        # Sort by score descending
        rankings.sort(key=lambda x: x["score"], reverse=True)

        return rankings

    def _get_available_modules(self) -> list[str]:
        """Get list of all available modules from module rankings.

        Returns:
            List of module names
        """
        rankings = self._prepare_module_rankings()
        return [module["module"] for module in rankings]

    def _get_root_path(self) -> Path:
        """Get the codebase root path from metadata.

        Returns:
            Path to codebase root
        """
        metadata = self.results.get("metadata", {})
        codebase_path = metadata.get("codebase_path", "")
        return Path(codebase_path) if codebase_path else Path.cwd()

    def _format_file_path(self, file_path: str, module_name: str = "") -> str:
        """Format file path as relative to codebase root.

        Args:
            file_path: Absolute file path
            module_name: Module name for context

        Returns:
            Relative path string
        """
        try:
            abs_path = Path(file_path).resolve()
            root_path = self._get_root_path()
            rel_path = abs_path.relative_to(root_path)
            return str(rel_path)
        except (ValueError, TypeError):
            # If path is not relative to root, return as-is
            return (
                str(file_path)
                .replace(str(self._get_root_path()), "")
                .lstrip("/")
            )

    def _extract_module_from_path(self, file_path: str) -> str:
        """Extract module name from file path.

        The module is the first directory component in the relative path.

        Args:
            file_path: Absolute or relative file path

        Returns:
            Module name (first directory component) or empty string
        """
        rel_path = self._format_file_path(file_path)
        parts = rel_path.split("/")
        return parts[0] if parts else ""

    def _format_file_path_html(self, file_path: str) -> str:
        """Format file path with module name highlighted for HTML display.

        Args:
            file_path: Absolute file path

        Returns:
            HTML-formatted path with module highlighted
        """
        rel_path = self._format_file_path(file_path)
        parts = rel_path.split("/")

        if len(parts) > 1:
            # Highlight first part (module name) in bold
            module = parts[0]
            rest = "/".join(parts[1:])
            return f"<strong>{module}</strong>/{rest}"
        return rel_path

    def _highlight_module_filter(self, file_path: str) -> str:
        """Jinja2 filter to highlight module name in file paths.

        Args:
            file_path: File path string (relative or absolute)

        Returns:
            HTML string with module name in <strong> tags
        """
        # Ensure it's a relative path
        if file_path.startswith("/"):
            rel_path = self._format_file_path(file_path)
        else:
            rel_path = file_path

        parts = rel_path.split("/")

        if len(parts) > 1:
            # Highlight first part (module name) in bold
            module = parts[0]
            rest = "/".join(parts[1:])
            try:
                from markupsafe import Markup
            except ImportError:
                from jinja2 import Markup

            return Markup(f"<strong>{module}</strong>/{rest}")
        return rel_path

    def _prepare_test_data(self) -> dict[str, Any]:
        """Prepare test data for template rendering.

        Transforms test analyzer results to template-friendly format with
        calculated metrics like estimated_coverage.

        Returns:
            Dictionary with template-friendly test data
        """
        test_results = self.results.get("tests", {})

        # Extract relevant fields
        total_test_files = test_results.get("total_test_files", 0)
        total_test_functions = test_results.get("total_test_functions", 0)
        test_details = test_results.get("test_details", [])

        # Calculate estimated coverage based on test/code ratio
        code_size = self.results.get("code_size", {})
        total_lines = code_size.get(
            "total_loc", 0
        )  # Use total_loc instead of total_lines

        # Calculate total test lines from test details (no file reads needed)
        total_test_lines = sum(test.get("lines", 0) for test in test_details)

        if total_lines > 0 and total_test_lines > 0:
            estimated_coverage = min(
                (total_test_lines / total_lines) * 100, 100.0
            )
        else:
            estimated_coverage = 0.0

        # Transform test_details to template format (no file reads needed)
        test_files = [
            {
                "file": self._format_file_path(test.get("file", "")),
                "lines": test.get("lines", 0),
                "module": test.get("module", ""),
            }
            for test in test_details
        ]

        return {
            "estimated_coverage": estimated_coverage,
            "test_file_count": total_test_files,
            "total_test_lines": total_test_lines,
            "test_files": test_files,
            # Include additional data from test results for other templates
            **test_results,
        }

    def _prepare_code_smells_data(self) -> dict[str, Any]:
        """Prepare code smells data for template rendering.

        Transforms code smells analyzer results to template-friendly format with
        calculated metrics like long_files_count and complex_classes_count.

        Returns:
            Dictionary with template-friendly code smells data
        """
        code_smells_results = self.results.get("code_smells", {})
        class_metrics_results = self.results.get("class_metrics", {})

        # Transform long_methods to file-level data
        # Note: long_methods only has module names, not file paths
        long_methods = code_smells_results.get("long_methods", [])
        long_files_dict: dict[str, dict[str, Any]] = {}

        for method in long_methods:
            # Group by module since we don't have file paths
            module_name = method.get("module", "unknown")

            if module_name not in long_files_dict:
                long_files_dict[module_name] = {
                    "file": module_name,  # Using module name as identifier
                    "module": module_name,
                    "lines": method.get("sloc", 0),
                    "functions": 1,
                }
            else:
                long_files_dict[module_name]["functions"] += 1
                # Keep track of max SLOC in this module
                long_files_dict[module_name]["lines"] = max(
                    long_files_dict[module_name]["lines"],
                    method.get("sloc", 0)
                )

        long_files = list(long_files_dict.values())

        # Get complex classes from class_metrics analyzer
        # Use WMC (Weighted Methods per Class) > 50 as threshold for complex classes
        per_class = class_metrics_results.get("per_class", [])
        complex_classes = []

        for cls_data in per_class:
            wmc = cls_data.get("wmc", 0)
            # Classes with high WMC (> 50) are considered complex
            if wmc > 50 or cls_data.get("cohesion_level") == "low":
                file_path = cls_data.get("file", "")
                rel_path = self._format_file_path(file_path) if file_path else "unknown"
                module_name = self._extract_module_from_path(file_path) if file_path else ""

                complex_classes.append({
                    "class_name": cls_data.get("class", ""),
                    "file": rel_path,
                    "module": module_name,
                    "method_count": cls_data.get("methods", 0),
                    "avg_complexity": wmc / cls_data.get("methods", 1) if cls_data.get("methods", 0) > 0 else 0,
                    "wmc": wmc,
                    "cohesion": cls_data.get("cohesion_level", "unknown"),
                })

        # Map analyzer fields to template expectations
        return {
            "long_files_count": len(long_files),
            "complex_classes_count": len(complex_classes),
            "long_files": long_files,
            "complex_classes": complex_classes,
            # Include all other fields from results
            **code_smells_results,
        }

    def _prepare_db_coupling_data(self) -> dict[str, Any]:
        """Prepare database coupling data for template rendering.

        Returns:
            Dictionary with template-friendly database coupling data
        """
        db_coupling_results = self.results.get("db_coupling", {})

        # Format file paths in violations
        violations = db_coupling_results.get("violations", [])
        formatted_violations = []
        violations_by_file: dict[str, dict[str, Any]] = {}

        for violation in violations:
            if isinstance(violation, dict):
                file_path = violation.get("file", "")
                rel_path = (
                    self._format_file_path(file_path)
                    if file_path
                    else "unknown"
                )
                formatted_violation = violation.copy()
                formatted_violation["file"] = rel_path

                # Normalize field names for template compatibility
                # Analyzer uses "type", template expects "operation_type"
                if (
                    "type" in formatted_violation
                    and "operation_type" not in formatted_violation
                ):
                    formatted_violation["operation_type"] = formatted_violation[
                        "type"
                    ]

                # Analyzer uses "collection", template expects "table"
                if (
                    "collection" in formatted_violation
                    and "table" not in formatted_violation
                ):
                    formatted_violation["table"] = formatted_violation[
                        "collection"
                    ]

                formatted_violations.append(formatted_violation)

                # Aggregate by file
                if rel_path not in violations_by_file:
                    module_name = self._extract_module_from_path(file_path)
                    violations_by_file[rel_path] = {
                        "file": rel_path,
                        "module": module_name,
                        "write_count": 0,
                        "read_count": 0,
                        "total_count": 0,
                    }

                # Check both "operation_type" and "type" fields for compatibility
                op_type = (
                    violation.get("operation_type") or violation.get("type", "")
                ).lower()
                if op_type == "write":
                    violations_by_file[rel_path]["write_count"] += 1
                elif op_type == "read":
                    violations_by_file[rel_path]["read_count"] += 1
                violations_by_file[rel_path]["total_count"] += 1

        # Convert to list and sort by write violations first, then total count
        violations_by_file_list = list(violations_by_file.values())
        violations_by_file_list.sort(
            key=lambda x: (-x["write_count"], -x["total_count"])
        )

        return {
            **db_coupling_results,
            "violations": formatted_violations,
            "violations_by_file": violations_by_file_list,
        }

    def _prepare_maintainability_data(self) -> dict[str, Any]:
        """Prepare maintainability data for template rendering, aggregated by file.

        Returns:
            Dictionary with template-friendly maintainability data
        """
        maintainability_results = self.results.get("maintainability", {})

        # Get per_file data if available (it's a list)
        per_file = maintainability_results.get("per_file", [])

        # Transform per_file data to list format with relative paths
        low_maintainability_files = []
        for file_data in per_file:
            if isinstance(file_data, dict):
                file_path = file_data.get("file", "")
                rel_path = self._format_file_path(file_path)
                module_name = self._extract_module_from_path(file_path)
                low_maintainability_files.append(
                    {
                        "file": rel_path,
                        "module": module_name,
                        "maintainability_index": file_data.get("mi_score", 0),
                    }
                )

        # Sort by maintainability index (lower is worse)
        low_maintainability_files.sort(key=lambda x: x["maintainability_index"])

        return {
            "avg_mi": maintainability_results.get("avg_mi", 0),
            "low_maintainability_count": len(
                [
                    f
                    for f in low_maintainability_files
                    if f["maintainability_index"] < 20
                ]
            ),
            "low_maintainability_files": low_maintainability_files,
            **maintainability_results,
        }

    def _prepare_code_size_data(self) -> dict[str, Any]:
        """Prepare code size data for template rendering, aggregated by file.

        Returns:
            Dictionary with template-friendly code size data
        """
        code_size_results = self.results.get("code_size", {})
        complexity_results = self.results.get("complexity", {})
        class_metrics_results = self.results.get("class_metrics", {})

        # Get large_files from code_size analyzer (it's already a list)
        large_files_raw = code_size_results.get("large_files", [])

        # Transform large_files data to template format with relative paths
        large_files = []
        for file_data in large_files_raw:
            if isinstance(file_data, dict):
                file_path = file_data.get("file", "")
                rel_path = self._format_file_path(file_path)
                module_name = self._extract_module_from_path(file_path)
                large_files.append(
                    {
                        "file": rel_path,
                        "module": module_name,
                        "lines": file_data.get("sloc", 0),
                        "comment_ratio": file_data.get("comment_ratio", 0),
                    }
                )

        # Sort by lines of code (largest first)
        large_files.sort(key=lambda x: x["lines"], reverse=True)

        # Calculate average file size
        file_count = code_size_results.get("file_count", 0)
        total_sloc = code_size_results.get("total_sloc", 0)
        avg_file_size = total_sloc / file_count if file_count > 0 else 0

        # Prepare per_file data with module names and relative paths
        per_file = []
        for file_data in code_size_results.get("per_file", []):
            if isinstance(file_data, dict):
                file_path = file_data.get("file", "")
                rel_path = self._format_file_path(file_path)
                module_name = self._extract_module_from_path(file_path)
                per_file.append(
                    {
                        "file": rel_path,
                        "module": file_data.get("module", module_name),
                        "sloc": file_data.get("sloc", 0),
                        "comment_ratio": file_data.get("comment_ratio", 0),
                        "function_count": file_data.get("function_count", 0),
                        "class_count": file_data.get("class_count", 0),
                    }
                )

        # Get file size threshold from config (default 500)
        large_files_threshold = self.results.get("code_size", {}).get(
            "file_size_threshold", 500
        )

        # Count files larger than threshold
        large_files_threshold_count = sum(
            1 for f in per_file if f["sloc"] > large_files_threshold
        )

        return {
            "total_lines": code_size_results.get(
                "total_sloc", 0
            ),  # Analyzer uses total_sloc
            "total_functions": complexity_results.get(
                "total_functions", 0
            ),  # From complexity analyzer
            "total_classes": class_metrics_results.get(
                "total_classes", 0
            ),  # From class_metrics analyzer
            "avg_file_size": avg_file_size,
            "large_files": large_files,
            "per_file": per_file,
            "large_files_threshold": large_files_threshold,
            "large_files_threshold_count": large_files_threshold_count,
            **code_size_results,
        }

    def _prepare_technical_debt_data(self) -> dict[str, Any]:
        """Prepare technical debt data for template rendering.

        Formats debt data with relative file paths and module organization.

        Returns:
            Dictionary with template-friendly technical debt data
        """
        technical_debt_results = self.results.get("technical_debt", {})

        # Format top debt files with relative paths
        top_debt_files = technical_debt_results.get("top_debt_files", [])
        formatted_debt_files = []

        for file_data in top_debt_files:
            if isinstance(file_data, dict):
                file_path = file_data.get("file", "")
                rel_path = (
                    self._format_file_path(file_path)
                    if file_path
                    else "unknown"
                )
                module_name = (
                    self._extract_module_from_path(file_path)
                    if file_path
                    else ""
                )
                formatted_file = file_data.copy()
                formatted_file["file"] = rel_path
                formatted_file["module"] = module_name
                formatted_debt_files.append(formatted_file)

        # Sort by debt hours (highest first - worst files first)
        formatted_debt_files.sort(
            key=lambda x: x.get("debt_hours", 0), reverse=True
        )

        # Prepare by-module data
        by_module = technical_debt_results.get("by_module", {})
        by_module_list = []
        for module_name, module_data in by_module.items():
            if isinstance(module_data, dict):
                by_module_list.append(
                    {
                        "module": module_name,
                        "debt_hours": module_data.get("debt_hours", 0),
                        "debt_ratio": module_data.get("debt_ratio", 0),
                        "sqale_rating": module_data.get("sqale_rating", "N/A"),
                        "sloc": module_data.get("sloc", 0),
                    }
                )

        # Sort modules by debt hours (worst first)
        by_module_list.sort(key=lambda x: x.get("debt_hours", 0), reverse=True)

        return {
            **technical_debt_results,
            "top_debt_files": formatted_debt_files,
            "by_module_list": by_module_list,
        }

    def _prepare_complexity_data(self) -> dict[str, Any]:
        """Prepare complexity data for template rendering, aggregated by file.

        Transforms function-level complexity data to file-level metrics.

        Returns:
            Dictionary with template-friendly complexity data
        """
        complexity_results = self.results.get("complexity", {})

        # Get per_file data if available
        per_file = complexity_results.get("per_file", [])

        # Aggregate high complexity by file
        high_complexity_files: dict[str, dict[str, Any]] = {}

        for file_data in per_file:
            if not file_data:
                continue

            file_path = file_data.get("file", "")
            functions = file_data.get("functions", [])

            # Count high complexity functions in this file
            high_complexity_funcs = [
                f for f in functions if f.get("complexity", 0) > 10
            ]

            if high_complexity_funcs:
                rel_path = self._format_file_path(file_path)
                module_name = self._extract_module_from_path(file_path)
                high_complexity_files[file_path] = {
                    "file": rel_path,
                    "module": module_name,
                    "function_count": len(functions),
                    "avg_complexity": file_data.get("avg_complexity", 0),
                    "max_complexity": file_data.get("max_complexity", 0),
                    "high_complexity_count": len(high_complexity_funcs),
                    "high_complexity_functions": high_complexity_funcs,
                }

        # Convert to list and sort by high complexity count
        high_complexity_files_list = list(high_complexity_files.values())
        high_complexity_files_list.sort(
            key=lambda x: x["high_complexity_count"], reverse=True
        )

        return {
            "avg_complexity": complexity_results.get("avg_complexity", 0),
            "high_complexity_count": complexity_results.get(
                "high_complexity_count", 0
            ),
            "total_functions": complexity_results.get("total_functions", 0),
            "max_complexity": complexity_results.get("max_complexity", 0),
            "max_complexity_function": complexity_results.get(
                "max_complexity_function"
            ),
            "high_complexity_files": high_complexity_files_list,
            "per_file": per_file,
            # Include all other fields from results
            **complexity_results,
        }

    def _create_module_overview_template(self) -> str:
        """Create module overview section template."""
        return """
<section id="module-overview">
    <h2>📦 Module Overview</h2>

    <div class="explanation-box">
        <h3>📚 What are modules?</h3>
        <p>Modules are organizational units in your codebase (typically folders with Python packages).
        We analyze each module's health based on complexity, maintainability, test coverage, and code quality.</p>
    </div>

    {% if module_rankings %}
    <table>
        <thead>
            <tr>
                <th>Module</th>
                <th>Health Score</th>
                <th>Files</th>
                <th>Avg Complexity</th>
                <th>Maintainability</th>
                <th>Unit Test %</th>
            </tr>
        </thead>
        <tbody>
            {% for ranking in module_rankings %}
            {% set module_name = ranking.module %}
            {% set data = module_health.get(module_name, {}) if module_health else {} %}
            <tr>
                <td><code>{{ module_name }}</code></td>
                <td>
                    {% set score = ranking.score %}
                    <span class="badge {{ 'badge-success' if score >= 80 else 'badge-warning' if score >= 60 else 'badge-danger' }}">
                        {{ "%.1f"|format(score) }}/100
                    </span>
                </td>
                <td>{{ data.get('file_count', 0) }}</td>
                <td>{{ "%.1f"|format(data.get('avg_complexity', 0)) }}</td>
                <td>{{ "%.1f"|format(data.get('avg_maintainability', 0)) }}</td>
                <td>
                    <span class="badge {{ 'badge-success' if data.get('test_coverage', 0) >= 70 else 'badge-warning' if data.get('test_coverage', 0) >= 50 else 'badge-danger' }}">
                        {{ "%.0f"|format(data.get('test_coverage', 0)) }}%
                    </span>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p>No module data available.</p>
    {% endif %}
</section>
"""

    def _create_db_coupling_template(self) -> str:
        """Create database coupling section template."""
        return """
<section id="database-coupling">
    <h2>🔗 Database Coupling</h2>

    <div class="explanation-box">
        <h3>📚 What is database coupling?</h3>
        <p>Database coupling measures how closely your application logic is tied to database operations.
        Direct database calls in business logic (write operations) create tight coupling and make code harder to test and maintain.
        We detect coupling with SQL databases (PostgreSQL, MySQL, SQLite, etc.) and NoSQL databases (MongoDB, DynamoDB, etc.).</p>
        <ul>
            <li><strong>🔴 Write operations</strong> (INSERT, UPDATE, DELETE, UPSERT, SAVE) - Critical violations</li>
            <li><strong>🟡 Read operations</strong> (SELECT, FIND, GET) - Warnings</li>
            <li><strong>NoSQL</strong> - MongoDB, DynamoDB, and other NoSQL operations detected</li>
        </ul>
        <p><strong>⚡ Why it matters:</strong> Proper layering isolates database logic in repositories/DAOs,
        making code testable, maintainable, and easier to refactor.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'danger' if db_coupling.get('violation_count_write', 0) > 0 else 'success' }}">
            <h4>Write Violations</h4>
            <div class="metric-value">{{ db_coupling.get('violation_count_write', 0) }}</div>
            <div class="metric-label">Critical coupling issues</div>
        </div>
        <div class="metric-card {{ 'warning' if db_coupling.get('violation_count_read', 0) > 0 else 'success' }}">
            <h4>Read Operations</h4>
            <div class="metric-value">{{ db_coupling.get('violation_count_read', 0) }}</div>
            <div class="metric-label">Potential improvements</div>
        </div>
        <div class="metric-card">
            <h4>Total Operations</h4>
            <div class="metric-value">{{ db_coupling.get('total_operations', 0) }}</div>
            <div class="metric-label">Database interactions found</div>
        </div>
    </div>

    {% if db_coupling.get('violations') %}
    <details open>
        <summary>🔴 Write Violations ({{ db_coupling.get('violation_count_write', 0) }})</summary>
        <div class="issue-list">
            {% for violation in db_coupling.get('violations', []) %}
            {% if violation.get('operation_type') == 'write' %}
            <div class="issue-item critical">
                <strong>{{ violation.get('operation', '') }}</strong> in <code>{{ violation.get('file', '') | highlight_module }}:{{ violation.get('line', 0) }}</code>
                {% if violation.get('table') %}
                <br>Table: <code>{{ violation.get('table') }}</code>
                {% endif %}
            </div>
            {% endif %}
            {% endfor %}
        </div>
    </details>

    <details>
        <summary>🟡 Read Operations ({{ db_coupling.get('violation_count_read', 0) }})</summary>
        <div class="issue-list">
            {% for violation in db_coupling.get('violations', []) %}
            {% if violation.get('operation_type') == 'read' %}
            <div class="issue-item">
                <strong>{{ violation.get('operation', '') }}</strong> in <code>{{ violation.get('file', '') | highlight_module }}:{{ violation.get('line', 0) }}</code>
                {% if violation.get('table') %}
                <br>Table: <code>{{ violation.get('table') }}</code>
                {% endif %}
            </div>
            {% endif %}
            {% endfor %}
        </div>
    </details>

    {% if db_coupling.get('violations_by_file') %}
    <details>
        <summary>📁 Violations by File (Worst First)</summary>
        {% if max_items > 0 and db_coupling.get('violations_by_file')|length > max_items %}
        <p style="margin: 10px 0; color: #666; font-size: 0.9em;">
            📌 Showing {{ max_items }} most relevant files from {{ db_coupling.get('violations_by_file')|length }} total analyzed
        </p>
        {% endif %}
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Write Violations</th>
                    <th>Read Operations</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {% for file_violation in db_coupling.get('violations_by_file', []) %}
                <tr data-module="{{ file_violation.get('module', '') }}">
                    <td><code>{{ file_violation.get('file', '') | highlight_module }}</code></td>
                    <td>
                        {% if file_violation.get('write_count', 0) > 0 %}
                        <span class="badge badge-danger">{{ file_violation.get('write_count', 0) }}</span>
                        {% else %}
                        -
                        {% endif %}
                    </td>
                    <td>
                        {% if file_violation.get('read_count', 0) > 0 %}
                        <span class="badge badge-warning">{{ file_violation.get('read_count', 0) }}</span>
                        {% else %}
                        -
                        {% endif %}
                    </td>
                    <td><strong>{{ file_violation.get('total_count', 0) }}</strong></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% endif %}
    {% else %}
    <p>✅ No database coupling violations found!</p>
    {% endif %}
</section>
"""

    def _create_complexity_template(self) -> str:
        """Create complexity section template."""
        return """
<section id="complexity">
    <h2>📊 Code Complexity</h2>

    <div class="explanation-box">
        <h3>📚 What is cyclomatic complexity?</h3>
        <p>Cyclomatic complexity measures the number of independent paths through code.
        It counts decision points (if, for, while, etc.) to estimate code complexity.</p>
        <ul>
            <li><strong>1-5:</strong> Simple, easy to understand 🟢</li>
            <li><strong>6-10:</strong> Moderate complexity 🟡</li>
            <li><strong>11+:</strong> High complexity, consider refactoring 🔴</li>
        </ul>
        <p><strong>⚡ Why it matters:</strong> High complexity makes code harder to test, debug, and maintain.
        Functions with complexity >10 should be refactored into smaller, focused units.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'success' if complexity.get('avg_complexity', 0) < 6 else 'warning' if complexity.get('avg_complexity', 0) < 11 else 'danger' }}">
            <h4>Average Complexity</h4>
            <div class="metric-value">{{ "%.1f"|format(complexity.get('avg_complexity', 0)) }}</div>
            <div class="metric-label">Across all functions</div>
        </div>
        <div class="metric-card {{ 'danger' if complexity.get('high_complexity_count', 0) > 0 else 'success' }}">
            <h4>High Complexity</h4>
            <div class="metric-value">{{ complexity.get('high_complexity_count', 0) }}</div>
            <div class="metric-label">Functions with complexity > 10</div>
        </div>
        <div class="metric-card">
            <h4>Total Functions</h4>
            <div class="metric-value">{{ complexity.get('total_functions', 0) }}</div>
            <div class="metric-label">Analyzed</div>
        </div>
    </div>

    {% if complexity.get('high_complexity_files') %}
    <details open data-section="complexity">
        <summary>🔴 High Complexity Files ({{ complexity.get('high_complexity_count', 0) }})</summary>
        {% if max_items > 0 and complexity.get('high_complexity_files')|length > max_items %}
        <p style="margin: 10px 0; color: #666; font-size: 0.9em;">
            📌 Showing {{ max_items }} most relevant files from {{ complexity.get('high_complexity_files')|length }} total analyzed
        </p>
        {% endif %}
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Avg Complexity</th>
                    <th>Max Complexity</th>
                    <th>High Complexity Functions</th>
                </tr>
            </thead>
            <tbody>
                {% set files = complexity.get('high_complexity_files', [])[:max_items] if max_items > 0 else complexity.get('high_complexity_files', []) %}
                {% for file in files %}
                <tr data-module="{{ file.get('module', '') }}">
                    <td><code>{{ file.get('file', '') | highlight_module }}</code></td>
                    <td>
                        <span class="badge {{ 'badge-success' if file.get('avg_complexity', 0) < 6 else 'badge-warning' if file.get('avg_complexity', 0) < 11 else 'badge-danger' }}">
                            {{ "%.1f"|format(file.get('avg_complexity', 0)) }}
                        </span>
                    </td>
                    <td>
                        <span class="badge {{ 'badge-danger' if file.get('max_complexity', 0) > 15 else 'badge-warning' }}">
                            {{ file.get('max_complexity', 0) }}
                        </span>
                    </td>
                    <td>{{ file.get('high_complexity_count', 0) }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% else %}
    <p>✅ No high complexity files found!</p>
    {% endif %}
</section>
"""

    def _create_maintainability_template(self) -> str:
        """Create maintainability section template."""
        return """
<section id="maintainability">
    <h2>🔧 Maintainability Index</h2>

    <div class="explanation-box">
        <h3>📚 What is the Maintainability Index?</h3>
        <p>A score (0-100) that combines cyclomatic complexity, lines of code, and Halstead volume
        to estimate how maintainable code is. Higher scores mean easier maintenance.</p>
        <ul>
            <li><strong>85-100:</strong> Highly maintainable 🟢</li>
            <li><strong>65-84:</strong> Moderately maintainable 🟡</li>
            <li><strong>0-64:</strong> Difficult to maintain 🔴</li>
        </ul>
        <p><strong>⚡ Why it matters:</strong> Low maintainability means higher costs for changes,
        more bugs, and slower development velocity.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'success' if maintainability.get('avg_mi', 0) >= 65 else 'warning' if maintainability.get('avg_mi', 0) >= 50 else 'danger' }}">
            <h4>Average MI</h4>
            <div class="metric-value">{{ "%.1f"|format(maintainability.get('avg_mi', 0)) }}</div>
            <div class="metric-label">Out of 100</div>
        </div>
        <div class="metric-card {{ 'danger' if maintainability.get('low_maintainability_count', 0) > 0 else 'success' }}">
            <h4>Low Maintainability</h4>
            <div class="metric-value">{{ maintainability.get('low_maintainability_count', 0) }}</div>
            <div class="metric-label">Files with MI < 20</div>
        </div>
    </div>

    {% if maintainability.get('per_file') %}
    <details open data-section="maintainability">
        <summary>📁 Per-File Maintainability Index ({{ maintainability.get('per_file')|length }} files) - Worst First</summary>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>MI Score</th>
                    <th>Rank</th>
                </tr>
            </thead>
            <tbody>
                {% for file in maintainability.get('per_file', []) | sort(attribute='mi_score') %}
                <tr data-module="{{ file.get('module', '') }}">
                    <td><code>{{ file.get('file', '') | highlight_module }}</code></td>
                    <td>
                        <span class="badge {{ 'badge-success' if file.get('mi_score', 0) >= 65 else 'badge-warning' if file.get('mi_score', 0) >= 50 else 'badge-danger' }}">
                            {{ "%.1f"|format(file.get('mi_score', 0)) }}
                        </span>
                    </td>
                    <td>{{ file.get('rank', 'N/A') }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% elif maintainability.get('low_maintainability_files') %}
    <details open data-section="maintainability">
        <summary>🔴 Low Maintainability Files ({{ maintainability.get('low_maintainability_files')|length }})</summary>
        {% if max_items > 0 and maintainability.get('low_maintainability_files')|length > max_items %}
        <p style="margin: 10px 0; color: #666; font-size: 0.9em;">
            📌 Showing {{ max_items }} most relevant files from {{ maintainability.get('low_maintainability_files')|length }} total analyzed
        </p>
        {% endif %}
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>MI Score</th>
                </tr>
            </thead>
            <tbody>
                {% set files = maintainability.get('low_maintainability_files', [])[:max_items] if max_items > 0 else maintainability.get('low_maintainability_files', []) %}
                {% for file in files %}
                <tr data-module="{{ file.get('module', '') }}">
                    <td><code>{{ file.get('file', '') | highlight_module }}</code></td>
                    <td>
                        <span class="badge {{ 'badge-danger' if file.get('maintainability_index', 0) < 50 else 'badge-warning' }}">
                            {{ "%.1f"|format(file.get('maintainability_index', 0)) }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% else %}
    <p>✅ All files have good maintainability!</p>
    {% endif %}
</section>
"""

    def _create_code_size_template(self) -> str:
        """Create code size section template."""
        return """
<section id="code-size">
    <h2>📊 Code Size Metrics</h2>

    <div class="explanation-box">
        <h3>📚 What are code size metrics?</h3>
        <p>Code size metrics measure the volume of code in your codebase. They help identify
        files that may be too large and benefit from refactoring.</p>
        <ul>
            <li><strong>Lines of Code (LOC):</strong> Total non-blank, non-comment lines</li>
            <li><strong>Functions:</strong> Total number of functions/methods</li>
            <li><strong>Classes:</strong> Total number of classes</li>
        </ul>
        <p><strong>⚡ Why it matters:</strong> Larger files are harder to understand and maintain.
        Consider breaking files with >500 LOC into smaller modules.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card">
            <h4>Total Lines</h4>
            <div class="metric-value">{{ code_size.get('total_lines', 0) }}</div>
            <div class="metric-label">Lines of code</div>
        </div>
        <div class="metric-card">
            <h4>Total Functions</h4>
            <div class="metric-value">{{ code_size.get('total_functions', 0) }}</div>
            <div class="metric-label">Functions/methods</div>
        </div>
        <div class="metric-card">
            <h4>Total Classes</h4>
            <div class="metric-value">{{ code_size.get('total_classes', 0) }}</div>
            <div class="metric-label">Classes/types</div>
        </div>
        <div class="metric-card">
            <h4>Average File Size</h4>
            <div class="metric-value">{{ "%.0f"|format(code_size.get('avg_file_size', 0)) }}</div>
            <div class="metric-label">Lines per file</div>
        </div>
    </div>

    {% if code_size.get('per_file') %}
    <details open data-section="code-size">
        <summary>📁 Large Files ({{ code_size.large_files_threshold_count }} files > {{ code_size.large_files_threshold }} lines)</summary>
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Lines of Code</th>
                    <th>Functions</th>
                    <th>Classes</th>
                    <th>Comment Ratio</th>
                </tr>
            </thead>
            <tbody>
                {% for file in code_size.get('per_file', []) | selectattr('sloc', '>', code_size.large_files_threshold) | sort(attribute='sloc', reverse=true) %}
                <tr data-module="{{ file.get('module', '') }}">
                    <td><code>{{ file.get('file', '') | highlight_module }}</code></td>
                    <td>{{ file.get('sloc', 0) }}</td>
                    <td>{{ file.get('function_count', 0) }}</td>
                    <td>{{ file.get('class_count', 0) }}</td>
                    <td>{{ "%.1f"|format(file.get('comment_ratio', 0)) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
            </tbody>
        </table>
    </details>
    {% elif code_size.get('large_files') %}
    <details open data-section="code-size">
        <summary>📈 Largest Files ({{ code_size.get('large_files')|length }})</summary>
        {% if max_items > 0 and code_size.get('large_files')|length > max_items %}
        <p style="margin: 10px 0; color: #666; font-size: 0.9em;">
            📌 Showing {{ max_items }} largest files from {{ code_size.get('large_files')|length }} total analyzed
        </p>
        {% endif %}
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Lines</th>
                    <th>Comment Ratio</th>
                </tr>
            </thead>
            <tbody>
                {% for file in code_size.get('large_files', []) %}
                <tr data-module="{{ file.get('module', '') }}">
                    <td><code>{{ file.get('file', '') | highlight_module }}</code></td>
                    <td>{{ file.get('sloc', 0) }}</td>
                    <td>{{ "%.1f"|format(file.get('comment_ratio', 0)) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% else %}
    <p>✅ No code size data available.</p>
    {% endif %}
</section>
"""

    def _create_tests_template(self) -> str:
        """Create tests section template."""
        return """
<section id="tests">
    <h2>🧪 Test Analysis</h2>

    <div class="explanation-box">
        <h3>📚 What is test coverage?</h3>
        <p>Test coverage measures how much of your code is covered by automated tests.
        We analyze test files, categorize them (unit vs integration), and calculate function coverage.</p>
        <ul>
            <li><strong>Unit Tests:</strong> Pure, isolated tests with no external dependencies</li>
            <li><strong>Integration Tests:</strong> Tests that interact with databases, networks, filesystem, etc.</li>
            <li><strong>Function Coverage:</strong> Percentage of functions that have corresponding test_* functions</li>
        </ul>
        <p><strong>⚡ Why it matters:</strong> Higher test coverage with more unit tests correlates with fewer bugs
        and easier refactoring. Aim for >80% coverage with >70% unit tests.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card">
            <h4>Total Tests</h4>
            <div class="metric-value">{{ tests.total_test_functions or 0 }}</div>
            <div class="metric-label">{{ tests.test_file_count or 0 }} files</div>
        </div>
        <div class="metric-card {{ 'success' if tests.test_ratio.unit_percentage >= 70 else 'warning' if tests.test_ratio.unit_percentage >= 50 else 'danger' }}">
            <h4>Unit Tests</h4>
            <div class="metric-value">{{ tests.unit_test_functions or 0 }}</div>
            <div class="metric-label">{{ "%.1f"|format(tests.test_ratio.unit_percentage or 0) }}% of total</div>
        </div>
        <div class="metric-card {{ 'warning' if tests.integration_test_functions > tests.unit_test_functions else 'success' }}">
            <h4>Integration Tests</h4>
            <div class="metric-value">{{ tests.integration_test_functions or 0 }}</div>
            <div class="metric-label">{{ "%.1f"|format(tests.test_ratio.integration_percentage or 0) }}% of total</div>
        </div>
        <div class="metric-card {{ 'success' if tests.estimated_coverage >= 80 else 'warning' if tests.estimated_coverage >= 60 else 'danger' }}">
            <h4>Line Coverage (Est.)</h4>
            <div class="metric-value">{{ "%.1f"|format(tests.estimated_coverage or 0) }}%</div>
            <div class="metric-label">Based on test/code lines</div>
        </div>
    </div>

    {% if tests.edge_case_analysis %}
    <h3 style="margin-top: 40px;">⚡ Edge Case & Error Path Testing</h3>
    <div class="explanation-box">
        <h4>Why Edge Case Testing Matters</h4>
        <p><strong>Production systems rarely fail on happy paths.</strong> They fail when users enter unexpected input,
        systems encounter boundary conditions, or external dependencies behave incorrectly.</p>

        <p><strong>What is an edge case?</strong> Scenarios at the "edges" of normal operation:</p>
        <ul>
            <li><strong>Boundary values:</strong> 0, None, empty strings/arrays, maximum values</li>
            <li><strong>Error conditions:</strong> Invalid input, missing data, failed operations</li>
            <li><strong>Exception handling:</strong> Tests that verify errors are caught and handled gracefully</li>
            <li><strong>Regression tests:</strong> Tests for previously fixed bugs to ensure they don't return</li>
        </ul>

        <p><strong>🔴 The danger of happy path-only testing:</strong></p>
        <ul>
            <li>100% code coverage doesn't mean 100% scenario coverage</li>
            <li>Production failures occur in untested edge cases</li>
            <li>Fixing production bugs costs 10-100x more than catching them in tests</li>
            <li>Customer trust is damaged when "it worked in testing" doesn't prevent failures</li>
        </ul>

        <p><strong>Recommended target:</strong> ≥30% of tests should cover edge cases and error conditions.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'success' if tests.edge_case_analysis.edge_case_percentage >= 30 else 'warning' if tests.edge_case_analysis.edge_case_percentage >= 15 else 'danger' }}">
            <h4>Edge Case Coverage</h4>
            <div class="metric-value">{{ "%.1f"|format(tests.edge_case_analysis.edge_case_percentage or 0) }}%</div>
            <div class="metric-label">Of total tests</div>
        </div>
        <div class="metric-card {{ 'success' if tests.edge_case_analysis.total_edge_case_tests > 0 else 'danger' }}">
            <h4>Edge Case Tests</h4>
            <div class="metric-value">{{ tests.edge_case_analysis.total_edge_case_tests or 0 }}</div>
            <div class="metric-label">Exception, boundary, error tests</div>
        </div>
        <div class="metric-card {{ 'warning' if tests.edge_case_analysis.total_happy_path_tests > tests.edge_case_analysis.total_edge_case_tests * 2 else 'success' }}">
            <h4>Happy Path Tests</h4>
            <div class="metric-value">{{ tests.edge_case_analysis.total_happy_path_tests or 0 }}</div>
            <div class="metric-label">Expected scenario tests</div>
        </div>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'success' if tests.edge_case_analysis.exception_handling_tests > 0 else 'warning' }}">
            <h4>Exception Handling</h4>
            <div class="metric-value">{{ tests.edge_case_analysis.exception_handling_tests or 0 }}</div>
            <div class="metric-label">Tests with pytest.raises or assertRaises</div>
        </div>
        <div class="metric-card {{ 'success' if tests.edge_case_analysis.boundary_value_tests > 0 else 'warning' }}">
            <h4>Boundary Values</h4>
            <div class="metric-value">{{ tests.edge_case_analysis.boundary_value_tests or 0 }}</div>
            <div class="metric-label">Tests with 0, None, empty, max values</div>
        </div>
        <div class="metric-card {{ 'success' if tests.edge_case_analysis.error_condition_tests > 0 else 'warning' }}">
            <h4>Error Conditions</h4>
            <div class="metric-value">{{ tests.edge_case_analysis.error_condition_tests or 0 }}</div>
            <div class="metric-label">Tests for invalid/wrong/missing input</div>
        </div>
        <div class="metric-card {{ 'success' if tests.edge_case_analysis.regression_tests > 0 else 'info' }}">
            <h4>Regression Tests</h4>
            <div class="metric-value">{{ tests.edge_case_analysis.regression_tests or 0 }}</div>
            <div class="metric-label">Tests for previously fixed bugs</div>
        </div>
    </div>

    {% if tests.edge_case_analysis.edge_case_details %}
    <details>
        <summary>✅ Edge Case Tests Detected ({{ tests.edge_case_analysis.edge_case_details|length }})</summary>
        <table>
            <thead>
                <tr>
                    <th>Test Function</th>
                    <th>Module</th>
                    <th>File</th>
                    <th>Line</th>
                    <th>Patterns Detected</th>
                    <th>Boundary Values</th>
                </tr>
            </thead>
            <tbody>
                {% for edge_test in tests.edge_case_analysis.edge_case_details %}
                <tr data-module="{{ edge_test.get('module', '') }}">
                    <td><code>{{ edge_test.function }}</code></td>
                    <td><code>{{ edge_test.module }}</code></td>
                    <td><code>{{ edge_test.file | highlight_module }}</code></td>
                    <td>{{ edge_test.line }}</td>
                    <td>
                        {% for pattern in edge_test.patterns %}
                        <span class="badge badge-info">{{ pattern.replace('_', ' ').title() }}</span>
                        {% endfor %}
                    </td>
                    <td>
                        {% if edge_test.boundary_values %}
                            {{ edge_test.boundary_values | join(', ') }}
                        {% else %}
                            -
                        {% endif %}
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% endif %}
    {% endif %}

    {% if tests.by_module %}
    <details open>
        <summary>📊 Test Analysis by Module</summary>
        <table>
            <thead>
                <tr>
                    <th>Module</th>
                    <th>Test Files</th>
                    <th>Unit Tests</th>
                    <th>Integration Tests</th>
                    <th>Edge Cases</th>
                    <th>Edge %</th>
                    <th>Total Tests</th>
                    <th>Unit %</th>
                </tr>
            </thead>
            <tbody>
                {% for module_name, module_data in tests.by_module.items() %}
                {% set total_tests = module_data.get('unit_tests', 0) + module_data.get('integration_tests', 0) %}
                {% set unit_pct = (module_data.get('unit_tests', 0) / total_tests * 100) if total_tests > 0 else 0 %}
                <tr>
                    <td><code>{{ module_name }}</code></td>
                    <td>{{ module_data.get('test_files', 0) }}</td>
                    <td>{{ module_data.get('unit_tests', 0) }}</td>
                    <td>{{ module_data.get('integration_tests', 0) }}</td>
                    <td>{{ module_data.get('edge_case_tests', 0) }}</td>
                    <td>
                        <span class="badge {{ 'badge-success' if module_data.get('edge_case_percentage', 0) >= 30 else 'badge-warning' if module_data.get('edge_case_percentage', 0) >= 15 else 'badge-danger' }}">
                            {{ "%.0f"|format(module_data.get('edge_case_percentage', 0)) }}%
                        </span>
                    </td>
                    <td><strong>{{ total_tests }}</strong></td>
                    <td>
                        <span class="badge {{ 'badge-success' if unit_pct >= 70 else 'badge-warning' if unit_pct >= 50 else 'badge-danger' }}">
                            {{ "%.0f"|format(unit_pct) }}%
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% endif %}

    {% if tests.testability %}
    <h3 style="margin-top: 40px;">Code Testability Analysis</h3>
    <div class="explanation-box">
        <p>Testability measures how easy your code is to test. Functions that mix business logic with direct database access are hard to test in isolation.</p>
        <p><strong>Best Practice:</strong> Separate business logic from data access using repository/DAO patterns.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'success' if tests.testability.testability_score >= 80 else 'warning' if tests.testability.testability_score >= 60 else 'danger' }}">
            <h4>Testability Score</h4>
            <div class="metric-value">{{ "%.1f"|format(tests.testability.testability_score or 0) }}%</div>
            <div class="metric-label">Business logic functions that are testable</div>
        </div>
        <div class="metric-card">
            <h4>Business Logic Functions</h4>
            <div class="metric-value">{{ tests.testability.functions_with_business_logic or 0 }}</div>
            <div class="metric-label">Total with control flow/operations</div>
        </div>
        <div class="metric-card {{ 'danger' if tests.testability.functions_mixing_both > 0 else 'success' }}">
            <h4>Untestable Functions</h4>
            <div class="metric-value">{{ tests.testability.functions_mixing_both or 0 }}</div>
            <div class="metric-label">Mixing business logic + DB access</div>
        </div>
    </div>

    {% if tests.testability.untestable_functions %}
    <details>
        <summary>⚠️ Untestable Functions ({{ tests.testability.untestable_functions|length }})</summary>
        <table>
            <thead>
                <tr>
                    <th>Function</th>
                    <th>Module</th>
                    <th>File</th>
                    <th>Line</th>
                    <th>Reason</th>
                </tr>
            </thead>
            <tbody>
                {% for func in tests.testability.untestable_functions %}
                <tr data-module="{{ func.get('module', '') }}">
                    <td><code>{{ func.function }}</code></td>
                    <td><code>{{ func.module }}</code></td>
                    <td><code>{{ func.file | highlight_module }}</code></td>
                    <td>{{ func.line }}</td>
                    <td>{{ func.reason.replace('_', ' ').title() }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% endif %}
    {% endif %}

    {% if tests.test_files %}
    <details style="margin-top: 30px;">
        <summary>📝 Test Files ({{ tests.test_file_count or 0 }})</summary>
        <table>
            <thead>
                <tr>
                    <th>Test File</th>
                    <th>Module</th>
                    <th>Type</th>
                    <th>Test Count</th>
                    <th>Lines</th>
                </tr>
            </thead>
            <tbody>
                {% for test_file in tests.test_details %}
                <tr data-module="{{ test_file.get('module', '') }}">
                    <td><code>{{ test_file.file | highlight_module }}</code></td>
                    <td><code>{{ test_file.module }}</code></td>
                    <td>
                        <span class="badge {{ 'badge-success' if test_file.type == 'unit' else 'badge-warning' }}">
                            {{ test_file.type }}
                        </span>
                    </td>
                    <td>{{ test_file.test_count }}</td>
                    <td>{{ test_file.lines }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% else %}
    <p>⚠️ No test files detected!</p>
    {% endif %}
</section>
"""

    def _create_code_smells_template(self) -> str:
        """Create code smells section template."""
        return """
<section id="code-smells">
    <h2>👃 Code Smells</h2>

    <div class="explanation-box">
        <h3>📚 What are code smells?</h3>
        <p>Code smells are indicators of potential problems in code structure. They're not bugs,
        but suggest areas that may benefit from refactoring.</p>
        <ul>
            <li><strong>Long files:</strong> Files with >500 lines may have too many responsibilities</li>
            <li><strong>Complex classes:</strong> Classes with high complexity or many methods</li>
            <li><strong>Deep nesting:</strong> Code with excessive indentation levels</li>
        </ul>
        <p><strong>⚡ Why it matters:</strong> Code smells make code harder to understand and maintain.
        Addressing them early prevents technical debt accumulation.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'danger' if code_smells.long_files_count > 0 else 'success' }}">
            <h4>Long Files</h4>
            <div class="metric-value">{{ code_smells.long_files_count or 0 }}</div>
            <div class="metric-label">Files > 500 lines</div>
        </div>
        <div class="metric-card {{ 'danger' if code_smells.complex_classes_count > 0 else 'success' }}">
            <h4>Complex Classes</h4>
            <div class="metric-value">{{ code_smells.complex_classes_count or 0 }}</div>
            <div class="metric-label">High complexity classes</div>
        </div>
    </div>

    {% if code_smells.long_files %}
    <details open data-section="code-smells">
        <summary>📏 Long Files ({{ code_smells.long_files_count or 0 }})</summary>
        {% if max_items > 0 and code_smells.long_files|length > max_items %}
        <p style="margin: 10px 0; color: #666; font-size: 0.9em;">
            📌 Showing {{ max_items }} most relevant files from {{ code_smells.long_files|length }} total analyzed
        </p>
        {% endif %}
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Lines</th>
                    <th>Functions</th>
                </tr>
            </thead>
            <tbody>
                {% set files = code_smells.long_files[:max_items] if max_items > 0 else code_smells.long_files %}
                {% for file in files %}
                <tr data-module="{{ file.get('module', '') }}">
                    <td><code>{{ file.file | highlight_module }}</code></td>
                    <td>
                        <span class="badge {{ 'badge-danger' if file.lines > 1000 else 'badge-warning' }}">
                            {{ file.lines }}
                        </span>
                    </td>
                    <td>{{ file.functions }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% endif %}

    {% if code_smells.complex_classes %}
    <details>
        <summary>🏗️ Complex Classes ({{ code_smells.complex_classes_count or 0 }})</summary>
        {% if max_items > 0 and code_smells.complex_classes|length > max_items %}
        <p style="margin: 10px 0; color: #666; font-size: 0.9em;">
            📌 Showing {{ max_items }} most relevant classes from {{ code_smells.complex_classes|length }} total analyzed
        </p>
        {% endif %}
        <table>
            <thead>
                <tr>
                    <th>Class</th>
                    <th>File</th>
                    <th>Methods</th>
                    <th>Avg Complexity</th>
                </tr>
            </thead>
            <tbody>
                {% set classes = code_smells.complex_classes[:max_items] if max_items > 0 else code_smells.complex_classes %}
                {% for cls in classes %}
                <tr>
                    <td><code>{{ cls.class_name }}</code></td>
                    <td><code>{{ cls.file | highlight_module }}</code></td>
                    <td>{{ cls.method_count }}</td>
                    <td>
                        <span class="badge {{ 'badge-danger' if cls.avg_complexity > 10 else 'badge-warning' }}">
                            {{ "%.1f"|format(cls.avg_complexity) }}
                        </span>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% endif %}

    {% if not code_smells.long_files and not code_smells.complex_classes %}
    <p>✅ No significant code smells detected!</p>
    {% endif %}
</section>
"""

    def _create_technical_debt_template(self) -> str:
        """Create technical debt section template."""
        return """
<section id="technical-debt">
    <h2>💰 Technical Debt</h2>

    <div class="explanation-box">
        <h3>📚 What is technical debt?</h3>
        <p>Technical debt represents the cost of additional work caused by choosing quick solutions
        over better approaches. We calculate debt using the SQALE methodology.</p>
        <ul>
            <li><strong>Debt Ratio:</strong> Technical debt / development cost (lower is better)</li>
            <li><strong>SQALE Rating:</strong> A (≤5%), B (6-10%), C (11-20%), D (21-50%), E (>50%)</li>
            <li><strong>Remediation Time:</strong> Estimated hours to fix all issues</li>
        </ul>
        <p><strong>⚡ Why it matters:</strong> Unchecked technical debt slows development,
        increases bugs, and makes changes increasingly expensive over time.</p>
    </div>

    <div class="metric-cards">
        <div class="metric-card {{ 'success' if technical_debt.sqale_rating in ['A', 'B'] else 'warning' if technical_debt.sqale_rating == 'C' else 'danger' }}">
            <h4>SQALE Rating</h4>
            <div class="metric-value">{{ technical_debt.sqale_rating or 'N/A' }}</div>
            <div class="metric-label">Overall code quality</div>
        </div>
        <div class="metric-card {{ 'success' if technical_debt.debt_ratio <= 5 else 'warning' if technical_debt.debt_ratio <= 10 else 'danger' }}">
            <h4>Debt Ratio</h4>
            <div class="metric-value">{{ "%.1f"|format(technical_debt.debt_ratio or 0) }}%</div>
            <div class="metric-label">Debt vs development cost</div>
        </div>
        <div class="metric-card">
            <h4>Remediation Time</h4>
            <div class="metric-value">{{ "%.1f"|format(technical_debt.total_remediation_hours or 0) }}</div>
            <div class="metric-label">Hours to fix</div>
        </div>
    </div>

    {% if technical_debt.by_category %}
    <h3>Debt by Category</h3>
    <table>
        <thead>
            <tr>
                <th>Category</th>
                <th>Issues</th>
                <th>Remediation Time</th>
                <th>% of Total</th>
            </tr>
        </thead>
        <tbody>
            {% for category, data in technical_debt.by_category.items() %}
            <tr>
                <td><strong>{{ category }}</strong></td>
                <td>{{ data.count }}</td>
                <td>{{ "%.1f"|format(data.hours) }} hours</td>
                <td>{{ "%.1f"|format(data.percentage) }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    {% if technical_debt.by_module_list %}
    <h3>Debt by Module</h3>
    <table>
        <thead>
            <tr>
                <th>Module</th>
                <th>SQALE Rating</th>
                <th>Debt Hours</th>
                <th>Debt Ratio</th>
                <th>Lines of Code</th>
            </tr>
        </thead>
        <tbody>
            {% for module in technical_debt.by_module_list %}
            <tr>
                <td><code>{{ module.module }}</code></td>
                <td>
                    <span class="badge {{ 'badge-success' if module.sqale_rating in ['A', 'B'] else 'badge-warning' if module.sqale_rating == 'C' else 'badge-danger' }}">
                        {{ module.sqale_rating }}
                    </span>
                </td>
                <td>{{ "%.1f"|format(module.debt_hours) }}</td>
                <td>{{ "%.1f"|format(module.debt_ratio) }}%</td>
                <td>{{ module.sloc }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% endif %}

    {% if technical_debt.top_debt_files %}
    <details open data-section="technical-debt">
        <summary>📊 Top Debt Files</summary>
        {% if max_items > 0 and technical_debt.top_debt_files|length > max_items %}
        <p style="margin: 10px 0; color: #666; font-size: 0.9em;">
            📌 Showing {{ max_items }} files with highest debt from {{ technical_debt.top_debt_files|length }} total analyzed
        </p>
        {% endif %}
        <table>
            <thead>
                <tr>
                    <th>File</th>
                    <th>Debt (hours)</th>
                    <th>Issues</th>
                </tr>
            </thead>
            <tbody>
                {% set files = technical_debt.top_debt_files[:max_items] if max_items > 0 else technical_debt.top_debt_files %}
                {% for file in files %}
                <tr data-module="{{ file.get('module', '') }}">
                    <td><code>{{ file.file | highlight_module }}</code></td>
                    <td>
                        <span class="badge {{ 'badge-danger' if file.debt_hours > 5 else 'badge-warning' if file.debt_hours > 2 else 'badge-success' }}">
                            {{ "%.1f"|format(file.debt_hours) }}
                        </span>
                    </td>
                    <td>{{ file.issue_count }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </details>
    {% endif %}
</section>
"""

    def generate_to_stdout(self) -> None:
        """Print HTML report to stdout."""
        print(self.get_html_string())
