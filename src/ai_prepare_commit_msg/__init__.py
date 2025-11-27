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

"""Module that provides a command-line for generating commit messages.

This module exposes a `click` command `cli` that generates a commit message
using an AI model and writes it to the repository's `COMMIT_EDITMSG` file.
"""

import logging
import os
from typing import Sequence

import click
import litellm
from git import Repo

from ai_prepare_commit_msg.prompt_loader import load_prompt_messages

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "--model",
    help="The LiteLLM model to use for generating commit messages.",
    envvar="LITELLM_PROXY_MODEL",
    required=True,
)
@click.option(
    "--prompt-file",
    help="Path to the YAML file containing prompt messages.",
    default="prompts/default.yml",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging.",
)
@click.argument("files", nargs=-1, type=click.UNPROCESSED)
def cli(model: str, prompt_file: str, verbose: bool, files: Sequence[str]) -> None:
    """Generate commit messages using AI assistance.

    Args:
        model: LiteLLM model identifier (required).
        prompt_file: Path to the YAML prompt definition file.
        verbose: Enable debug logging when True.
        files: Files passed by pre-commit (unused except to detect pre-commit).
    """
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    if os.environ.get("PRE_COMMIT") == "1" and files:
        logger.info("Running in pre-commit mode. Exiting.")

    messages = load_prompt_messages(prompt_file)
    logger.info("Loaded %d prompt messages from %s.", len(messages), prompt_file)

    try:
        repo = Repo(os.getcwd())
    except Exception as exc:  # pragma: no cover - guard for non-repo environments
        logger.error("Not a git repository (cwd=%s): %s", os.getcwd(), exc)
        raise

    git_cmd = repo.git
    messages.append({"role": "user", "content": git_cmd.diff(cached=True)})

    response = litellm.completion(messages=messages, model=model)
    logger.info("Generated commit message using AI.")

    choices = getattr(response, "choices", []) or []
    commit_msg = "\n".join(getattr(choice.message, "content", "") for choice in choices)
    logger.debug("Commit message:\n%s", commit_msg)

    # Write to the repository's git directory to handle non-standard paths.
    git_dir = getattr(repo, "git_dir", os.path.join(os.getcwd(), ".git"))
    commit_editmsg = os.path.join(git_dir, "COMMIT_EDITMSG")
    with open(commit_editmsg, "w", encoding="utf-8") as f:
        f.write(commit_msg)
    logger.info("Wrote commit message to %s.", commit_editmsg)
