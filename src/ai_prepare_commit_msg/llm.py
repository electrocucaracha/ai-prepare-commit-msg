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

Utilities to load prompt messages, compress them with Headroom, call a
LiteLLM-style completion API, and extract text from model responses. The
public API is ``get_commit_msg`` which returns the concatenated textual
output from the model's choices, plus ``get_compression_stats`` which
reports how many prompt tokens Headroom saved. When a diff is too large for
the model's context window even after Headroom compression, the map-reduce
summarization chain in :mod:`ai_prepare_commit_msg.summarize` is used to
shrink the diff before falling back to ``OVERSIZED_DIFF_WARNING``.
"""

import concurrent.futures
import logging
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path

import litellm
import yaml

from .summarize import extract_choice_content as _extract_choice_content
from .summarize import summarize_diff as _summarize_diff

# Third-party compression errors must fall back to the original prompt.
try:
    from headroom.compress import compress as headroom_compress
except ImportError:  # pragma: no cover - exercised via integration environment
    headroom_compress = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

CUSTOM_PROVIDER_ENTRY_POINT_GROUP = "ai_prepare_commit_msg.litellm_providers"

MAX_PROMPT_TOKENS = 120_000
OVERSIZED_DIFF_WARNING = (
    "Warning: staged diff is too large for AI commit message generation. "
    "Skipping the LLM request. Please write the commit message manually."
)


@dataclass
class CompressionStats:
    """Prompt token counts accumulated across Headroom compression runs.

    Examples
    --------
    >>> stats = CompressionStats()
    >>> stats.format_summary()
    'Headroom: prompt compression unavailable; no token metrics collected.'
    >>> stats.record(1000, 750)
    >>> stats.tokens_saved
    250
    >>> stats.format_summary()
    'Headroom: 1000 -> 750 prompt tokens over 1 request(s); saved 250 (25.0%).'

    """

    requests: int = 0
    tokens_before: int = 0
    tokens_after: int = 0

    @property
    def tokens_saved(self) -> int:
        """Number of prompt tokens removed by compression."""
        return self.tokens_before - self.tokens_after

    @property
    def savings_ratio(self) -> float:
        """Fraction of prompt tokens removed, in the range 0.0 to 1.0."""
        if self.tokens_before <= 0:
            return 0.0
        return self.tokens_saved / self.tokens_before

    def record(self, tokens_before: int, tokens_after: int) -> None:
        """Add one compression run to the accumulated totals."""
        self.requests += 1
        self.tokens_before += tokens_before
        self.tokens_after += tokens_after

    def reset(self) -> None:
        """Clear the accumulated totals."""
        self.requests = 0
        self.tokens_before = 0
        self.tokens_after = 0

    def format_summary(self) -> str:
        """Return a single-line, human-readable metrics summary."""
        if not self.requests:
            return (
                "Headroom: prompt compression unavailable; no token metrics collected."
            )

        return (
            f"Headroom: {self.tokens_before} -> {self.tokens_after} prompt tokens "
            f"over {self.requests} request(s); "
            f"saved {self.tokens_saved} ({self.savings_ratio:.1%})."
        )


_COMPRESSION_STATS = CompressionStats()


def get_compression_stats() -> CompressionStats:
    """Return the Headroom metrics accumulated in this process."""
    return _COMPRESSION_STATS


def load_custom_providers() -> None:
    """Register LiteLLM custom providers advertised through entry points.

    Any installed package declaring an entry point in the
    ``ai_prepare_commit_msg.litellm_providers`` group is loaded and added to
    :attr:`litellm.custom_provider_map`, so the model string
    ``<entry-point-name>/<model>`` routes to that handler. Registration is
    idempotent, and a plugin that fails to load is logged and skipped so a
    broken plugin never blocks commit message generation.
    """
    discovered = list(entry_points(group=CUSTOM_PROVIDER_ENTRY_POINT_GROUP))
    if not discovered:
        return

    if not isinstance(getattr(litellm, "custom_provider_map", None), list):
        litellm.custom_provider_map = []

    registered = {
        entry["provider"]
        for entry in litellm.custom_provider_map
        if isinstance(entry, dict) and "provider" in entry
    }

    # A plugin is third-party code, so any import or construction error here
    # must degrade to a warning instead of aborting the git hook.
    # pylint: disable=broad-exception-caught
    for entry_point in discovered:
        if entry_point.name in registered:
            logger.debug(
                "LiteLLM custom provider '%s' is already registered; skipping",
                entry_point.name,
            )
            continue

        try:
            handler_cls = entry_point.load()
            litellm.custom_provider_map.append(
                {"provider": entry_point.name, "custom_handler": handler_cls()}
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to load LiteLLM custom provider '%s' from '%s': %s",
                entry_point.name,
                entry_point.value,
                exc,
            )
        else:
            logger.info(
                "Registered LiteLLM custom provider '%s' from '%s'",
                entry_point.name,
                entry_point.value,
            )
    # pylint: enable=broad-exception-caught


def _compress_messages(
    model: str, messages: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Compress prompt messages with Headroom and record token metrics.

    Returns the original messages when Headroom is unavailable or fails.
    """
    if headroom_compress is None:
        logger.debug("Headroom is not installed; sending the prompt uncompressed.")
        return list(messages)

    try:
        # Third-party compression errors must fall back to the original prompt.
        # pylint: disable=broad-exception-caught
        result = headroom_compress(
            messages=messages,
            model=model,
            model_limit=MAX_PROMPT_TOKENS,
            # The staged diff is the trailing user message, so Headroom has to be
            # told to compress it instead of protecting it as live conversation.
            compress_user_messages=True,
            protect_recent=0,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Headroom compression failed; using original prompt: %s", exc)
        return list(messages)
    # pylint: enable=broad-exception-caught

    if result.tokens_before <= 0:
        logger.debug("Headroom reported no token counts; using original prompt.")
        return list(messages)

    _COMPRESSION_STATS.record(result.tokens_before, result.tokens_after)
    logger.debug(
        "Headroom compressed the prompt from %d to %d tokens using %s",
        result.tokens_before,
        result.tokens_after,
        result.transforms_applied,
    )
    return list(result.messages)


def _estimate_prompt_tokens(model: str, messages: list[dict[str, str]]) -> int | None:
    """Estimate prompt tokens for a model request.

    Returns ``None`` when LiteLLM cannot provide a token estimate for the
    current model or message shape.
    """
    # Token estimation is an optional safeguard and must never block generation.
    # pylint: disable=broad-exception-caught
    try:
        prompt_tokens = litellm.token_counter(model=model, messages=messages)
    except Exception as exc:  # noqa: BLE001
        logger.debug("Unable to estimate prompt tokens for model '%s': %s", model, exc)
        return None
    # pylint: enable=broad-exception-caught

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
    load_custom_providers()

    loaded: list[dict[str, str]] = _load_prompt_messages(prompt_file)
    logger.debug("Loaded %d prompt messages from %s", len(loaded), prompt_file)

    loaded.append({"role": "user", "content": diff_message})
    messages = _compress_messages(model, loaded)

    prompt_tokens = _estimate_prompt_tokens(model, messages)
    if prompt_tokens is not None and prompt_tokens > MAX_PROMPT_TOKENS:
        logger.warning(
            "Estimated prompt token count %d exceeds safe limit %d; "
            "attempting summarization chain.",
            prompt_tokens,
            MAX_PROMPT_TOKENS,
        )
        loaded[-1] = {
            "role": "user",
            "content": _summarize_diff(model, diff_message),
        }
        messages = _compress_messages(model, loaded)
        prompt_tokens = _estimate_prompt_tokens(model, messages)

    if prompt_tokens is not None and prompt_tokens > MAX_PROMPT_TOKENS:
        logger.warning(
            "Skipping LLM call: prompt still %d tokens after summarization, "
            "exceeding safe limit %d.",
            prompt_tokens,
            MAX_PROMPT_TOKENS,
        )
        return OVERSIZED_DIFF_WARNING

    def call_llm():
        response = litellm.completion(
            model=model,
            messages=messages,
            max_tokens=1024,
            drop_params=True,
        )
        logger.debug("Sent prompt to model '%s'; awaiting response", model)
        return response

    result = ""
    timeout = 10  # seconds

    # Provider errors must produce a safe fallback for this git hook.
    # pylint: disable=broad-exception-caught
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
    except Exception as e:  # noqa: BLE001
        if _has_oversized_prompt_error(e):
            logger.warning("Skipping LLM call after oversized prompt rejection: %s", e)
            result = OVERSIZED_DIFF_WARNING
        else:
            logger.error("LLM call failed: %s", e)
            result = ""  # Fallback to empty commit message
    # pylint: enable=broad-exception-caught

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
        TypeError: If the YAML structure or message entries have invalid types.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Prompt file not found or not a file: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(data, dict):
        raise TypeError("Prompt file must contain a mapping at the top level")

    messages = data.get("messages")
    if messages is None:
        logger.debug("No 'messages' key in prompt file %s; returning empty list", path)
        return []

    if not isinstance(messages, list):
        raise TypeError("'messages' must be a list in the prompt file")

    validated: list[dict[str, str]] = []
    for idx, item in enumerate(messages):
        if not isinstance(item, dict):
            raise TypeError(f"message at index {idx} must be a mapping/dict")

        role = item.get("role")
        content = item.get("content")

        if not isinstance(role, str) or not isinstance(content, str):
            raise TypeError(
                f"message at index {idx} must contain string 'role' and 'content'"
            )

        validated.append({"role": role, "content": content})

    logger.debug("Loaded %d prompt messages from %s", len(validated), path)
    return validated
