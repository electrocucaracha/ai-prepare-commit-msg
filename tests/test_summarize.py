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

from types import SimpleNamespace

from ai_prepare_commit_msg import summarize


def _diff(path: str, body: str = "+change\n") -> str:
    """Build a minimal single-file diff section."""
    return f"diff --git a/{path} b/{path}\n{body}"


def test_split_diff_by_file():
    """Diffs are split into per-file sections, preamble included."""
    diff = "preamble\ndiff --git a b\n+1\ndiff --git c d\n+2"

    sections = summarize.split_diff_by_file(diff)

    assert sections == ["preamble\n", "diff --git a b\n+1\n", "diff --git c d\n+2"]
    assert summarize.split_diff_by_file("preamble\ndiff --git a b\n+1") == [
        "preamble\n",
        "diff --git a b\n+1",
    ]
    assert summarize.split_diff_by_file("no markers here") == ["no markers here"]
    assert not summarize.split_diff_by_file("")


def test_split_text_by_token_budget_splits_oversized_section(monkeypatch):
    """A single file section larger than the budget is split by line."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, text: len(text))

    diff = "line one\nline two\nline six\n"
    chunks = summarize.split_text_by_token_budget("mymodel", diff, max_chunk_tokens=10)

    assert "".join(chunks) == diff
    assert all(len(chunk) <= 10 for chunk in chunks)
    assert not summarize.split_text_by_token_budget("mymodel", "", 10)


def test_split_text_by_token_budget_splits_one_oversized_line(monkeypatch):
    """A single long line is split instead of exceeding the chunk budget."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, text: len(text))

    text = "x" * 21 + "\n"
    chunks = summarize.split_text_by_token_budget("mymodel", text, 10)

    assert "".join(chunks) == text
    assert all(len(chunk) <= 10 for chunk in chunks)


def test_split_text_by_token_budget_packs_lines_with_the_requested_model(monkeypatch):
    """Whole lines fill each chunk up to the budget using the requested model."""
    observed_models = []

    def count_tokens(model, text):
        observed_models.append(model)
        return len(text)

    monkeypatch.setattr(summarize, "count_tokens", count_tokens)
    lines = ["abc\n", "def\n", "ghi\n", "jkl\n"]

    chunks = summarize.split_text_by_token_budget(
        "custom-model", "".join(lines), max_chunk_tokens=6
    )

    assert chunks == lines
    assert observed_models and set(observed_models) == {"custom-model"}


def test_split_text_by_token_budget_keeps_exact_fit_line_intact(monkeypatch):
    """A line that exactly fits is not recursively split or recounted."""
    counted = []

    def count_tokens(_model, text):
        counted.append(text)
        return len(text)

    monkeypatch.setattr(summarize, "count_tokens", count_tokens)
    text = "x" * 10

    assert summarize.split_text_by_token_budget("model", text, 10) == [text]
    assert counted == [text]


def test_split_text_by_token_budget_splits_short_oversized_line(monkeypatch):
    """Even a two-character line is split when it exceeds a one-token budget."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, text: len(text))

    assert summarize.split_text_by_token_budget("model", "xy", 1) == ["x", "y"]


def test_count_tokens_falls_back_to_heuristic_on_failure(monkeypatch):
    """Token counting failures fall back to a character-based heuristic."""

    def boom(**_kwargs):
        raise RuntimeError("model not recognized")

    monkeypatch.setattr(summarize.litellm, "token_counter", boom)

    assert summarize.count_tokens("mymodel", "12345678") == 2


def test_count_tokens_normalizes_successful_result(monkeypatch):
    """A successful provider count is converted to an integer with its inputs."""
    observed = {}

    def token_counter(**kwargs):
        observed.update(kwargs)
        return 123

    monkeypatch.setattr(summarize.litellm, "token_counter", token_counter)

    assert summarize.count_tokens("mymodel", "12345678") == 123
    assert observed == {"model": "mymodel", "text": "12345678"}


def test_file_path_and_change_stat_are_derived_from_headers():
    """File identity and change type come from the diff, not the model."""
    added = "diff --git a/src/new.py b/src/new.py\nnew file mode 100644\n+one\n"
    renamed = "diff --git a/old.py b/moved.py\nrename from old.py\nrename to moved.py\n"

    assert summarize.file_path_from_section(added) == "src/new.py"
    assert summarize.file_path_from_section("preamble only") == ""
    assert (
        summarize.file_path_from_section('diff --git a/old.py b/"new file.py"\n+one\n')
        == "new file.py"
    )
    assert summarize.file_path_from_section("diff --git a/old.py c/new.py\n+one") == ""
    assert (
        summarize.file_change_stat("src/new.py", added) == "- src/new.py (added, +1/-0)"
    )
    modified = (
        "diff --git a/src/app.py b/src/app.py\n"
        "index abc..def 100644\n"
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "+new\n-old\n"
    )
    assert summarize.file_change_stat("src/app.py", modified) == (
        "- src/app.py (modified, +1/-1)"
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
    assert all(
        summarize.is_low_signal_path(path)
        for path in (
            "dist/app.min.js",
            "pkg/service.pb.go",
            "web/node_modules/app.js",
            "src/vendor/generated.py",
            "uv.lock",
        )
    )
    assert not summarize.is_low_signal_path("src/app.py")


def test_build_skeleton_truncates_very_wide_change_sets():
    """A change set beyond the skeleton cap is summarized with a counter."""
    sections = [
        (f"src/mod{index}.py", _diff(f"src/mod{index}.py")) for index in range(205)
    ]

    skeleton = summarize.build_skeleton(sections)

    assert skeleton.splitlines()[-1] == "- ... and 5 more file(s)"
    assert len(skeleton.splitlines()) == 201
    assert skeleton.splitlines()[0].startswith("- src/mod0.py ")
    assert skeleton.splitlines()[-2].startswith("- src/mod199.py ")


def test_plan_chunks_groups_small_files_into_one_request(monkeypatch):
    """Many small files share a chunk so the map step stays cheap."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, _text: 1)

    sections = [(f"f{index}.py", _diff(f"f{index}.py")) for index in range(3)]
    chunks = summarize.plan_chunks("mymodel", sections)

    assert len(chunks) == 1
    assert chunks[0].paths == ("f0.py", "f1.py", "f2.py")
    assert chunks[0].system_prompt == summarize.GROUP_SUMMARY_SYSTEM_PROMPT
    assert chunks[0].text == (
        "Files in this batch:\n"
        "- f0.py\n- f1.py\n- f2.py\n\n"
        f"File: f0.py\n\n{sections[0][1]}\n\n"
        f"File: f1.py\n\n{sections[1][1]}\n\n"
        f"File: f2.py\n\n{sections[2][1]}"
    )


def test_plan_chunks_uses_one_token_minimum_for_default_budget(monkeypatch):
    """A tiny model budget still splits files into valid one-token chunks."""
    monkeypatch.setattr(summarize, "get_prompt_token_limit", lambda _model: 6)
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, _text: 2)
    observed_budgets = []

    def split(_model, text, budget):
        observed_budgets.append(budget)
        return [text]

    monkeypatch.setattr(summarize, "split_text_by_token_budget", split)

    chunks = summarize.plan_chunks("small-model", [("a.py", "a"), ("b.py", "b")])

    assert [chunk.label for chunk in chunks] == [
        "a.py (part 1/1)",
        "b.py (part 1/1)",
    ]
    assert all(
        chunk.system_prompt == summarize.PART_SUMMARY_SYSTEM_PROMPT for chunk in chunks
    )
    assert observed_budgets == [1, 1]


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
    assert chunks[1].text == f"File: f{count - 1}.py\n\n{sections[-1][1]}"


def test_plan_chunks_starts_a_new_chunk_when_the_budget_is_reached(monkeypatch):
    """A file that does not fit the running batch opens the next chunk."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, _text: 6)

    sections = [("a.py", _diff("a.py")), ("b.py", _diff("b.py"))]
    chunks = summarize.plan_chunks("mymodel", sections, chunk_tokens=10)

    assert [chunk.paths for chunk in chunks] == [("a.py",), ("b.py",)]


def test_plan_chunks_splits_a_file_larger_than_the_budget(monkeypatch):
    """An oversized file becomes labelled parts instead of one huge request."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, _text: 11)
    monkeypatch.setattr(
        summarize,
        "split_text_by_token_budget",
        lambda _model, text, _budget: [text[:1], text[1:]],
    )

    chunks = summarize.plan_chunks("mymodel", [("big.py", "xy")], chunk_tokens=10)

    assert [chunk.label for chunk in chunks] == [
        "big.py (part 1/2)",
        "big.py (part 2/2)",
    ]
    assert all(
        chunk.system_prompt == summarize.PART_SUMMARY_SYSTEM_PROMPT for chunk in chunks
    )
    assert [chunk.text for chunk in chunks] == [
        "File: big.py\nFragment 1 of 2\n\nx",
        "File: big.py\nFragment 2 of 2\n\ny",
    ]


def test_plan_chunks_flushes_the_batch_before_an_oversized_file(monkeypatch):
    """Pending small files are emitted before a split file, keeping diff order."""
    sizes = {"small.py": 1}
    monkeypatch.setattr(
        summarize,
        "count_tokens",
        lambda _model, text: sizes.get(text, 11),
    )
    monkeypatch.setattr(
        summarize, "split_text_by_token_budget", lambda _model, text, _budget: [text]
    )

    chunks = summarize.plan_chunks(
        "mymodel",
        [("small.py", "small.py"), ("big.py", "big body")],
        chunk_tokens=10,
    )

    assert [chunk.label for chunk in chunks] == ["small.py", "big.py (part 1/1)"]


def test_map_chunks_returns_empty_list_without_chunks(monkeypatch):
    """No chunks to summarize means no summarization calls happen."""

    def fail(*_args, **_kwargs):
        raise AssertionError("summarization should not be called")

    monkeypatch.setattr(summarize, "summarize_text", fail)

    assert not summarize.map_chunks("mymodel", [])


def test_map_chunks_labels_single_file_notes_by_path(monkeypatch):
    """A single-file chunk is rendered as one path-prefixed bullet."""
    seen = {}
    worker_limits = []
    real_executor = summarize.concurrent.futures.ThreadPoolExecutor

    def make_executor(*args, **kwargs):
        worker_limits.append(kwargs.get("max_workers"))
        return real_executor(*args, **kwargs)

    monkeypatch.setattr(
        summarize.concurrent.futures, "ThreadPoolExecutor", make_executor
    )

    def fake_summarize(model, system_prompt, content, max_tokens=512):
        seen[content] = (model, system_prompt, max_tokens)
        return "note"

    monkeypatch.setattr(summarize, "summarize_text", fake_summarize)

    chunks = [
        summarize.DiffChunk("a.py", "File: a.py\n\ndiff a", "sys", ("a.py",)),
        summarize.DiffChunk("b.py", "File: b.py\n\ndiff b", "sys", ("b.py",)),
    ]

    assert summarize.map_chunks("mymodel", chunks) == ["- a.py: note", "- b.py: note"]
    assert seen == {
        "File: a.py\n\ndiff a": ("mymodel", "sys", 256),
        "File: b.py\n\ndiff b": ("mymodel", "sys", 256),
    }
    assert worker_limits == [summarize.MAX_WORKERS]


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


def test_map_chunks_ignores_whitespace_only_summaries(monkeypatch):
    """Blank provider output does not create an empty file note."""
    monkeypatch.setattr(
        summarize, "summarize_text", lambda *_args, **_kwargs: " \n- \n\t "
    )
    chunk = summarize.DiffChunk("a.py", "diff a", "sys", ("a.py",))

    assert not summarize.map_chunks("mymodel", [chunk])


def test_map_chunks_keeps_partial_results_on_timeout(monkeypatch):
    """A map step that exceeds the timeout keeps whatever completed."""
    monkeypatch.setattr(summarize, "summarize_text", lambda *_args, **_kwargs: "note")
    real_executor = summarize.concurrent.futures.ThreadPoolExecutor
    shutdown_calls = []
    warnings = []
    monkeypatch.setattr(
        summarize.logger,
        "warning",
        lambda message, *args: warnings.append(message % args),
    )

    class RecordingExecutor:
        """Capture executor shutdown arguments while using a real executor."""

        def __init__(self, max_workers):
            """Create the underlying thread pool."""
            self.executor = real_executor(max_workers=max_workers)

        def submit(self, *args, **kwargs):
            """Submit work to the underlying thread pool."""
            return self.executor.submit(*args, **kwargs)

        def shutdown(self, **kwargs):
            """Record shutdown options before forwarding them."""
            shutdown_calls.append(kwargs)
            self.executor.shutdown(**kwargs)

    monkeypatch.setattr(
        summarize.concurrent.futures, "ThreadPoolExecutor", RecordingExecutor
    )

    def fake_as_completed(futures, timeout=None):
        assert timeout == summarize.MAP_TIMEOUT
        yield list(futures)[-1]
        raise summarize.concurrent.futures.TimeoutError("map step took too long")

    monkeypatch.setattr(summarize.concurrent.futures, "as_completed", fake_as_completed)

    chunks = [
        summarize.DiffChunk("a.py", "diff a", "sys", ("a.py",)),
        summarize.DiffChunk("b.py", "diff b", "sys", ("b.py",)),
    ]

    assert summarize.map_chunks("mymodel", chunks) == ["- b.py: note"]
    assert shutdown_calls == [{"wait": False, "cancel_futures": True}]
    assert warnings == [
        "Summarization map step exceeded 120 seconds; using partial results."
    ]


def test_diff_chunk_reply_tokens_scale_with_file_count():
    """Grouped chunks get a bigger reply budget than single-file chunks."""
    single = summarize.DiffChunk("a.py", "body", "sys", ("a.py",))
    grouped = summarize.DiffChunk("3 files", "body", "sys", ("a.py", "b.py", "c.py"))

    assert single.reply_tokens == 256
    assert grouped.reply_tokens > single.reply_tokens


def test_format_note_returns_empty_string_when_summary_has_no_content():
    """A summary made only of blank lines and bullet markers yields no note."""
    chunk = summarize.DiffChunk("a.py", "diff a", "sys", ("a.py",))

    assert summarize._format_note(chunk, "  \n- \n* \n") == ""


def test_format_note_preserves_text_starting_with_bullet_characters():
    """Only bullet markers and whitespace are removed from the start of lines."""
    chunk = summarize.DiffChunk("a.py", "diff a", "sys", ("a.py",))

    assert summarize._format_note(chunk, "Xylophone changed") == (
        "- a.py: Xylophone changed"
    )


def test_summarize_text_returns_joined_choices(monkeypatch):
    """A summarization request joins the returned choice contents."""

    class Resp:
        """Response-like object exposing a ``choices`` sequence."""

        def __init__(self, choices):
            self.choices = choices

    observed = {}

    def complete(**kwargs):
        observed.update(kwargs)
        return Resp(
            [
                {"text": " summary "},
                {"message": {"content": " second "}},
                {"text": ""},
            ]
        )

    monkeypatch.setattr(summarize.litellm, "completion", complete)

    assert summarize.summarize_text("mymodel", "system prompt", "content") == (
        "summary\nsecond"
    )
    assert observed == {
        "model": "mymodel",
        "messages": [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "content"},
        ],
        "max_tokens": 512,
        "drop_params": True,
    }


def test_summarize_text_returns_empty_on_failure(monkeypatch):
    """Provider failures during summarization degrade to an empty string."""

    def boom(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(summarize.litellm, "completion", boom)

    assert summarize.summarize_text("mymodel", "system prompt", "content") == ""


def test_summarize_text_returns_empty_when_response_has_no_choices(monkeypatch):
    """Missing, null, and empty choice collections all produce an empty summary."""
    responses = [
        SimpleNamespace(),
        SimpleNamespace(choices=None),
        SimpleNamespace(choices=[]),
    ]

    for response in responses:
        monkeypatch.setattr(
            summarize.litellm,
            "completion",
            lambda response=response, **_kwargs: response,
        )
        assert summarize.summarize_text("mymodel", "system prompt", "content") == ""


def test_reduce_summaries_collapses_until_within_budget(monkeypatch):
    """Oversized per-file notes are re-summarized before being returned."""
    token_counts = iter([11, 1])
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: next(token_counts))
    monkeypatch.setattr(
        summarize, "split_text_by_token_budget", lambda _model, text, _budget: [text]
    )

    calls: list[str] = []

    def fake_summarize(_model, system_prompt, *_args):
        calls.append(system_prompt)
        return "reduced"

    monkeypatch.setattr(summarize, "summarize_text", fake_summarize)

    notes = summarize.reduce_summaries(
        "mymodel", ["- a.py: one", "- b.py: two"], chunk_tokens=10
    )

    assert notes == "reduced"
    assert calls == [summarize.REDUCE_SUMMARY_SYSTEM_PROMPT]


def test_reduce_summaries_repeats_until_the_reduced_text_fits(monkeypatch):
    """More than one reduction round runs when an intermediate still exceeds budget."""
    token_counts = iter([30, 20, 1])
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: next(token_counts))
    split_inputs = iter([["first", "second"], ["combined"]])

    def split(_model, _text, budget):
        assert budget == 10
        return next(split_inputs)

    monkeypatch.setattr(summarize, "split_text_by_token_budget", split)

    calls = []

    def fake_summarize(_model, system_prompt, content):
        calls.append((system_prompt, content))
        return {"first": "one", "second": "two", "combined": "done"}[content]

    monkeypatch.setattr(summarize, "summarize_text", fake_summarize)

    assert (
        summarize.reduce_summaries(
            "mymodel", ["- a.py: one", "- b.py: two"], chunk_tokens=10
        )
        == "done"
    )
    assert calls == [
        (summarize.REDUCE_SUMMARY_SYSTEM_PROMPT, "first"),
        (summarize.REDUCE_SUMMARY_SYSTEM_PROMPT, "second"),
        (summarize.REDUCE_SUMMARY_SYSTEM_PROMPT, "combined"),
    ]


def test_reduce_summaries_stops_after_three_rounds(monkeypatch):
    """Reduction is capped to bound repeated model calls when notes stay oversized."""
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: 11)
    monkeypatch.setattr(
        summarize, "split_text_by_token_budget", lambda _model, text, _budget: [text]
    )
    summaries = []

    def reduce(_model, _system_prompt, _content):
        summaries.append(None)
        return f"round {len(summaries)}"

    monkeypatch.setattr(summarize, "summarize_text", reduce)

    result = summarize.reduce_summaries("mymodel", ["oversized notes"], chunk_tokens=10)

    assert result == "round 3"
    assert len(summaries) == 3


def test_reduce_summaries_keeps_notes_within_budget(monkeypatch):
    """Notes that already fit are returned verbatim, with no extra LLM call."""
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: 1)

    def fail(*_args, **_kwargs):
        raise AssertionError("reduce should not call the model")

    monkeypatch.setattr(summarize, "summarize_text", fail)

    assert (
        summarize.reduce_summaries("mymodel", ["- a.py: one"], chunk_tokens=10)
        == "- a.py: one"
    )


def test_reduce_summaries_uses_model_budget_when_unspecified(monkeypatch):
    """An omitted chunk budget is resolved from the model metadata."""
    monkeypatch.setattr(summarize, "get_prompt_token_limit", lambda _model: 60)
    observed = []
    monkeypatch.setattr(
        summarize,
        "count_tokens",
        lambda _model, text: observed.append(text) or 1,
    )

    assert summarize.reduce_summaries("mymodel", ["- a.py: one"]) == "- a.py: one"
    assert observed == ["- a.py: one"]


def test_reduce_summaries_uses_one_token_minimum_for_tiny_model_budget(monkeypatch):
    """A tiny model limit triggers reduction instead of returning oversized notes."""
    monkeypatch.setattr(summarize, "get_prompt_token_limit", lambda _model: 6)
    token_counts = iter([2, 1])
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: next(token_counts))
    observed_budgets = []

    def split(_model, _text, budget):
        observed_budgets.append(budget)
        return ["oversized notes"]

    monkeypatch.setattr(summarize, "split_text_by_token_budget", split)
    monkeypatch.setattr(summarize, "summarize_text", lambda *_args: "reduced")

    assert summarize.reduce_summaries("small-model", ["notes"]) == "reduced"
    assert observed_budgets == [1]


def test_reduce_summaries_stops_when_reduce_step_produces_nothing(monkeypatch):
    """The reduce loop bails out instead of looping forever on empty output."""
    monkeypatch.setattr(summarize, "count_tokens", lambda *_args: 11)
    monkeypatch.setattr(
        summarize, "split_text_by_token_budget", lambda _model, text, _budget: [text]
    )
    monkeypatch.setattr(summarize, "summarize_text", lambda *_args, **_kwargs: "")

    summaries = ["- a.py: one", "- b.py: two"]

    assert summarize.reduce_summaries(
        "mymodel", summaries, chunk_tokens=10
    ) == "\n".join(summaries)


def test_low_signal_files_are_reported_without_an_llm_call(monkeypatch):
    """Generated files appear in the skeleton but are never summarized."""
    diff = (
        "diff --git a/poetry.lock b/poetry.lock\n+lock\n"
        "diff --git a/src/app.py b/src/app.py\n+real change\n"
    )
    analyzed: list[tuple[str, ...]] = []
    prompt_models = []
    chunk_models = []
    map_models = []
    reduce_models = []

    def get_prompt_token_limit(model):
        prompt_models.append(model)
        return 600

    def count_tokens(model, _text):
        chunk_models.append(model)
        return 1

    def fake_map(model, chunks):
        map_models.append(model)
        analyzed.extend(chunk.paths for chunk in chunks)
        return ["- src/app.py: adds a real change"]

    monkeypatch.setattr(summarize, "map_chunks", fake_map)
    monkeypatch.setattr(summarize, "get_prompt_token_limit", get_prompt_token_limit)
    monkeypatch.setattr(summarize, "count_tokens", count_tokens)

    def reduce_summaries(model, notes, _chunk_tokens):
        reduce_models.append(model)
        return "\n".join(notes)

    monkeypatch.setattr(summarize, "reduce_summaries", reduce_summaries)

    result = summarize.summarize_diff("mymodel", diff)

    assert analyzed == [("src/app.py",)]
    assert result == (
        "Files changed:\n"
        "- poetry.lock (modified, +1/-0) [generated; not analyzed]\n"
        "- src/app.py (modified, +1/-0)\n\n"
        "What changed:\n"
        "- src/app.py: adds a real change"
    )
    assert prompt_models == ["mymodel"]
    assert chunk_models == ["mymodel"]
    assert map_models == ["mymodel"]
    assert reduce_models == ["mymodel"]


def test_summarize_diff_returns_original_when_all_sections_are_blank():
    """A diff whose sections are all blank/whitespace is returned unchanged."""
    diff = "\n\n   \n"

    assert summarize.summarize_diff("mymodel", diff) == diff


def test_summarize_diff_returns_original_when_no_summaries(monkeypatch, caplog):
    """The original diff is kept if the map step produces no summaries."""
    monkeypatch.setattr(summarize, "map_chunks", lambda _model, _chunks: [])

    diff = "diff --git a/a.py b/a.py\n+x\n"
    with caplog.at_level("WARNING", logger=summarize.__name__):
        assert summarize.summarize_diff("mymodel", diff) == diff
    assert caplog.messages == ["Summarization chain produced no output; giving up."]


def test_summarize_diff_keeps_one_token_minimum_for_tiny_budgets(monkeypatch):
    """A prompt budget below one chunk divisor still splits oversized files."""
    monkeypatch.setattr(summarize, "count_tokens", lambda _model, _text: 2)
    monkeypatch.setattr(
        summarize,
        "split_text_by_token_budget",
        lambda _model, text, _budget: [text],
    )
    planned_chunks = []

    def map_chunks(_model, chunks):
        planned_chunks.extend(chunks)
        return ["- src/app.py: change"]

    monkeypatch.setattr(summarize, "map_chunks", map_chunks)
    monkeypatch.setattr(
        summarize, "reduce_summaries", lambda _model, notes, _budget: "\n".join(notes)
    )

    summarize.summarize_diff("mymodel", _diff("src/app.py"), prompt_token_limit=6)

    assert len(planned_chunks) == 1
    assert planned_chunks[0].label == "src/app.py (part 1/1)"
    assert planned_chunks[0].system_prompt == summarize.PART_SUMMARY_SYSTEM_PROMPT


def test_summarize_diff_passes_integer_chunk_budget(monkeypatch):
    """The model prompt budget is divided into an integer chunk size."""
    planned = []
    reduced = []

    def plan_chunks(model, sections, chunk_tokens):
        planned.append((model, sections, chunk_tokens))
        return []

    def map_chunks(_model, _chunks):
        return ["summary"]

    def reduce_summaries(model, notes, chunk_tokens):
        reduced.append((model, notes, chunk_tokens))
        return "summary"

    monkeypatch.setattr(summarize, "get_prompt_token_limit", lambda _model: 11)
    monkeypatch.setattr(summarize, "plan_chunks", plan_chunks)
    monkeypatch.setattr(summarize, "map_chunks", map_chunks)
    monkeypatch.setattr(summarize, "reduce_summaries", reduce_summaries)

    result = summarize.summarize_diff("mymodel", _diff("src/app.py"))

    assert result.startswith("Files changed:")
    assert planned[0][0] == "mymodel"
    assert planned[0][2] == 1
    assert reduced == [("mymodel", ["summary"], 1)]
