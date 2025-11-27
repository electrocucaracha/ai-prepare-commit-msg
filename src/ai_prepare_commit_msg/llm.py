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

"""LLM helpers for generating commit messages.

Utilities to load prompt messages, call a LiteLLM-style completion API,
and extract text from model responses. The public API is
``get_commit_msg`` which returns the concatenated textual output from
the model's choices.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Union

import litellm
import yaml

logger = logging.getLogger(__name__)


def _extract_choice_content(choice: Any) -> str:
    """Return the textual content for a model "choice".

    Supports objects with a ``message`` attribute (which itself may be an
    object or mapping), mapping choices with ``message.content`` or
    ``text``, and falls back to the string form of ``choice``.
    """
    # Prefer explicit message attribute when present
    if hasattr(choice, "message"):
        msg = getattr(choice, "message")
    elif isinstance(choice, dict):
        # dict-like choice: prefer message, otherwise fall back to text
        msg = choice.get("message", choice.get("text", ""))
    else:
        return str(choice)

    if isinstance(msg, dict):
        return msg.get("content", "") or ""

    # msg might be an object with .content, or a plain string
    if hasattr(msg, "content"):
        return getattr(msg, "content") or ""

    return str(msg) if msg is not None else ""


def get_commit_msg(model: str, diff_message: str, prompt_file: str) -> str:
    """Generate a commit message using an LLM.

    Args:
        model: LiteLLM model identifier.
        diff_message: The staged git diff message.
        prompt_file: Path to the YAML prompt definition file.

    Returns:
        A single string that contains the concatenated model outputs.
    """
    messages: List[Dict[str, str]] = _load_prompt_messages(prompt_file)
    logger.info("Loaded %d prompt messages from %s", len(messages), prompt_file)

    messages.append({"role": "user", "content": diff_message})

    response = litellm.completion(messages=messages, model=model)
    logger.info("Sent prompt to model '%s'", model)

    choices = getattr(response, "choices", []) or []
    contents = (_extract_choice_content(c) for c in choices)
    # Filter empty strings and join with a single newline
    result = "\n".join(filter(None, (s.strip() for s in contents))).strip()
    logger.debug("Generated commit message length=%d", len(result))
    return result


def _load_prompt_messages(file_path: Union[str, Path]) -> List[Dict[str, str]]:
    """Load and validate prompt messages from a YAML file.

    The prompt YAML must be a mapping with a top-level `messages` key whose
    value is a list of mappings. Each message mapping must have string keys
    `role` and `content`.

    Args:
        file_path: Path to the YAML file containing prompt messages.

    Returns:
        A list of validated message dictionaries with `role` and `content`.

    Raises:
        FileNotFoundError: If the file does not exist or is not a file.
        ValueError: If the YAML structure or message entries are invalid.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found or not a file: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise ValueError("Prompt file must contain a mapping at the top level")

    messages = data.get("messages")
    if messages is None:
        logger.debug("No 'messages' key in prompt file %s; returning empty list", path)
        return []

    if not isinstance(messages, list):
        raise ValueError("'messages' must be a list in the prompt file")

    validated: List[Dict[str, str]] = []
    for idx, item in enumerate(messages):
        if not isinstance(item, dict):
            raise ValueError(f"message at index {idx} must be a mapping/dict")

        role = item.get("role")
        content = item.get("content")

        if not isinstance(role, str) or not isinstance(content, str):
            raise ValueError(
                f"message at index {idx} must contain string 'role' and 'content'"
            )

        validated.append({"role": role, "content": content})

    logger.debug("Loaded %d prompt messages from %s", len(validated), path)
    return validated
