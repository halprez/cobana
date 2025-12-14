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
