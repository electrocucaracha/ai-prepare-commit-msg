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
