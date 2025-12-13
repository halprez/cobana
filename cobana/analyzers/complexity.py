"""Complexity Analyzer

Analyzes cyclomatic complexity of functions using the Radon library.
"""

from pathlib import Path
from typing import Any
from collections import defaultdict
import logging

from radon.complexity import cc_visit
from cobana.utils.file_utils import read_file_safely

logger = logging.getLogger(__name__)


class ComplexityAnalyzer:
    """Analyzes cyclomatic complexity in Python codebases."""

    def __init__(self, config: dict[str, Any]):
        """Initialize analyzer.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.threshold = config.get('thresholds', {}).get('complexity', 10)

        # Results storage
        self.results: dict[str, Any] = {
            'total_functions': 0,
            'avg_complexity': 0.0,
            'max_complexity': 0,
            'max_complexity_function': None,
            'distribution': {
                'simple_1_5': 0,
                'moderate_6_10': 0,
                'complex_11_20': 0,
                'very_complex_21_plus': 0,
            },
            'by_module': defaultdict(lambda: {
                'total_functions': 0,
                'avg_complexity': 0.0,
                'max_complexity': 0,
                'high_complexity_count': 0,
                'complexity_sum': 0,
            }),
            'high_complexity_functions': [],
            'per_file': [],
        }

    def analyze_file(self, file_path: Path, module_name: str) -> dict[str, Any]:
        """Analyze complexity of a single file.

        Args:
            file_path: Path to file to analyze
            module_name: Module the file belongs to

        Returns:
            Dictionary with file analysis results
        """
        content = read_file_safely(file_path)
        if content is None:
            return {}

        try:
            # Use Radon to calculate complexity
            complexity_blocks = cc_visit(content)
        except Exception as e:
            logger.warning(f"Failed to analyze complexity in {file_path}: {e}")
            return {}

        if not complexity_blocks:
            return {}

        # Process complexity results
        file_results = self._process_complexity_blocks(
            complexity_blocks,
            file_path,
            module_name
        )

        # Update overall results
        self._update_results(file_results, module_name)

        return file_results

    def _process_complexity_blocks(
        self,
        blocks: list,
        file_path: Path,
        module_name: str
    ) -> dict[str, Any]:
        """Process complexity blocks from Radon.

        Args:
            blocks: List of complexity blocks from cc_visit()
            file_path: Path to file
            module_name: Module name

        Returns:
            Processed file results
        """
        functions = []
        complexity_sum = 0
        max_complexity = 0
        max_complexity_func = None

        for block in blocks:
            complexity = block.complexity
            complexity_sum += complexity

            if complexity > max_complexity:
                max_complexity = complexity
                max_complexity_func = block.name

            # Categorize complexity
            category = self._categorize_complexity(complexity)

            # Get class name (if this is a method)
            class_name = getattr(block, 'classname', None)

            func_info = {
                'name': block.name,
                'complexity': complexity,
                'category': category,
                'line': block.lineno,
                'is_method': class_name is not None,
                'class_name': class_name,
            }

            functions.append(func_info)

            # Track high complexity functions
            if complexity > self.threshold:
                self.results['high_complexity_functions'].append({
                    'function': block.name,
                    'module': module_name,
                    'file': str(file_path),
                    'line': block.lineno,
                    'complexity': complexity,
                    'category': category,
                    'class_name': class_name,
                })

        avg_complexity = complexity_sum / len(functions) if functions else 0.0

        return {
            'file': str(file_path),
            'module': module_name,
            'function_count': len(functions),
            'avg_complexity': avg_complexity,
            'max_complexity': max_complexity,
            'max_complexity_function': max_complexity_func,
            'functions': functions,
        }

    def _categorize_complexity(self, complexity: int) -> str:
        """Categorize complexity level.

        Args:
            complexity: Cyclomatic complexity value

        Returns:
            Category string
        """
        match complexity:
            case c if c <= 5:
                return 'simple'
            case c if c <= 10:
                return 'moderate'
            case c if c <= 20:
                return 'complex'
            case _:
                return 'very_complex'

    def _update_results(self, file_results: dict[str, Any], module_name: str) -> None:
        """Update overall results with file results.

        Args:
            file_results: Results from analyzing a single file
            module_name: Module the file belongs to
        """
        if not file_results.get('functions'):
            return

        # Update overall stats
        self.results['total_functions'] += file_results['function_count']

        # Track max complexity
        if file_results['max_complexity'] > self.results['max_complexity']:
            self.results['max_complexity'] = file_results['max_complexity']
            self.results['max_complexity_function'] = {
                'name': file_results['max_complexity_function'],
                'file': file_results['file'],
                'module': module_name,
                'complexity': file_results['max_complexity'],
            }

        # Update distribution
        for func in file_results['functions']:
            category = func['category']
            match category:
                case 'simple':
                    self.results['distribution']['simple_1_5'] += 1
                case 'moderate':
                    self.results['distribution']['moderate_6_10'] += 1
                case 'complex':
                    self.results['distribution']['complex_11_20'] += 1
                case 'very_complex':
                    self.results['distribution']['very_complex_21_plus'] += 1

        # Update module stats
        module_stats = self.results['by_module'][module_name]
        module_stats['total_functions'] += file_results['function_count']
        module_stats['complexity_sum'] += sum(f['complexity'] for f in file_results['functions'])

        if file_results['max_complexity'] > module_stats['max_complexity']:
            module_stats['max_complexity'] = file_results['max_complexity']

        module_stats['high_complexity_count'] += sum(
            1 for f in file_results['functions'] if f['complexity'] > self.threshold
        )

        # Add to per-file results
        self.results['per_file'].append({
            'file': file_results['file'],
            'module': module_name,
            'avg_complexity': file_results['avg_complexity'],
            'max_complexity': file_results['max_complexity'],
            'function_count': file_results['function_count'],
        })

    def finalize_results(self) -> dict[str, Any]:
        """Finalize and return analysis results.

        Returns:
            Complete analysis results
        """
        # Calculate average complexity
        if self.results['total_functions'] > 0:
            total_complexity = sum(
                module['complexity_sum']
                for module in self.results['by_module'].values()
            )
            self.results['avg_complexity'] = total_complexity / self.results['total_functions']

        # Calculate module averages
        for module_name, module_stats in self.results['by_module'].items():
            if module_stats['total_functions'] > 0:
                module_stats['avg_complexity'] = (
                    module_stats['complexity_sum'] / module_stats['total_functions']
                )
            # Remove complexity_sum (internal use only)
            del module_stats['complexity_sum']

        # Sort high complexity functions
        self.results['high_complexity_functions'].sort(
            key=lambda x: x['complexity'],
            reverse=True
        )

        # Convert by_module from defaultdict to regular dict
        self.results['by_module'] = dict(self.results['by_module'])

        return self.results

    def get_summary(self) -> dict[str, Any]:
        """Get summary statistics.

        Returns:
            Summary dictionary
        """
        return {
            'total_functions': self.results['total_functions'],
            'avg_complexity': round(self.results['avg_complexity'], 2),
            'max_complexity': self.results['max_complexity'],
            'high_complexity_count': len(self.results['high_complexity_functions']),
            'simple_functions': self.results['distribution']['simple_1_5'],
            'complex_functions': (
                self.results['distribution']['complex_11_20'] +
                self.results['distribution']['very_complex_21_plus']
            ),
        }
