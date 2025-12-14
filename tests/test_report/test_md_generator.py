"""Unit tests for Markdown report generator."""

import pytest
from pathlib import Path

from cobana.report.md_generator import MarkdownReportGenerator


@pytest.mark.unit
class TestMarkdownReportGenerator:
    """Unit tests for MarkdownReportGenerator class."""

    def test_generator_initialization(self, sample_analysis_results):
        """Test MarkdownReportGenerator initialization."""
        generator = MarkdownReportGenerator(sample_analysis_results)
        assert generator.results == sample_analysis_results
        assert generator.metadata == sample_analysis_results['metadata']
        assert generator.summary == sample_analysis_results['summary']

    def test_generate_markdown_content(self, sample_analysis_results):
        """Test generating markdown content."""
        generator = MarkdownReportGenerator(sample_analysis_results)
        markdown = generator.get_markdown()

        # Check for key sections
        assert "# Codebase Analysis Report" in markdown
        assert "## Executive Summary" in markdown
        assert "## Key Metrics" in markdown
        assert "Overall Health:" in markdown
        assert "Technical Debt:" in markdown

    def test_markdown_includes_metrics(self, sample_analysis_results):
        """Test that markdown includes all major metrics."""
        generator = MarkdownReportGenerator(sample_analysis_results)
        markdown = generator.get_markdown()

        # Check for metric sections
        assert "Database Coupling" in markdown
        assert "Code Complexity" in markdown
        assert "Maintainability" in markdown
        assert "Code Size" in markdown
        assert "Tests" in markdown
        assert "Code Smells" in markdown
        assert "Class Metrics" in markdown

    def test_markdown_includes_explanations(self, sample_analysis_results):
        """Test that explanations are included."""
        generator = MarkdownReportGenerator(sample_analysis_results)
        markdown = generator.get_markdown()

        # Check for educational content
        assert "📚 What is this?" in markdown
        assert "⚡ Why it matters" in markdown

    def test_markdown_includes_module_breakdown(self, sample_analysis_results):
        """Test that module-level breakdown is included."""
        generator = MarkdownReportGenerator(sample_analysis_results)
        markdown = generator.get_markdown()

        assert "## Module-Level Breakdown" in markdown
        assert "module_a" in markdown or "module_b" in markdown

    def test_generate_to_file(self, sample_analysis_results, temp_dir):
        """Test generating markdown to a file."""
        output_path = temp_dir / "report.md"
        generator = MarkdownReportGenerator(sample_analysis_results)
        generator.generate(output_path)

        assert output_path.exists()
        content = output_path.read_text()
        assert "# Codebase Analysis Report" in content

    def test_health_emoji_assignment(self, sample_analysis_results):
        """Test that health scores get appropriate emojis."""
        generator = MarkdownReportGenerator(sample_analysis_results)

        # Test different score ranges
        assert "🟢" == generator._get_health_emoji(85)
        assert "🟡" == generator._get_health_emoji(65)
        assert "🟠" == generator._get_health_emoji(45)
        assert "🔴" == generator._get_health_emoji(25)

    def test_handles_missing_data_gracefully(self):
        """Test that generator handles missing data gracefully."""
        minimal_results = {
            'metadata': {
                'service_name': 'test',
                'total_files_analyzed': 0,
                'module_count': 0,
            },
            'summary': {},
            'module_health': {},
        }

        generator = MarkdownReportGenerator(minimal_results)
        markdown = generator.get_markdown()

        # Should not crash, should produce valid markdown
        assert "# Codebase Analysis Report" in markdown
        assert "test" in markdown
