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

"""Module that provides a command-line for generating commit messages."""


import logging
import os

import click
import litellm
from git import Repo

from ai_prepare_commit_msg.prompt_loader import load_prompt_messages


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
def cli(model: str, prompt_file: str, verbose: bool, files: list[str]) -> None:
    """Generate commit messages using AI assistance."""
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    if os.environ.get("PRE_COMMIT") == "1" and files:
        logging.info("Running in pre-commit mode. Exiting.")

    messages = load_prompt_messages(prompt_file)
    logging.info(f"Loaded {len(messages)} prompt messages from {prompt_file}.")

    repo = Repo(os.getcwd())
    git_cmd = repo.git
    messages.append({"role": "user", "content": git_cmd.diff(cached=True)})

    response = litellm.completion(messages=messages, model=model)
    logging.info("Generated commit message using AI.")
    commit_msg = "\n".join([choice.message.content for choice in response.choices])
    logging.debug(f"Commit message:\n{commit_msg}")
    with open(
        os.path.join(os.getcwd(), ".git/COMMIT_EDITMSG"), "w", encoding="utf-8"
    ) as f:
        f.write(commit_msg)
        logging.info("Wrote commit message to .git/COMMIT_EDITMSG.")
