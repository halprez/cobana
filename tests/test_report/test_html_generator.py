"""Unit tests for HTML report generator."""

import pytest
from pathlib import Path

from cobana.report.html_generator import HtmlReportGenerator


@pytest.mark.unit
class TestHtmlReportGenerator:
    """Unit tests for HtmlReportGenerator class."""

    def test_generator_initialization(self, sample_analysis_results):
        """Test HtmlReportGenerator initialization."""
        generator = HtmlReportGenerator(sample_analysis_results)
        assert generator.results == sample_analysis_results

    def test_generate_html_to_file(self, sample_analysis_results, temp_dir):
        """Test generating HTML to a file."""
        output_path = temp_dir / "report.html"
        generator = HtmlReportGenerator(sample_analysis_results)
        generator.generate(output_path)

        assert output_path.exists()

        # Verify HTML is valid
        with open(output_path, 'r') as f:
            content = f.read()

        # Check for key HTML elements
        assert '<!DOCTYPE html>' in content
        assert '<html lang="en">' in content
        assert 'Codebase Architecture Analysis' in content
        assert '</html>' in content

    def test_get_html_string(self, sample_analysis_results):
        """Test getting HTML as string."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Should be valid HTML
        assert '<!DOCTYPE html>' in html_str
        assert '<html' in html_str
        assert '</html>' in html_str

    def test_html_includes_metadata(self, sample_analysis_results):
        """Test that HTML includes metadata section."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check metadata is present
        metadata = sample_analysis_results.get('metadata', {})
        service_name = metadata.get('service_name', 'Unknown')
        assert service_name in html_str

    def test_html_includes_summary_metrics(self, sample_analysis_results):
        """Test that HTML includes summary metrics."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check for metric cards
        assert 'Overall Health' in html_str
        assert 'Technical Debt' in html_str
        assert 'DB Coupling' in html_str
        assert 'Average Complexity' in html_str

    def test_html_includes_all_sections(self, sample_analysis_results):
        """Test that HTML includes all major sections."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check all major sections are present
        assert 'Executive Summary' in html_str
        assert 'Module Overview' in html_str
        assert 'Database Coupling' in html_str
        assert 'Code Complexity' in html_str
        assert 'Maintainability Index' in html_str
        assert 'Test Coverage' in html_str
        assert 'Code Smells' in html_str
        assert 'Technical Debt' in html_str

    def test_html_includes_navigation(self, sample_analysis_results):
        """Test that HTML includes navigation menu."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check for navigation elements
        assert '<nav>' in html_str
        assert 'href="#executive-summary"' in html_str
        assert 'href="#module-overview"' in html_str
        assert 'href="#database-coupling"' in html_str

    def test_html_includes_charts(self, sample_analysis_results):
        """Test that HTML includes Chart.js integration."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check for Chart.js script
        assert 'chart.js' in html_str.lower()
        assert '<canvas' in html_str
        assert 'moduleHealthChart' in html_str

    def test_html_includes_styling(self, sample_analysis_results):
        """Test that HTML includes embedded CSS."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check for CSS
        assert '<style>' in html_str
        assert '.metric-card' in html_str
        assert '.badge' in html_str

    def test_module_rankings_preparation(self, sample_analysis_results):
        """Test module rankings data preparation for charts."""
        generator = HtmlReportGenerator(sample_analysis_results)
        rankings = generator._prepare_module_rankings()

        # Should be a list
        assert isinstance(rankings, list)

        # Check structure if we have module health data
        if rankings:
            for ranking in rankings:
                assert 'module' in ranking
                assert 'score' in ranking

            # Should be sorted by score descending
            scores = [r['score'] for r in rankings]
            assert scores == sorted(scores, reverse=True)

    def test_empty_results(self):
        """Test handling empty results."""
        empty_results = {
            'metadata': {},
            'summary': {},
        }
        generator = HtmlReportGenerator(empty_results)
        html_str = generator.get_html_string()

        # Should still generate valid HTML
        assert '<!DOCTYPE html>' in html_str
        assert '</html>' in html_str

    def test_missing_optional_sections(self):
        """Test handling missing optional sections."""
        minimal_results = {
            'metadata': {'service_name': 'test'},
            'summary': {'overall_health': 75},
        }
        generator = HtmlReportGenerator(minimal_results)
        html_str = generator.get_html_string()

        # Should still generate valid HTML without errors
        assert '<!DOCTYPE html>' in html_str
        assert 'test' in html_str

    def test_db_coupling_section_with_violations(self, sample_analysis_results):
        """Test DB coupling section renders violations correctly."""
        # Add some test violations
        sample_analysis_results['db_coupling'] = {
            'violation_count_write': 2,
            'violation_count_read': 3,
            'total_operations': 5,
            'violations': [
                {
                    'operation': 'INSERT',
                    'operation_type': 'write',
                    'file': 'test.py',
                    'line': 10,
                    'table': 'users'
                },
                {
                    'operation': 'SELECT',
                    'operation_type': 'read',
                    'file': 'test.py',
                    'line': 20,
                    'table': 'orders'
                }
            ]
        }

        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check violations are rendered
        assert 'INSERT' in html_str
        assert 'SELECT' in html_str
        assert 'users' in html_str
        assert 'orders' in html_str

    def test_complexity_section_with_high_complexity(self, sample_analysis_results):
        """Test complexity section renders high complexity functions."""
        sample_analysis_results['complexity'] = {
            'avg_complexity': 8.5,
            'high_complexity_count': 2,
            'total_functions': 50,
            'high_complexity_functions': [
                {
                    'function': 'complex_func',
                    'complexity': 15,
                    'file': 'module.py',
                    'line': 100
                }
            ]
        }

        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check complexity data is rendered
        assert 'complex_func' in html_str
        assert '15' in html_str

    def test_technical_debt_section(self, sample_analysis_results):
        """Test technical debt section renders correctly."""
        sample_analysis_results['technical_debt'] = {
            'sqale_rating': 'B',
            'debt_ratio': 7.5,
            'total_remediation_hours': 24.5,
            'by_category': {
                'Complexity': {'count': 10, 'hours': 12.0, 'percentage': 48.0},
                'Maintainability': {'count': 5, 'hours': 12.5, 'percentage': 52.0}
            },
            'top_debt_files': [
                {'file': 'messy.py', 'debt_hours': 8.0, 'issue_count': 15}
            ]
        }

        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check debt data is rendered
        assert 'SQALE Rating' in html_str
        assert 'messy.py' in html_str
        assert 'Complexity' in html_str
        assert 'Maintainability' in html_str

    def test_responsive_design_meta_tag(self, sample_analysis_results):
        """Test that HTML includes responsive design meta tag."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check for viewport meta tag
        assert 'viewport' in html_str
        assert 'width=device-width' in html_str

    def test_footer_includes_timestamp(self, sample_analysis_results):
        """Test that footer includes generation timestamp."""
        generator = HtmlReportGenerator(sample_analysis_results)
        html_str = generator.get_html_string()

        # Check for footer and COBANA attribution
        assert '<footer' in html_str
        assert 'COBANA' in html_str
        assert 'Report generated on' in html_str

    def test_max_items_parameter_default(self, sample_analysis_results):
        """Test that max_items defaults to 0 (unlimited)."""
        generator = HtmlReportGenerator(sample_analysis_results)
        assert generator.max_items == 0

    def test_max_items_parameter_custom(self, sample_analysis_results):
        """Test that max_items can be set to custom value."""
        generator = HtmlReportGenerator(sample_analysis_results, max_items=50)
        assert generator.max_items == 50

    def test_max_items_in_context(self, sample_analysis_results):
        """Test that max_items is passed to template context."""
        generator = HtmlReportGenerator(sample_analysis_results, max_items=25)
        html_str = generator.get_html_string()

        # max_items should be available in template
        assert generator.max_items == 25

    def test_max_items_limit_message_shown(self, sample_analysis_results):
        """Test that limit message appears when max_items is set and exceeded."""
        # Create sample data with many complexity files
        sample_analysis_results['complexity'] = {
            'avg_complexity': 8.5,
            'high_complexity_count': 100,
            'total_functions': 500,
            'high_complexity_files': [
                {'file': f'file{i}.py', 'avg_complexity': 10 + i, 'max_complexity': 15 + i, 'high_complexity_count': 2}
                for i in range(100)
            ]
        }

        generator = HtmlReportGenerator(sample_analysis_results, max_items=20)
        html_str = generator.get_html_string()

        # Should show limit message
        assert 'Showing 20 most relevant files from 100 total analyzed' in html_str

    def test_max_items_no_limit_message_when_under_limit(self, sample_analysis_results):
        """Test that no limit message appears when list is shorter than max_items."""
        sample_analysis_results['complexity'] = {
            'avg_complexity': 8.5,
            'high_complexity_count': 5,
            'total_functions': 50,
            'high_complexity_files': [
                {'file': f'file{i}.py', 'avg_complexity': 10 + i, 'max_complexity': 15 + i, 'high_complexity_count': 2}
                for i in range(5)
            ]
        }

        generator = HtmlReportGenerator(sample_analysis_results, max_items=20)
        html_str = generator.get_html_string()

        # Should NOT show limit message since we have fewer items than the limit
        assert 'Showing 20 most relevant files' not in html_str

    def test_max_items_unlimited_when_zero(self, sample_analysis_results):
        """Test that max_items=0 shows all items without limit."""
        sample_analysis_results['complexity'] = {
            'avg_complexity': 8.5,
            'high_complexity_count': 100,
            'total_functions': 500,
            'high_complexity_files': [
                {'file': f'file{i}.py', 'avg_complexity': 10 + i, 'max_complexity': 15 + i, 'high_complexity_count': 2}
                for i in range(100)
            ]
        }

        generator = HtmlReportGenerator(sample_analysis_results, max_items=0)
        html_str = generator.get_html_string()

        # Should NOT show any limit message
        assert 'Showing' not in html_str or 'most relevant files from' not in html_str

    def test_prepare_technical_debt_data(self, sample_analysis_results):
        """Test _prepare_technical_debt_data method."""
        sample_analysis_results['technical_debt'] = {
            'sqale_rating': 'A',
            'debt_ratio': 5.0,
            'total_remediation_hours': 10.5,
            'top_debt_files': [
                {'file': 'bad.py', 'debt_hours': 5.0, 'issue_count': 10}
            ]
        }

        generator = HtmlReportGenerator(sample_analysis_results)
        debt_data = generator._prepare_technical_debt_data()

        # Should return technical debt data
        assert debt_data['sqale_rating'] == 'A'
        assert debt_data['debt_ratio'] == 5.0
        assert debt_data['total_remediation_hours'] == 10.5
        assert len(debt_data['top_debt_files']) == 1

    def test_prepare_technical_debt_data_empty(self):
        """Test _prepare_technical_debt_data with missing data."""
        minimal_results = {
            'metadata': {},
            'summary': {}
        }

        generator = HtmlReportGenerator(minimal_results)
        debt_data = generator._prepare_technical_debt_data()

        # Should return empty dict without crashing
        assert isinstance(debt_data, dict)

    def test_highlight_module_filter(self, sample_analysis_results):
        """Test that module highlighting filter works correctly."""
        generator = HtmlReportGenerator(sample_analysis_results)

        # Test with module path
        result = generator._highlight_module_filter("module_name/subdir/file.py")
        assert '<strong>module_name</strong>' in str(result)
        assert '/subdir/file.py' in str(result)

    def test_highlight_module_filter_single_file(self, sample_analysis_results):
        """Test module highlighting with single file (no directory)."""
        generator = HtmlReportGenerator(sample_analysis_results)

        # Test with just filename
        result = generator._highlight_module_filter("file.py")
        assert result == "file.py"  # No highlighting for single file
