"""
/refactor - Multi-File Refactoring Orchestrator

Implements 8 priority improvements:
1. Rollback Automation (git-based)
2. Test Generation Integration (TDD phases)
3. Synergy Detection (cross-file patterns)
4. Complexity Triage (risk-based prioritization)
5. Incremental Refactoring Mode (state persistence)
6. Configuration-Based Thresholds (CLI + config file)
7. Progress Persistence (tracking completed findings)
8. Integration with /synergy skill
"""

# Import automation modules from canonical location
from __csf.src.refactor import (
    ComplexityScore,
    ComplexityTriage,
    RefactorConfig,
    RefactorState,
    RollbackManager,
    StateManager,
    TestGenerator,
    create_rollback_plan,
    detect_synergy,
    get_config,
    green_phase,
    load_refactor_state,
    red_phase,
    regression_phase,
    save_refactor_state,
    triage_by_complexity,
)

__all__ = [
    'RefactorConfig',
    'get_config',
    'RollbackManager',
    'create_rollback_plan',
    'TestGenerator',
    'red_phase',
    'green_phase',
    'regression_phase',
    'detect_synergy',
    'ComplexityTriage',
    'ComplexityScore',
    'triage_by_complexity',
    'StateManager',
    'RefactorState',
    'load_refactor_state',
    'save_refactor_state',
]


def main() -> int:
    """Main entry point for refactor skill."""
    # TODO: Implement CLI interface
    return 0
