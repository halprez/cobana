"""File handling utilities for COBANA.

Handles scanning directories, filtering files, and managing file operations.
"""

from pathlib import Path
from typing import Iterator
import fnmatch
import logging

logger = logging.getLogger(__name__)


class FileScanner:
    """Scans directories for Python files with filtering and error handling."""

    def __init__(
        self,
        root_path: Path | str,
        exclude_patterns: list[str] | None = None,
        verbose: bool = False,
        max_depth: int | None = None,
        tests_dir: Path | None = None,
    ):
        """Initialize file scanner.

        Args:
            root_path: Root directory to scan
            exclude_patterns: List of glob patterns to exclude
            verbose: Enable verbose logging
            max_depth: Maximum folder depth to scan (None = unlimited)
                      Depth 1 = only files in root, 2 = root + 1 level, etc.
            tests_dir: Optional tests directory. Files under this directory
                      will not be excluded even if they match exclude patterns.
        """
        self.root_path = Path(root_path).resolve()
        self.exclude_patterns = exclude_patterns or []
        self.verbose = verbose
        self.max_depth = max_depth
        self.tests_dir = tests_dir.resolve() if tests_dir else None
        self.files_scanned = 0
        self.files_skipped = 0
        self.skipped_files: list[tuple[Path, str]] = []  # (path, reason)

    def scan_python_files(self) -> Iterator[Path]:
        """Scan directory for Python files.

        Yields:
            Path objects for each Python file found

        Raises:
            FileNotFoundError: If root_path doesn't exist
            NotADirectoryError: If root_path is not a directory
        """
        if not self.root_path.exists():
            raise FileNotFoundError(
                f"Root path does not exist: {self.root_path}"
            )

        if not self.root_path.is_dir():
            raise NotADirectoryError(
                f"Root path is not a directory: {self.root_path}"
            )

        # Find all .py files in root_path
        for py_file in self.root_path.rglob("*.py"):
            if self._should_include(py_file):
                self.files_scanned += 1
                if self.verbose and self.files_scanned % 50 == 0:
                    logger.info(f"Scanned {self.files_scanned} files...")
                yield py_file
            else:
                self.files_skipped += 1
                reason = self._get_skip_reason(py_file)
                self.skipped_files.append((py_file, reason))
                if self.verbose:
                    logger.debug(f"Skipped {py_file}: {reason}")

        # If tests_dir is specified and outside root_path, scan it separately
        if self.tests_dir:
            try:
                # Check if tests_dir is outside root_path
                self.tests_dir.relative_to(self.root_path)
                # If no exception, tests_dir is under root_path, already scanned
            except ValueError:
                # tests_dir is outside root_path, need to scan it
                if self.tests_dir.exists() and self.tests_dir.is_dir():
                    logger.info(f"Scanning external tests directory: {self.tests_dir}")
                    for py_file in self.tests_dir.rglob("*.py"):
                        if self._should_include(py_file):
                            self.files_scanned += 1
                            if self.verbose and self.files_scanned % 50 == 0:
                                logger.info(f"Scanned {self.files_scanned} files...")
                            yield py_file
                        else:
                            self.files_skipped += 1
                            reason = self._get_skip_reason(py_file)
                            self.skipped_files.append((py_file, reason))
                            if self.verbose:
                                logger.debug(f"Skipped {py_file}: {reason}")

    def _should_include(self, file_path: Path) -> bool:
        """Check if file should be included in analysis.

        Test files are always included, even if they match exclude patterns.
        This ensures test files are analyzed for test metrics.

        A file is considered a test file if:
        1. It's under the specified tests_dir, OR
        2. Its filename starts with 'test_' or ends with '_test.py', OR
        3. It's in a directory named 'test', 'tests', 'testing', etc.

        Args:
            file_path: Path to check

        Returns:
            True if file should be included
        """
        # Check if this is a test file using multiple heuristics
        is_test_file = False
        name = file_path.name

        # 1. Check if file is under specified tests_dir
        if self.tests_dir:
            try:
                file_path.resolve().relative_to(self.tests_dir)
                is_test_file = True
            except ValueError:
                pass

        # 2. Check filename patterns (test_*.py or *_test.py)
        if not is_test_file:
            if name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py":
                is_test_file = True

        # 3. Check if in a test directory (test/, tests/, testing/, spec/, etc.)
        if not is_test_file:
            path_parts = file_path.parts
            test_dir_names = {"test", "tests", "testing", "spec", "specs", "__tests__"}
            if any(part in test_dir_names for part in path_parts):
                # If in test directory and is a Python file, it's a test file
                if name.endswith(".py") and not name.startswith("__"):
                    is_test_file = True

        # If it's a test file, include it (skip exclude pattern checks and depth checks)
        if is_test_file:
            return True

        # For non-test files, get relative path for pattern matching and depth checks
        try:
            rel_path = file_path.relative_to(self.root_path)
        except ValueError:
            # File is outside root_path and not a test file, exclude it
            return False

        rel_path_str = str(rel_path)

        # Check depth limit
        if self.max_depth is not None:
            # Count folder depth from root
            # e.g., "file.py" = depth 1, "folder/file.py" = depth 2, "folder/sub/file.py" = depth 3
            depth = len(rel_path.parent.parts) + 1
            if depth > self.max_depth:
                return False

        # For non-test files, check against exclude patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return False

        return True

    def _get_skip_reason(self, file_path: Path) -> str:
        """Get reason why file was skipped.

        Args:
            file_path: Path that was skipped

        Returns:
            Reason string
        """
        try:
            rel_path = file_path.relative_to(self.root_path)
        except ValueError:
            return "outside root path"

        rel_path_str = str(rel_path)

        # Check depth
        if self.max_depth is not None:
            depth = len(rel_path.parent.parts) + 1
            if depth > self.max_depth:
                return f"exceeds max depth ({depth} > {self.max_depth})"

        # Check patterns
        for pattern in self.exclude_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern):
                return f"matched exclude pattern: {pattern}"

        return "unknown"


def read_file_safely(file_path: Path) -> str | None:
    """Read file content with encoding fallback.

    Tries UTF-8 first, then latin-1, then skips the file.

    Args:
        file_path: Path to file to read

    Returns:
        File content as string, or None if reading failed
    """
    # Check if file exists first
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return None

    # Try UTF-8 first
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decode failed for {file_path}, trying latin-1")
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return None

    # Fallback to latin-1
    try:
        with open(file_path, "r", encoding="latin-1") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read {file_path}: {e}")
        return None


def get_file_stats(file_path: Path) -> dict[str, int]:
    """Get basic file statistics.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file statistics:
        - total_lines: Total number of lines
        - blank_lines: Number of blank lines
        - file_size: File size in bytes
    """
    content = read_file_safely(file_path)
    if content is None:
        return {"total_lines": 0, "blank_lines": 0, "file_size": 0}

    lines = content.splitlines()
    blank_lines = sum(1 for line in lines if not line.strip())

    return {
        "total_lines": len(lines),
        "blank_lines": blank_lines,
        "file_size": file_path.stat().st_size,
    }


def find_tests_directory(root_path: Path | str) -> Path | None:
    """Auto-detect the tests directory in a codebase.

    Searches for common test directory names at the root level and one level deep.

    Args:
        root_path: Root directory of the codebase

    Returns:
        Path to tests directory if found, None otherwise
    """
    root = Path(root_path).resolve()

    # Common test directory names (in order of preference)
    test_dir_names = ["tests", "test", "testing", "spec", "specs", "__tests__"]

    # First check root level
    for name in test_dir_names:
        test_dir = root / name
        if test_dir.exists() and test_dir.is_dir():
            logger.info(f"Auto-detected tests directory: {test_dir}")
            return test_dir

    # Then check one level deep (e.g., backend/tests)
    for child_dir in root.iterdir():
        if child_dir.is_dir():
            for name in test_dir_names:
                test_dir = child_dir / name
                if test_dir.exists() and test_dir.is_dir():
                    logger.info(f"Auto-detected tests directory: {test_dir}")
                    return test_dir

    logger.warning("Could not auto-detect tests directory")
    return None


def format_file_path(
    file_path: Path | str, root_path: Path | str, module_name: str = ""
) -> str:
    """Format file path as relative to root with optional module highlight.

    Args:
        file_path: Path to file (absolute or relative)
        root_path: Root codebase path
        module_name: Module name to highlight

    Returns:
        Formatted path string (e.g., "module_name/path/to/file.py")
    """
    file_path = Path(file_path).resolve()
    root_path = Path(root_path).resolve()

    try:
        rel_path = file_path.relative_to(root_path)
    except ValueError:
        # Path is not relative to root, return as-is
        return str(file_path)

    rel_str = str(rel_path)

    # If module_name is provided and path starts with it, keep it highlighted
    if module_name:
        parts = rel_str.split("/")
        if parts and parts[0] == module_name:
            # Return with module name first for emphasis
            return rel_str
        # Otherwise prepend module name
        return f"{module_name}/{rel_str}"

    return rel_str
