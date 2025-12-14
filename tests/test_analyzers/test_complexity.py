"""Unit tests for complexity analyzer."""

import pytest
from pathlib import Path

from cobana.analyzers.complexity import ComplexityAnalyzer


@pytest.mark.unit
class TestComplexityAnalyzer:
    """Unit tests for ComplexityAnalyzer class."""

    def test_analyzer_initialization(self, basic_config):
        """Test ComplexityAnalyzer initialization."""
        analyzer = ComplexityAnalyzer(basic_config)
        assert analyzer.config == basic_config
        assert analyzer.threshold == 10

    def test_analyze_simple_file(self, sample_python_file, basic_config):
        """Test analyzing a file with simple functions."""
        analyzer = ComplexityAnalyzer(basic_config)
        analyzer.analyze_file(sample_python_file, "test_module")

        results = analyzer.finalize_results()

        assert results['total_functions'] >= 2
        assert results['avg_complexity'] > 0
        assert 'per_file' in results
        assert len(results['per_file']) > 0
        assert any(str(sample_python_file) in f['file'] for f in results['per_file'])

    def test_complexity_categorization(self, temp_dir, basic_config):
        """Test that complexity is categorized correctly."""
        # Create file with functions of varying complexity
        file_path = temp_dir / "complexity_test.py"
        content = '''
def simple():  # Complexity 1
    return 1

def moderate(x):  # Complexity 2
    if x > 0:
        return x
    return 0

def complex_func(a, b, c, d, e, f, g, h):  # High complexity (>10)
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            if g:
                                if h:
                                    return 1
    elif b:
        if c:
            return 2
    elif c:
        return 3
    elif d:
        return 4
    return 0
'''
        file_path.write_text(content)

        analyzer = ComplexityAnalyzer(basic_config)
        analyzer.analyze_file(file_path, "test_module")
        results = analyzer.finalize_results()

        # Check categorization exists
        assert 'distribution' in results
        assert 'high_complexity_functions' in results

        # Should have at least one high complexity function (complexity > threshold)
        assert len(results['high_complexity_functions']) >= 1

    def test_module_level_metrics(self, sample_codebase, basic_config):
        """Test that module-level metrics are tracked."""
        analyzer = ComplexityAnalyzer(basic_config)

        # Analyze files from different modules
        for py_file in sample_codebase.rglob("*.py"):
            if "module_a" in str(py_file):
                analyzer.analyze_file(py_file, "module_a")
            elif "module_b" in str(py_file):
                analyzer.analyze_file(py_file, "module_b")

        results = analyzer.finalize_results()

        assert 'by_module' in results
        if 'module_a' in results['by_module']:
            assert 'avg_complexity' in results['by_module']['module_a']
        if 'module_b' in results['by_module']:
            assert 'avg_complexity' in results['by_module']['module_b']

    def test_empty_file(self, temp_dir, basic_config):
        """Test analyzing an empty file."""
        file_path = temp_dir / "empty.py"
        file_path.write_text("")

        analyzer = ComplexityAnalyzer(basic_config)
        analyzer.analyze_file(file_path, "test_module")
        results = analyzer.finalize_results()

        # Should handle empty file gracefully
        assert results['total_functions'] >= 0
        assert results['avg_complexity'] >= 0

    def test_max_complexity_tracking(self, temp_dir, basic_config):
        """Test that maximum complexity is tracked."""
        file_path = temp_dir / "max_test.py"
        content = '''
def high_complexity():
    if True:
        if True:
            if True:
                if True:
                    if True:
                        return 1
    return 0
'''
        file_path.write_text(content)

        analyzer = ComplexityAnalyzer(basic_config)
        analyzer.analyze_file(file_path, "test_module")
        results = analyzer.finalize_results()

        assert results['max_complexity'] >= 5
        assert 'max_complexity_function' in results
