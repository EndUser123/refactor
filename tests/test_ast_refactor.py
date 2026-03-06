"""
Tests for AST refactoring helpers.

Tests cover:
- Attribute renaming transformer
- Syntax verification (valid and invalid code)
- Code string transformation
- Graceful fallback when LibCST unavailable
"""
from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from unittest.mock import patch

import pytest

# Import helpers module
if str(Path(__file__).parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent.parent))

from ast_refactor_helpers import (
    LIBCST_AVAILABLE,
    LibCSTTransformer,
    safe_transform_file,
    transform_code_string,
    verify_syntax,
)

if LIBCST_AVAILABLE:
    from ast_refactor_helpers import RenameAttribute


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_valid_code():
    """Sample valid Python code for testing."""
    return dedent("""
        import os
        from pathlib import Path

        def example_function():
            data = {"old_key": "value"}
            path = Path("/tmp/test")
            return path.exists()

        class ExampleClass:
            def __init__(self):
                self.old_attr = "value"

            def method(self):
                return self.old_attr
    """).strip()


@pytest.fixture
def sample_invalid_code():
    """Sample invalid Python code (syntax error)."""
    return dedent("""
        def broken_function():
            # Missing closing parenthesis
            print("hello"
    """).strip()


@pytest.fixture
def attribute_rename_code():
    """Sample code with attributes to rename."""
    return dedent("""
        class MyClass:
            def __init__(self):
                self.old_name = "value"
                self.another_old_name = "another"

            def get_old_name(self):
                return self.old_name

            def set_old_name(self, value):
                self.old_name = value
    """).strip()


@pytest.fixture
def temp_file(tmp_path, sample_valid_code):
    """Create a temporary file with sample code."""
    test_file = tmp_path / "test_module.py"
    test_file.write_text(sample_valid_code, encoding="utf-8")
    return test_file


# =============================================================================
# Test: Rename Attribute Success
# =============================================================================

@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_rename_attribute_success():
    """Test attribute renaming works correctly."""
    # Test transformer directly
    transformer = RenameAttribute(old_name="old_name", new_name="new_name")
    assert transformer.old_name == "old_name"
    assert transformer.new_name == "new_name"
    assert transformer.modifications == 0


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_rename_attribute_transform_code():
    """Test attribute renaming transforms code correctly."""
    code = 'obj.old_name = "value"\nvalue = obj.old_name'

    success, error, result = transform_code_string(
        code,
        RenameAttribute,
        old_name="old_name",
        new_name="new_name"
    )

    assert success, f"Transform failed: {error}"
    assert "new_name" in result
    assert "old_name" not in result
    assert error == ""


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_rename_attribute_partial_match():
    """Test that renaming only affects exact matches."""
    code = 'obj.old_name = "value"\nobj.another_old_name = "value"'

    success, error, result = transform_code_string(
        code,
        RenameAttribute,
        old_name="old_name",
        new_name="new_name"
    )

    assert success
    # Only exact matches should be renamed
    assert "new_name" in result
    # Partial matches should remain unchanged
    assert "another_old_name" in result


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_rename_attribute_with_file(temp_file):
    """Test attribute renaming on a file."""
    code = 'class MyClass:\n    def __init__(self):\n        self.old_attr = "value"'
    temp_file.write_text(code)

    success, error, count = safe_transform_file(
        str(temp_file),
        RenameAttribute,
        old_name="old_attr",
        new_name="new_attr"
    )

    assert success, f"Transform failed: {error}"
    assert count == 1
    assert error == ""

    # Verify file was modified
    result = temp_file.read_text(encoding="utf-8")
    assert "new_attr" in result
    assert "old_attr" not in result


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_rename_attribute_no_modifications():
    """Test that no modifications returns correct count."""
    code = 'obj.other_name = "value"'

    success, error, result = transform_code_string(
        code,
        RenameAttribute,
        old_name="old_name",
        new_name="new_name"
    )

    assert success
    assert "old_name" not in result  # No changes
    assert "other_name" in result  # Original preserved


# =============================================================================
# Test: Syntax Verification - Valid Code
# =============================================================================

def test_syntax_verification_valid(sample_valid_code):
    """Test syntax checker accepts valid code."""
    is_valid, error = verify_syntax(sample_valid_code)

    assert is_valid, f"Valid code rejected: {error}"
    assert error == ""


def test_syntax_verification_valid_simple():
    """Test syntax checker accepts simple valid code."""
    valid_codes = [
        "print('hello')",
        "x = 42",
        "def foo(): return 1",
        "class Bar: pass",
        "import os",
        "from pathlib import Path",
        "",
        "# Just a comment",
    ]

    for code in valid_codes:
        is_valid, error = verify_syntax(code)
        assert is_valid, f"Code rejected: {code}\nError: {error}"


def test_syntax_verification_valid_complex(sample_valid_code):
    """Test syntax checker accepts complex valid code."""
    is_valid, error = verify_syntax(sample_valid_code)

    assert is_valid
    assert error == ""


# =============================================================================
# Test: Syntax Verification - Invalid Code
# =============================================================================

def test_syntax_verification_invalid(sample_invalid_code):
    """Test syntax checker rejects invalid code."""
    is_valid, error = verify_syntax(sample_invalid_code)

    assert not is_valid, "Invalid code was accepted"
    assert len(error) > 0, "Expected error message"


def test_syntax_verification_invalid_various_errors():
    """Test syntax checker catches various syntax errors."""
    invalid_codes = [
        ("print('hello'", "Missing closing paren"),
        ("def foo(: pass", "Invalid function definition"),
        ("class 123Class: pass", "Invalid class name"),
        ("if True", "Missing colon"),
        ("import", "Incomplete import"),
        ("from import foo", "Invalid import"),
        ("x = ", "Incomplete assignment"),
    ]

    for code, description in invalid_codes:
        is_valid, error = verify_syntax(code)
        assert not is_valid, f"Invalid code accepted: {description}"
        assert len(error) > 0, f"No error for: {description}"


def test_syntax_verification_invalid_mixed_syntax():
    """Test syntax checker with mixed valid/invalid content."""
    # Valid code followed by invalid
    code = dedent("""
        x = 42
        def foo():
            return x
        print('missing paren'
    """)

    is_valid, error = verify_syntax(code)
    assert not is_valid


# =============================================================================
# Test: Transform Code String
# =============================================================================

@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_transform_code_string_basic():
    """Test string transformation works with basic code."""
    code = "x = old_value\ny = old_value"

    class SimpleRenameTransformer(LibCSTTransformer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.old = "old_value"
            self.new = "new_value"

        def leave_Name(self, original_node, updated_node):
            if updated_node.value == self.old:
                self._increment_modifications()
                return updated_node.with_changes(value=self.new)
            return updated_node

    success, error, result = transform_code_string(
        code,
        SimpleRenameTransformer
    )

    assert success, f"Transform failed: {error}"
    assert "new_value" in result
    assert error == ""


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_transform_code_string_preserves_formatting():
    """Test that transformation preserves code formatting."""
    code = dedent("""
        # Comment
        x = old_value  # Inline comment

        def func():
            return old_value
    """)

    class SimpleRenameTransformer(LibCSTTransformer):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.old = "old_value"
            self.new = "new_value"

        def leave_Name(self, original_node, updated_node):
            if updated_node.value == self.old:
                self._increment_modifications()
                return updated_node.with_changes(value=self.new)
            return updated_node

    success, error, result = transform_code_string(
        code,
        SimpleRenameTransformer
    )

    assert success
    assert "# Comment" in result
    assert "# Inline comment" in result


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_transform_code_string_no_changes():
    """Test transformation when no changes needed."""
    code = "x = 42\ny = 100"

    class NoOpTransformer(LibCSTTransformer):
        pass

    success, error, result = transform_code_string(
        code,
        NoOpTransformer
    )

    assert success
    assert result.strip() == code.strip()


# =============================================================================
# Test: LibCST Not Installed (Graceful Fallback)
# =============================================================================

def test_libcst_not_installed_verify_syntax_fallback():
    """Test graceful fallback when LibCST unavailable for syntax check."""
    # Mock LIBCST_AVAILABLE as False
    with patch('ast_refactor_helpers.LIBCST_AVAILABLE', False):
        # Verify syntax still works using ast fallback
        valid_code = "x = 42"
        is_valid, error = verify_syntax(valid_code)

        assert is_valid, "Fallback syntax check failed for valid code"
        assert error == ""


def test_libcst_not_installed_verify_syntax_invalid():
    """Test fallback syntax check rejects invalid code."""
    with patch('ast_refactor_helpers.LIBCST_AVAILABLE', False):
        invalid_code = "print('hello'"
        is_valid, error = verify_syntax(invalid_code)

        assert not is_valid, "Fallback syntax check accepted invalid code"
        assert len(error) > 0


def test_libcst_not_installed_transform_code_string():
    """Test transform_code_string graceful failure when LibCST unavailable."""
    with patch('ast_refactor_helpers.LIBCST_AVAILABLE', False):
        code = "x = 42"

        success, error, result = transform_code_string(
            code,
            RenameAttribute,
            old_name="old",
            new_name="new"
        )

        assert not success
        assert "LibCST not installed" in error
        assert result == code  # Returns original code unchanged


def test_libcst_not_installed_safe_transform_file(tmp_path):
    """Test safe_transform_file graceful failure when LibCST unavailable."""
    with patch('ast_refactor_helpers.LIBCST_AVAILABLE', False):
        test_file = tmp_path / "test.py"
        test_file.write_text("x = 42")

        success, error, count = safe_transform_file(
            str(test_file),
            RenameAttribute,
            old_name="old",
            new_name="new"
        )

        assert not success
        assert "LibCST not installed" in error
        assert count == 0


# =============================================================================
# Test: Edge Cases and Error Handling
# =============================================================================

def test_verify_syntax_empty_string():
    """Test syntax verification with empty string."""
    is_valid, error = verify_syntax("")
    assert is_valid, "Empty string should be valid"


def test_verify_syntax_whitespace_only():
    """Test syntax verification with whitespace only."""
    is_valid, error = verify_syntax("   \n\t\n  ")
    assert is_valid, "Whitespace-only should be valid"


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_transform_code_string_with_syntax_error():
    """Test transform handles syntax errors gracefully."""
    invalid_code = "print('hello'"

    success, error, result = transform_code_string(
        invalid_code,
        RenameAttribute,
        old_name="old",
        new_name="new"
    )

    assert not success
    assert len(error) > 0
    assert result == invalid_code


def test_safe_transform_file_not_found(tmp_path):
    """Test safe_transform_file with non-existent file."""
    non_existent = tmp_path / "does_not_exist.py"

    success, error, count = safe_transform_file(
        str(non_existent),
        RenameAttribute,
        old_name="old",
        new_name="new"
    )

    assert not success
    assert "not found" in error.lower()
    assert count == 0


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_transformer_modification_counter():
    """Test that modification counter works correctly."""
    code = "old = old + old"

    class CountingTransformer(LibCSTTransformer):
        def leave_Name(self, original_node, updated_node):
            if updated_node.value == "old":
                self._increment_modifications()
                return updated_node.with_changes(value="new")
            return updated_node

    transformer = CountingTransformer()
    assert transformer.modifications == 0

    # Apply transformation via transform_code_string
    from ast_refactor_helpers import cst
    module = cst.parse_module(code)
    module.visit(transformer)

    assert transformer.modifications == 3


# =============================================================================
# Test: Real-World Scenarios
# =============================================================================

@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_rename_attribute_preserves_comments():
    """Test that renaming preserves surrounding comments."""
    code = dedent("""
        # Initialize old_attr
        self.old_attr = value  # TODO: refactor

        # Access old_attr
        return self.old_attr
    """)

    success, error, result = transform_code_string(
        code,
        RenameAttribute,
        old_name="old_attr",
        new_name="new_attr"
    )

    assert success
    assert "# Initialize" in result
    assert "# TODO: refactor" in result
    assert "# Access" in result
    assert "new_attr" in result


@pytest.mark.skipif(not LIBCST_AVAILABLE, reason="LibCST not installed")
def test_transform_multiple_attributes():
    """Test renaming multiple different attributes."""
    code = dedent("""
        obj.foo = 1
        obj.bar = 2
        obj.baz = 3
    """)

    # Rename foo -> new_foo
    success, error, result = transform_code_string(
        code,
        RenameAttribute,
        old_name="foo",
        new_name="new_foo"
    )

    assert success
    assert "new_foo" in result
    assert "obj.bar" in result  # Other attributes unchanged
    assert "obj.baz" in result
