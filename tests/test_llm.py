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

"""Tests for the ``ai_prepare_commit_msg.llm`` helpers.

These tests validate content extraction from model choices and prompt
file handling. The tests access module-internal helpers on purpose.
"""

# Tests access internal helpers and use small helper classes.
# pylint: disable=protected-access,too-few-public-methods

from types import SimpleNamespace

import pytest

from ai_prepare_commit_msg import llm


def test__extract_choice_content_various_shapes():
    """Various model choice shapes are normalized to text."""

    class MsgObj:
        """Simple object holding a ``content`` attribute."""

        def __init__(self, content):
            self.content = content

    class ChoiceObj:
        """Simple object holding a ``message`` attribute."""

        def __init__(self, message):
            self.message = message

    # object with .message that has .content
    assert llm._extract_choice_content(ChoiceObj(MsgObj("hello"))) == "hello"

    # dict-like message with nested content
    assert llm._extract_choice_content({"message": {"content": "hi"}}) == "hi"

    # dict-like fallback to text
    assert llm._extract_choice_content({"text": "plain text"}) == "plain text"

    # plain string fallback
    assert llm._extract_choice_content("just a string") == "just a string"

    # message attribute present but None -> empty string
    assert llm._extract_choice_content(ChoiceObj(None)) == ""


def test_get_commit_msg_uses_litellm_and_joins_choices(monkeypatch):
    """The public helper calls ``litellm.completion`` and joins choices."""

    # Replace prompt loader to keep this test self-contained
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )

    class Msg:
        """Message-like object with ``content``."""

        def __init__(self, content):
            self.content = content

    class ChoiceObj:
        """Choice-like object with ``message`` attribute."""

        def __init__(self, message):
            self.message = message

    class Resp:
        """Response-like object exposing a ``choices`` sequence."""

        def __init__(self, choices):
            self.choices = choices

    def fake_completion(messages, model, **kwargs):  # pylint: disable=unused-argument
        # return a mixture of object choice and dict/text choice
        return Resp([ChoiceObj(Msg("generated")), {"text": "more"}])

    # Monkeypatch the litellm completion function in the imported module
    monkeypatch.setattr(llm.litellm, "completion", fake_completion)
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)

    result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")
    assert result == "generated\nmore"


def test_get_commit_msg_skips_oversized_diff_when_summarization_does_not_help(
    monkeypatch,
):
    """A warning is returned when the diff is still oversized after summarizing."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(
        llm, "_estimate_prompt_tokens", lambda *_args: llm.MAX_PROMPT_TOKENS + 1
    )
    monkeypatch.setattr(llm, "_summarize_diff_in_chunks", lambda _model, diff: diff)

    def fail_completion(**_kwargs):
        raise AssertionError("litellm.completion should not be called")

    monkeypatch.setattr(llm.litellm, "completion", fail_completion)

    result = llm.get_commit_msg("mymodel", "very large diff", "prompt.yml")

    assert result == llm.OVERSIZED_DIFF_WARNING


def test_get_commit_msg_uses_summarization_chain_for_oversized_diff(monkeypatch):
    """When the diff is oversized, a compressed summary is retried against the LLM."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )

    token_counts = iter([llm.MAX_PROMPT_TOKENS + 1, 42])
    monkeypatch.setattr(
        llm, "_estimate_prompt_tokens", lambda *_args: next(token_counts)
    )

    summarize_calls: list[str] = []

    def fake_summarize(_model, diff):
        summarize_calls.append(diff)
        return "summarized diff"

    monkeypatch.setattr(llm, "_summarize_diff_in_chunks", fake_summarize)

    seen_messages: list[list[dict[str, str]]] = []

    class Msg:
        """Message-like object with ``content``."""

        def __init__(self, content):
            self.content = content

    class ChoiceObj:
        """Choice-like object with ``message`` attribute."""

        def __init__(self, message):
            self.message = message

    class Resp:
        """Response-like object exposing a ``choices`` sequence."""

        def __init__(self, choices):
            self.choices = choices

    def fake_completion(messages, model, **kwargs):  # pylint: disable=unused-argument
        seen_messages.append(messages)
        return Resp([ChoiceObj(Msg("generated from summary"))])

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    result = llm.get_commit_msg("mymodel", "very large diff", "prompt.yml")

    assert summarize_calls == ["very large diff"]
    assert result == "generated from summary"
    assert seen_messages[-1][-1] == {"role": "user", "content": "summarized diff"}


def test_get_commit_msg_returns_warning_for_oversized_provider_error(monkeypatch):
    """Provider token-limit failures degrade to a warning message."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)

    def fake_completion(**_kwargs):
        raise RuntimeError("prompt token count of 287975 exceeds the limit of 128000")

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")

    assert result == llm.OVERSIZED_DIFF_WARNING


def test_compress_messages_records_savings(monkeypatch):
    """Headroom compression is applied and its token savings recorded."""
    compressed_result = SimpleNamespace(
        messages=[{"role": "system", "content": "x"}],
        tokens_before=1000,
        tokens_after=600,
        transforms_applied=["router:diff:0.6"],
    )

    llm.get_compression_stats().reset()
    monkeypatch.setattr(llm, "headroom_compress", lambda **_kwargs: compressed_result)

    messages = [{"role": "user", "content": "diff"}]

    assert llm._compress_messages("mymodel", messages) == compressed_result.messages

    stats = llm.get_compression_stats()
    assert stats.requests == 1
    assert stats.tokens_saved == 400
    assert stats.savings_ratio == pytest.approx(0.4)
    assert "saved 400 (40.0%)" in stats.format_summary()


def test_compress_messages_when_headroom_unavailable(monkeypatch):
    """Prompt messages pass through untouched when Headroom is missing."""
    llm.get_compression_stats().reset()
    monkeypatch.setattr(llm, "headroom_compress", None)

    messages = [{"role": "user", "content": "diff"}]

    assert llm._compress_messages("mymodel", messages) == messages
    assert llm.get_compression_stats().requests == 0


def test_compress_messages_falls_back_when_headroom_raises(monkeypatch):
    """Compression failures degrade to the original prompt."""

    def boom(**_kwargs):
        raise RuntimeError("compression backend unavailable")

    llm.get_compression_stats().reset()
    monkeypatch.setattr(llm, "headroom_compress", boom)

    messages = [{"role": "user", "content": "diff"}]

    assert llm._compress_messages("mymodel", messages) == messages
    assert llm.get_compression_stats().requests == 0


def test_split_diff_by_file():
    """Diffs are split into per-file sections, preamble included."""
    diff = "preamble\ndiff --git a b\n+1\ndiff --git c d\n+2"

    sections = llm._split_diff_by_file(diff)

    assert sections == ["preamble\n", "diff --git a b\n+1\n", "diff --git c d\n+2"]
    assert llm._split_diff_by_file("no markers here") == ["no markers here"]
    assert not llm._split_diff_by_file("")


def test_split_diff_into_chunks_groups_by_token_budget(monkeypatch):
    """Chunks stay under the budget and group whole file sections together."""
    monkeypatch.setattr(llm, "_count_tokens", lambda _model, text: len(text))

    diff = "diff --git a b\nfoodiff --git c d\nbardiff --git e f\nbaz"
    chunks = llm._split_diff_into_chunks("mymodel", diff, max_chunk_tokens=20)

    assert "".join(chunks) == diff
    assert all(len(chunk) <= 20 for chunk in chunks)


def test_split_diff_into_chunks_splits_oversized_section(monkeypatch):
    """A single file section larger than the budget is split by line."""
    monkeypatch.setattr(llm, "_count_tokens", lambda _model, text: len(text))

    diff = "line one\nline two\nline six\n"
    chunks = llm._split_diff_into_chunks("mymodel", diff, max_chunk_tokens=10)

    assert "".join(chunks) == diff
    assert all(len(chunk) <= 10 for chunk in chunks)


def test_summarize_text_returns_joined_choices(monkeypatch):
    """A summarization request joins the returned choice contents."""

    class Resp:
        """Response-like object exposing a ``choices`` sequence."""

        def __init__(self, choices):
            self.choices = choices

    monkeypatch.setattr(
        llm.litellm, "completion", lambda **_kwargs: Resp([{"text": "summary"}])
    )

    assert llm._summarize_text("mymodel", "system prompt", "content") == "summary"


def test_summarize_text_returns_empty_on_failure(monkeypatch):
    """Provider failures during summarization degrade to an empty string."""

    def boom(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm.litellm, "completion", boom)

    assert llm._summarize_text("mymodel", "system prompt", "content") == ""


def test_summarize_diff_in_chunks_maps_and_reduces(monkeypatch):
    """Oversized diffs are chunked, summarized, then reduced to one summary."""
    monkeypatch.setattr(
        llm,
        "_split_diff_into_chunks",
        lambda _model, _diff, _budget: ["chunk-a", "chunk-b"],
    )

    calls: list[tuple[str, str]] = []

    def fake_summarize(_model, system_prompt, content):
        calls.append((system_prompt, content))
        if system_prompt == llm._MAP_SUMMARY_SYSTEM_PROMPT:
            return f"summary of {content}"
        return "final summary"

    monkeypatch.setattr(llm, "_summarize_text", fake_summarize)
    monkeypatch.setattr(llm, "_count_tokens", lambda *_args: 1)

    result = llm._summarize_diff_in_chunks("mymodel", "big diff")

    assert result == "final summary"
    assert calls[0] == (llm._MAP_SUMMARY_SYSTEM_PROMPT, "chunk-a")
    assert calls[1] == (llm._MAP_SUMMARY_SYSTEM_PROMPT, "chunk-b")
    assert calls[2][0] == llm._REDUCE_SUMMARY_SYSTEM_PROMPT


def test_summarize_diff_in_chunks_returns_original_when_no_summaries(monkeypatch):
    """The original diff is kept if the map step produces no summaries."""
    monkeypatch.setattr(
        llm, "_split_diff_into_chunks", lambda _model, _diff, _budget: ["a", "b"]
    )
    monkeypatch.setattr(llm, "_summarize_text", lambda *_args: "")

    assert llm._summarize_diff_in_chunks("mymodel", "big diff") == "big diff"


def test__load_prompt_messages_file_handling(tmp_path):
    """Prompt YAML parsing and validation scenarios."""

    # non-existent file -> FileNotFoundError
    with pytest.raises(FileNotFoundError):
        llm._load_prompt_messages(tmp_path / "nope.yml")

    # top-level not a mapping -> TypeError
    p = tmp_path / "bad.yml"
    p.write_text("- not: a mapping")
    with pytest.raises(TypeError):
        llm._load_prompt_messages(p)

    # no messages key -> empty list
    p2 = tmp_path / "empty.yml"
    p2.write_text("{}")
    assert not llm._load_prompt_messages(p2)

    # messages not a list -> TypeError
    p3 = tmp_path / "notalist.yml"
    p3.write_text("messages: yes")
    with pytest.raises(TypeError):
        llm._load_prompt_messages(p3)

    # message item not a mapping -> TypeError
    p4 = tmp_path / "baditem.yml"
    p4.write_text("messages:\n  - not-a-mapping")
    with pytest.raises(TypeError):
        llm._load_prompt_messages(p4)

    # message missing role/content or not strings -> TypeError
    p5 = tmp_path / "badroles.yml"
    p5.write_text("messages:\n  - role: 1\n    content: 2")
    with pytest.raises(TypeError):
        llm._load_prompt_messages(p5)

    # valid file
    p6 = tmp_path / "good.yml"
    p6.write_text("messages:\n  - role: system\n    content: hi")
    msgs = llm._load_prompt_messages(p6)
    assert isinstance(msgs, list) and msgs[0]["role"] == "system"
