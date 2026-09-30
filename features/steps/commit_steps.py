"""Behave steps that exercise the commit-message CLI boundary."""

from collections.abc import Iterator

import litellm
from behave import given, then, when
from click.testing import CliRunner

import ai_prepare_commit_msg


class DummyRepository:
    """In-memory repository used to observe CLI output."""

    def __init__(self, _path) -> None:
        """Initialize the repository with a fixed staged diff.

        Args:
            _path: Repository path supplied by the CLI.
        """
        self.written_message: str | None = None

    def get_diff_message(self) -> str:
        """Return staged changes that trigger message generation.

        Returns:
            A non-empty staged diff.
        """
        return "staged diff"

    def write_commit_msg(self, commit_msg: str) -> None:
        """Capture the commit message produced by the CLI.

        Args:
            commit_msg: Generated message to write.
        """
        self.written_message = commit_msg


class EmptyRepository(DummyRepository):
    """In-memory repository with no staged changes."""

    def get_diff_message(self) -> str:
        """Return no staged diff."""
        return ""


@given("staged changes are available")
def given_staged_changes(context) -> None:
    """Configure the CLI to read a repository containing staged changes.

    Args:
        context: Behave's shared scenario context.
    """
    repository = DummyRepository(None)
    context.repo = repository
    context.patches.setattr(
        ai_prepare_commit_msg.git, "GitRepository", lambda _path: repository
    )


@given("no staged changes are available")
def given_no_staged_changes(context) -> None:
    """Configure the CLI to read a repository with no staged changes."""
    repository = EmptyRepository(None)
    context.repo = repository
    context.patches.setattr(
        ai_prepare_commit_msg.git, "GitRepository", lambda _path: repository
    )


@given('the generator produces "{message}"')
def given_generated_message(context, message: str) -> None:
    """Configure LiteLLM to return a successful mock response.

    Args:
        context: Behave's shared scenario context.
        message: Commit message returned by the LLM.
    """
    _patch_litellm_completion(context, iter([message]))


@given('the generator returns empty messages before "{message}"')
def given_retrying_generator(context, message: str) -> None:
    """Configure LiteLLM with two empty responses followed by a success.

    Args:
        context: Behave's shared scenario context.
        message: Commit message returned after retries.
    """
    responses: Iterator[str] = iter([" ", " ", message])
    _patch_litellm_completion(context, responses)
    context.patches.setattr(
        ai_prepare_commit_msg.time,
        "sleep",
        context.retry_waits.append,
    )


@given("the generator returns only empty messages")
def given_empty_generator(context) -> None:
    """Configure LiteLLM to return whitespace for every retry."""
    _patch_litellm_completion(context, iter([" ", " "]))
    context.patches.setattr(
        ai_prepare_commit_msg.time,
        "sleep",
        context.retry_waits.append,
    )


@given("the LLM provider fails")
def given_failing_provider(context) -> None:
    """Configure the completion provider to raise an unexpected error."""

    def fail_completion(**_kwargs):
        raise RuntimeError("provider unavailable")

    context.patches.setattr(
        ai_prepare_commit_msg.llm.litellm,
        "completion",
        fail_completion,
    )


def _patch_litellm_completion(context, responses: Iterator[str]) -> None:
    """Make LiteLLM return documented ``mock_response`` completions.

    Args:
        context: Behave's shared scenario context.
        responses: Mock response text returned for each completion call.
    """
    real_completion = litellm.completion

    def completion_with_mock_response(**kwargs):
        return real_completion(mock_response=next(responses), **kwargs)

    context.patches.setattr(
        ai_prepare_commit_msg.llm.litellm,
        "completion",
        completion_with_mock_response,
    )


@given('the decision service selects "{commit_type}"')
def given_decision_type(context, commit_type: str) -> None:
    """Configure the decision service's selected Conventional Commit type.

    Args:
        context: Behave's shared scenario context.
        commit_type: Type returned by the decision service.
    """
    context.patches.setattr(
        ai_prepare_commit_msg.decision,
        "choose_type",
        lambda *_args: commit_type,
    )


@when("the generated message is approved")
def when_message_is_approved(context) -> None:
    """Run the CLI with confirmation accepted.

    Args:
        context: Behave's shared scenario context.
    """
    context.patches.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", lambda _message: True
    )
    context.result = CliRunner().invoke(
        ai_prepare_commit_msg.cli, ["--model", "openai/test-model"]
    )


@when("the generated message is rejected")
def when_message_is_rejected(context) -> None:
    """Run the CLI with confirmation declined."""
    context.patches.delenv("AI_PREPARE_COMMIT_AUTO_APPROVE", raising=False)
    context.patches.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", lambda _message: False
    )
    context.result = CliRunner().invoke(
        ai_prepare_commit_msg.cli, ["--model", "openai/test-model"]
    )


@when("generation is auto-approved with a retry limit of {retry_limit:d}")
def when_generation_retries(context, retry_limit: int) -> None:
    """Run the CLI with auto-approval and a bounded retry limit.

    Args:
        context: Behave's shared scenario context.
        retry_limit: Maximum number of LLM calls.
    """
    context.result = CliRunner().invoke(
        ai_prepare_commit_msg.cli,
        [
            "--model",
            "openai/test-model",
            "--auto-approve",
            "--retry",
            str(retry_limit),
        ],
    )


@when("generation is auto-approved with a decision service")
def when_generation_uses_decision_service(context) -> None:
    """Run the CLI with the optional decision service enabled.

    Args:
        context: Behave's shared scenario context.
    """
    context.result = CliRunner().invoke(
        ai_prepare_commit_msg.cli,
        [
            "--model",
            "openai/test-model",
            "--auto-approve",
            "--decision-url",
            "http://127.0.0.1:11435",
        ],
    )


@then("the command succeeds")
def then_command_succeeds(context) -> None:
    """Assert the CLI completed successfully.

    Args:
        context: Behave's shared scenario context.
    """
    assert context.result.exit_code == 0, context.result.output


@then('the command fails with "{message}"')
def then_command_fails_with(context, message: str) -> None:
    """Assert the CLI failed with the expected user-facing error."""
    assert context.result.exit_code != 0, context.result.output
    error_text = f"{context.result.output}{context.result.exception or ''}"
    assert message in error_text, f"Expected {message!r} in {error_text!r}"


@then('the commit message is "{message}"')
def then_commit_message_is_written(context, message: str) -> None:
    """Assert the generated message was sent to the repository.

    Args:
        context: Behave's shared scenario context.
        message: Expected commit message.
    """
    assert context.repo.written_message == message


@then("no commit message is written")
def then_no_commit_message_is_written(context) -> None:
    """Assert the repository did not receive a commit message."""
    assert context.repo.written_message is None


@then("{wait_count:d} retry waits occur")
def then_retry_waits_occur(context, wait_count: int) -> None:
    """Assert the configured number of retry delays occurred.

    Args:
        context: Behave's shared scenario context.
        wait_count: Expected number of retry waits.
    """
    assert len(context.retry_waits) == wait_count
