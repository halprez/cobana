"""Module detection utilities for COBANA.

Handles detecting logical modules from folder structure and mapping files to modules.
"""

from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


class Module:
    """Represents a logical module in the codebase."""

    def __init__(self, name: str, path: str, description: str = ""):
        """Initialize a module.

        Args:
            name: Module name
            path: Relative path from codebase root
            description: Optional module description
        """
        self.name = name
        self.path = path
        self.description = description or f"Module: {name}"

    def __repr__(self) -> str:
        return f"Module(name='{self.name}', path='{self.path}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Module):
            return False
        return self.name == other.name and self.path == other.path

    def to_dict(self) -> dict[str, str]:
        """Convert module to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "name": self.name,
            "path": self.path,
            "description": self.description,
        }


class ModuleDetector:
    """Detects and manages modules in a codebase."""

    def __init__(self, root_path: Path | str, config: dict[str, Any]):
        """Initialize module detector.

        Args:
            root_path: Root path of codebase
            config: Configuration dictionary
        """
        self.root_path = Path(root_path).resolve()
        self.config = config
        self.modules: list[Module] = []
        self._file_to_module_cache: dict[Path, str] = {}

    def detect_modules(self) -> list[Module]:
        """Detect modules based on configuration.

        Returns:
            List of detected modules

        Raises:
            ValueError: If configuration is invalid
        """
        method = self.config.get("module_detection", {}).get("method", "auto")

        match method:
            case "manual":
                self.modules = self._detect_manual()
            case "auto":
                self.modules = self._detect_auto()
            case _:
                raise ValueError(f"Invalid module detection method: {method}")

        logger.info(f"Detected {len(self.modules)} modules: {[m.name for m in self.modules]}")
        return self.modules

    def _detect_manual(self) -> list[Module]:
        """Detect modules using manual configuration.

        Returns:
            List of manually configured modules
        """
        manual_modules = self.config.get("module_detection", {}).get("manual_modules", [])

        modules = []
        for module_config in manual_modules:
            module = Module(
                name=module_config.get("name", "unknown"),
                path=module_config.get("path", ""),
                description=module_config.get("description", ""),
            )
            modules.append(module)

        return modules

    def _detect_auto(self) -> list[Module]:
        """Auto-detect modules from folder structure.

        Returns:
            List of auto-detected modules
        """
        depth = self.config.get("module_detection", {}).get("depth", 1)
        modules = []
        exclude_patterns = self.config.get("exclude_patterns", [])

        # Get all directories at specified depth
        for item in self.root_path.iterdir():
            if not item.is_dir():
                continue

            # Skip if matches exclude pattern
            if self._should_exclude(item, exclude_patterns):
                continue

            # Check if this is at the right depth
            rel_path = item.relative_to(self.root_path)
            current_depth = len(rel_path.parts)

            if current_depth == depth:
                module = Module(
                    name=item.name,
                    path=str(rel_path),
                    description=f"Module: {item.name}",
                )
                modules.append(module)
            elif current_depth < depth:
                # Recurse into subdirectories
                modules.extend(self._detect_at_depth(item, depth, current_depth, exclude_patterns))

        return modules

    def _detect_at_depth(
        self,
        current_dir: Path,
        target_depth: int,
        current_depth: int,
        exclude_patterns: list[str]
    ) -> list[Module]:
        """Recursively detect modules at target depth.

        Args:
            current_dir: Current directory being examined
            target_depth: Target depth for module detection
            current_depth: Current depth level
            exclude_patterns: Patterns to exclude

        Returns:
            List of modules found at target depth
        """
        if current_depth >= target_depth:
            return []

        modules = []
        for item in current_dir.iterdir():
            if not item.is_dir():
                continue

            if self._should_exclude(item, exclude_patterns):
                continue

            rel_path = item.relative_to(self.root_path)
            item_depth = len(rel_path.parts)

            if item_depth == target_depth:
                module = Module(
                    name=item.name,
                    path=str(rel_path),
                    description=f"Module: {item.name}",
                )
                modules.append(module)
            elif item_depth < target_depth:
                modules.extend(self._detect_at_depth(item, target_depth, item_depth, exclude_patterns))

        return modules

    def _should_exclude(self, path: Path, exclude_patterns: list[str]) -> bool:
        """Check if path should be excluded.

        Args:
            path: Path to check
            exclude_patterns: List of patterns to exclude

        Returns:
            True if should be excluded
        """
        import fnmatch

        try:
            rel_path = path.relative_to(self.root_path)
        except ValueError:
            return True

        rel_path_str = str(rel_path)

        for pattern in exclude_patterns:
            if fnmatch.fnmatch(rel_path_str, pattern) or fnmatch.fnmatch(path.name, pattern):
                return True

        # Also exclude common non-module directories
        if path.name.startswith('.'):
            return True

        return False

    def get_module_for_file(self, file_path: Path) -> str:
        """Determine which module a file belongs to.

        Args:
            file_path: Path to file

        Returns:
            Module name, or "root" if not in any module
        """
        # Check cache first
        if file_path in self._file_to_module_cache:
            return self._file_to_module_cache[file_path]

        try:
            rel_path = file_path.relative_to(self.root_path)
        except ValueError:
            self._file_to_module_cache[file_path] = "root"
            return "root"

        rel_path_str = str(rel_path)

        # Find matching module
        for module in self.modules:
            if rel_path_str.startswith(module.path):
                self._file_to_module_cache[file_path] = module.name
                return module.name

        # No module found
        self._file_to_module_cache[file_path] = "root"
        return "root"

    def get_module_files(self, module_name: str, all_files: list[Path]) -> list[Path]:
        """Get all files belonging to a specific module.

        Args:
            module_name: Name of module
            all_files: List of all files in codebase

        Returns:
            List of files belonging to the module
        """
        return [f for f in all_files if self.get_module_for_file(f) == module_name]
