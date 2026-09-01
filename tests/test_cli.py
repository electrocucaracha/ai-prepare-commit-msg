# Copyright (c) 2026
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the CLI confirmation flow."""

# Tests intentionally access internal helpers of the CLI module.
# pylint: disable=protected-access

import io

from click.testing import CliRunner

import ai_prepare_commit_msg


class DummyRepo:
    """Small fake repository object for CLI tests."""

    def __init__(self, _path):
        self.written_message = None

    def get_diff_message(self):
        """Return a fixed non-empty diff to trigger message generation."""
        return "staged diff"

    def write_commit_msg(self, commit_msg):
        """Capture the generated commit message for assertions."""
        self.written_message = commit_msg


def _configure_cli_dependencies(monkeypatch):
    """Patch repo builder and LLM response for CLI tests.

    Returns:
        dict: Mutable holder with the created fake repository at ``holder["repo"]``.
    """
    holder = {}

    def build_repo(_path):
        repo = DummyRepo(_path)
        holder["repo"] = repo
        return repo

    monkeypatch.setattr(ai_prepare_commit_msg.git, "GitRepository", build_repo)
    monkeypatch.setattr(ai_prepare_commit_msg, "get_commit_msg", lambda *_args: "msg")

    return holder


def _always_true(_message):
    """Return True for confirmation prompts."""
    return True


def _always_empty_message(*_args):
    """Return an empty LLM response."""
    return ""


def _next_message(responses):
    """Create a function that returns the next mocked LLM response."""

    def get_message(*_args):
        return next(responses)

    return get_message


def _record_sleep_calls(monkeypatch):
    """Patch time.sleep and return a list that captures sleep durations."""
    sleep_calls = []

    def record_sleep(seconds):
        sleep_calls.append(seconds)

    monkeypatch.setattr(ai_prepare_commit_msg.time, "sleep", record_sleep)
    return sleep_calls


def _invoke_cli_with_retries(monkeypatch, llm_response, args):
    """Run the CLI with patched retry-related dependencies.

    Returns:
        tuple: (result, sleep_calls)
    """
    monkeypatch.setattr(ai_prepare_commit_msg, "get_commit_msg", llm_response)
    monkeypatch.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", _always_true
    )
    sleep_calls = _record_sleep_calls(monkeypatch)

    runner = CliRunner()
    result = runner.invoke(ai_prepare_commit_msg.cli, args)
    return result, sleep_calls


def test_cli_writes_message_after_confirmation(monkeypatch):
    """CLI writes the generated message when user confirms."""
    holder = _configure_cli_dependencies(monkeypatch)
    monkeypatch.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", lambda _m: True
    )

    runner = CliRunner()
    result = runner.invoke(ai_prepare_commit_msg.cli, ["--model", "test-model"])

    assert result.exit_code == 0
    assert holder["repo"].written_message == "msg"


def test_cli_aborts_when_confirmation_rejected(monkeypatch):
    """CLI aborts commit when user rejects generated message."""
    holder = _configure_cli_dependencies(monkeypatch)
    monkeypatch.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", lambda _m: False
    )

    runner = CliRunner()
    result = runner.invoke(ai_prepare_commit_msg.cli, ["--model", "test-model"])

    assert result.exit_code != 0
    assert "Commit message not approved; aborting commit." in result.output
    assert holder["repo"].written_message is None


def test_cli_auto_approve_skips_confirmation(monkeypatch):
    """CLI skips the confirmation function when auto-approve is enabled."""
    holder = _configure_cli_dependencies(monkeypatch)

    def fail_if_called(_message):
        raise AssertionError("confirmation should be skipped")

    monkeypatch.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", fail_if_called
    )

    runner = CliRunner()
    result = runner.invoke(
        ai_prepare_commit_msg.cli,
        ["--model", "test-model", "--auto-approve"],
    )

    assert result.exit_code == 0
    assert holder["repo"].written_message == "msg"


def test_cli_retries_until_message_generated(monkeypatch):
    """CLI retries empty results and writes the first non-empty message."""
    holder = {}

    def build_repo(_path):
        repo = DummyRepo(_path)
        holder["repo"] = repo
        return repo

    monkeypatch.setattr(ai_prepare_commit_msg.git, "GitRepository", build_repo)

    responses = iter(["", "   ", "final message"])
    result, sleep_calls = _invoke_cli_with_retries(
        monkeypatch,
        _next_message(responses),
        ["--model", "test-model", "--retry", "5"],
    )

    assert result.exit_code == 0
    assert holder["repo"].written_message == "final message"
    assert sleep_calls == [3, 3]


def test_cli_errors_when_retry_limit_reached(monkeypatch):
    """CLI exits with an error when message remains empty after all retries."""
    holder = {}

    def build_repo(_path):
        repo = DummyRepo(_path)
        holder["repo"] = repo
        return repo

    monkeypatch.setattr(ai_prepare_commit_msg.git, "GitRepository", build_repo)
    result, sleep_calls = _invoke_cli_with_retries(
        monkeypatch,
        _always_empty_message,
        ["--model", "test-model", "--retry", "2"],
    )

    assert result.exit_code != 0
    assert (
        "Generated commit message is empty after all retry attempts." in result.output
    )
    assert holder["repo"].written_message is None
    assert sleep_calls == [3]


def test_cli_uses_user_provided_retry_sleep(monkeypatch):
    """CLI waits for the user-provided retry sleep duration."""
    holder = {}

    def build_repo(_path):
        repo = DummyRepo(_path)
        holder["repo"] = repo
        return repo

    monkeypatch.setattr(ai_prepare_commit_msg.git, "GitRepository", build_repo)

    responses = iter(["", "message after wait"])
    result, sleep_calls = _invoke_cli_with_retries(
        monkeypatch,
        _next_message(responses),
        ["--model", "test-model", "--retry", "5", "--retry-sleep", "1.5"],
    )

    assert result.exit_code == 0
    assert holder["repo"].written_message == "message after wait"
    assert sleep_calls == [1.5]


def test_cli_skips_generation_when_no_staged_changes(monkeypatch):
    """CLI exits early without calling the LLM when there is nothing staged."""

    class EmptyDiffRepo(DummyRepo):
        """Fake repository reporting no staged changes."""

        def get_diff_message(self):
            """Return an empty diff to simulate no staged changes."""
            return ""

    holder = {}

    def build_repo(_path):
        repo = EmptyDiffRepo(_path)
        holder["repo"] = repo
        return repo

    monkeypatch.setattr(ai_prepare_commit_msg.git, "GitRepository", build_repo)

    def fail_if_called(*_args):
        raise AssertionError("LLM should not be called without staged changes")

    monkeypatch.setattr(ai_prepare_commit_msg, "get_commit_msg", fail_if_called)

    runner = CliRunner()
    result = runner.invoke(ai_prepare_commit_msg.cli, ["--model", "test-model"])

    assert result.exit_code == 0
    assert holder["repo"].written_message is None


def test_cli_logs_pre_commit_mode(monkeypatch, caplog):
    """CLI logs that it is running under pre-commit when files are passed."""
    _configure_cli_dependencies(monkeypatch)
    monkeypatch.setattr(
        ai_prepare_commit_msg, "_confirm_generated_message", lambda _m: True
    )
    monkeypatch.setenv("PRE_COMMIT", "1")

    runner = CliRunner()
    with caplog.at_level("INFO", logger=ai_prepare_commit_msg.__name__):
        result = runner.invoke(
            ai_prepare_commit_msg.cli,
            ["--model", "test-model", "--log-level", "INFO", "some_file.py"],
        )

    assert result.exit_code == 0
    assert any(
        "Running in pre-commit mode" in record.getMessage() for record in caplog.records
    )


class _FakeInteractiveStream:
    """Minimal stream stub with independent read and write buffers.

    ``io.StringIO`` shares a single cursor for reads and writes, so writing
    prompt text advances past pre-seeded input. This stub keeps input lines
    and captured output separate, matching how a real TTY behaves.
    """

    def __init__(self, input_text=""):
        self._lines = io.StringIO(input_text)
        self._output = io.StringIO()

    def write(self, text):
        """Capture written prompt/output text."""
        self._output.write(text)

    def flush(self):
        """No-op flush to satisfy the stream interface."""

    def readline(self):
        """Return the next pre-seeded input line."""
        return self._lines.readline()

    def getvalue(self):
        """Return everything written to this stream so far."""
        return self._output.getvalue()


def test_prompt_on_stream_accepts_default_yes_on_enter():
    """Pressing enter alone accepts the generated message (default 'yes')."""
    stream = _FakeInteractiveStream("\n")

    assert ai_prepare_commit_msg._prompt_on_stream(stream, "commit body") is True


def test_prompt_on_stream_accepts_explicit_yes():
    """An explicit 'y' response accepts the generated message."""
    stream = _FakeInteractiveStream("y\n")

    assert ai_prepare_commit_msg._prompt_on_stream(stream, "commit body") is True


def test_prompt_on_stream_rejects_explicit_no():
    """An explicit 'n' response rejects the generated message."""
    stream = _FakeInteractiveStream("n\n")

    assert ai_prepare_commit_msg._prompt_on_stream(stream, "commit body") is False


def test_prompt_on_stream_returns_false_on_eof():
    """Reaching end-of-stream without a response rejects the message."""
    stream = _FakeInteractiveStream("")

    assert ai_prepare_commit_msg._prompt_on_stream(stream, "commit body") is False


def test_prompt_on_stream_reprompts_on_invalid_input_then_accepts():
    """Invalid answers are re-prompted until a valid answer is given."""
    stream = _FakeInteractiveStream("maybe\nyes\n")

    assert ai_prepare_commit_msg._prompt_on_stream(stream, "commit body") is True
    output = stream.getvalue()
    assert "Please answer 'y' or 'n'." in output
    assert "commit body" in output


def test_confirm_generated_message_reads_from_tty(monkeypatch):
    """The confirmation helper delegates to the interactive TTY stream."""
    fake_tty = _FakeInteractiveStream("y\n")

    class _FakeTtyContext:
        """Context manager wrapping a fake TTY stream."""

        def __enter__(self):
            return fake_tty

        def __exit__(self, *_exc_info):
            return False

    def fake_open(self, *_args, **_kwargs):  # pylint: disable=unused-argument
        return _FakeTtyContext()

    monkeypatch.setattr(ai_prepare_commit_msg.Path, "open", fake_open)

    assert ai_prepare_commit_msg._confirm_generated_message("commit body") is True


def test_confirm_generated_message_returns_false_without_tty(monkeypatch):
    """Missing an interactive TTY refuses auto-approval instead of raising."""

    def fake_open(self, *_args, **_kwargs):  # pylint: disable=unused-argument
        raise OSError("no such device or address")

    monkeypatch.setattr(ai_prepare_commit_msg.Path, "open", fake_open)

    assert ai_prepare_commit_msg._confirm_generated_message("commit body") is False
