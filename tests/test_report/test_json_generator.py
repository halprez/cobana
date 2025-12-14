"""Unit tests for JSON report generator."""

import pytest
import json
from pathlib import Path

from cobana.report.json_generator import JSONReportGenerator


@pytest.mark.unit
class TestJSONReportGenerator:
    """Unit tests for JSONReportGenerator class."""

    def test_generator_initialization(self, sample_analysis_results):
        """Test JSONReportGenerator initialization."""
        generator = JSONReportGenerator(sample_analysis_results)
        assert generator.results == sample_analysis_results

    def test_generate_json_to_file(self, sample_analysis_results, temp_dir):
        """Test generating JSON to a file."""
        output_path = temp_dir / "report.json"
        generator = JSONReportGenerator(sample_analysis_results)
        generator.generate(output_path)

        assert output_path.exists()

        # Verify JSON is valid
        with open(output_path, 'r') as f:
            data = json.load(f)

        assert 'analysis_date' in data
        assert 'metadata' in data
        assert 'summary' in data

    def test_get_json_string(self, sample_analysis_results):
        """Test getting JSON as string."""
        generator = JSONReportGenerator(sample_analysis_results)
        json_str = generator.get_json_string()

        # Should be valid JSON
        data = json.loads(json_str)
        assert 'analysis_date' in data
        assert 'metadata' in data

    def test_json_includes_all_results(self, sample_analysis_results):
        """Test that JSON includes all analysis results."""
        generator = JSONReportGenerator(sample_analysis_results)
        json_str = generator.get_json_string()
        data = json.loads(json_str)

        # Check all major sections are present
        assert 'metadata' in data
        assert 'summary' in data
        assert 'complexity' in data
        assert 'module_health' in data

    def test_pretty_print_option(self, sample_analysis_results):
        """Test pretty print option."""
        generator = JSONReportGenerator(sample_analysis_results)

        pretty = generator.get_json_string(pretty=True)
        compact = generator.get_json_string(pretty=False)

        # Pretty version should be longer (has indentation and newlines)
        assert len(pretty) > len(compact)

        # Both should be valid JSON
        pretty_data = json.loads(pretty)
        compact_data = json.loads(compact)

        # Compare without timestamp (which may differ slightly)
        pretty_data.pop('analysis_date', None)
        compact_data.pop('analysis_date', None)
        assert pretty_data == compact_data
