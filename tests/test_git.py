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


import pytest

from ai_prepare_commit_msg import git as gitmod


def test_init_raises_runtimeerror_when_repo_invalid(monkeypatch, tmp_path):
    def fake_repo(path):
        raise gitmod.InvalidGitRepositoryError("not a repo")

    monkeypatch.setattr(gitmod, "Repo", fake_repo)

    with pytest.raises(RuntimeError):
        gitmod.GitRepository(tmp_path)


def test_get_diff_message_and_write_commit_msg(monkeypatch, tmp_path):
    # prepare a fake git directory where rev_parse will point
    fake_git_dir = tmp_path / "gitdir"
    fake_git_dir.mkdir()

    class DummyGit:
        def __init__(self, diff_text="difftext"):
            self._diff = diff_text

        def diff(self, cached=False):
            return self._diff

        def rev_parse(self, arg):
            return str(fake_git_dir)

    class DummyRepo:
        def __init__(self, path):
            self.git = DummyGit()

    # inject DummyRepo in place of imported Repo
    monkeypatch.setattr(gitmod, "Repo", DummyRepo)

    repo = gitmod.GitRepository(tmp_path)

    # get_diff_message should return the dummy diff
    assert repo.get_diff_message() == "difftext"

    # writing commit message should create COMMIT_EDITMSG inside fake_git_dir
    msg = "commit-body"
    repo.write_commit_msg(msg)
    commit_file = fake_git_dir / "COMMIT_EDITMSG"
    assert commit_file.is_file()
    assert commit_file.read_text(encoding="utf-8") == msg


def test_get_diff_message_empty_when_no_staged_changes(monkeypatch, tmp_path):
    class DummyGitEmpty:
        def diff(self, cached=False):
            return ""

        def rev_parse(self, arg):
            return str(tmp_path / "gitdir2")

    class DummyRepoEmpty:
        def __init__(self, path):
            self.git = DummyGitEmpty()

    monkeypatch.setattr(gitmod, "Repo", DummyRepoEmpty)

    repo = gitmod.GitRepository(tmp_path)
    assert repo.get_diff_message() == ""
