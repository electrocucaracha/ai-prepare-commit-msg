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

"""Module that provides git-related utilities."""

import logging
from pathlib import Path
from typing import Union

from git import InvalidGitRepositoryError, NoSuchPathError, Repo

logger = logging.getLogger(__name__)


class GitRepository:
    """A small helper around a local Git repository.

    This wraps a ``git.Repo`` and provides helpers used by the CLI.
    """

    def __init__(self, path: Union[str, Path] = ".") -> None:
        """Initialize the GitRepository object.

        Args:
            path: Path to the repository work tree (defaults to current dir).

        Examples
        --------
        >>> # constructing with a path that does not exist raises RuntimeError
        >>> from ai_prepare_commit_msg.git import GitRepository
        >>> try:
        ...     GitRepository('/unlikely/path/that/does/not/exist')
        ... except RuntimeError:
        ...     print('error')
        error

        """
        try:
            self.repo = Repo(path)
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise RuntimeError(f"Not a git repository: {path}") from exc

    def get_diff_message(self) -> str:
        """Return the staged git diff (the cached diff) as a string.

        An empty string is returned if there are no staged changes.
        """
        git_cmd = self.repo.git
        result = git_cmd.diff(cached=True) or ""
        return str(result)

    def write_commit_msg(self, commit_msg: str) -> None:
        """Write the generated commit message to the repository's COMMIT_EDITMSG.

        Args:
            commit_msg: The commit message to write.
        """
        # rev_parse may return a str with whitespace; normalize to Path
        git_dir = self.repo.git.rev_parse("--git-dir")
        git_dir_path = Path(str(git_dir).strip()).resolve()
        commit_editmsg_path = git_dir_path / "COMMIT_EDITMSG"

        try:
            commit_editmsg_path.parent.mkdir(parents=True, exist_ok=True)
            with commit_editmsg_path.open("w", encoding="utf-8") as fh:
                fh.write(commit_msg)
        except OSError:
            logger.exception("Failed writing commit message to %s", commit_editmsg_path)
            raise

        logger.info("Wrote commit message to %s.", commit_editmsg_path)
