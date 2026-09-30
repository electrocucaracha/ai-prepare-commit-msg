"""Shared lifecycle hooks for Behave scenarios."""

from pytest import MonkeyPatch


def before_scenario(context, _scenario) -> None:
    """Create isolated monkeypatch state for each scenario.

    Args:
        context: Behave's shared scenario context.
        _scenario: Scenario being prepared.
    """
    context.patches = MonkeyPatch()
    context.retry_waits = []
    context.result = None
    context.repo = None


def after_scenario(context, _scenario) -> None:
    """Restore collaborators patched during a scenario.

    Args:
        context: Behave's shared scenario context.
        _scenario: Scenario that just completed.
    """
    context.patches.undo()
