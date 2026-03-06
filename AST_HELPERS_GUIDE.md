# AST-Based Refactoring Helpers

**Safe, syntax-preserving code transformations for Python.**

## Quick Reference

**Problem**: String-based code replacement (`.replace()`, `sed`, regex) can corrupt syntax.

**Solution**: Use LibCST (Concrete Syntax Tree) for structural changes.

## Installation

```bash
pip install libcst
```

## Quick Start

```python
from refactor.ast_refactor_helpers import safe_transform_file, RenameAttribute

# Rename all 'old_attr' to 'new_attr'
success, error, count = safe_transform_file(
    "src/module.py",
    RenameAttribute,
    old_name="old_attr",
    new_name="new_attr"
)
```

## Built-in Transformers

### `RenameAttribute(old_name, new_name)`

Rename attribute access across file.

```python
success, error, count = safe_transform_file(
    "src/module.py",
    RenameAttribute,
    old_name="foo",
    new_name="bar"
)
```

### `RemoveUnusedImport(module_name)`

Remove specific import statement.

```python
success, error, count = safe_transform_file(
    "src/module.py",
    RemoveUnusedImport,
    module_name="unused.module"
)
```

## Custom Transformers

```python
from refactor.ast_refactor_helpers import LibCSTTransformer, safe_transform_file
import libcst as cst

class MyTransformer(LibCSTTransformer):
    """Your custom transformer."""

    def leave_Call(self, original_node: cst.Call) -> cst.Call:
        """Transform function calls."""
        # Your transformation logic
        return modified_node

# Use it
success, error, count = safe_transform_file("src/module.py", MyTransformer)
```

## API

### `safe_transform_file(filepath, transformer, **kwargs)`

Apply AST transformation to file safely.

**Returns**: `(success: bool, error_message: str, modification_count: int)`

### `transform_code_string(code, transformer, **kwargs)`

Apply AST transformation to code string.

**Returns**: `(success: bool, error_message: str, modified_code: str)`

### `verify_syntax(code)`

Verify Python code syntax.

**Returns**: `(is_valid: bool, error_message: str)`

## Best Practices

### ✅ DO

- Use LibCST for structural changes
- Test transformers before applying
- Verify syntax after transformation

### ❌ DON'T

- Use `.replace()` on code blocks
- Use regex for structural changes
- Use `sed` for Python code

## Common Node Types

| Node Type | Usage |
|-----------|-------|
| `cst.Name` | Variable names, function names |
| `cst.Attribute` | Attribute access (obj.attr) |
| `cst.Call` | Function/method calls |
| `cst.FunctionDef` | Function definitions |
| `cst.Param` | Function parameters |

## Integration

This module is used by:
- `/simplify` - Code quality fixes
- `/refactor` - Multi-file refactoring
- `/code` - Feature development
- `/tdd` - Test-driven development

## Full Documentation

See `AST_REFACTORING_INTEGRATION.md` for complete integration guide and migration path.

## Requirements

- Python 3.12+
- LibCST 1.0+

## License

MIT
