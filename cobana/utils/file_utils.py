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
        max_depth: int | None = None
    ):
        """Initialize file scanner.

        Args:
            root_path: Root directory to scan
            exclude_patterns: List of glob patterns to exclude
            verbose: Enable verbose logging
            max_depth: Maximum folder depth to scan (None = unlimited)
                      Depth 1 = only files in root, 2 = root + 1 level, etc.
        """
        self.root_path = Path(root_path).resolve()
        self.exclude_patterns = exclude_patterns or []
        self.verbose = verbose
        self.max_depth = max_depth
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
            raise FileNotFoundError(f"Root path does not exist: {self.root_path}")

        if not self.root_path.is_dir():
            raise NotADirectoryError(f"Root path is not a directory: {self.root_path}")

        # Find all .py files
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

    def _should_include(self, file_path: Path) -> bool:
        """Check if file should be included in analysis.

        Args:
            file_path: Path to check

        Returns:
            True if file should be included
        """
        # Get relative path for pattern matching
        try:
            rel_path = file_path.relative_to(self.root_path)
        except ValueError:
            return False

        rel_path_str = str(rel_path)

        # Check depth limit
        if self.max_depth is not None:
            # Count folder depth from root
            # e.g., "file.py" = depth 1, "folder/file.py" = depth 2, "folder/sub/file.py" = depth 3
            depth = len(rel_path.parent.parts) + 1
            if depth > self.max_depth:
                return False

        # Check against exclude patterns
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
