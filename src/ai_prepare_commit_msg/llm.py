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
the model's context window even after Headroom compression, a per-file
map-reduce summarization chain (``_summarize_diff``) is used to shrink the
diff before falling back to ``OVERSIZED_DIFF_WARNING``.
"""

import concurrent.futures
import logging
import re
from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import Any

import litellm
import yaml  # type: ignore[import-untyped]

# Third-party compression errors must fall back to the original prompt.
# pylint: disable=broad-exception-caught
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

# Summarization chain: chunks are sized well below MAX_PROMPT_TOKENS so the
# per-chunk summarization request (plus its system prompt) stays in budget.
SUMMARIZATION_CHUNK_TOKENS = MAX_PROMPT_TOKENS // 6
MAX_SUMMARIZATION_ROUNDS = 3
MAX_SUMMARIZATION_WORKERS = 4
SUMMARIZATION_TIMEOUT = 120  # seconds for the whole map step
_FILE_DIFF_MARKER = "diff --git "

# Machine-generated files inflate a diff without describing intent, so they are
# reported from their diff stats instead of spending an LLM call on them.
_LOW_SIGNAL_FILENAMES = frozenset(
    {
        "Cargo.lock",
        "Gemfile.lock",
        "composer.lock",
        "go.sum",
        "package-lock.json",
        "pnpm-lock.yaml",
        "poetry.lock",
        "uv.lock",
        "yarn.lock",
    }
)
_LOW_SIGNAL_DIRS = frozenset(
    {".terraform", "generated", "node_modules", "third_party", "vendor"}
)
_LOW_SIGNAL_SUFFIXES = (".min.css", ".min.js", ".map", ".snap", ".pb.go", "_pb2.py")

_MAP_SUMMARY_SYSTEM_PROMPT = (
    "You analyze the git diff of a single file. Reply with one to three short "
    "bullet points describing exactly what changed and, where the diff makes "
    "it evident, why. Name the specific functions, classes, constants, or "
    "options that were added, removed, renamed, or modified. State only what "
    "the diff shows and never guess at intent that is not visible. Do not "
    "repeat the file path and do not include code or diff syntax."
)
_REDUCE_SUMMARY_SYSTEM_PROMPT = (
    "Merge the following per-file change notes into a shorter list that still "
    "preserves every distinct change. Group related changes together and drop "
    "only redundancy, never detail that is unique to one file."
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
        msg = choice.message
    elif isinstance(choice, dict):
        # dict-like choice: prefer message, otherwise fall back to text
        msg = choice.get("message", choice.get("text", ""))
    else:
        return str(choice)

    if isinstance(msg, dict):
        return msg.get("content", "") or ""

    # msg might be an object with .content, or a plain string
    if hasattr(msg, "content"):
        return msg.content or ""

    return str(msg) if msg is not None else ""


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


def _count_tokens(model: str, text: str) -> int:
    """Estimate the token count of plain text, falling back to a heuristic."""
    # Token estimation is an optional safeguard and must never block generation.
    # pylint: disable=broad-exception-caught
    try:
        return int(litellm.token_counter(model=model, text=text))
    except Exception as exc:  # noqa: BLE001
        logger.debug("Unable to count tokens for model '%s': %s", model, exc)
        return len(text) // 4  # rough heuristic: ~4 characters per token
    # pylint: enable=broad-exception-caught


def _split_diff_by_file(diff_message: str) -> list[str]:
    """Split a unified diff into per-file sections, preserving the marker."""
    parts = diff_message.split(_FILE_DIFF_MARKER)
    if len(parts) <= 1:
        return [diff_message] if diff_message else []

    sections = [parts[0]] if parts[0] else []
    sections.extend(_FILE_DIFF_MARKER + part for part in parts[1:])
    return sections


def _split_text_by_token_budget(
    model: str, text: str, max_chunk_tokens: int
) -> list[str]:
    """Split ``text`` into chunks of at most ``max_chunk_tokens`` tokens."""
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = _count_tokens(model, line)
        if current and current_tokens + line_tokens > max_chunk_tokens:
            chunks.append("".join(current))
            current = []
            current_tokens = 0
        current.append(line)
        current_tokens += line_tokens

    if current:
        chunks.append("".join(current))

    return chunks


def _file_path_from_section(section: str) -> str:
    """Return the post-image path from a ``diff --git`` header line.

    Examples
    --------
    >>> _file_path_from_section('diff --git a/src/app.py b/src/app.py\\n+x')
    'src/app.py'
    >>> _file_path_from_section('no header here')
    ''

    """
    header = section.split("\n", 1)[0]
    if not header.startswith(_FILE_DIFF_MARKER):
        return ""

    _, separator, new_path = header[len(_FILE_DIFF_MARKER) :].partition(" b/")
    return new_path.strip().strip('"') if separator else ""


def _is_low_signal_path(path: str) -> bool:
    """Return ``True`` for machine-generated paths not worth an LLM call.

    Examples
    --------
    >>> _is_low_signal_path('poetry.lock')
    True
    >>> _is_low_signal_path('web/node_modules/left-pad/index.js')
    True
    >>> _is_low_signal_path('src/app.py')
    False

    """
    segments = path.split("/")
    if segments[-1] in _LOW_SIGNAL_FILENAMES:
        return True
    if path.endswith(_LOW_SIGNAL_SUFFIXES):
        return True
    return any(segment in _LOW_SIGNAL_DIRS for segment in segments)


def _file_change_stat(path: str, section: str) -> str:
    """Describe a file's diff section from its headers and line counts.

    These facts are derived rather than inferred, so they anchor the model
    against hallucinated file names and change types.

    Examples
    --------
    >>> _file_change_stat('a.py', 'diff --git a/a.py b/a.py\\n+one\\n-two')
    '- a.py (modified, +1/-1)'

    """
    if re.search(r"^new file mode ", section, re.MULTILINE):
        status = "added"
    elif re.search(r"^deleted file mode ", section, re.MULTILINE):
        status = "deleted"
    elif re.search(r"^rename to ", section, re.MULTILINE):
        status = "renamed"
    elif re.search(r"^Binary files ", section, re.MULTILINE):
        status = "binary"
    else:
        status = "modified"

    added = removed = 0
    for line in section.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1

    stat = f"- {path or 'unknown path'} ({status}, +{added}/-{removed})"
    if path and _is_low_signal_path(path):
        return f"{stat} [generated; not analyzed]"
    return stat


def _summarize_text(
    model: str, system_prompt: str, content: str, max_tokens: int = 512
) -> str:
    """Ask the model to summarize ``content``; return "" on failure."""
    # Summarization is a best-effort compression step and must never raise.
    # pylint: disable=broad-exception-caught
    try:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=0.1,
            max_tokens=max_tokens,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Summarization request failed: %s", exc)
        return ""
    # pylint: enable=broad-exception-caught

    choices = getattr(response, "choices", []) or []
    contents = (_extract_choice_content(c) for c in choices)
    return "\n".join(filter(None, (s.strip() for s in contents))).strip()


def _build_map_work_items(
    model: str, sections: list[tuple[str, str]]
) -> list[tuple[str, str]]:
    """Pair each file with the text to summarize, splitting oversized files."""
    work: list[tuple[str, str]] = []
    for path, section in sections:
        label = path or "unknown path"
        if _count_tokens(model, section) <= SUMMARIZATION_CHUNK_TOKENS:
            work.append((label, section))
            continue

        parts = _split_text_by_token_budget(model, section, SUMMARIZATION_CHUNK_TOKENS)
        work.extend(
            (f"{label} (part {index}/{len(parts)})", part)
            for index, part in enumerate(parts, start=1)
        )
    return work


def _map_file_summaries(model: str, sections: list[tuple[str, str]]) -> list[str]:
    """Summarize each file's diff independently, in parallel and time-bounded.

    One request per file keeps a small change from being crowded out by a
    large neighbour, which is the main source of lost detail when several
    files share a single summarization call.
    """
    work = _build_map_work_items(model, sections)
    if not work:
        return []

    ordered: list[str | None] = [None] * len(work)
    executor = concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_SUMMARIZATION_WORKERS
    )
    try:
        futures = {
            executor.submit(
                _summarize_text,
                model,
                _MAP_SUMMARY_SYSTEM_PROMPT,
                f"File: {label}\n\n{text}",
                256,
            ): index
            for index, (label, text) in enumerate(work)
        }
        try:
            for future in concurrent.futures.as_completed(
                futures, timeout=SUMMARIZATION_TIMEOUT
            ):
                ordered[futures[future]] = future.result()
        except concurrent.futures.TimeoutError:
            logger.warning(
                "Summarization map step exceeded %d seconds; using partial results.",
                SUMMARIZATION_TIMEOUT,
            )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    return [
        f"- {work[index][0]}: {summary.strip()}"
        for index, summary in enumerate(ordered)
        if summary and summary.strip()
    ]


def _reduce_summaries(model: str, summaries: list[str]) -> str:
    """Collapse per-file notes until they fit the summarization budget."""
    text = "\n".join(summaries)

    for _ in range(MAX_SUMMARIZATION_ROUNDS):
        if _count_tokens(model, text) <= SUMMARIZATION_CHUNK_TOKENS:
            break

        groups = _split_text_by_token_budget(model, text, SUMMARIZATION_CHUNK_TOKENS)
        reduced = [
            summary
            for group in groups
            if (summary := _summarize_text(model, _REDUCE_SUMMARY_SYSTEM_PROMPT, group))
        ]
        if not reduced:
            logger.warning("Reduce step produced no output; keeping current notes.")
            break

        text = "\n".join(reduced)

    return text


def _summarize_diff(model: str, diff_message: str) -> str:
    """Compress an oversized diff into a file-anchored change report.

    Every file contributes a deterministic stat line derived from the diff
    headers, and every non-generated file is summarized on its own (map)
    before the notes are collapsed to fit the budget (reduce). Returns the
    original diff when no summary could be produced.
    """
    sections = [
        (_file_path_from_section(section), section)
        for section in _split_diff_by_file(diff_message)
        if section.strip()
    ]
    if not sections:
        return diff_message

    skeleton = "\n".join(_file_change_stat(path, section) for path, section in sections)
    analyzable = [
        (path, section)
        for path, section in sections
        if not (path and _is_low_signal_path(path))
    ]

    summaries = _map_file_summaries(model, analyzable)
    if not summaries:
        logger.warning("Summarization chain produced no output; giving up.")
        return diff_message

    notes = _reduce_summaries(model, summaries)
    logger.debug(
        "Summarized %d file(s) (%d analyzed): %d -> %d chars",
        len(sections),
        len(analyzable),
        len(diff_message),
        len(notes),
    )
    return f"Files changed:\n{skeleton}\n\nWhat changed:\n{notes}"


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
            temperature=0.1,
            max_tokens=1024,
            num_ctx=16384,
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
