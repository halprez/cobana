"""AST (Abstract Syntax Tree) utilities for COBANA.

Handles parsing Python files and extracting information from AST.
"""

import ast
from pathlib import Path
from typing import Any
import logging

logger = logging.getLogger(__name__)


class ASTParser:
    """Parses Python files into AST and extracts information."""

    # Class-level set to track files with logged syntax errors (avoid duplicate warnings)
    _logged_syntax_errors: set[str] = set()

    def __init__(self, file_path: Path, content: str | None = None):
        """Initialize AST parser.

        Args:
            file_path: Path to Python file
            content: Optional file content (if already read)
        """
        self.file_path = file_path
        self.content = content
        self.tree: ast.Module | None = None
        self.parse_error: Exception | None = None

    def parse(self) -> ast.Module | None:
        """Parse file into AST.

        Returns:
            AST Module node, or None if parsing failed
        """
        if self.content is None:
            from cobana.utils.file_utils import read_file_safely
            self.content = read_file_safely(self.file_path)

        if self.content is None:
            logger.error(f"Could not read file: {self.file_path}")
            return None

        try:
            self.tree = ast.parse(self.content, filename=str(self.file_path))
            return self.tree
        except SyntaxError as e:
            self.parse_error = e
            # Only log each file's syntax error once to avoid spam
            file_key = str(self.file_path)
            if file_key not in ASTParser._logged_syntax_errors:
                ASTParser._logged_syntax_errors.add(file_key)
                logger.warning(f"Syntax error in {self.file_path}: {e}")
            return None
        except Exception as e:
            self.parse_error = e
            # Only log each file's parse error once
            file_key = str(self.file_path)
            if file_key not in ASTParser._logged_syntax_errors:
                ASTParser._logged_syntax_errors.add(file_key)
                logger.error(f"Failed to parse {self.file_path}: {e}")
            return None

    def get_functions(self) -> list[tuple[str, ast.FunctionDef]]:
        """Extract all function definitions from AST.

        Returns:
            List of (function_name, FunctionDef) tuples
        """
        if self.tree is None:
            if not self.parse():
                return []

        functions = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.FunctionDef):
                functions.append((node.name, node))

        return functions

    def get_classes(self) -> list[tuple[str, ast.ClassDef]]:
        """Extract all class definitions from AST.

        Returns:
            List of (class_name, ClassDef) tuples
        """
        if self.tree is None:
            if not self.parse():
                return []

        classes = []
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                classes.append((node.name, node))

        return classes

    def get_imports(self) -> list[dict[str, Any]]:
        """Extract all import statements.

        Returns:
            List of import information dictionaries
        """
        if self.tree is None:
            if not self.parse():
                return []

        imports = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append({
                        "type": "import",
                        "module": alias.name,
                        "asname": alias.asname,
                        "line": node.lineno,
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    imports.append({
                        "type": "from_import",
                        "module": module,
                        "name": alias.name,
                        "asname": alias.asname,
                        "line": node.lineno,
                    })

        return imports

    def get_function_calls(self, target_attr: str | None = None) -> list[dict[str, Any]]:
        """Extract function/method calls from AST.

        Args:
            target_attr: If specified, only return calls to this attribute (e.g., "db")

        Returns:
            List of call information dictionaries
        """
        if self.tree is None:
            if not self.parse():
                return []

        calls = []

        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call):
                call_info = self._extract_call_info(node)
                if call_info:
                    if target_attr is None or call_info.get("object") == target_attr:
                        calls.append(call_info)

        return calls

    def _extract_call_info(self, node: ast.Call) -> dict[str, Any] | None:
        """Extract information from a Call node.

        Args:
            node: AST Call node

        Returns:
            Dictionary with call information, or None if not extractable
        """
        call_info: dict[str, Any] = {"line": node.lineno}

        # Handle different call patterns
        if isinstance(node.func, ast.Attribute):
            # Method call: obj.method()
            call_info["method"] = node.func.attr

            # Try to get the object
            if isinstance(node.func.value, ast.Name):
                call_info["object"] = node.func.value.id
            elif isinstance(node.func.value, ast.Attribute):
                # Nested attribute: obj.attr.method()
                call_info["object"] = self._get_attribute_chain(node.func.value)

        elif isinstance(node.func, ast.Name):
            # Function call: function()
            call_info["function"] = node.func.id

        return call_info if call_info else None

    def _get_attribute_chain(self, node: ast.Attribute) -> str:
        """Get full attribute chain as string.

        Args:
            node: Attribute node

        Returns:
            Attribute chain as string (e.g., "obj.attr")
        """
        parts = []
        current = node

        while isinstance(current, ast.Attribute):
            parts.append(current.attr)
            current = current.value

        if isinstance(current, ast.Name):
            parts.append(current.id)

        return ".".join(reversed(parts))


def count_lines(node: ast.AST) -> int:
    """Count lines of code in an AST node.

    Args:
        node: AST node

    Returns:
        Number of lines
    """
    if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
        return 0

    return node.end_lineno - node.lineno + 1


def get_function_params(func_def: ast.FunctionDef) -> list[str]:
    """Get parameter names from function definition.

    Args:
        func_def: FunctionDef node

    Returns:
        List of parameter names
    """
    params = []

    # Regular arguments
    for arg in func_def.args.args:
        params.append(arg.arg)

    # *args
    if func_def.args.vararg:
        params.append(f"*{func_def.args.vararg.arg}")

    # **kwargs
    if func_def.args.kwarg:
        params.append(f"**{func_def.args.kwarg.arg}")

    return params


def get_nesting_depth(node: ast.AST) -> int:
    """Calculate maximum nesting depth in an AST node.

    Args:
        node: AST node to analyze

    Returns:
        Maximum nesting depth
    """
    def _depth(n: ast.AST, current_depth: int = 0) -> int:
        max_depth = current_depth

        # Nodes that increase nesting
        nesting_nodes = (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)

        for child in ast.iter_child_nodes(n):
            if isinstance(child, nesting_nodes):
                child_depth = _depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = _depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    return _depth(node)
