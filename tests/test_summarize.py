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

"""Tests for the ``ai_prepare_commit_msg.summarize`` map-reduce chain.

These tests access module-internal helpers on purpose.
"""

# Tests access internal helpers and use small helper classes.
# pylint: disable=protected-access,too-few-public-methods

from ai_prepare_commit_msg import summarize


def _diff(path: str, body: str = "+change\n") -> str:
    """Build a minimal single-file diff section."""
    return f"diff --git a/{path} b/{path}\n{body}"


def test_split_diff_by_file():
    """Diffs are split into per-file sections, preamble included."""
    diff = "preamble\ndiff --git a b\n+1\ndiff --git c d\n+2"

    sections = summarize.split_diff_by_file(diff)

    assert sections == ["preamble\n", "diff --git a b\n+1\n", "diff --git c d\n+2"]
    assert summarize.split_diff_by_file("no markers here") == ["no markers here"]
    assert not summarize.split_diff_by_file("")


def test_split_text_by_token_budget_splits_oversized_section(monkeypatch):
    """A single file section larger than the budget is split by line."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, text: len(text))

    diff = "line one\nline two\nline six\n"
    chunks = summarize.split_text_by_token_budget("mymodel", diff, max_chunk_tokens=10)

    assert "".join(chunks) == diff
    assert all(len(chunk) <= 10 for chunk in chunks)


def test_count_tokens_falls_back_to_heuristic_on_failure(monkeypatch):
    """Token counting failures fall back to a character-based heuristic."""

    def boom(**_kwargs):
        raise RuntimeError("model not recognized")

    monkeypatch.setattr(summarize.litellm, "token_counter", boom)

    assert summarize.count_tokens("mymodel", "12345678") == 2


def test_file_path_and_change_stat_are_derived_from_headers():
    """File identity and change type come from the diff, not the model."""
    added = "diff --git a/src/new.py b/src/new.py\nnew file mode 100644\n+one\n"
    renamed = "diff --git a/old.py b/moved.py\nrename from old.py\nrename to moved.py\n"

    assert summarize.file_path_from_section(added) == "src/new.py"
    assert (
        summarize.file_change_stat("src/new.py", added) == "- src/new.py (added, +1/-0)"
    )
    assert summarize.file_change_stat("moved.py", renamed).startswith(
        "- moved.py (renamed,"
    )


def test_file_change_stat_detects_deleted_and_binary_files():
    """Deleted and binary diff sections are reported with the right status."""
    deleted = "diff --git a/old.py b/old.py\ndeleted file mode 100644\n-one\n"
    binary = (
        "diff --git a/img.png b/img.png\nBinary files a/img.png and b/img.png differ\n"
    )

    assert summarize.file_change_stat("old.py", deleted) == "- old.py (deleted, +0/-1)"
    assert summarize.file_change_stat("img.png", binary) == "- img.png (binary, +0/-0)"


def test_is_low_signal_path_matches_generated_suffixes():
    """Minified and generated-code suffixes are treated as low signal."""
    assert summarize.is_low_signal_path("dist/app.min.js")
    assert summarize.is_low_signal_path("pkg/service.pb.go")
    assert not summarize.is_low_signal_path("src/app.py")


def test_build_skeleton_truncates_very_wide_change_sets():
    """A change set beyond the skeleton cap is summarized with a counter."""
    sections = [
        (f"src/mod{index}.py", _diff(f"src/mod{index}.py"))
        for index in range(summarize.MAX_SKELETON_FILES + 5)
    ]

    skeleton = summarize.build_skeleton(sections)

    assert skeleton.splitlines()[-1] == "- ... and 5 more file(s)"
    assert len(skeleton.splitlines()) == summarize.MAX_SKELETON_FILES + 1


def test_plan_chunks_groups_small_files_into_one_request(monkeypatch):
    """Many small files share a chunk so the map step stays cheap."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, _text: 1)

    sections = [(f"f{index}.py", _diff(f"f{index}.py")) for index in range(3)]
    chunks = summarize.plan_chunks("mymodel", sections)

    assert len(chunks) == 1
    assert chunks[0].paths == ("f0.py", "f1.py", "f2.py")
    assert chunks[0].system_prompt == summarize.GROUP_SUMMARY_SYSTEM_PROMPT
    assert all(f"f{index}.py" in chunks[0].text for index in range(3))


def test_plan_chunks_respects_the_file_count_cap(monkeypatch):
    """Grouping stops at ``MAX_FILES_PER_CHUNK`` even for tiny diffs."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, _text: 1)

    count = summarize.MAX_FILES_PER_CHUNK + 1
    sections = [(f"f{index}.py", _diff(f"f{index}.py")) for index in range(count)]
    chunks = summarize.plan_chunks("mymodel", sections)

    assert [len(chunk.paths) for chunk in chunks] == [
        summarize.MAX_FILES_PER_CHUNK,
        1,
    ]
    assert chunks[1].system_prompt == summarize.FILE_SUMMARY_SYSTEM_PROMPT


def test_plan_chunks_starts_a_new_chunk_when_the_budget_is_reached(monkeypatch):
    """A file that does not fit the running batch opens the next chunk."""
    monkeypatch.setattr(
        summarize, "count_tokens", lambda _model, _text: summarize.CHUNK_TOKENS // 2 + 1
    )

    sections = [("a.py", _diff("a.py")), ("b.py", _diff("b.py"))]
    chunks = summarize.plan_chunks("mymodel", sections)

    assert [chunk.paths for chunk in chunks] == [("a.py",), ("b.py",)]


def test_plan_chunks_splits_a_file_larger_than_the_budget(monkeypatch):
    """An oversized file becomes labelled parts instead of one huge request."""
    monkeypatch.setattr(
        summarize, "count_tokens", lambda _model, _text: summarize.CHUNK_TOKENS + 1
    )
    monkeypatch.setattr(
        summarize,
        "split_text_by_token_budget",
        lambda _model, text, _budget: [text[:1], text[1:]],
    )

    chunks = summarize.plan_chunks("mymodel", [("big.py", "xy")])

    assert [chunk.label for chunk in chunks] == [
        "big.py (part 1/2)",
        "big.py (part 2/2)",
    ]
    assert all(
        chunk.system_prompt == summarize.PART_SUMMARY_SYSTEM_PROMPT for chunk in chunks
    )


def test_plan_chunks_flushes_the_batch_before_an_oversized_file(monkeypatch):
    """Pending small files are emitted before a split file, keeping diff order."""
    sizes = {"small.py": 1}
    monkeypatch.setattr(
        summarize,
        "count_tokens",
        lambda _model, text: sizes.get(text, summarize.CHUNK_TOKENS + 1),
    )
    monkeypatch.setattr(
        summarize, "split_text_by_token_budget", lambda _model, text, _budget: [text]
    )

    chunks = summarize.plan_chunks(
        "mymodel", [("small.py", "small.py"), ("big.py", "big body")]
    )

    assert [chunk.label for chunk in chunks] == ["small.py", "big.py (part 1/1)"]


def test_map_chunks_returns_empty_list_without_chunks(monkeypatch):
    """No chunks to summarize means no summarization calls happen."""

    def fail(*_args, **_kwargs):
        raise AssertionError("summarization should not be called")

    monkeypatch.setattr(summarize, "summarize_text", fail)

    assert summarize.map_chunks("mymodel", []) == []


def test_map_chunks_labels_single_file_notes_by_path(monkeypatch):
    """A single-file chunk is rendered as one path-prefixed bullet."""
    seen: list[str] = []

    def fake_summarize(_model, _system_prompt, content, _max_tokens=512):
        seen.append(content)
        return "note"

    monkeypatch.setattr(summarize, "summarize_text", fake_summarize)

    chunks = [
        summarize.DiffChunk("a.py", "File: a.py\n\ndiff a", "sys", ("a.py",)),
        summarize.DiffChunk("b.py", "File: b.py\n\ndiff b", "sys", ("b.py",)),
    ]

    assert summarize.map_chunks("mymodel", chunks) == ["- a.py: note", "- b.py: note"]
    assert seen[0].startswith("File: a.py")


def test_map_chunks_keeps_group_replies_as_separate_bullets(monkeypatch):
    """A grouped reply already names each file, so its lines are kept as-is."""
    monkeypatch.setattr(
        summarize,
        "summarize_text",
        lambda *_args, **_kwargs: "* a.py: adds x\n- b.py: drops y\n",
    )

    chunk = summarize.DiffChunk("2 files", "body", "sys", ("a.py", "b.py"))

    assert summarize.map_chunks("mymodel", [chunk]) == [
        "- a.py: adds x\n- b.py: drops y"
    ]


def test_map_chunks_keeps_partial_results_on_timeout(monkeypatch):
    """A map step that exceeds the timeout keeps whatever completed."""
    monkeypatch.setattr(summarize, "summarize_text", lambda *_args, **_kwargs: "note")

    def fake_as_completed(_futures, timeout=None):  # pylint: disable=unused-argument
        # Raising here (rather than returning an iterable) is enough: the
        # exception fires before the ``for`` loop in ``map_chunks`` starts.
        raise summarize.concurrent.futures.TimeoutError("map step took too long")

    monkeypatch.setattr(summarize.concurrent.futures, "as_completed", fake_as_completed)

    chunk = summarize.DiffChunk("a.py", "diff a", "sys", ("a.py",))

    assert summarize.map_chunks("mymodel", [chunk]) == []


def test_diff_chunk_reply_tokens_scale_with_file_count():
    """Grouped chunks get a bigger reply budget than single-file chunks."""
    single = summarize.DiffChunk("a.py", "body", "sys", ("a.py",))
    grouped = summarize.DiffChunk("3 files", "body", "sys", ("a.py", "b.py", "c.py"))

    assert single.reply_tokens == 256
    assert grouped.reply_tokens > single.reply_tokens


def test_summarize_text_returns_joined_choices(monkeypatch):
    """A summarization request joins the returned choice contents."""

    class Resp:
        """Response-like object exposing a ``choices`` sequence."""

        def __init__(self, choices):
            self.choices = choices

    monkeypatch.setattr(
        summarize.litellm, "completion", lambda **_kwargs: Resp([{"text": "summary"}])
    )

    assert summarize.summarize_text("mymodel", "system prompt", "content") == "summary"


def test_summarize_text_returns_empty_on_failure(monkeypatch):
    """Provider failures during summarization degrade to an empty string."""

    def boom(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(summarize.litellm, "completion", boom)

    assert summarize.summarize_text("mymodel", "system prompt", "content") == ""


def test_reduce_summaries_collapses_until_within_budget(monkeypatch):
    """Oversized per-file notes are re-summarized before being returned."""
    token_counts = iter([summarize.CHUNK_TOKENS + 1, 1])
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: next(token_counts))
    monkeypatch.setattr(
        summarize, "split_text_by_token_budget", lambda _model, text, _budget: [text]
    )

    calls: list[str] = []

    def fake_summarize(_model, system_prompt, *_args):
        calls.append(system_prompt)
        return "reduced"

    monkeypatch.setattr(summarize, "summarize_text", fake_summarize)

    notes = summarize.reduce_summaries("mymodel", ["- a.py: one", "- b.py: two"])

    assert notes == "reduced"
    assert calls == [summarize.REDUCE_SUMMARY_SYSTEM_PROMPT]


def test_reduce_summaries_keeps_notes_within_budget(monkeypatch):
    """Notes that already fit are returned verbatim, with no extra LLM call."""
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: 1)

    def fail(*_args, **_kwargs):
        raise AssertionError("reduce should not call the model")

    monkeypatch.setattr(summarize, "summarize_text", fail)

    assert summarize.reduce_summaries("mymodel", ["- a.py: one"]) == "- a.py: one"


def test_reduce_summaries_stops_when_reduce_step_produces_nothing(monkeypatch):
    """The reduce loop bails out instead of looping forever on empty output."""
    monkeypatch.setattr(
        summarize, "count_tokens", lambda *_args: summarize.CHUNK_TOKENS + 1
    )
    monkeypatch.setattr(
        summarize, "split_text_by_token_budget", lambda _model, text, _budget: [text]
    )
    monkeypatch.setattr(summarize, "summarize_text", lambda *_args, **_kwargs: "")

    summaries = ["- a.py: one", "- b.py: two"]

    assert summarize.reduce_summaries("mymodel", summaries) == "\n".join(summaries)


def test_low_signal_files_are_reported_without_an_llm_call(monkeypatch):
    """Generated files appear in the skeleton but are never summarized."""
    diff = (
        "diff --git a/poetry.lock b/poetry.lock\n+lock\n"
        "diff --git a/src/app.py b/src/app.py\n+real change\n"
    )
    analyzed: list[tuple[str, ...]] = []

    def fake_map(_model, chunks):
        analyzed.extend(chunk.paths for chunk in chunks)
        return ["- src/app.py: adds a real change"]

    monkeypatch.setattr(summarize, "map_chunks", fake_map)
    monkeypatch.setattr(
        summarize, "reduce_summaries", lambda _model, notes: "\n".join(notes)
    )

    result = summarize.summarize_diff("mymodel", diff)

    assert analyzed == [("src/app.py",)]
    assert "poetry.lock" in result
    assert "[generated; not analyzed]" in result
    assert "adds a real change" in result


def test_summarize_diff_returns_original_when_all_sections_are_blank():
    """A diff whose sections are all blank/whitespace is returned unchanged."""
    diff = "\n\n   \n"

    assert summarize.summarize_diff("mymodel", diff) == diff


def test_summarize_diff_returns_original_when_no_summaries(monkeypatch):
    """The original diff is kept if the map step produces no summaries."""
    monkeypatch.setattr(summarize, "map_chunks", lambda _model, _chunks: [])

    diff = "diff --git a/a.py b/a.py\n+x\n"
    assert summarize.summarize_diff("mymodel", diff) == diff
