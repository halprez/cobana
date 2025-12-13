"""Technical Debt Calculator

Calculates technical debt based on remediation costs and assigns SQALE ratings.
"""

from typing import Any
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TechnicalDebtCalculator:
    """Calculates technical debt metrics from analyzer results."""

    def __init__(self, config: dict[str, Any]):
        """Initialize calculator.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.remediation_costs = config.get('remediation_costs', {})
        self.avg_hours_per_loc = 0.1  # Industry standard

        # Results storage
        self.results: dict[str, Any] = {
            'total_remediation_hours': 0.0,
            'total_remediation_days': 0.0,
            'development_cost_hours': 0.0,
            'debt_ratio': 0.0,
            'sqale_rating': 'A',
            'debt_breakdown': {},
            'by_module': defaultdict(lambda: {
                'debt_hours': 0.0,
                'debt_ratio': 0.0,
                'sqale_rating': 'A',
                'sloc': 0,
            }),
            'top_debt_files': [],
            'issue_costs': defaultdict(lambda: {'count': 0, 'total_hours': 0.0}),
        }

    def calculate(
        self,
        complexity_results: dict[str, Any],
        maintainability_results: dict[str, Any],
        code_size_results: dict[str, Any],
        db_coupling_results: dict[str, Any],
        class_metrics_results: dict[str, Any],
        code_smells_results: dict[str, Any],
    ) -> dict[str, Any]:
        """Calculate technical debt from all analyzer results.

        Args:
            complexity_results: Results from complexity analyzer
            maintainability_results: Results from maintainability analyzer
            code_size_results: Results from code size analyzer
            db_coupling_results: Results from DB coupling analyzer
            class_metrics_results: Results from class metrics analyzer
            code_smells_results: Results from code smells analyzer

        Returns:
            Technical debt analysis results
        """
        # Calculate development cost
        total_sloc = code_size_results.get('total_sloc', 0)
        self.results['development_cost_hours'] = total_sloc * self.avg_hours_per_loc

        # Calculate remediation costs for each issue type
        self._calculate_complexity_debt(complexity_results)
        self._calculate_maintainability_debt(maintainability_results)
        self._calculate_db_coupling_debt(db_coupling_results)
        self._calculate_class_debt(class_metrics_results)
        self._calculate_smells_debt(code_smells_results)

        # Calculate module-level debt
        self._calculate_module_debt(
            code_size_results,
            complexity_results,
            maintainability_results,
            db_coupling_results,
            class_metrics_results,
            code_smells_results,
        )

        # Calculate total debt and ratios
        self._finalize_debt_calculations()

        return self.results

    def _calculate_complexity_debt(self, results: dict[str, Any]) -> None:
        """Calculate debt from complexity issues."""
        high_complexity = results.get('high_complexity_functions', [])

        for func in high_complexity:
            complexity = func.get('complexity', 0)

            if complexity > 20:
                issue_type = 'very_high_complexity'
            else:
                issue_type = 'high_complexity'

            cost = self.remediation_costs.get(issue_type, 0.5)
            self._add_debt(issue_type, cost)

        self.results['debt_breakdown']['complexity'] = sum(
            self.results['issue_costs'][k]['total_hours']
            for k in ['very_high_complexity', 'high_complexity']
        )

    def _calculate_maintainability_debt(self, results: dict[str, Any]) -> None:
        """Calculate debt from maintainability issues."""
        low_mi_files = results.get('low_maintainability_files', [])

        for _ in low_mi_files:
            cost = self.remediation_costs.get('low_maintainability', 2.0)
            self._add_debt('low_maintainability', cost)

        self.results['debt_breakdown']['maintainability'] = (
            self.results['issue_costs']['low_maintainability']['total_hours']
        )

    def _calculate_db_coupling_debt(self, results: dict[str, Any]) -> None:
        """Calculate debt from database coupling issues."""
        violations = results.get('violations', [])

        for violation in violations:
            if violation.get('type') == 'write':
                issue_type = 'ownership_violation_write'
            else:
                issue_type = 'ownership_violation_read'

            cost = self.remediation_costs.get(issue_type, 1.0)
            self._add_debt(issue_type, cost)

        self.results['debt_breakdown']['db_coupling'] = sum(
            self.results['issue_costs'][k]['total_hours']
            for k in ['ownership_violation_write', 'ownership_violation_read']
        )

    def _calculate_class_debt(self, results: dict[str, Any]) -> None:
        """Calculate debt from class metric issues."""
        god_classes = results.get('god_classes', [])
        low_cohesion = results.get('low_cohesion_classes', [])

        for _ in god_classes:
            cost = self.remediation_costs.get('god_class', 4.0)
            self._add_debt('god_class', cost)

        for _ in low_cohesion:
            cost = self.remediation_costs.get('low_cohesion', 3.0)
            self._add_debt('low_cohesion', cost)

        self.results['debt_breakdown']['class_design'] = sum(
            self.results['issue_costs'][k]['total_hours']
            for k in ['god_class', 'low_cohesion']
        )

    def _calculate_smells_debt(self, results: dict[str, Any]) -> None:
        """Calculate debt from code smells."""
        long_methods = results.get('long_methods', [])
        long_params = results.get('long_parameter_lists', [])
        deep_nesting = results.get('deep_nesting', [])

        for _ in long_methods:
            cost = self.remediation_costs.get('long_method', 0.5)
            self._add_debt('long_method', cost)

        for _ in long_params:
            cost = self.remediation_costs.get('long_parameter_list', 0.25)
            self._add_debt('long_parameter_list', cost)

        for _ in deep_nesting:
            cost = self.remediation_costs.get('deep_nesting', 0.5)
            self._add_debt('deep_nesting', cost)

        self.results['debt_breakdown']['code_smells'] = sum(
            self.results['issue_costs'][k]['total_hours']
            for k in ['long_method', 'long_parameter_list', 'deep_nesting']
        )

    def _add_debt(self, issue_type: str, hours: float) -> None:
        """Add debt for an issue.

        Args:
            issue_type: Type of issue
            hours: Hours of remediation cost
        """
        self.results['total_remediation_hours'] += hours
        self.results['issue_costs'][issue_type]['count'] += 1
        self.results['issue_costs'][issue_type]['total_hours'] += hours

    def _calculate_module_debt(
        self,
        code_size_results: dict[str, Any],
        complexity_results: dict[str, Any],
        maintainability_results: dict[str, Any],
        db_coupling_results: dict[str, Any],
        class_metrics_results: dict[str, Any],
        code_smells_results: dict[str, Any],
    ) -> None:
        """Calculate debt per module."""
        # Get module SLOC
        module_sloc = code_size_results.get('by_module', {})

        # Initialize module debt from SLOC
        for module_name, module_stats in module_sloc.items():
            sloc = module_stats.get('total_sloc', 0)
            self.results['by_module'][module_name]['sloc'] = sloc

        # Add debt from each analyzer
        for module_name in self.results['by_module'].keys():
            module_debt = 0.0

            # Complexity debt
            complexity_by_module = complexity_results.get('by_module', {})
            if module_name in complexity_by_module:
                high_count = complexity_by_module[module_name].get('high_complexity_count', 0)
                module_debt += high_count * self.remediation_costs.get('high_complexity', 0.5)

            # Maintainability debt
            mi_by_module = maintainability_results.get('by_module', {})
            if module_name in mi_by_module:
                low_mi_count = mi_by_module[module_name].get('low_mi_count', 0)
                module_debt += low_mi_count * self.remediation_costs.get('low_maintainability', 2.0)

            # DB coupling debt
            db_by_module = db_coupling_results.get('by_module', {})
            if module_name in db_by_module:
                write_violations = db_by_module[module_name].get('violations_write', 0)
                read_violations = db_by_module[module_name].get('violations_read', 0)
                module_debt += write_violations * self.remediation_costs.get('ownership_violation_write', 2.0)
                module_debt += read_violations * self.remediation_costs.get('ownership_violation_read', 0.5)

            # Class debt
            class_by_module = class_metrics_results.get('by_module', {})
            if module_name in class_by_module:
                god_classes = class_by_module[module_name].get('god_classes_count', 0)
                module_debt += god_classes * self.remediation_costs.get('god_class', 4.0)

            # Smells debt
            smells_by_module = code_smells_results.get('by_module', {})
            if module_name in smells_by_module:
                smells = smells_by_module[module_name]
                module_debt += smells.get('long_methods', 0) * self.remediation_costs.get('long_method', 0.5)
                module_debt += smells.get('long_parameter_lists', 0) * self.remediation_costs.get('long_parameter_list', 0.25)
                module_debt += smells.get('deep_nesting', 0) * self.remediation_costs.get('deep_nesting', 0.5)

            self.results['by_module'][module_name]['debt_hours'] = module_debt

            # Calculate module debt ratio
            sloc = self.results['by_module'][module_name]['sloc']
            if sloc > 0:
                module_dev_cost = sloc * self.avg_hours_per_loc
                module_debt_ratio = (module_debt / module_dev_cost) * 100
                self.results['by_module'][module_name]['debt_ratio'] = module_debt_ratio
                self.results['by_module'][module_name]['sqale_rating'] = self._get_sqale_rating(module_debt_ratio)

    def _finalize_debt_calculations(self) -> None:
        """Finalize debt calculations."""
        # Calculate total remediation days
        self.results['total_remediation_days'] = self.results['total_remediation_hours'] / 8

        # Calculate overall debt ratio
        if self.results['development_cost_hours'] > 0:
            self.results['debt_ratio'] = (
                self.results['total_remediation_hours'] /
                self.results['development_cost_hours']
            ) * 100
        else:
            self.results['debt_ratio'] = 0.0

        # Assign SQALE rating
        self.results['sqale_rating'] = self._get_sqale_rating(self.results['debt_ratio'])

        # Convert issue_costs from defaultdict to regular dict
        self.results['issue_costs'] = dict(self.results['issue_costs'])

        # Convert by_module from defaultdict to regular dict
        self.results['by_module'] = dict(self.results['by_module'])

    def _get_sqale_rating(self, debt_ratio: float) -> str:
        """Get SQALE rating based on debt ratio.

        Args:
            debt_ratio: Debt ratio percentage

        Returns:
            SQALE rating (A-E)
        """
        match debt_ratio:
            case r if r <= 5:
                return 'A'
            case r if r <= 10:
                return 'B'
            case r if r <= 20:
                return 'C'
            case r if r <= 50:
                return 'D'
            case _:
                return 'E'

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        return {
            'total_remediation_hours': round(self.results['total_remediation_hours'], 1),
            'total_remediation_days': round(self.results['total_remediation_days'], 1),
            'debt_ratio': round(self.results['debt_ratio'], 2),
            'sqale_rating': self.results['sqale_rating'],
        }
