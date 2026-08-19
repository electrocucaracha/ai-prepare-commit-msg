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
import time
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

import click

from ai_prepare_commit_msg import git, llm
from ai_prepare_commit_msg.llm import get_commit_msg

logger = logging.getLogger(__name__)


def _confirm_generated_message(commit_msg: str) -> bool:
    """Prompt the user to accept the generated commit message.

    Args:
        commit_msg: Generated commit message content.

    Returns:
        True when the user accepts the message, otherwise False.
    """
    try:
        with Path("/dev/tty").open("r+", encoding="utf-8") as tty_stream:
            return _prompt_on_stream(tty_stream, commit_msg)
    except OSError:
        logger.error(
            "No interactive TTY available; refusing to auto-approve commit message."
        )
        return False


def _prompt_on_stream(stream: TextIO, commit_msg: str) -> bool:
    """Render commit message and read a yes/no confirmation from a stream."""
    stream.write("\nGenerated commit message:\n\n")
    stream.write(f"{commit_msg}\n\n")

    while True:
        stream.write("Use this generated commit message? [Y/n]: ")
        stream.flush()
        response = stream.readline()

        if not response:
            return False

        normalized = response.strip().lower()
        if normalized in {"", "y", "yes"}:
            return True
        if normalized in {"n", "no"}:
            return False

        stream.write("Please answer 'y' or 'n'.\n")


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
@click.option(
    "--retry",
    type=click.IntRange(min=1),
    default=5,
    show_default=True,
    help="Maximum number of attempts when the generated commit message is empty.",
)
@click.option(
    "--retry-sleep",
    type=click.FloatRange(min=0),
    default=3.0,
    show_default=True,
    help="Seconds to wait between retries when the generated message is empty.",
)
@click.option(
    "--auto-approve",
    is_flag=True,
    envvar="AI_PREPARE_COMMIT_AUTO_APPROVE",
    help="Skip confirmation and write the generated message immediately.",
)
@click.argument("files", nargs=-1, type=click.UNPROCESSED)
# Click injects option values as positional args for this command callback.
# pylint: disable=too-many-arguments,too-many-positional-arguments
def cli(
    model: str,
    prompt_file: str,
    log_level: str,
    retry: int,
    retry_sleep: float,
    auto_approve: bool,
    files: Sequence[str],
) -> None:
    """Generate commit messages using AI assistance.

    Args:
        model: LiteLLM model identifier (required).
        prompt_file: Path to the YAML prompt definition file.
        log_level: Logging verbosity level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        retry: Maximum attempts when generated commit message is empty.
        retry_sleep: Seconds to wait between retry attempts.
        auto_approve: Skip interactive confirmation when set.
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

    prompt_path = Path(__file__).parent / prompt_file
    commit_msg = ""
    for attempt in range(1, retry + 1):
        commit_msg = get_commit_msg(model, diff_message, str(prompt_path)).strip()
        if commit_msg:
            break

        if attempt < retry:
            logger.warning(
                "Generated commit message is empty (attempt %d/%d). Retrying in %s seconds.",
                attempt,
                retry,
                retry_sleep,
            )
            time.sleep(retry_sleep)

    if not commit_msg:
        raise click.ClickException(
            "Generated commit message is empty after all retry attempts."
        )

    logger.debug(
        "Generated commit message (%d chars):\n%s", len(commit_msg), commit_msg
    )

    click.echo(llm.get_compression_stats().format_summary(), err=True)

    if not auto_approve and not _confirm_generated_message(commit_msg):
        raise click.ClickException("Commit message not approved; aborting commit.")

    repo.write_commit_msg(commit_msg)
    logger.info("Commit message written successfully.")
