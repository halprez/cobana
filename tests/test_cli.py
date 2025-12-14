"""Integration and UI tests for CLI interface."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch
import json

from cobana.cli import main, create_parser, get_health_status, get_debt_status


@pytest.mark.ui
class TestCLIParser:
    """Tests for CLI argument parser."""

    def test_create_parser(self):
        """Test that parser is created with all expected arguments."""
        parser = create_parser()
        assert parser.prog == 'cobana'

    def test_parser_requires_path(self):
        """Test that path argument is required."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            parser.parse_args([])

    def test_parser_optional_arguments(self):
        """Test parsing optional arguments."""
        parser = create_parser()
        args = parser.parse_args([
            '/test/path',
            '--config', 'config.yaml',
            '--json', 'output.json',
            '--markdown', 'output.md',
            '--service-name', 'test_service',
            '--module-depth', '2',
            '--max-depth', '3',
            '--verbose',
        ])

        assert args.path == '/test/path'
        assert args.config == 'config.yaml'
        assert args.json == 'output.json'
        assert args.markdown == 'output.md'
        assert args.service_name == 'test_service'
        assert args.module_depth == 2
        assert args.max_depth == 3
        assert args.verbose is True


@pytest.mark.ui
class TestCLIHelpers:
    """Tests for CLI helper functions."""

    def test_get_health_status(self):
        """Test health status emoji/text generation."""
        assert "🟢" in get_health_status(85)
        assert "Excellent" in get_health_status(85)

        assert "🟡" in get_health_status(65)
        assert "Good" in get_health_status(65)

        assert "🟠" in get_health_status(45)
        assert "Warning" in get_health_status(45)

        assert "🔴" in get_health_status(25)
        assert "Critical" in get_health_status(25)

    def test_get_debt_status(self):
        """Test debt status emoji/text generation."""
        assert "🟢" in get_debt_status('A')
        assert "Excellent" in get_debt_status('A')

        assert "🟢" in get_debt_status('B')
        assert "🟡" in get_debt_status('C')
        assert "🟠" in get_debt_status('D')
        assert "🔴" in get_debt_status('E')


@pytest.mark.integration
@pytest.mark.ui
class TestCLIIntegration:
    """Integration tests for CLI execution."""

    def test_cli_with_nonexistent_path(self):
        """Test CLI with nonexistent path returns error."""
        with patch.object(sys, 'argv', ['cobana', '/nonexistent/path']):
            exit_code = main()
            assert exit_code == 1

    def test_cli_with_file_instead_of_directory(self, temp_dir):
        """Test CLI with file instead of directory returns error."""
        file_path = temp_dir / "test.txt"
        file_path.write_text("test")

        with patch.object(sys, 'argv', ['cobana', str(file_path)]):
            exit_code = main()
            assert exit_code == 1

    def test_cli_analyze_sample_codebase(self, sample_codebase):
        """Test CLI can analyze a sample codebase successfully."""
        with patch.object(sys, 'argv', ['cobana', str(sample_codebase)]):
            exit_code = main()
            assert exit_code == 0

    def test_cli_generate_json_report(self, sample_codebase, temp_dir):
        """Test CLI can generate JSON report."""
        json_output = temp_dir / "output.json"

        with patch.object(sys, 'argv', [
            'cobana',
            str(sample_codebase),
            '--json', str(json_output)
        ]):
            exit_code = main()
            assert exit_code == 0
            assert json_output.exists()

            # Verify JSON is valid
            with open(json_output) as f:
                data = json.load(f)
            assert 'metadata' in data

    def test_cli_generate_markdown_report(self, sample_codebase, temp_dir):
        """Test CLI can generate Markdown report."""
        md_output = temp_dir / "output.md"

        with patch.object(sys, 'argv', [
            'cobana',
            str(sample_codebase),
            '--markdown', str(md_output)
        ]):
            exit_code = main()
            assert exit_code == 0
            assert md_output.exists()

            content = md_output.read_text()
            assert "Codebase Analysis Report" in content

    def test_cli_with_service_name_override(self, sample_codebase):
        """Test CLI with service name override."""
        with patch.object(sys, 'argv', [
            'cobana',
            str(sample_codebase),
            '--service-name', 'custom_service'
        ]):
            exit_code = main()
            assert exit_code == 0

    def test_cli_with_max_depth(self, sample_codebase):
        """Test CLI with max-depth parameter."""
        with patch.object(sys, 'argv', [
            'cobana',
            str(sample_codebase),
            '--max-depth', '2'
        ]):
            exit_code = main()
            assert exit_code == 0

    def test_cli_keyboard_interrupt(self, sample_codebase):
        """Test CLI handles keyboard interrupt gracefully."""
        with patch.object(sys, 'argv', ['cobana', str(sample_codebase)]):
            with patch('cobana.analyzer.CodebaseAnalyzer.analyze', side_effect=KeyboardInterrupt):
                exit_code = main()
                assert exit_code == 130

    @pytest.mark.slow
    def test_cli_analyze_self_with_reports(self, temp_dir):
        """Test CLI analyzing COBANA itself and generating all reports."""
        cobana_root = Path(__file__).parent.parent
        json_output = temp_dir / "self_analysis.json"
        md_output = temp_dir / "self_analysis.md"

        with patch.object(sys, 'argv', [
            'cobana',
            str(cobana_root),
            '--json', str(json_output),
            '--markdown', str(md_output),
            '--max-depth', '3',
        ]):
            exit_code = main()
            assert exit_code == 0
            assert json_output.exists()
            assert md_output.exists()
