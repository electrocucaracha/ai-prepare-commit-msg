"""Tests for TypeSafe-compatible commit type decisions."""

from types import SimpleNamespace

import pytest

from ai_prepare_commit_msg import decision


def test_add_commit_type_replaces_prefix_and_preserves_body(monkeypatch):
    """Classify untyped text even if the generator supplied a type and scope."""
    observed = []

    def classify(description, base_url, model):
        observed.append((description, base_url, model))
        return "fix"

    monkeypatch.setattr(decision, "choose_type", classify)
    message = "chore(scope): correct invalid input\n\nExplain why."

    assert decision.add_commit_type(message, "http://127.0.0.1:11435", "laya") == (
        "fix: correct invalid input\n\nExplain why."
    )
    assert observed == [
        ("correct invalid input\n\nExplain why.", "http://127.0.0.1:11435", "laya")
    ]


def test_add_commit_type_rejects_empty_description(monkeypatch):
    """An empty title must fail before contacting the decision service."""
    monkeypatch.setattr(
        decision,
        "choose_type",
        lambda *_args: pytest.fail("Decision should not be requested"),
    )
    with pytest.raises(ValueError, match="Generated commit description is empty"):
        decision.add_commit_type("chore: ", "http://127.0.0.1:11435")


@pytest.mark.parametrize(
    ("base_url", "expected_model"),
    [
        (
            "https://api.typesafe.ai",
            "jev-latest",
        ),
        (
            "http://127.0.0.1:11435",
            "laya",
        ),
    ],
)
def test_choose_type_uses_compatible_choice_api(monkeypatch, base_url, expected_model):
    """Both services receive the generated description and return a choice."""
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    observed = {}

    class FakeClient:
        def __init__(self, **kwargs):
            observed["options"] = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def system_one(self, *, state, questions):
            observed["state"] = state
            observed["question"] = questions["commit_type"]
            return SimpleNamespace(
                choices={"commit_type": SimpleNamespace(choice="fix")}
            )

    monkeypatch.setattr(decision, "TypeSafeClient", FakeClient)
    assert decision.choose_type("correct invalid input", base_url) == "fix"
    assert observed["options"] == {
        "base_url": base_url,
        "api_key": "test-key",
        "model": expected_model,
        "timeout": 15,
    }
    assert observed["state"] == "correct invalid input"
    assert isinstance(observed["question"], decision.Choice)
    assert "fix" in observed["question"].criteria


def test_choose_type_requires_jev_key(monkeypatch):
    """Do not send an unauthenticated request to Jev."""
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="TYPESAFE_API_KEY"):
        decision.choose_type("description", "https://api.typesafe.ai")


def test_choose_type_rejects_unknown_answer(monkeypatch):
    """Reject unsupported types rather than writing malformed commits."""

    class FakeClient:
        def __init__(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def system_one(self, **_kwargs):
            return SimpleNamespace(
                choices={"commit_type": SimpleNamespace(choice="unknown")}
            )

    monkeypatch.setattr(decision, "TypeSafeClient", FakeClient)
    with pytest.raises(ValueError, match="unsupported commit type"):
        decision.choose_type("description", "http://127.0.0.1:11435")


def test_choose_type_does_not_require_key_for_local_service(monkeypatch):
    """The SDK gets a placeholder key for an unprotected local Ollaya server."""
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    observed = {}

    class FakeClient:
        def __init__(self, **kwargs):
            observed.update(kwargs)

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def system_one(self, **_kwargs):
            return SimpleNamespace(
                choices={"commit_type": SimpleNamespace(choice="docs")}
            )

    monkeypatch.setattr(decision, "TypeSafeClient", FakeClient)
    assert decision.choose_type("update docs", "http://127.0.0.1:11435") == "docs"
    assert observed["api_key"] == "local"


def test_choose_type_rejects_insecure_jev_url(monkeypatch):
    """Never send a Jev API key over plain HTTP."""
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    with pytest.raises(ValueError, match="HTTPS"):
        decision.choose_type("description", "http://api.typesafe.ai")
