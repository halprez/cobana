"""Unit tests for file_utils module."""

import pytest
from pathlib import Path

from cobana.utils.file_utils import FileScanner, read_file_safely, get_file_stats


@pytest.mark.unit
class TestFileScanner:
    """Unit tests for FileScanner class."""

    def test_scanner_initialization(self, temp_dir):
        """Test FileScanner initialization."""
        scanner = FileScanner(temp_dir, verbose=False)
        assert scanner.root_path == temp_dir.resolve()
        assert scanner.files_scanned == 0
        assert scanner.files_skipped == 0

    def test_scan_empty_directory(self, temp_dir):
        """Test scanning an empty directory."""
        scanner = FileScanner(temp_dir)
        files = list(scanner.scan_python_files())
        assert len(files) == 0
        assert scanner.files_scanned == 0

    def test_scan_with_python_files(self, sample_codebase):
        """Test scanning directory with Python files."""
        scanner = FileScanner(sample_codebase)
        files = list(scanner.scan_python_files())
        assert len(files) == 6  # All .py files in sample codebase
        assert scanner.files_scanned == 6

    def test_exclude_patterns(self, temp_dir):
        """Test file exclusion patterns."""
        # Create test files
        (temp_dir / "include.py").write_text("# include")
        (temp_dir / "test_exclude.py").write_text("# exclude")
        (temp_dir / "exclude_test.py").write_text("# exclude")

        scanner = FileScanner(
            temp_dir,
            exclude_patterns=["test_*.py", "*_test.py"]
        )
        files = list(scanner.scan_python_files())

        assert len(files) == 1
        assert files[0].name == "include.py"
        assert scanner.files_skipped == 2

    def test_max_depth_limit(self, sample_codebase):
        """Test max_depth parameter limits file discovery."""
        # Test depth 1 (only root level - should be 0 in this case)
        scanner = FileScanner(sample_codebase, max_depth=1)
        files = list(scanner.scan_python_files())
        assert len(files) == 0

        # Test depth 2 (root + 1 level)
        scanner = FileScanner(sample_codebase, max_depth=2)
        files = list(scanner.scan_python_files())
        assert len(files) == 4  # module_a/__init__, module_a/file1, module_b/__init__, module_b/file3

        # Test depth 3 (root + 2 levels)
        scanner = FileScanner(sample_codebase, max_depth=3)
        files = list(scanner.scan_python_files())
        assert len(files) == 6  # All files including submodule

    def test_nonexistent_directory(self):
        """Test scanning a nonexistent directory raises error."""
        scanner = FileScanner("/nonexistent/path")
        with pytest.raises(FileNotFoundError):
            list(scanner.scan_python_files())

    def test_file_instead_of_directory(self, temp_dir):
        """Test scanning a file instead of directory raises error."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")

        scanner = FileScanner(file_path)
        with pytest.raises(NotADirectoryError):
            list(scanner.scan_python_files())


@pytest.mark.unit
class TestReadFileSafely:
    """Unit tests for read_file_safely function."""

    def test_read_utf8_file(self, temp_dir):
        """Test reading a UTF-8 encoded file."""
        file_path = temp_dir / "utf8.py"
        content = "# UTF-8 file with émojis 🎉"
        file_path.write_text(content, encoding='utf-8')

        result = read_file_safely(file_path)
        assert result == content

    def test_read_nonexistent_file(self, temp_dir):
        """Test reading a nonexistent file returns None."""
        # Use a file path that doesn't exist in the temp directory
        nonexistent = temp_dir / "nonexistent_file.py"
        result = read_file_safely(nonexistent)
        assert result is None


@pytest.mark.unit
class TestGetFileStats:
    """Unit tests for get_file_stats function."""

    def test_get_stats_for_file(self, temp_dir):
        """Test getting statistics for a file."""
        file_path = temp_dir / "test.py"
        content = """# Line 1
# Line 2

# Line 4 (line 3 is blank)
def foo():
    pass
"""
        file_path.write_text(content)

        stats = get_file_stats(file_path)
        assert stats['total_lines'] == 6
        assert stats['blank_lines'] == 1
        assert stats['file_size'] > 0

    def test_get_stats_for_nonexistent_file(self, temp_dir):
        """Test getting stats for nonexistent file."""
        # Use a file path that doesn't exist in the temp directory
        nonexistent = temp_dir / "nonexistent_file.py"
        stats = get_file_stats(nonexistent)
        assert stats['total_lines'] == 0
        assert stats['blank_lines'] == 0
        assert stats['file_size'] == 0
