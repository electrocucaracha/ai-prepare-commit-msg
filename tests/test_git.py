# Copyright (c) 2025
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

"""Tests for the ``ai_prepare_commit_msg.git`` helper.

These tests exercise the small helper classes used to interact with a
local git repository. Helper/dummy classes are intentionally minimal.
"""

import pytest

from ai_prepare_commit_msg import git as gitmod


@pytest.mark.parametrize(
    "error_type", [gitmod.InvalidGitRepositoryError, gitmod.NoSuchPathError]
)
def test_init_raises_runtimeerror_when_repo_invalid(monkeypatch, tmp_path, error_type):
    """Constructing with a non-repo path raises RuntimeError."""

    def fake_repo(path):
        assert path == tmp_path
        raise error_type("not a repo")

    monkeypatch.setattr(gitmod, "Repo", fake_repo)

    with pytest.raises(RuntimeError):
        gitmod.GitRepository(tmp_path)


def test_get_diff_message_and_write_commit_msg(monkeypatch, tmp_path):
    """Ensure the staged diff is returned and commit message written."""

    # prepare a fake git directory where rev_parse will point
    fake_git_dir = tmp_path / "gitdir" / "nested"

    class DummyGit:
        """Fake git interface returning a preset diff and git dir."""  # pylint: disable=too-few-public-methods

        def __init__(self, diff_text="difftext"):
            """Store the preset diff text for later retrieval."""
            self._diff = diff_text

        def diff(self, cached=False):
            """Return the preset diff text (simulates staged diff)."""
            assert cached is True
            return self._diff

        def rev_parse(self, arg):
            """Return the path to the fake git directory."""
            assert arg == "--git-dir"
            return f" {fake_git_dir} \n"

    class DummyRepo:
        """Container exposing a ``git`` attribute for the fake git."""  # pylint: disable=too-few-public-methods

        def __init__(self, _path):
            """Initialize the container with a `DummyGit` instance."""
            self.git = DummyGit()

    # inject DummyRepo in place of imported Repo
    monkeypatch.setattr(gitmod, "Repo", DummyRepo)

    open_calls = []
    original_open = gitmod.Path.open

    def recording_open(path, *args, **kwargs):
        mode = args[0] if args else kwargs.get("mode", "r")
        if mode == "w":
            open_calls.append((mode, kwargs.get("encoding")))
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(gitmod.Path, "open", recording_open)

    repo = gitmod.GitRepository(tmp_path)

    # get_diff_message should return the dummy diff
    assert repo.get_diff_message() == "difftext"

    # writing commit message should create COMMIT_EDITMSG inside fake_git_dir
    msg = "commit-body"
    repo.write_commit_msg(msg)
    commit_file = fake_git_dir / "COMMIT_EDITMSG"
    assert commit_file.is_file()
    assert [path.name for path in fake_git_dir.iterdir()] == ["COMMIT_EDITMSG"]
    assert commit_file.read_text(encoding="utf-8") == msg

    repo.write_commit_msg("replacement")

    assert commit_file.read_text(encoding="utf-8") == "replacement"
    assert open_calls == [("w", "utf-8"), ("w", "utf-8")]


@pytest.mark.parametrize("diff_text", ["", None])
def test_get_diff_message_empty_when_no_staged_changes(
    monkeypatch, tmp_path, diff_text
):
    """When there are no staged changes an empty string is returned."""

    class DummyGitEmpty:
        """Fake git returning an empty diff and a git directory."""  # pylint: disable=too-few-public-methods

        def diff(self, cached=False):
            """Return an empty diff string (no staged changes)."""
            assert cached is True
            return diff_text

        def rev_parse(self, _arg):
            """Return the path to the fake git directory for the empty case."""
            return str(tmp_path / "gitdir2")

    class DummyRepoEmpty:
        """Container exposing a ``git`` attribute for the empty case."""  # pylint: disable=too-few-public-methods

        def __init__(self, _path):
            """Initialize the container with a `DummyGitEmpty` instance."""
            self.git = DummyGitEmpty()

    monkeypatch.setattr(gitmod, "Repo", DummyRepoEmpty)

    repo = gitmod.GitRepository(tmp_path)
    assert repo.get_diff_message() == ""


def test_write_commit_msg_reraises_on_os_error(monkeypatch, tmp_path):
    """A write failure is logged and re-raised instead of being swallowed."""

    class DummyGit:
        """Fake git interface returning a preset git dir."""  # pylint: disable=too-few-public-methods

        def rev_parse(self, _arg):
            """Return the path to a git directory that cannot be written to."""
            return str(tmp_path / "gitdir3")

    class DummyRepo:
        """Container exposing a ``git`` attribute for the failure case."""  # pylint: disable=too-few-public-methods

        def __init__(self, _path):
            """Initialize the container with a `DummyGit` instance."""
            self.git = DummyGit()

    monkeypatch.setattr(gitmod, "Repo", DummyRepo)

    def fake_open(self, *_args, **_kwargs):  # pylint: disable=unused-argument
        raise OSError("disk full")

    monkeypatch.setattr(gitmod.Path, "open", fake_open)

    repo = gitmod.GitRepository(tmp_path)
    with pytest.raises(OSError):
        repo.write_commit_msg("commit-body")
