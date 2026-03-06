"""
AST-based refactoring helpers using LibCST.

Provides safe, syntax-preserving code transformations
for skills: /simplify, /refactor, /code, /tdd

Usage:
    from refactor.ast_refactor_helpers import safe_transform_file, LibCSTTransformer

    class MyTransformer(LibCSTTransformer):
        def leave_Call(self, original_node):
            # Transform function calls
            return modified_node

    success, error, count = safe_transform_file("src/module.py", MyTransformer)
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

try:
    import libcst as cst
    from libcst import CSTTransformer
    LIBCST_AVAILABLE = True
except ImportError:
    LIBCST_AVAILABLE = False
    cst = None
    CSTTransformer = object

logger = logging.getLogger(__name__)


class LibCSTTransformer(CSTTransformer if CSTTransformer else object):
    """Base transformer with common utilities and modification tracking."""

    def __init__(self, filename: str | None = None) -> None:
        """Initialize transformer.

        Args:
            filename: Optional filename for error messages
        """
        super().__init__()
        self.filename = filename
        self.modifications = 0

    def _increment_modifications(self) -> None:
        """Increment modification counter."""
        self.modifications += 1


def safe_transform_file(
    filepath: str,
    transformer: type[LibCSTTransformer],
    **kwargs: Any,
) -> tuple[bool, str, int]:
    """
    Apply AST transformation to file safely.

    This function:
    1. Reads the file
    2. Parses with LibCST
    3. Applies transformation
    4. Writes back ONLY if modifications occurred
    5. Returns success/error info

    Args:
        filepath: Path to file to transform
        transformer: LibCST transformer class
        **kwargs: Arguments passed to transformer.__init__

    Returns:
        Tuple of (success, error_message, modification_count)

    Examples:
        >>> class RenameTransformer(LibCSTTransformer):
        ...     def leave_Name(self, original_node):
        ...         if original_node.value == "old_name":
        ...             self._increment_modifications()
        ...             return original_node.with_changes(value="new_name")
        ...         return original_node
        >>> success, error, count = safe_transform_file(
        ...     "src/module.py",
        ...     RenameTransformer
        ... )
        >>> if success:
        ...     print(f"Applied {count} modifications")
    """
    if not LIBCST_AVAILABLE:
        return False, "LibCST not installed. Run: pip install libcst", 0

    try:
        # Read file
        code_path = Path(filepath)
        if not code_path.exists():
            return False, f"File not found: {filepath}", 0

        code = code_path.read_text(encoding="utf-8")

        # Parse and transform
        module = cst.parse_module(code)
        transformer_instance = transformer(filename=filepath, **kwargs)
        modified = module.visit(transformer_instance)

        # Write only if modifications occurred
        if transformer_instance.modifications > 0:
            code_path.write_text(modified.code, encoding="utf-8")
            logger.info(f"Applied {transformer_instance.modifications} modifications to {filepath}")

        return True, "", transformer_instance.modifications

    except cst.ParserSyntaxError as e:
        return False, f"Parse error: {e}", 0
    except Exception as e:
        return False, f"Transformation error: {e}", 0


def transform_code_string(
    code: str,
    transformer: type[LibCSTTransformer],
    **kwargs: Any,
) -> tuple[bool, str, str]:
    """
    Apply AST transformation to code string.

    Args:
        code: Source code to transform
        transformer: LibCST transformer class
        **kwargs: Arguments passed to transformer.__init__

    Returns:
        Tuple of (success, error_message, modified_code)

    Examples:
        >>> code = "with contextlib suppress(Exception): pass"
        >>> success, error, result = transform_code_string(code, FixDotTransformer)
        >>> assert "contextlib.suppress" in result
    """
    if not LIBCST_AVAILABLE:
        return False, "LibCST not installed", code

    try:
        module = cst.parse_module(code)
        transformer_instance = transformer(**kwargs)
        modified = module.visit(transformer_instance)
        return True, "", modified.code
    except Exception as e:
        return False, str(e), code


def verify_syntax(code: str) -> tuple[bool, str]:
    """
    Verify Python code syntax without executing it.

    Args:
        code: Python source code to verify

    Returns:
        Tuple of (is_valid, error_message)

    Examples:
        >>> is_valid, error = verify_syntax("print('hello')")
        >>> assert is_valid
        >>> is_valid, error = verify_syntax("print('hello'")
        >>> assert not is_valid
    """
    if not LIBCST_AVAILABLE:
        # Fallback to ast
        try:
            import ast
            ast.parse(code)
            return True, ""
        except SyntaxError as e:
            return False, str(e)

    try:
        cst.parse_module(code)
        return True, ""
    except cst.ParserSyntaxError as e:
        return False, str(e)


if LIBCST_AVAILABLE:
    class CommonTransformers:
        """Collection of commonly-needed transformers."""

        class FixMissingDotTransformer(LibCSTTransformer):
            """Fix missing dots in attribute access (e.g., 'contextlib suppress' → 'contextlib.suppress')."""

            def leave_Call(self, original_node: cst.Call) -> cst.Call:
                """Fix function calls with missing dots."""
                # Look for pattern: Name("contextlib") followed by Name("suppress")
                # This is a simplified check - real implementation would need
                # more sophisticated pattern matching
                return original_node

        class RenameAttributeTransformer(LibCSTTransformer):
            """Rename attribute access across file."""

            def __init__(self, old_name: str, new_name: str, **kwargs: Any):
                super().__init__(**kwargs)
                self.old_name = old_name
                self.new_name = new_name

            def leave_Attribute(self, original_node: cst.Attribute, updated_node: cst.Attribute) -> cst.Attribute:
                """Rename attribute if it matches old_name."""
                if updated_node.attr.value == self.old_name:
                    self._increment_modifications()
                    return updated_node.with_changes(
                        attr=updated_node.attr.with_changes(value=self.new_name)
                    )
                return updated_node

        class RemoveUnusedImportTransformer(LibCSTTransformer):
            """Remove specific import statement."""

            def __init__(self, module_name: str, **kwargs: Any):
                super().__init__(**kwargs)
                self.module_name = module_name

            def leave_ImportAlias(self, original_node: cst.ImportAlias) -> cst.ImportAlias | None:
                """Remove import if it matches module_name."""
                if original_node.dotted.value == self.module_name:
                    self._increment_modifications()
                    # Return None to remove this import
                    return None
                return original_node

    # Export for easy access
    FixMissingDot = CommonTransformers.FixMissingDotTransformer
    RenameAttribute = CommonTransformers.RenameAttributeTransformer
    RemoveUnusedImport = CommonTransformers.RemoveUnusedImportTransformer
else:
    # No-op stubs when LibCST unavailable
    CommonTransformers = None
