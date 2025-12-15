"""Module Health Score Calculator

Calculates composite health scores for modules based on all metrics.
"""

from typing import Any
import logging

logger = logging.getLogger(__name__)


class ModuleHealthCalculator:
    """Calculates module health scores from all analyzer results."""

    # Weights for each metric in the health score
    WEIGHTS = {
        "coupling": 0.30,  # Database coupling (highest priority)
        "complexity": 0.20,  # Code complexity
        "maintainability": 0.20,  # Maintainability index
        "testability": 0.15,  # Test coverage and testability
        "smells": 0.10,  # Code smells
        "debt": 0.05,  # Technical debt ratio
    }

    def __init__(self, config: dict[str, Any]):
        """Initialize calculator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.results: dict[str, Any] = {
            "overall_health": 0.0,
            "by_module": {},
            "module_rankings": [],
        }

    def calculate(
        self,
        modules: list[str],
        db_coupling_results: dict[str, Any],
        complexity_results: dict[str, Any],
        maintainability_results: dict[str, Any],
        test_results: dict[str, Any],
        code_smells_results: dict[str, Any],
        tech_debt_results: dict[str, Any],
        code_size_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate health scores for all modules.

        Args:
            modules: List of module names
            db_coupling_results: Database coupling results
            complexity_results: Complexity results
            maintainability_results: Maintainability results
            test_results: Test analysis results
            code_smells_results: Code smells results
            tech_debt_results: Technical debt results
            code_size_results: Code size results

        Returns:
            Health score analysis results
        """
        total_health = 0.0
        module_count = 0

        for module_name in modules:
            # Skip if module has no files
            module_sloc = (
                code_size_results.get("by_module", {})
                .get(module_name, {})
                .get("total_sloc", 0)
            )
            if module_sloc == 0:
                continue

            health = self._calculate_module_health(
                module_name,
                db_coupling_results,
                complexity_results,
                maintainability_results,
                test_results,
                code_smells_results,
                tech_debt_results,
                code_size_results,
            )

            self.results["by_module"][module_name] = health
            total_health += health["score"]
            module_count += 1

        # Calculate overall health
        if module_count > 0:
            self.results["overall_health"] = total_health / module_count

        # Create module rankings
        self._create_rankings()

        return self.results

    def _calculate_module_health(
        self,
        module_name: str,
        db_coupling_results: dict[str, Any],
        complexity_results: dict[str, Any],
        maintainability_results: dict[str, Any],
        test_results: dict[str, Any],
        code_smells_results: dict[str, Any],
        tech_debt_results: dict[str, Any],
        code_size_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate health score for a single module.

        Args:
            module_name: Name of module
            (other args): Results from all analyzers

        Returns:
            Health score dictionary
        """
        # Normalize each metric to 0-100 scale
        coupling_score = self._normalize_coupling(
            db_coupling_results.get("by_module", {}).get(module_name, {})
        )

        complexity_score = self._normalize_complexity(
            complexity_results.get("by_module", {}).get(module_name, {})
        )

        maintainability_score = (
            maintainability_results.get("by_module", {})
            .get(module_name, {})
            .get("avg_mi", 50.0)
        )  # Already 0-100 scale

        # Use unit test percentage as testability score
        # Higher % of unit tests = better testability
        test_module_data = test_results.get("by_module", {}).get(module_name, {})
        unit_tests = test_module_data.get("unit_tests", 0)
        integration_tests = test_module_data.get("integration_tests", 0)
        total_tests = unit_tests + integration_tests

        if total_tests > 0:
            testability_score = (unit_tests / total_tests) * 100
        else:
            testability_score = 0.0  # No tests = lowest score

        smells_score = self._normalize_smells(
            code_smells_results.get("by_module", {}).get(module_name, {}),
            code_size_results.get("by_module", {}).get(module_name, {}),
        )

        debt_score = self._normalize_debt(
            tech_debt_results.get("by_module", {}).get(module_name, {})
        )

        # Calculate weighted health score
        health_score = (
            coupling_score * self.WEIGHTS["coupling"]
            + complexity_score * self.WEIGHTS["complexity"]
            + maintainability_score * self.WEIGHTS["maintainability"]
            + testability_score * self.WEIGHTS["testability"]
            + smells_score * self.WEIGHTS["smells"]
            + debt_score * self.WEIGHTS["debt"]
        )

        # Categorize health
        category = self._categorize_health(health_score)

        # Get actual metrics for display
        complexity_data = complexity_results.get("by_module", {}).get(module_name, {})
        maintainability_data = maintainability_results.get("by_module", {}).get(module_name, {})
        test_data = test_results.get("by_module", {}).get(module_name, {})
        code_size_data = code_size_results.get("by_module", {}).get(module_name, {})

        return {
            "module": module_name,
            "score": health_score,
            "category": category,
            "components": {
                "coupling": coupling_score,
                "complexity": complexity_score,
                "maintainability": maintainability_score,
                "testability": testability_score,
                "smells": smells_score,
                "debt": debt_score,
            },
            # Add actual metrics for display in module overview
            "file_count": code_size_data.get("file_count", 0),
            "avg_complexity": complexity_data.get("avg_complexity", 0),
            "avg_maintainability": maintainability_data.get("avg_mi", 0),
            "test_coverage": testability_score,  # Unit test percentage
        }

    def _normalize_coupling(self, module_stats: dict[str, Any]) -> float:
        """Normalize coupling score to 0-100 (100 = best).

        Lower severity is better.

        Args:
            module_stats: Module coupling statistics

        Returns:
            Normalized score
        """
        severity = module_stats.get("severity_score", 0)

        # Severity can range widely. Use log scale.
        # No violations = 100, increasing violations decrease score
        if severity == 0:
            return 100.0

        # Penalize severely: each point of severity reduces score
        # Cap at reasonable values
        score = max(0, 100 - (severity * 2))
        return score

    def _normalize_complexity(self, module_stats: dict[str, Any]) -> float:
        """Normalize complexity score to 0-100 (100 = best).

        Lower complexity is better.

        Args:
            module_stats: Module complexity statistics

        Returns:
            Normalized score
        """
        avg_complexity = module_stats.get("avg_complexity", 5.0)

        # Complexity 1-5 = excellent (100-80)
        # Complexity 6-10 = good (80-60)
        # Complexity 11-20 = moderate (60-20)
        # Complexity 21+ = poor (20-0)

        match avg_complexity:
            case c if c <= 5:
                return 100 - (c - 1) * 5  # 100-80
            case c if c <= 10:
                return 80 - (c - 5) * 4  # 80-60
            case c if c <= 20:
                return 60 - (c - 10) * 4  # 60-20
            case _:
                return max(0, 20 - (avg_complexity - 20))

    def _normalize_smells(
        self, smell_stats: dict[str, Any], size_stats: dict[str, Any]
    ) -> float:
        """Normalize code smells score to 0-100 (100 = best).

        Fewer smells per SLOC is better.

        Args:
            smell_stats: Code smell statistics
            size_stats: Code size statistics

        Returns:
            Normalized score
        """
        total_smells = smell_stats.get("total_smells", 0)
        sloc = size_stats.get("total_sloc", 1)

        # Calculate smells per 1000 lines
        smells_per_kloc = (total_smells / sloc) * 1000 if sloc > 0 else 0

        # 0 smells = 100
        # 1 smell per 1000 lines = 90
        # 5 smells per 1000 lines = 50
        # 10+ smells per 1000 lines = 0
        score = max(0, 100 - (smells_per_kloc * 10))
        return score

    def _normalize_debt(self, debt_stats: dict[str, Any]) -> float:
        """Normalize debt score to 0-100 (100 = best).

        Lower debt ratio is better.

        Args:
            debt_stats: Technical debt statistics

        Returns:
            Normalized score
        """
        debt_ratio = debt_stats.get("debt_ratio", 0)

        # Map SQALE ratings to scores
        # A (≤5%) = 100-90
        # B (6-10%) = 90-80
        # C (11-20%) = 80-60
        # D (21-50%) = 60-20
        # E (>50%) = 20-0

        match debt_ratio:
            case r if r <= 5:
                return 100 - (r * 2)  # 100-90
            case r if r <= 10:
                return 90 - ((r - 5) * 2)  # 90-80
            case r if r <= 20:
                return 80 - ((r - 10) * 2)  # 80-60
            case r if r <= 50:
                return 60 - ((r - 20) * 1.33)  # 60-20
            case _:
                return max(0, 20 - ((debt_ratio - 50) * 0.4))

    def _categorize_health(self, score: float) -> str:
        """Categorize health score.

        Args:
            score: Health score

        Returns:
            Category string
        """
        match score:
            case s if s >= 80:
                return "excellent"
            case s if s >= 60:
                return "good"
            case s if s >= 40:
                return "warning"
            case s if s >= 20:
                return "critical"
            case _:
                return "emergency"

    def _create_rankings(self) -> None:
        """Create ranked list of modules by health (worst first)."""
        rankings = [
            {
                "module": module_name,
                "score": health["score"],
                "category": health["category"],
            }
            for module_name, health in self.results["by_module"].items()
        ]

        # Sort by score ascending (worst first)
        rankings.sort(key=lambda x: x["score"])

        self.results["module_rankings"] = rankings

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        if not self.results["module_rankings"]:
            return {
                "overall_health": 0.0,
                "best_module": None,
                "worst_module": None,
            }

        # Rankings are now worst first, so reverse indices
        worst = self.results["module_rankings"][0]
        best = self.results["module_rankings"][-1]

        return {
            "overall_health": round(self.results["overall_health"], 1),
            "best_module": best["module"],
            "best_score": round(best["score"], 1),
            "worst_module": worst["module"],
            "worst_score": round(worst["score"], 1),
        }
