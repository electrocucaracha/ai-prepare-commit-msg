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

"""Command-line entry for generating AI-assisted commit messages.

This module exposes a `click` command `cli` that:
- loads prompt messages from a YAML file,
- sends the combined prompt and staged git diff to an LLM, and
- writes the generated commit message to the repository's `COMMIT_EDITMSG` file.

When run under a pre-commit environment (the `PRE_COMMIT` env var is set
to ``1`` and files are passed), the CLI logs that it's running in
pre-commit mode. The presence of the `files` argument is only used for
pre-commit detection; the command does not short-circuit or modify
behavior beyond logging.
"""

import logging
import os
from pathlib import Path
from typing import Sequence

import click

from ai_prepare_commit_msg import git
from ai_prepare_commit_msg.llm import get_commit_msg

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
    "--log-level",
    type=click.Choice(
        ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
    ),
    default="WARNING",
    show_default=True,
    help="Set the logging level.",
)
@click.argument("files", nargs=-1, type=click.UNPROCESSED)
def cli(model: str, prompt_file: str, log_level: str, files: Sequence[str]) -> None:
    """Generate commit messages using AI assistance.

    Args:
        model: LiteLLM model identifier (required).
        prompt_file: Path to the YAML prompt definition file.
        log_level: Logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        files: Files passed by pre-commit (unused except to detect pre-commit).
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(levelname)s %(name)s: %(message)s",
    )

    logger.debug("Using model: %s", model)
    logger.debug("Using prompt file: %s", prompt_file)

    if os.environ.get("PRE_COMMIT") == "1" and files:
        logger.info("Running in pre-commit mode (files passed); continuing.")

    repo = git.GitRepository(Path.cwd())

    diff_message = repo.get_diff_message()

    if not diff_message:
        logger.debug("No staged changes detected; skipping commit message generation.")
        return

    logger.debug("Staged diff length: %d chars", len(diff_message))

    commit_msg = get_commit_msg(
        model, diff_message, Path(__file__).parent / prompt_file
    )
    logger.debug(
        "Generated commit message (%d chars):\n%s", len(commit_msg), commit_msg
    )

    repo.write_commit_msg(commit_msg)
    logger.info("Commit message written successfully.")
