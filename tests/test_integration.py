"""Integration tests for COBANA.

These tests verify that multiple components work together correctly.
"""

import pytest
from pathlib import Path
import json

from cobana.analyzer import CodebaseAnalyzer


@pytest.mark.integration
class TestCodebaseAnalyzer:
    """Integration tests for CodebaseAnalyzer."""

    def test_analyze_sample_codebase(self, sample_codebase, basic_config):
        """Test analyzing a complete sample codebase."""
        analyzer = CodebaseAnalyzer(
            root_path=sample_codebase,
            config_path=None,
            verbose=False
        )
        analyzer.config = basic_config

        results = analyzer.analyze()

        # Verify results structure
        assert 'metadata' in results
        assert 'summary' in results
        assert 'complexity' in results
        assert 'maintainability' in results
        assert 'code_size' in results
        assert 'module_health' in results

        # Verify metadata
        assert results['metadata']['total_files_analyzed'] > 0
        assert results['metadata']['module_count'] >= 2

        # Verify summary exists
        assert 'overall_health' in results['summary']
        assert 'avg_complexity' in results['summary']

    def test_max_depth_integration(self, sample_codebase, basic_config):
        """Test that max_depth parameter works end-to-end."""
        # Analyze with depth limit
        analyzer = CodebaseAnalyzer(
            root_path=sample_codebase,
            config_path=None,
            verbose=False
        )
        config_with_depth = basic_config.copy()
        config_with_depth['max_depth'] = 2
        analyzer.config = config_with_depth

        results = analyzer.analyze()

        # Should analyze fewer files with depth limit
        files_with_limit = results['metadata']['total_files_analyzed']

        # Analyze without limit
        analyzer2 = CodebaseAnalyzer(
            root_path=sample_codebase,
            config_path=None,
            verbose=False
        )
        analyzer2.config = basic_config
        results2 = analyzer2.analyze()

        files_without_limit = results2['metadata']['total_files_analyzed']

        # Should have fewer files with depth limit
        assert files_with_limit <= files_without_limit

    def test_module_detection_integration(self, sample_codebase, basic_config):
        """Test module detection integrates correctly with analysis."""
        analyzer = CodebaseAnalyzer(
            root_path=sample_codebase,
            config_path=None,
            verbose=False
        )
        analyzer.config = basic_config

        results = analyzer.analyze()

        # Should detect modules
        assert results['metadata']['module_count'] >= 2

        # Should have module-level data
        assert 'by_module' in results['complexity']
        assert 'by_module' in results['module_health']

    def test_all_analyzers_produce_results(self, sample_codebase, basic_config):
        """Test that all analyzers produce valid results."""
        analyzer = CodebaseAnalyzer(
            root_path=sample_codebase,
            config_path=None,
            verbose=False
        )
        analyzer.config = basic_config

        results = analyzer.analyze()

        # Verify each analyzer produced results
        analyzers = [
            'complexity',
            'maintainability',
            'code_size',
            'tests',
            'code_smells',
            'class_metrics',
            'technical_debt',
            'module_health',
        ]

        for analyzer_name in analyzers:
            assert analyzer_name in results, f"Missing results for {analyzer_name}"
            assert results[analyzer_name] is not None

    @pytest.mark.slow
    def test_analyze_self(self, basic_config):
        """Test analyzing COBANA's own codebase."""
        # Get COBANA's root directory
        cobana_root = Path(__file__).parent.parent

        analyzer = CodebaseAnalyzer(
            root_path=cobana_root,
            config_path=None,
            verbose=False
        )
        analyzer.config = basic_config

        results = analyzer.analyze()

        # Should successfully analyze
        assert results['metadata']['total_files_analyzed'] > 0
        assert results['summary']['overall_health'] >= 0
        assert results['summary']['overall_health'] <= 100

    def test_report_generation_integration(self, sample_codebase, basic_config, temp_dir):
        """Test that analysis results can be used to generate reports."""
        analyzer = CodebaseAnalyzer(
            root_path=sample_codebase,
            config_path=None,
            verbose=False
        )
        analyzer.config = basic_config

        results = analyzer.analyze()

        # Generate JSON report
        from cobana.report.json_generator import JSONReportGenerator
        json_path = temp_dir / "test_report.json"
        json_gen = JSONReportGenerator(results)
        json_gen.generate(json_path)

        assert json_path.exists()
        with open(json_path) as f:
            data = json.load(f)
        assert 'metadata' in data

        # Generate Markdown report
        from cobana.report.md_generator import MarkdownReportGenerator
        md_path = temp_dir / "test_report.md"
        md_gen = MarkdownReportGenerator(results)
        md_gen.generate(md_path)

        assert md_path.exists()
        content = md_path.read_text()
        assert "Codebase Analysis Report" in content


@pytest.mark.integration
@pytest.mark.regression
class TestRegressions:
    """Regression tests to ensure fixed bugs stay fixed."""

    def test_empty_directory_doesnt_crash(self, temp_dir, basic_config):
        """Regression: Ensure analyzing empty directory doesn't crash."""
        analyzer = CodebaseAnalyzer(
            root_path=temp_dir,
            config_path=None,
            verbose=False
        )
        analyzer.config = basic_config

        # Should not raise exception
        results = analyzer.analyze()
        assert results['metadata']['total_files_analyzed'] == 0

    def test_module_breakdown_doesnt_crash_with_no_modules(self, temp_dir, basic_config):
        """Regression: Module breakdown should handle case with no modules."""
        analyzer = CodebaseAnalyzer(
            root_path=temp_dir,
            config_path=None,
            verbose=False
        )
        analyzer.config = basic_config

        results = analyzer.analyze()

        # Should generate reports without crashing
        from cobana.report.md_generator import MarkdownReportGenerator
        md_gen = MarkdownReportGenerator(results)
        markdown = md_gen.get_markdown()

        assert isinstance(markdown, str)
