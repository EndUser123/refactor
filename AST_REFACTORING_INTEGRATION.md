# AST-Based Refactoring Integration Plan

## Problem Statement

**Issue**: String-based code replacement (`.replace()`, `sed`, regex) can corrupt syntax and cause bugs.

**Example from yt-fts session**:
```python
# Intended replacement
"with contextlib.suppress(Exception):"

# Actual result after .replace()
"with contextlib suppress(Exception):"  # Missing dot - SyntaxError!
```

**Root Cause**: String replacement operates on text without understanding Python syntax structure.

## Proposed Solution

### Option 1: LibCST (Concrete Syntax Tree) - **RECOMMENDED**

**Why LibCST over ast/stdlib**:
- **Preserves formatting**: Comments, whitespace, style intact
- **Bijective**: Parse → Modify → Code roundtrip without loss
- **Safe**: Type-safe transformations, won't corrupt syntax
- **Battle-tested**: Used by Black, Pyupgrade, Pyright

**Installation**:
```bash
pip install libcst
```

**Example Usage**:
```python
import libcst as cst

# Safe: Replace function call while preserving formatting
class ContextlibSuppressReplacer(cst.CSTTransformer):
    def leave_Call(self, original_node):
        # Match: contextlib suppress(...)
        if (isinstance(original_node.func, cst.Attribute) and
            original_node.func.value.value == "contextlib" and
            original_node.func.attr.value == "suppress"):

            # Fix to: contextlib.suppress(...)
            return original_node.with_changes(
                func=original_node.func.with_changes(
                    attr=original_node.func.attr.with_changes(value="suppress")
                )
            )
        return original_node

# Apply transformation
code = Path("file.py").read_text()
module = cst.parse_module(code)
fixed = module.visit(ContextlibSuppressReplacer())
Path("file.py").write_text(fixed.code)
```

### Option 2: AST (stdlib) + Black formatting

**Pros**: No dependencies
**Cons**: Loses formatting (requires Black to fix), harder to write

**Example**:
```python
import ast

class ContextlibSuppressFixer(ast.NodeTransformer):
    def visit_Attribute(self, node):
        if (isinstance(node.value, ast.Name) and
            node.value.id == "contextlib" and
            node.attr == "suppress"):
            node.attr = "suppress"
        return node

# Parse, transform, regenerate (loses formatting)
tree = ast.parse(code)
fixed = ContextlibSuppressFixer().visit(tree)
ast.fix_missing_locations(fixed)
# Then run Black to restore formatting
```

## Integration Strategy

### Phase 1: Create Shared Utility Module

**File**: `P:/packages/refactor/ast_refactor_helpers.py`

**Contents**:
```python
"""
AST-based refactoring helpers using LibCST.

Provides safe, syntax-preserving code transformations
for skills: /simplify, /refactor, /code, /tdd
"""
import libcst as cst
from pathlib import Path
from typing import Callable


class LibCSTTransformer(cst.CSTTransformer):
    """Base transformer with common utilities."""

    def __init__(self, filename: str | None = None):
        super().__init__()
        self.filename = filename
        self.modifications = 0


def safe_transform_file(
    filepath: str,
    transformer: type[cst.CSTTransformer],
    **kwargs
) -> tuple[bool, str, int]:
    """
    Apply AST transformation to file safely.

    Args:
        filepath: Path to file to transform
        transformer: LibCST transformer class
        **kwargs: Arguments passed to transformer

    Returns:
        (success, error_message, modification_count)
    """
    try:
        code = Path(filepath).read_text(encoding="utf-8")
        module = cst.parse_module(code)
        transformer_instance = transformer(**kwargs)
        modified = module.visit(transformer_instance)

        if transformer_instance.modifications > 0:
            Path(filepath).write_text(modified.code, encoding="utf-8")

        return True, "", transformer_instance.modifications
    except Exception as e:
        return False, str(e), 0


def transform_code_string(
    code: str,
    transformer: type[cst.CSTTransformer],
    **kwargs
) -> tuple[bool, str, str]:
    """
    Apply AST transformation to code string.

    Returns:
        (success, error_message, modified_code)
    """
    try:
        module = cst.parse_module(code)
        transformer_instance = transformer(**kwargs)
        modified = module.visit(transformer_instance)
        return True, "", modified.code
    except Exception as e:
        return False, str(e), code
```

### Phase 2: Update Skill Documentation

#### /simplify SKILL.md

**Add to "Phase 3: Fix Issues"**:
```markdown
### Code Modification Protocol (MANDATORY)

**CRITICAL**: Use AST-based refactoring for ALL Python code modifications.

**Priority Order**:
1. **AST-based (LibCST)**: Required for structural changes
   - Function/method renames
   - Import reorganization
   - Parameter additions/removals
   - Code extraction/inlining

2. **Precise string patterns**: Only for simple text substitutions
   - Variable name changes (no structural changes)
   - String content updates
   - Comment modifications
   - MUST include surrounding context (indentation, line breaks)

3. **Prohibited**:
   - NEVER use `.replace()` on code blocks
   - NEVER use `sed` for Python code
   - NEVER use regex for structural changes

**AST Refactoring Helpers**:
```python
from P.packages.refactor.ast_refactor_helpers import safe_transform_file

# Example: Fix corrupted method call
class MethodNameFixer(LibCSTTransformer):
    def leave_Attribute(self, original_node):
        if original_node.attr.value == "old_method":
            self.modifications += 1
            return original_node.with_changes(
                attr=original_node.attr.with_changes(value="new_method")
            )
        return original_node

success, error, count = safe_transform_file(
    "src/module.py",
    MethodNameFixer
)
```

**String Pattern Safety Checklist**:
- [ ] Pattern includes unique surrounding context
- [ ] Pattern includes indentation/line breaks
- [ ] Test pattern on file first before replacement
- [ ] Verify syntax after replacement
```

#### /refactor SKILL.md

**Add to "Refactoring Guidelines"**:
```markdown
### AST-Based Refactoring (REQUIRED)

**All Python refactoring MUST use LibCST transformations.**

**When to use AST**:
- Function/method extraction
- Parameter reordering
- Import reorganization
- Code movement across files
- Signature changes

**Available Helpers**:
```python
from P.packages.refactor.ast_refactor_helpers import (
    safe_transform_file,
    LibCSTTransformer,
)
```

**Example: Extract Method**:
```python
class ExtractMethodTransformer(LibCSTTransformer):
    def __init__(self, target_function: str, new_method: str):
        super().__init__()
        self.target_function = target_function
        self.new_method = new_method

    def leave_FunctionDef(self, original_node):
        if original_node.name.value == self.target_function:
            self.modifications += 1
            # Extract logic to new method
            return create_extracted_method(original_node)
        return original_node
```
```

#### /code SKILL.md

**Add to "Phase 5: TDD"**:
```markdown
### GREEN Phase: AST-Safe Implementation

**When implementing code from RED tests**:
- Use LibCST helpers for structural changes
- Use Write tool (full file replacement) for simple changes
- NEVER use `.replace()` on partial code blocks

**Implementation Pattern**:
```python
# 1. Write test (RED)
# 2. Implement using AST-safe method
# 3. Verify GREEN
```
```

#### /tdd SKILL.md

**Add to "GREEN Phase"**:
```markdown
### Code Modification Safety

**AST-based changes**:
```python
# Use LibCST for structural modifications
from refactor_helpers import safe_transform_file
```

**String-based changes** (only when safe):
- Full file replacement (Write tool)
- Comment-only changes
- String literal content changes

**Prohibited**:
- Partial code block `.replace()`
- Regex on code structure
- sed/awk for Python code
```

### Phase 3: Create Common Transformer Library

**File**: `P:/packages/refactor/transformers.py`

**Contents**:
```python
"""
Common LibCST transformers for refactoring tasks.
"""
import libcst as cst


class FixDotNotationTransformer(LibCSTTransformer):
    """Fix missing dots in attribute access (e.g., contextlib suppress)."""

    def leave_Call(self, original_node):
        if isinstance(original_node.func, cst.Name):
            # Pattern: "contextlib suppress(" should be "contextlib.suppress("
            if original_node.func.value == "contextlib":
                # Look for next token being a Name
                # This requires checking parent context
                pass
        return original_node


class ExtractMethodTransformer(LibCSTTransformer):
    """Extract selected statements into new method."""

    def __init__(self, target_lines: list[int], new_method_name: str):
        super().__init__()
        self.target_lines = target_lines
        self.new_method_name = new_method_name


class RenameParameterTransformer(LibCSTTransformer):
    """Rename function/method parameter across all call sites."""

    def __init__(self, function_name: str, old_param: str, new_param: str):
        super().__init__()
        self.function_name = function_name
        self.old_param = old_param
        self.new_param = new_param
```

### Phase 4: Create Verification Tests

**File**: `P:/packages/refactor/tests/test_ast_refactor.py`

```python
"""
Tests for AST-based refactoring helpers.
"""
import pytest
from refactor.ast_refactor_helpers import safe_transform_file, transform_code_string


def test_fix_contextlib suppress():
    """Test fixing missing dot in contextlib.suppress."""
    code = """
import contextlib
with contextlib suppress(Exception):
    pass
"""
    expected = """
import contextlib
with contextlib.suppress(Exception):
    pass
"""
    success, error, result = transform_code_string(
        code,
        FixDotNotationTransformer
    )
    assert success
    assert result == expected


def test_syntax_preservation():
    """Test that AST transformation preserves comments and formatting."""
    code = """
# This is a comment
with    contextlib.   suppress(Exception):  # Weird spacing
    pass
"""
    success, error, result = transform_code_string(
        code,
        FixDotNotationTransformer
    )
    assert success
    assert "# This is a comment" in result
```

## Benefits

1. **Syntax Safety**: Cannot corrupt Python syntax
2. **Formatting Preservation**: Comments, whitespace intact
3. **Testability**: Transformers are unit testable
4. **Debuggability**: Clear transformation logic
5. **Reusability**: Transformers shared across skills

## Trade-offs

| Approach | Pros | Cons | Use Case |
|----------|------|------|----------|
| **LibCST** | Safe, preserves formatting | Dependency (small) | All structural changes |
| **String (Write tool)** | Simple, no dependencies | Full file replacement only | Small changes, new files |
| **String (.replace)** | Fast for simple cases | **UNSAFE - syntax corruption** | Prohibited for code |

## Migration Path

1. **Immediate**: Update documentation to require LibCST
2. **Week 1**: Create `ast_refactor_helpers.py` module
3. **Week 2**: Write tests for common transformers
4. **Week 3**: Update skills to use helpers
5. **Week 4**: Audit existing code for string replacement bugs

## Success Criteria

- [ ] No more `.replace()` on Python code blocks
- [ ] All structural changes use LibCST
- [ ] Helper module has 90%+ test coverage
- [ ] Skills document AST-first approach
- [ ] 0 syntax corruption bugs reported

## References

- **LibCST**: https://libcst.readthedocs.io/
- **Black AST**: https://github.com/psf/black
- **Pyupgrade**: https://github.com/asottile/pyupgrade (uses LibCST)
