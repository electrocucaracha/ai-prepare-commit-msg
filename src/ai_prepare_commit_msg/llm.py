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

import concurrent.futures
import functools
import logging
from pathlib import Path
from typing import Any

import litellm
import yaml  # type: ignore[import-untyped]

try:
    from headroom.integrations.litellm_callback import HeadroomCallback
except ImportError:  # pragma: no cover - exercised via integration environment
    HeadroomCallback = None  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

MAX_PROMPT_TOKENS = 120_000
OVERSIZED_DIFF_WARNING = (
    "Warning: staged diff is too large for AI commit message generation. "
    "Skipping the LLM request. Please write the commit message manually."
)


@functools.lru_cache(maxsize=1)
def _configure_headroom_callback() -> None:
    """Enable Headroom prompt compression callback for LiteLLM when available."""
    if HeadroomCallback is None:
        logger.debug("Headroom is not installed; skipping prompt compression callback.")
        return

    callbacks = getattr(litellm, "callbacks", None)
    if callbacks is None:
        callbacks = []
        litellm.callbacks = callbacks
    elif not isinstance(callbacks, list):
        callbacks = list(callbacks)
        litellm.callbacks = callbacks

    if any(isinstance(callback, HeadroomCallback) for callback in callbacks):
        logger.debug("Headroom callback already configured for LiteLLM.")
        return

    callbacks.append(HeadroomCallback())
    logger.debug("Headroom callback configured for LiteLLM prompt compression.")


def _extract_choice_content(choice: Any) -> str:
    """Return the textual content for a model "choice".

    Supports objects with a ``message`` attribute (which itself may be an
    object or mapping), mapping choices with ``message.content`` or
    ``text``, and falls back to the string form of ``choice``.

    Examples
    --------
    >>> # object with .message that has .content
    >>> class MsgObj:
    ...     def __init__(self, content):
    ...         self.content = content
    >>> class Choice:
    ...     def __init__(self, message):
    ...         self.message = message
    >>> _extract_choice_content(Choice(MsgObj("hello")))
    'hello'

    >>> # dict-like message with nested content
    >>> _extract_choice_content({'message': {'content': 'hi'}})
    'hi'

    >>> # dict-like fallback to text
    >>> _extract_choice_content({'text': 'plain text'})
    'plain text'

    >>> # plain string fallback
    >>> _extract_choice_content('just a string')
    'just a string'

    >>> # message attribute present but None -> empty string
    >>> _extract_choice_content(Choice(None))
    ''

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


def _estimate_prompt_tokens(model: str, messages: list[dict[str, str]]) -> int | None:
    """Estimate prompt tokens for a model request.

    Returns ``None`` when LiteLLM cannot provide a token estimate for the
    current model or message shape.
    """
    try:
        prompt_tokens = litellm.token_counter(model=model, messages=messages)
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Unable to estimate prompt tokens for model '%s': %s", model, exc)
        return None

    return int(prompt_tokens)


def _has_oversized_prompt_error(error: Exception) -> bool:
    """Return ``True`` when an exception indicates the prompt is too large."""
    message = str(error).lower()
    oversized_markers = (
        "prompt token count",
        "context length",
        "maximum context length",
        "too many tokens",
        "exceeds the limit",
    )
    return any(marker in message for marker in oversized_markers)


def get_commit_msg(model: str, diff_message: str, prompt_file: str) -> str:
    """Generate a commit message using an LLM with a timeout fallback."""
    _configure_headroom_callback()

    messages: list[dict[str, str]] = _load_prompt_messages(prompt_file)
    logger.debug("Loaded %d prompt messages from %s", len(messages), prompt_file)

    messages.append({"role": "user", "content": diff_message})

    prompt_tokens = _estimate_prompt_tokens(model, messages)
    if prompt_tokens is not None and prompt_tokens > MAX_PROMPT_TOKENS:
        logger.warning(
            "Skipping LLM call: estimated prompt token count %d exceeds safe limit %d.",
            prompt_tokens,
            MAX_PROMPT_TOKENS,
        )
        return OVERSIZED_DIFF_WARNING

    def call_llm():
        response = litellm.completion(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=1024,
            num_ctx=16384,
        )
        logger.debug("Sent prompt to model '%s'; awaiting response", model)
        return response

    result = ""
    timeout = 10  # seconds

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(call_llm)
            response = future.result(timeout=timeout)

            choices = getattr(response, "choices", []) or []
            contents = (_extract_choice_content(c) for c in choices)
            # Filter empty strings and join with a single newline
            result = "\n".join(filter(None, (s.strip() for s in contents))).strip()
            logger.debug("Generated commit message length=%d", len(result))
    except concurrent.futures.TimeoutError:
        logger.error("LLM call timed out after %d seconds", timeout)
        result = ""  # Fallback to empty commit message
    except Exception as e:  # pylint: disable=broad-except
        if _has_oversized_prompt_error(e):
            logger.warning("Skipping LLM call after oversized prompt rejection: %s", e)
            result = OVERSIZED_DIFF_WARNING
        else:
            logger.error("LLM call failed: %s", e)
            result = ""  # Fallback to empty commit message

    return result


def _load_prompt_messages(file_path: str | Path) -> list[dict[str, str]]:
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

    validated: list[dict[str, str]] = []
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
