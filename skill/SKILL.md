---
name: refactor
description: Multi-file refactoring with orchestration - discovers synergies and assigns tasks to agents.
category: Refactoring
triggers:
  - /refactor
aliases:
  - /refactor

suggest:
  - /analyze
  - /test
  - /comply
  - /evolve
---

## Code Editing Patterns

For Python code editing patterns and anti-patterns:
- **Authority**: code-python Neural Cache
- **Example**: `/search "ThreadPoolExecutor KeyboardInterrupt immediate cleanup"`
- **Example**: `/search "string manipulation AST LibCST code editing"`

Reflect automatically propagates code editing learnings to code-python. Query CKS for patterns.


# /refactor - Multi-File Refactoring Orchestrator

## Purpose

Multi-file refactoring with orchestration — discovers synergies across files, prioritizes findings, and executes TDD characterization tests before refactoring.

## Project Context

### Constitution / Constraints
- **Solo-dev constraints apply** (CLAUDE.md)
- **No enterprise patterns**: Filter out service extraction, factory patterns, complex abstractions
- **Constitutional filter required**: All recommendations must pass SoloDevConstitutionalFilter
- **TDD mandatory**: Refactoring uses characterization tests before changes

### Technical Context
### Python Regex Best Practices

#### Regex Pattern String Escaping

When writing Python regex patterns with character classes containing quote characters (`['"`]`), match the outer string delimiter to avoid syntax errors:

- **Pattern has double quotes inside:** Use `r'...'` (single-quoted raw string)
  ```python
  # CORRECT: Character class has ", so use ' as outer delimiter
  re.compile(r'pattern["\`](.+?)["\`]')
  ```

- **Pattern has single quotes inside:** Use `r"..."` (double-quoted raw string)
  ```python
  # CORRECT: Character class has ', so use " as outer delimiter
  re.compile(r"pattern['`](.+?)['`]")
  ```

**Verification:** Always compile regex patterns immediately after creation with `re.compile()` to catch syntax errors early.

- **7-step workflow**: Discovery → Prioritization → Constitutional Filter → RED Phase → Output → Refactor → Regression
- **Parallel agents**: 3+ agents for bugs/logic, DRY/simplicity, conventions
- **Priority levels**: P0 (bugs/race), P1 (error handling), P2 (DRY), P3 (conventions)
- **Synergy types**: extract, merge, consolidate, standardize, restructure
- **Integration**: /aid (single-file), /code-python (standards), /complexity (analysis)

### Architecture Alignment
- Integrates with /analyze (code analysis), /test (coverage), /comply (standards)
- Links to /evolve (modernization), /tdd (test-driven refactoring)
- Part of code quality ecosystem

## Your Workflow

1. **DISCOVER** — Launch 3+ parallel Task agents (bugs/logic, DRY/simplicity, conventions). For Python, add `python-simplifier` as Agent 4.
2. **DEDUPLICATE** — Merge findings where multiple agents flagged the same code location.
3. **PRIORITIZE** — Aggregate findings by priority (P0→P3)
4. **CONSTITUTIONAL FILTER** — Apply SoloDevConstitutionalFilter to all recommendations
   - **If `--dry-run`: STOP HERE.** Present findings and summary. Do not proceed.
5. **RED PHASE** — Create characterization tests for each finding BEFORE applying changes
6. **REFACTOR** — Apply changes for each finding (tests now pass - GREEN phase)
7. **REGRESSION** — Run full test suite, verify no new failures


## TDD Checkpoint (MANDATORY - Cannot Skip)

**CRITICAL:** Before ANY code modification, complete TDD phases for each finding.

### TDD Enforcement Flow

```
For each refactoring finding:
    ↓
1. Check exemption status
    ├─ Exempt? → Skip TDD (docs, config, .staging/)
    └─ Not exempt? → Continue
    ↓
2. RED Phase: Write characterization test
    └─ Verify test FAILS (must fail before changes)
    ↓
3. Apply refactoring changes
    ↓
4. GREEN Phase: Verify test PASSES
    └─ Verify test PASSES (must pass after changes)
    ↓
5. REGRESSION Phase: Run related tests
    └─ Verify no new failures
    ↓
6. Store evidence in .evidence/
```

### Exemption Detection

**These file types are EXEMPT from TDD:**

| Pattern | Rationale |
|---------|-----------|
| `.md`, `.rst` | Documentation - no code behavior |
| `.json`, `.yaml`, `.toml`, `.ini` | Configuration - data only |
| `tests/` | Test files themselves |
| `.staging/`, `scripts/` | Exploratory/temporary code |

**Implementation:**

```python
def is_exempt_from_tdd(file_path: str) -> bool:
    """Check if file is exempt from TDD requirement.

    Args:
        file_path: Path to file being modified

    Returns:
        True if file is exempt from TDD, False otherwise
    """
    exempt_patterns = [
        '.md', '.rst',  # Documentation
        '.json', '.yaml', '.yml', '.toml', '.ini',  # Config files
        'tests/',  # Test files themselves
        '.staging/', 'scripts/',  # Exploratory/temporary
    ]

    file_path_lower = file_path.lower()
    return any(file_path_lower.endswith(p) or f'/{p}' in file_path_lower for p in exempt_patterns)
```

### TDD Phase Implementation

```python
import json
import subprocess
from datetime import datetime
from pathlib import Path
from src.core.evidence_collector import collect_test_evidence, verify_tdd_red, verify_tdd_green

def create_rollback_plan(finding: dict) -> dict:
    """Generate rollback plan before refactoring.

    Args:
        finding: Refactoring finding with file paths and changes

    Returns:
        dict: Rollback plan with git state and recovery commands
    """
    timestamp = datetime.now().isoformat()
    finding_id = finding.get('id', 'unknown')

    # Capture current git state
    git_commit_before = subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'],
        text=True,
        cwd=Path.cwd()
    ).strip()

    rollback_plan = {
        'timestamp': timestamp,
        'files_changed': finding.get('files', []),
        'git_commit_before': git_commit_before,
        'rollback_command': f'git revert {git_commit_before}',
        'test_baseline': 'pytest tests/ -v',  # Store test command
        'finding_id': finding_id
    }

    # Store in .evidence/refactor/rollbacks/{timestamp}_{finding_id}.json
    rollback_dir = Path('.evidence/refactor/rollbacks')
    rollback_dir.mkdir(parents=True, exist_ok=True)
    rollback_file = rollback_dir / f'{timestamp.replace(":", "-")}_{finding_id}.json'
    rollback_file.write_text(json.dumps(rollback_plan, indent=2), encoding='utf-8')

    return rollback_plan

def cleanup_rollback_plan(timestamp: str) -> None:
    """Remove rollback plan after successful refactoring.

    Args:
        timestamp: Timestamp of rollback plan to cleanup
    """
    rollback_dir = Path('.evidence/refactor/rollbacks')
    if rollback_dir.exists():
        for plan_file in rollback_dir.glob(f'{timestamp.replace(":", "-")}_*.json'):
            plan_file.unlink()

def characterize_behavior(func, inputs):
    """Capture current behavior before refactoring.

    Args:
        func: Function to characterize
        inputs: Input arguments for the function

    Returns:
        dict: Behavior snapshot with inputs, outputs, side-effects, performance
    """
    import time
    from typing import Any

    # Track state changes
    state_before = get_state_snapshot()

    # Measure performance
    start_time = time.perf_counter()
    try:
        output = func(*inputs)
        success = True
    except Exception as e:
        output = str(e)
        success = False
    end_time = time.perf_counter()

    # Detect side-effects
    state_after = get_state_snapshot()
    side_effects = detect_state_changes(state_before, state_after)

    return {
        'input': inputs,
        'output': output,
        'success': success,
        'side_effects': side_effects,
        'duration_ms': (end_time - start_time) * 1000
    }

def verify_behavior_preserved(before: dict, after: dict) -> bool:
    """Verify behavior preserved after refactoring.

    Args:
        before: Behavior characterization before refactoring
        after: Behavior characterization after refactoring

    Returns:
        bool: True if behavior preserved (within tolerance), False otherwise
    """
    # Compare outputs
    if before['output'] != after['output']:
        return False

    # Check performance within 10% tolerance
    if after['duration_ms'] > before['duration_ms'] * 1.1:
        return False

    # Verify no new side-effects
    if set(after['side_effects']) - set(before['side_effects']):
        return False

    return True

def get_state_snapshot() -> dict:
    """Capture current system state for side-effect detection.

    Returns:
        dict: Snapshot of file system, environment, and relevant state
    """
    import os
    from pathlib import Path

    # File system state (limited to working directory)
    cwd_files = {
        str(p): p.stat().st_mtime
        for p in Path.cwd().rglob('*')
        if p.is_file() and not p.name.startswith('.')
    }

    # Environment state (limited, non-sensitive)
    env_snapshot = {
        'cwd': os.getcwd(),
        'python_path': os.environ.get('PYTHONPATH', ''),
    }

    return {
        'files': cwd_files,
        'env': env_snapshot,
        'timestamp': datetime.now().isoformat()
    }

def detect_state_changes(before: dict, after: dict) -> list:
    """Detect side-effects from state snapshots.

    Args:
        before: State snapshot before function call
        after: State snapshot after function call

    Returns:
        list: List of detected side-effect descriptions
    """
    changes = []

    # Detect file changes
    before_files = set(before['files'].keys())
    after_files = set(after['files'].keys())

    # New files created
    new_files = after_files - before_files
    if new_files:
        changes.append(f'created_files: {len(new_files)}')

    # Modified files
    common_files = before_files & after_files
    modified = [
        f for f in common_files
        if before['files'][f] != after['files'][f]
    ]
    if modified:
        changes.append(f'modified_files: {len(modified)}')

    # Deleted files
    deleted_files = before_files - after_files
    if deleted_files:
        changes.append(f'deleted_files: {len(deleted_files)}')

    return changes

def red_phase(finding: dict) -> str:
    """RED: Write characterization test, verify it FAILS."""
    test_file = find_or_create_test(finding['file_path'], finding)
    artifact = collect_test_evidence(f"pytest {test_file} -v", description=f"RED: {finding['title']}")
    if not verify_tdd_red(artifact).is_verified:
        raise RuntimeError(f"TDD RED violated: {test_file} must FAIL before changes")
    return test_file

def green_phase(finding: dict, test_file: str):
    """GREEN: Verify test PASSES after refactoring."""
    artifact = collect_test_evidence(f"pytest {test_file} -v", description=f"GREEN: {finding['title']}")
    result = verify_tdd_green(artifact)
    if not result.is_verified:
        raise RuntimeError(f"TDD GREEN failed: {test_file} must PASS. Failures: {result.failure_output}")

def regression_phase(finding: dict):
    """REGRESSION: Run related tests, verify no new failures."""
    module = finding['file_path'].split('/')[-1].replace('.py', '')
    artifact = collect_test_evidence(f"pytest tests/ -k '{module}' -v", description=f"REGRESSION: {finding['title']}")
    failed = artifact.data.get('test_stats', {}).get('failed', 0)
    if failed > 0:
        raise RuntimeError(f"REGRESSION failed: {failed} new failures in {module}")

def find_or_create_test(file_path: str, finding: dict) -> str:
    """Find existing test or delegate to tdd-test-writer subagent."""
    module_name = file_path.split('/')[-1].replace('.py', '')
    for candidate in [f"tests/test_{module_name}.py", "tests/test_refactor_safety.py"]:
        if Path(candidate).exists():
            return candidate
    # No test exists — delegate to tdd-test-writer subagent
    content = tdd_test_writer.create_characterization_test(file_path=file_path, finding=finding)
    test_file = f"tests/test_{module_name}.py"
    Path(test_file).write_text(content, encoding='utf-8')
    return test_file

def refactor_with_tdd(finding: dict):
    """Full TDD cycle: exemption → rollback → characterize → RED → refactor → GREEN → REGRESSION."""
    if is_exempt_from_tdd(finding['file_path']):
        apply_refactoring(finding)
        return

    # Step 1: Create rollback plan
    rollback_plan = create_rollback_plan(finding)

    # Step 2: Characterize current behavior (if applicable)
    # Note: target_function and test_inputs should be extracted from finding context
    # This is an optional enhancement for critical refactoring operations
    target_function = finding.get('target_function')
    test_inputs = finding.get('test_inputs', [])

    behavior_before = None
    if target_function and test_inputs:
        behavior_before = characterize_behavior(target_function, test_inputs)

    # Step 3: RED phase
    test_file = red_phase(finding)

    # Step 4: Apply refactoring
    apply_refactoring(finding)

    # Step 5: GREEN phase with behavior verification (if characterization was performed)
    behavior_after = None
    if target_function and test_inputs:
        behavior_after = characterize_behavior(target_function, test_inputs)
        if not verify_behavior_preserved(behavior_before, behavior_after):
            raise RuntimeError("Behavior changed unexpectedly - rollback required")

    green_phase(finding, test_file)

    # Step 6: REGRESSION phase
    regression_phase(finding)

    # Step 7: Cleanup rollback plan on success
    cleanup_rollback_plan(rollback_plan['timestamp'])
```

### Error Messages Reference

**When TDD phases are violated, use these specific error messages:**

| Phase | Error Message | User Action |
|-------|--------------|-------------|
| **RED** | `TDD RED phase violated: {test_file} must FAIL before changes` | Write test that captures current behavior |
| **GREEN** | `TDD GREEN phase failed: {test_file} must PASS after changes` | Fix code to make test pass, or revert |
| **REGRESSION** | `REGRESSION phase failed: {N} new failures detected` | Fix regressions before completing |

---

## Validation Rules

- **Before recommending**: Apply SoloDevConstitutionalFilter check
- **Before refactoring**: Create characterization tests for current behavior
- **Before suggesting extraction**: Verify actual reuse benefit (not hypothetical)
- **Constitutional compliance**: Auto-filter prohibited patterns (service extraction, factory patterns)

### Prohibited Actions
- Recommending service extraction without proven need
- Adding abstraction layers for "flexibility" (YAGNI)
- Implementing factory patterns (enterprise bloat)
- Suggesting changes without reading actual code first

## Execution Directive

**Invoke the multi-file-refactor skill using the Skill tool.**

7-Step Workflow with Orchestration:

1. **DISCOVER** - If 3+ files, launch 5 parallel Task agents:
   - Agent 1: `adversarial-compliance` — Bugs/Logic focus (race conditions, error handling, **TOCTOU patterns**)
   - Agent 2: `adversarial-performance` — DRY/Simplicity focus (duplication, extraction, **concurrency analysis**)
   - Agent 3: `adversarial-quality` — Conventions focus (type hints, patterns, maintainability)
   - **For Python**: Add `python-simplifier` (assessment mode) as Agent 4 for Python-specific standards. Runs in parallel with the other 3 agents.
   - **Agent 5**: `code-reuse` — Searches for existing utilities and helpers before suggesting extraction (prevents duplicate abstractions)

   **Agent prompt must include:**
   - Target directory path and file list (or glob pattern)
   - Scope limits: "Analyze only files in {target}, do not suggest changes to files outside scope"
   - For `--dry-run`: "Report findings only. Do not edit files."

2. **DEDUPLICATE** - Before prioritizing, merge findings where multiple agents flagged the same code location. Keep the highest-severity version, combine evidence from both agents.

3. **PRIORITIZE** - Aggregate findings by priority:
   - P0: Bugs & Race Conditions (fix first)
   - P1: Error Handling (bare except, swallowed errors)
   - P2: DRY Violations (duplicate code)
   - P3: Conventions (type hints, formatting)

4. **CONSTITUTIONAL FILTER** - Apply SoloDevConstitutionalFilter to all recommendations

**If `--dry-run`: STOP HERE.** Present findings grouped by priority, then by file, with a summary of total findings by severity and top 3 most actionable items. Do not proceed to steps 5-7.

5. **RED PHASE** - Create characterization tests for each finding BEFORE applying changes
   - Write tests capturing current behavior
   - Verify tests FAIL (RED phase requirement)
   - Collect evidence in .evidence/

6. **REFACTOR** - Apply changes for each finding (tests now pass - GREEN phase)

7. **REGRESSION** - Run full test suite, verify no new failures

## CRITICAL: Test Before Presenting

**MANDATORY WORKFLOW:** Characterization tests MUST be created and verified as FAILING before any findings are presented to the user.

**DO NOT:** Ask user "Should I create tests first?" or "Create characterization tests first?"
**DO:** Create tests automatically as step 4 (RED phase)

**WRONG:** Discover findings → Ask user "Should I create tests first?"
**RIGHT:** Discover findings → Create tests → Verify RED → Present findings

The RED phase (capture current behavior) happens AUTOMATICALLY. This is not delegated to `/tdd` - it is executed immediately by this skill.

## Agent Enhancement Specifications

### Complexity Triage (Agent 2 Enhancement)

**Agent 2: `adversarial-performance` — DRY/Simplicity focus** now includes:

**Complexity triage process** (Priority 2 Enhancement):
For each file in target scope:
1. Calculate cyclomatic complexity (McCabe metric)
2. Flag files with CC ≥ 15 as HIGH_COMPLEXITY
3. Flag files with CC ≥ 20 as VERY_HIGH_COMPLEXITY
4. Recommend enhanced safety measures for high-complexity files:
   - Extra characterization tests
   - Smaller, incremental changes
   - Manual review before automated refactoring

**Output format:**
```
COMPLEXITY-001: HIGH_COMPLEXITY
File: src/complex_module.py
Cyclomatic Complexity: 18
Recommendation: Use smaller incremental changes, extra characterization tests
Priority: HIGH (complexity increases refactoring risk)
```

**Constitutional filter compliance:**
- Complexity detection is appropriate for professional quality standards
- Must not suggest "scalability requirements" or enterprise patterns
- Focus on code safety, not premature optimization

### Import Hygiene (Agent 3 Enhancement)

**Agent 3: `adversarial-quality` — Conventions focus** now includes:

**Import hygiene checks** (Priority 2 Enhancement):
1. **Unused imports:** Detect imported modules never referenced in code
2. **Circular dependencies:** Detect modules that import each other
3. **Dead code:** Detect unused functions, classes, variables
4. **Import ordering:** Verify PEP 8 compliance (stdlib, third-party, local)

**Allowed patterns** (false positive prevention):
- `from typing import TYPE_CHECKING` (used for type hints only)
- `if TYPE_CHECKING:` blocks (type checking imports)
- `# noqa` comments (explicitly allowed)
- `# type: ignore` comments (explicitly allowed)

**Output format:**
```
IMPORT-001: Unused import detected
File: src/module.py:5
Import: `import os` (never referenced)
Action: Remove unused import
Impact: Cleaner code, faster imports
```

```
IMPORT-002: Circular dependency detected
Files: src/auth.py → src/user.py → src/auth.py
Action: Restructure to break cycle
Impact: Prevents import errors, improves testability
```

**Constitutional filter compliance:**
- Import hygiene is appropriate for code quality standards
- Must not suggest "service extraction" to fix circular dependencies
- Focus on local restructuring, not architectural changes

## Quick Start

```bash
# Refactor a directory (finds synergies across all files)
/refactor src/features/lib/llm_providers/

# Refactor with glob pattern
/refactor "**/*provider*.py"

# Refactor specific files together
/refactor file1.py file2.py file3.py

# Dry run (analysis only, no changes)
/refactor src/ --dry-run

# Focus on specific concern (tunes agent prompts)
/refactor src/ --focus security
/refactor src/ --focus complexity
/refactor src/ --focus architecture

# Focus on specific synergy type
/refactor src/ --synergy-type extract
```

## Smart Defaults

| Feature | Default | When Disabled |
|---------|---------|---------------|
| **Comprehensive focus** | All agents run (bugs/logic, DRY/simplicity, conventions) | `--focus <lens>` |
| **Confidence filtering** | ON (80% threshold) | `--no-confidence-filter` |
| **Recent mode** | ON if git repo has changes | `--no-recent` |
| **Exploration** | ON for >20 files | `--no-explore` |
| **Multi-review** | ON by default (parallel) | `--no-multi-review` |

## Focus Lens (Scope Narrowing Only)

**IMPORTANT:** Default behavior runs ALL 3 agents with comprehensive analysis. Focus lens only tunes agent prompts, never reduces coverage.

| Focus | Agent Tuning | What It Emphasizes |
|-------|--------------|-------------------|
| **default** (no flag) | All agents: full scope | Publication-ready refactoring |
| `--focus security` | Agent 1: race conditions, injection, auth issues | Vulnerabilities first |
| `--focus complexity` | Agent 2: CC ≥ 10 functions, nested logic | High-CC targets first |
| `--focus performance` | Agent 1: resource leaks, bottlenecks, N+1 patterns | Performance issues first |
| `--focus architecture` | All agents: boundary violations, coupling | Structure and boundaries |
| `--focus test` | Agent 3: missing tests, coverage gaps | Test coverage first |
| `--focus quality` | Agent 2 & 3: standards, conventions | Code quality and style |

**Never skip agents without explicit user request. Default is always comprehensive analysis.**

## Constitutional Compliance (REQUIRED)

**CRITICAL:** All refactoring recommendations MUST be filtered against solo-dev constitutional constraints.

### Prohibited Patterns (Auto-Filter)

Before suggesting any refactoring, check against these prohibited patterns (CLAUDE.md:240-262):

| Pattern | Filter Because | Alternative |
|---------|---------------|-------------|
| `lock ordering`, `acquisition order` | Enterprise bloat | Use single RLock per object |
| `continuous monitoring` | Background service prohibited | Use on-demand `/health` |
| `real-time metrics` | Background service prohibited | Use query-based metrics |
| `complex abstraction` | Enterprise pattern prohibited | Keep it simple |
| `scalability requirement` | Enterprise pattern prohibited | Optimize when needed |
| `enterprise-grade` | Enterprise pattern prohibited | Use simple solution |

### Required Filter Step

**Before generating action items, ALWAYS run:**

```python
# Import the constitutional filter
from src.core.solo_dev_constitutional_filter import SoloDevConstitutionalFilter

filter_obj = SoloDevConstitutionalFilter()

# Check each proposed refactoring
for action in proposed_refactorings:
    result = filter_obj.check_action_item(action)
    if result.violates_constitution:
        # Skip this action - don't suggest it
        continue
```

### Why This Matters

Refactoring suggestions are high-risk for enterprise bloat:
- "Extract to service" → unnecessary microservice
- "Add abstraction layer" → over-engineering
- "Implement factory pattern" → enterprise pattern

## Synergy Types

| Type | Description | Example |
|------|-------------|---------|
| `extract` | Extract common code to shared module | 3 files have similar validation logic |
| `merge` | Merge similar interfaces | 2 protocol classes can combine |
| `consolidate` | Consolidate scattered patterns | Config access across 5 files |
| `standardize` | Standardize inconsistent patterns | Error handling varies by file |
| `restructure` | Restructure to break cycles | Circular imports between modules |

## Options

| Option | Description |
|--------|-------------|
| `--focus <lens>` | Tune agent prompts to specific concern (security, complexity, performance, architecture, test, quality) |
| `--agents N` | Override auto-determined agent count (1-10) |
| `--synergy-type TYPE` | Filter by synergy type |
| `--min-confidence N` | Only show synergies with confidence >= N (default: 80) |
| `--max-effort LEVEL` | Filter by effort (low, medium, high) |
| `--include-aid` | Run /aid refactor on each file |
| `--include-complexity` | Include complexity analysis |
| `--no-py2025-check` | Skip Python 2025 standards validation |
| `--no-confidence-filter` | Disable confidence filtering |
| `--no-recent` | Disable recent mode (analyze all files) |
| `--no-explore` | Disable exploration phase |
| `--no-multi-review` | Disable multi-agent review |

## Evidence Collection

**MANDATORY:** All TDD phases use `src.core.evidence_collector` for verification. See TDD Phase Implementation above for the full `red_phase`, `green_phase`, and `regression_phase` functions.

### Quick Reference

```python
from src.core.evidence_collector import collect_test_evidence, verify_tdd_green, get_evidence_collector

baseline = collect_test_evidence("pytest tests/test_module.py -v")           # 1. Baseline
# ... apply refactoring ...
after = collect_test_evidence("pytest tests/test_module.py -v")              # 2. Verify
assert verify_tdd_green(after).is_verified, "Refactoring broke tests"
regression = collect_test_evidence("pytest tests/ -v")                        # 3. Regression
```

### Evidence Storage

All artifacts stored in `P:\.evidence/` — subdirectories: `commands/`, `tests/`, `files/`, `state/`, `refactor/`.

**New directories** (Priority 1 enhancements):
- `.evidence/refactor/rollbacks/` — Rollback plans with git state
- `.evidence/refactor/behavior/` — Behavior characterizations

| Phase | Evidence Required | Verification |
|-------|------------------|--------------|
| Rollback planning | Rollback plan JSON with git commit | Rollback plan created before refactoring |
| Characterization | Behavior snapshots (before/after) | Behavior preserved within 10% tolerance |
| Refactoring | Post-change test results | `verify_tdd_green()` passes |
| Regression | Full suite results | No new failures introduced |

## Sequential Enforcement (from /v)

**/v provides hook-based stage tracking to prevent skipping validation steps.**

Reference these hooks when implementing sequential enforcement in /refactor:

| Hook | Event | Purpose |
|------|-------|---------|
| `PreToolUse_v_stage_enforcer.py` | PreToolUse | Blocks skipping stages |
| `PostToolUse_v_halt_enforcer.py` | PostToolUse | Enforces halt gates |
| `PostToolUse_v_state_tracker.py` | PostToolUse | Tracks stage completion |
| `StopHook_v_completion_gate.py` | Stop | Validates completion |

**Integration pattern:**
```python
# For sequential refactoring phases (DISCOVER → PRIORITIZE → FILTER → RED → REFACTOR)
# Use /v's state tracking pattern:
from terminal_detection import detect_terminal_id

state_file = f"P:/.claude/state/refactor_{detect_terminal_id()}.json"
# Track phase: 'discovery', 'prioritization', 'constitutional_filter', 'red', 'refactor'
```

## Dead Code Detection (from /v Stage 3)

**/v uses Vulture 2.14 for unused code detection.**

Reference when adding dead code detection to /refactor's conventions agent:

```bash
# Dead code detection with Vulture 2.14
python -m vulture <target> --min-confidence 80
```

| Confidence | Meaning |
|-----------|---------|
| 100% | Definitely unused |
| 90-99% | Likely unused |
| 80-89% | Possibly unused |
| <80% | Too many false positives |

## Layer 4 Quality Gate (from /v)

**/v applies ≥80% confidence filtering to reduce false positives.**

Reference this pattern for /refactor's synergy detection:

```python
# Filter synergy findings by confidence threshold
MIN_CONFIDENCE = 80

high_confidence_findings = [
    f for f in all_findings
    if f.get('confidence', 0) >= MIN_CONFIDENCE
]

# Quality gate summary
summary = {
    'input': len(all_findings),
    'output': len(high_confidence_findings),
    'rejection_rate': (len(all_findings) - len(high_confidence_findings)) / len(all_findings) * 100
}
```

## See Also

- `/aid` - Single-file refactoring analysis
- `/code-python` - Python 2025 standards compliance
- `/complexity` - Code complexity analysis
- `/p2` - Promotion Phase 2: Review (invokes `/refactor --dry-run` as Step 1.5 for cross-file synergy detection)
- `/tdd` - TDD workflow with evidence collection details
- `/v` - Sequential validation pipeline (source of stage enforcement, dead code detection, quality gate)
