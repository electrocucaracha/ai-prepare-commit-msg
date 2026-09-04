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

"""Map-reduce summarization of oversized git diffs.

``summarize_diff`` turns a staged diff that cannot fit in the model's context
window into a file-anchored change report. The diff is first split per file,
then packed into chunks by :func:`plan_chunks`, which adapts to the shape of
the change set:

* a file whose diff alone exceeds the chunk budget is split into parts and
  each part is summarized separately;
* files that individually fit are packed together, so a change touching many
  small files costs a handful of requests instead of one per file;
* machine-generated files are reported from their diff stats and never sent
  to the model.

The per-chunk notes (map) are then collapsed until they fit the budget
(reduce).
"""

import concurrent.futures
import logging
import re
from dataclasses import dataclass, field
from typing import Any

import litellm

logger = logging.getLogger(__name__)

# Chunks are sized well below the prompt limit so a summarization request
# (plus its system prompt and reply) stays in budget.
MAX_PROMPT_TOKENS = 120_000
CHUNK_TOKENS = MAX_PROMPT_TOKENS // 6
MAX_FILES_PER_CHUNK = 20
MAX_SKELETON_FILES = 200
MAX_REDUCE_ROUNDS = 3
MAX_WORKERS = 4
MAP_TIMEOUT = 120  # seconds for the whole map step

FILE_DIFF_MARKER = "diff --git "

# Machine-generated files inflate a diff without describing intent, so they are
# reported from their diff stats instead of spending an LLM call on them.
LOW_SIGNAL_FILENAMES = frozenset(
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
LOW_SIGNAL_DIRS = frozenset(
    {".terraform", "generated", "node_modules", "third_party", "vendor"}
)
LOW_SIGNAL_SUFFIXES = (".min.css", ".min.js", ".map", ".snap", ".pb.go", "_pb2.py")

_SHARED_MAP_RULES = (
    "State only what the diff shows and never guess at intent that is not "
    "visible. Name the specific functions, classes, constants, or options "
    "that were added, removed, renamed, or modified. Do not include code or "
    "diff syntax."
)
FILE_SUMMARY_SYSTEM_PROMPT = (
    "You analyze the git diff of a single file. Reply with one to three short "
    "bullet points describing exactly what changed and, where the diff makes "
    f"it evident, why. {_SHARED_MAP_RULES} Do not repeat the file path."
)
PART_SUMMARY_SYSTEM_PROMPT = (
    "You analyze one fragment of a large git diff for a single file. Reply "
    "with one to three short bullet points covering only this fragment; other "
    f"fragments are summarized separately. {_SHARED_MAP_RULES} Do not repeat "
    "the file path."
)
GROUP_SUMMARY_SYSTEM_PROMPT = (
    "You analyze the git diff of several files. Reply with one bullet point "
    "per file, in the form '<path>: <what changed>'. Keep every file, even "
    f"when its change is trivial. {_SHARED_MAP_RULES}"
)
REDUCE_SUMMARY_SYSTEM_PROMPT = (
    "Merge the following per-file change notes into a shorter list that still "
    "preserves every distinct change. Group related changes together and drop "
    "only redundancy, never detail that is unique to one file."
)


@dataclass(frozen=True)
class DiffChunk:
    """A unit of work for the map step of the summarization chain."""

    label: str
    text: str
    system_prompt: str
    paths: tuple[str, ...] = field(default=())

    @property
    def reply_tokens(self) -> int:
        """Response budget, scaled with the number of files in the chunk."""
        return min(256 + 48 * max(len(self.paths) - 1, 0), 768)


def extract_choice_content(choice: Any) -> str:
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
    >>> extract_choice_content(Choice(MsgObj("hello")))
    'hello'

    >>> # dict-like message with nested content
    >>> extract_choice_content({'message': {'content': 'hi'}})
    'hi'

    >>> # dict-like fallback to text
    >>> extract_choice_content({'text': 'plain text'})
    'plain text'

    >>> # plain string fallback
    >>> extract_choice_content('just a string')
    'just a string'

    >>> # message attribute present but None -> empty string
    >>> extract_choice_content(Choice(None))
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


def count_tokens(model: str, text: str) -> int:
    """Estimate the token count of plain text, falling back to a heuristic."""
    # Token estimation is an optional safeguard and must never block generation.
    # pylint: disable=broad-exception-caught
    try:
        return int(litellm.token_counter(model=model, text=text))
    except Exception as exc:  # noqa: BLE001
        logger.debug("Unable to count tokens for model '%s': %s", model, exc)
        return len(text) // 4  # rough heuristic: ~4 characters per token
    # pylint: enable=broad-exception-caught


def split_diff_by_file(diff_message: str) -> list[str]:
    """Split a unified diff into per-file sections, preserving the marker."""
    parts = diff_message.split(FILE_DIFF_MARKER)
    if len(parts) <= 1:
        return [diff_message] if diff_message else []

    sections = [parts[0]] if parts[0] else []
    sections.extend(FILE_DIFF_MARKER + part for part in parts[1:])
    return sections


def split_text_by_token_budget(
    model: str, text: str, max_chunk_tokens: int
) -> list[str]:
    """Split ``text`` into chunks of at most ``max_chunk_tokens`` tokens."""
    lines = text.splitlines(keepends=True)
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(model, line)
        if current and current_tokens + line_tokens > max_chunk_tokens:
            chunks.append("".join(current))
            current = []
            current_tokens = 0
        current.append(line)
        current_tokens += line_tokens

    if current:
        chunks.append("".join(current))

    return chunks


def file_path_from_section(section: str) -> str:
    """Return the post-image path from a ``diff --git`` header line.

    Examples
    --------
    >>> file_path_from_section('diff --git a/src/app.py b/src/app.py\\n+x')
    'src/app.py'
    >>> file_path_from_section('no header here')
    ''

    """
    header = section.split("\n", 1)[0]
    if not header.startswith(FILE_DIFF_MARKER):
        return ""

    _, separator, new_path = header[len(FILE_DIFF_MARKER) :].partition(" b/")
    return new_path.strip().strip('"') if separator else ""


def is_low_signal_path(path: str) -> bool:
    """Return ``True`` for machine-generated paths not worth an LLM call.

    Examples
    --------
    >>> is_low_signal_path('poetry.lock')
    True
    >>> is_low_signal_path('web/node_modules/left-pad/index.js')
    True
    >>> is_low_signal_path('src/app.py')
    False

    """
    segments = path.split("/")
    if segments[-1] in LOW_SIGNAL_FILENAMES:
        return True
    if path.endswith(LOW_SIGNAL_SUFFIXES):
        return True
    return any(segment in LOW_SIGNAL_DIRS for segment in segments)


def file_change_stat(path: str, section: str) -> str:
    """Describe a file's diff section from its headers and line counts.

    These facts are derived rather than inferred, so they anchor the model
    against hallucinated file names and change types.

    Examples
    --------
    >>> file_change_stat('a.py', 'diff --git a/a.py b/a.py\\n+one\\n-two')
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
    if path and is_low_signal_path(path):
        return f"{stat} [generated; not analyzed]"
    return stat


def build_skeleton(sections: list[tuple[str, str]]) -> str:
    """Return the deterministic per-file stat block, truncated when huge."""
    stats = [file_change_stat(path, section) for path, section in sections]
    if len(stats) <= MAX_SKELETON_FILES:
        return "\n".join(stats)

    hidden = len(stats) - MAX_SKELETON_FILES
    return "\n".join(stats[:MAX_SKELETON_FILES] + [f"- ... and {hidden} more file(s)"])


def _split_oversized_section(model: str, path: str, section: str) -> list[DiffChunk]:
    """Break a single file's diff into part-sized chunks."""
    parts = split_text_by_token_budget(model, section, CHUNK_TOKENS)
    return [
        DiffChunk(
            label=f"{path} (part {index}/{len(parts)})",
            text=f"File: {path}\nFragment {index} of {len(parts)}\n\n{part}",
            system_prompt=PART_SUMMARY_SYSTEM_PROMPT,
            paths=(path,),
        )
        for index, part in enumerate(parts, start=1)
    ]


def _pack_chunk(entries: list[tuple[str, str]]) -> DiffChunk:
    """Turn one or more whole-file sections into a single map chunk."""
    if len(entries) == 1:
        path, section = entries[0]
        return DiffChunk(
            label=path,
            text=f"File: {path}\n\n{section}",
            system_prompt=FILE_SUMMARY_SYSTEM_PROMPT,
            paths=(path,),
        )

    paths = tuple(path for path, _ in entries)
    manifest = "\n".join(f"- {path}" for path in paths)
    body = "\n\n".join(f"File: {path}\n\n{section}" for path, section in entries)
    return DiffChunk(
        label=f"{len(paths)} files",
        text=f"Files in this batch:\n{manifest}\n\n{body}",
        system_prompt=GROUP_SUMMARY_SYSTEM_PROMPT,
        paths=paths,
    )


def plan_chunks(model: str, sections: list[tuple[str, str]]) -> list[DiffChunk]:
    """Pack ``(path, section)`` pairs into map-step chunks.

    Oversized files are split into parts so no single request is truncated,
    while files that fit are packed together up to :data:`CHUNK_TOKENS` and
    :data:`MAX_FILES_PER_CHUNK` so a wide, shallow change set costs few
    requests. Packing follows diff order, which keeps sibling paths together.
    """
    chunks: list[DiffChunk] = []
    batch: list[tuple[str, str]] = []
    batch_tokens = 0

    def flush() -> None:
        nonlocal batch, batch_tokens
        if batch:
            chunks.append(_pack_chunk(batch))
            batch = []
            batch_tokens = 0

    for raw_path, section in sections:
        path = raw_path or "unknown path"
        tokens = count_tokens(model, section)

        if tokens > CHUNK_TOKENS:
            flush()
            chunks.extend(_split_oversized_section(model, path, section))
            continue

        if batch and (
            batch_tokens + tokens > CHUNK_TOKENS or len(batch) >= MAX_FILES_PER_CHUNK
        ):
            flush()

        batch.append((path, section))
        batch_tokens += tokens

    flush()
    return chunks


def summarize_text(
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
            max_tokens=max_tokens,
            drop_params=True,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("Summarization request failed: %s", exc)
        return ""
    # pylint: enable=broad-exception-caught

    choices = getattr(response, "choices", []) or []
    contents = (extract_choice_content(c) for c in choices)
    return "\n".join(filter(None, (s.strip() for s in contents))).strip()


def _format_note(chunk: DiffChunk, summary: str) -> str:
    """Render one map result, keeping multi-file replies as their own bullets."""
    lines = [line.strip().lstrip("-* ").strip() for line in summary.splitlines()]
    lines = [line for line in lines if line]
    if not lines:
        return ""

    if len(chunk.paths) > 1:
        return "\n".join(f"- {line}" for line in lines)
    return f"- {chunk.label}: " + "; ".join(lines)


def map_chunks(model: str, chunks: list[DiffChunk]) -> list[str]:
    """Summarize every chunk in parallel and time-bounded, preserving order."""
    if not chunks:
        return []

    ordered: list[str | None] = [None] * len(chunks)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS)
    try:
        futures = {
            executor.submit(
                summarize_text,
                model,
                chunk.system_prompt,
                chunk.text,
                chunk.reply_tokens,
            ): index
            for index, chunk in enumerate(chunks)
        }
        try:
            for future in concurrent.futures.as_completed(futures, timeout=MAP_TIMEOUT):
                ordered[futures[future]] = future.result()
        except concurrent.futures.TimeoutError:
            logger.warning(
                "Summarization map step exceeded %d seconds; using partial results.",
                MAP_TIMEOUT,
            )
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    notes: list[str] = []
    for chunk, summary in zip(chunks, ordered):
        if summary and summary.strip():
            note = _format_note(chunk, summary)
            if note:
                notes.append(note)
    return notes


def reduce_summaries(model: str, summaries: list[str]) -> str:
    """Collapse per-chunk notes until they fit the summarization budget."""
    text = "\n".join(summaries)

    for _ in range(MAX_REDUCE_ROUNDS):
        if count_tokens(model, text) <= CHUNK_TOKENS:
            break

        groups = split_text_by_token_budget(model, text, CHUNK_TOKENS)
        reduced = [
            summary
            for group in groups
            if (summary := summarize_text(model, REDUCE_SUMMARY_SYSTEM_PROMPT, group))
        ]
        if not reduced:
            logger.warning("Reduce step produced no output; keeping current notes.")
            break

        text = "\n".join(reduced)

    return text


def summarize_diff(model: str, diff_message: str) -> str:
    """Compress an oversized diff into a file-anchored change report.

    Every file contributes a deterministic stat line derived from the diff
    headers, and every non-generated file is covered by a map chunk before the
    notes are collapsed to fit the budget. Returns the original diff when no
    summary could be produced.
    """
    sections = [
        (file_path_from_section(section), section)
        for section in split_diff_by_file(diff_message)
        if section.strip()
    ]
    if not sections:
        return diff_message

    skeleton = build_skeleton(sections)
    analyzable = [
        (path, section)
        for path, section in sections
        if not (path and is_low_signal_path(path))
    ]

    chunks = plan_chunks(model, analyzable)
    summaries = map_chunks(model, chunks)
    if not summaries:
        logger.warning("Summarization chain produced no output; giving up.")
        return diff_message

    notes = reduce_summaries(model, summaries)
    logger.debug(
        "Summarized %d file(s) (%d analyzed) in %d chunk(s): %d -> %d chars",
        len(sections),
        len(analyzable),
        len(chunks),
        len(diff_message),
        len(notes),
    )
    return f"Files changed:\n{skeleton}\n\nWhat changed:\n{notes}"
