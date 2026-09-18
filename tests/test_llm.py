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


def _raise_timeout(self, timeout=None):  # pylint: disable=unused-argument
    """Stand-in for ``Future.result`` that always raises ``TimeoutError``."""
    raise llm.concurrent.futures.TimeoutError("future did not complete in time")


class _Msg:
    """Message-like object with ``content``, shared across LLM response fakes."""

    def __init__(self, content):
        self.content = content


class _Choice:
    """Choice-like object with ``message``, shared across LLM response fakes."""

    def __init__(self, message):
        self.message = message


class _Response:
    """Response-like object exposing a ``choices`` sequence."""

    def __init__(self, choices):
        self.choices = choices


def test__extract_choice_content_various_shapes():
    """Various model choice shapes are normalized to text."""

    # object with .message that has .content
    assert llm._extract_choice_content(_Choice(_Msg("hello"))) == "hello"

    # dict-like message with nested content
    assert llm._extract_choice_content({"message": {"content": "hi"}}) == "hi"

    # dict-like fallback to text
    assert llm._extract_choice_content({"text": "plain text"}) == "plain text"

    # plain string fallback
    assert llm._extract_choice_content("just a string") == "just a string"

    # message attribute present but None -> empty string
    assert llm._extract_choice_content(_Choice(None)) == ""


def test_compression_stats_savings_ratio_is_zero_without_baseline():
    """``savings_ratio`` avoids division by zero when nothing was recorded."""
    stats = llm.CompressionStats()

    assert stats.tokens_before == 0
    assert stats.savings_ratio == 0.0


def test_get_commit_msg_uses_litellm_and_joins_choices(monkeypatch):
    """The public helper calls ``litellm.completion`` and joins choices."""

    # Replace prompt loader to keep this test self-contained
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )

    seen_kwargs = {}

    def fake_completion(messages, model, **kwargs):  # pylint: disable=unused-argument
        # return a mixture of object choice and dict/text choice
        seen_kwargs.update(kwargs)
        return _Response([_Choice(_Msg("generated")), {"text": "more"}])

    # Monkeypatch the litellm completion function in the imported module
    monkeypatch.setattr(llm.litellm, "completion", fake_completion)
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)

    result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")
    assert result == "generated\nmore"
    assert seen_kwargs["extra_headers"] == {}


def test_get_extra_headers_reads_json_environment_variable(monkeypatch):
    """Optional request headers are loaded as string values."""
    monkeypatch.setenv(
        "LITELLM_EXTRA_HEADERS_JSON",
        '{"X-Request-Source":"local","X-Request-Mode":"test"}',
    )

    assert llm._get_extra_headers() == {
        "X-Request-Source": "local",
        "X-Request-Mode": "test",
    }


def test_get_extra_headers_rejects_non_string_values(monkeypatch):
    """Header configuration must contain only string values."""
    monkeypatch.setenv("LITELLM_EXTRA_HEADERS_JSON", '{"X-Retry": 1}')

    with pytest.raises(ValueError, match="JSON object of strings"):
        llm._get_extra_headers()


def test_get_extra_headers_rejects_malformed_json(monkeypatch):
    """Malformed JSON in the environment variable raises a clear error."""
    monkeypatch.setenv("LITELLM_EXTRA_HEADERS_JSON", "{not-valid-json")

    with pytest.raises(ValueError, match="must be valid JSON"):
        llm._get_extra_headers()


def test_get_llm_timeout_defaults_when_unset(monkeypatch):
    """The default timeout is used when the environment variable is unset."""
    monkeypatch.delenv("LITELLM_REQUEST_TIMEOUT", raising=False)

    assert llm._get_llm_timeout() == llm.DEFAULT_LLM_REQUEST_TIMEOUT


def test_get_llm_timeout_reads_environment_variable(monkeypatch):
    """A custom timeout is read from the environment as a float."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", "12.5")

    assert llm._get_llm_timeout() == 12.5


def test_get_llm_timeout_rejects_non_numeric_value(monkeypatch):
    """A non-numeric timeout value raises a clear error."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", "not-a-number")

    with pytest.raises(ValueError, match="positive number of seconds"):
        llm._get_llm_timeout()


def test_get_llm_timeout_rejects_non_positive_value(monkeypatch):
    """A zero or negative timeout value raises a clear error."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", "0")

    with pytest.raises(ValueError, match="positive number of seconds"):
        llm._get_llm_timeout()


def test_get_commit_msg_skips_oversized_diff_when_summarization_does_not_help(
    monkeypatch,
):
    """A warning is returned when the diff is still oversized after summarizing."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_get_prompt_token_limit", lambda _model: 7_000)
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 7_001)
    monkeypatch.setattr(llm, "_summarize_diff", lambda _model, diff, _limit: diff)

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

    monkeypatch.setattr(llm, "_get_prompt_token_limit", lambda _model: 7_000)
    token_counts = iter([7_001, 42])
    monkeypatch.setattr(
        llm, "_estimate_prompt_tokens", lambda *_args: next(token_counts)
    )

    summarize_calls: list[str] = []

    def fake_summarize(_model, diff, prompt_token_limit):
        summarize_calls.append(diff)
        assert prompt_token_limit == 7_000
        return "summarized diff"

    monkeypatch.setattr(llm, "_summarize_diff", fake_summarize)

    seen_messages: list[list[dict[str, str]]] = []

    def fake_completion(messages, model, **kwargs):  # pylint: disable=unused-argument
        seen_messages.append(messages)
        return _Response([_Choice(_Msg("generated from summary"))])

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    result = llm.get_commit_msg("mymodel", "very large diff", "prompt.yml")

    assert summarize_calls == ["very large diff"]
    assert result == "generated from summary"
    assert seen_messages[-1][-1] == {"role": "user", "content": "summarized diff"}


def test_get_commit_msg_returns_empty_on_timeout(monkeypatch):
    """A slow provider call falls back to an empty message on timeout."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)

    def fast_completion(**_kwargs):
        return SimpleNamespace(choices=[])

    monkeypatch.setattr(llm.litellm, "completion", fast_completion)
    monkeypatch.setattr(llm.concurrent.futures.Future, "result", _raise_timeout)

    result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")

    assert result == ""


def test_get_commit_msg_returns_empty_on_generic_provider_error(monkeypatch):
    """Non-oversized provider errors degrade to an empty commit message."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)

    def fake_completion(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")

    assert result == ""


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

    assert (
        llm._compress_messages("mymodel", messages, 7_000) == compressed_result.messages
    )

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


def test_compress_messages_ignores_zero_token_baseline(monkeypatch):
    """Headroom results with a non-positive token baseline are discarded."""
    compressed_result = SimpleNamespace(
        messages=[{"role": "system", "content": "compressed"}],
        tokens_before=0,
        tokens_after=0,
        transforms_applied=[],
    )

    llm.get_compression_stats().reset()
    monkeypatch.setattr(llm, "headroom_compress", lambda **_kwargs: compressed_result)

    messages = [{"role": "user", "content": "diff"}]

    assert llm._compress_messages("mymodel", messages) == messages
    assert llm.get_compression_stats().requests == 0


def test_estimate_prompt_tokens_returns_int_on_success(monkeypatch):
    """A successful token count is normalized to a plain ``int``."""
    monkeypatch.setattr(llm.litellm, "token_counter", lambda **_kwargs: 123)

    result = llm._estimate_prompt_tokens("mymodel", [{"role": "user", "content": "x"}])

    assert result == 123
    assert isinstance(result, int)


def test_estimate_prompt_tokens_returns_none_on_failure(monkeypatch):
    """Token estimation failures degrade to ``None`` instead of raising."""

    def boom(**_kwargs):
        raise RuntimeError("model not recognized")

    monkeypatch.setattr(llm.litellm, "token_counter", boom)

    assert (
        llm._estimate_prompt_tokens("mymodel", [{"role": "user", "content": "x"}])
        is None
    )


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


class _FakeHandler:
    """Stand-in for a third-party LiteLLM custom handler."""


def _patch_entry_points(monkeypatch, entries):
    monkeypatch.setattr(llm.litellm, "custom_provider_map", [], raising=False)
    monkeypatch.setattr(
        llm,
        "entry_points",
        lambda *, group: (
            list(entries) if group == llm.CUSTOM_PROVIDER_ENTRY_POINT_GROUP else []
        ),
    )


def test_load_custom_providers_initializes_non_list_provider_map(monkeypatch):
    """A pre-existing non-list ``custom_provider_map`` is replaced, not appended to."""
    monkeypatch.setattr(llm.litellm, "custom_provider_map", None, raising=False)
    entry = SimpleNamespace(
        name="my_provider",
        value="mypkg.llm:Handler",
        load=lambda: _FakeHandler,
    )
    monkeypatch.setattr(
        llm,
        "entry_points",
        lambda *, group: (
            [entry] if group == llm.CUSTOM_PROVIDER_ENTRY_POINT_GROUP else []
        ),
    )

    llm.load_custom_providers()

    assert isinstance(llm.litellm.custom_provider_map, list)
    assert any(
        item["provider"] == "my_provider" for item in llm.litellm.custom_provider_map
    )


def test_load_custom_providers_registers_discovered_provider(monkeypatch):
    """An entry-point provider is added to LiteLLM's custom provider map."""
    entry = SimpleNamespace(
        name="my_provider",
        value="mypkg.llm:Handler",
        load=lambda: _FakeHandler,
    )
    _patch_entry_points(monkeypatch, [entry])

    llm.load_custom_providers()

    assert any(
        item["provider"] == "my_provider"
        and isinstance(item["custom_handler"], _FakeHandler)
        for item in llm.litellm.custom_provider_map
    )


def test_load_custom_providers_is_idempotent(monkeypatch):
    """Repeated calls must not register the same provider twice."""
    entry = SimpleNamespace(
        name="my_provider",
        value="mypkg.llm:Handler",
        load=lambda: _FakeHandler,
    )
    _patch_entry_points(monkeypatch, [entry])

    llm.load_custom_providers()
    llm.load_custom_providers()

    matches = [
        item
        for item in llm.litellm.custom_provider_map
        if item.get("provider") == "my_provider"
    ]
    assert len(matches) == 1


def test_load_custom_providers_warns_on_load_failure(monkeypatch, caplog):
    """A broken entry point logs a warning instead of raising."""

    def _boom():
        raise ImportError("missing dep")

    entry = SimpleNamespace(name="bad_provider", value="badpkg.llm:Bad", load=_boom)
    _patch_entry_points(monkeypatch, [entry])

    with caplog.at_level("WARNING", logger=llm.__name__):
        llm.load_custom_providers()

    assert not llm.litellm.custom_provider_map
    assert any("bad_provider" in record.getMessage() for record in caplog.records)


def test_load_custom_providers_without_entry_points(monkeypatch):
    """No providers registered means the map is left untouched."""
    _patch_entry_points(monkeypatch, [])

    llm.load_custom_providers()

    assert not llm.litellm.custom_provider_map
