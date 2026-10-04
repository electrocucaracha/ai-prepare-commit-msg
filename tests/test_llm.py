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
    assert llm._extract_choice_content({}) == ""
    assert llm._extract_choice_content({"message": {}}) == ""
    assert llm._extract_choice_content({"message": None, "text": "fallback"}) == ""

    # plain string fallback
    assert llm._extract_choice_content("just a string") == "just a string"

    # message attribute present but None -> empty string
    assert llm._extract_choice_content(_Choice(None)) == ""


@pytest.mark.parametrize("tokens_before", [0, -1])
def test_compression_stats_savings_ratio_is_zero_without_baseline(tokens_before):
    """A non-positive baseline cannot produce a meaningful savings ratio."""
    stats = llm.CompressionStats(tokens_before=tokens_before)

    assert stats.tokens_before == tokens_before
    assert stats.savings_ratio == 0.0


def test_get_commit_msg_uses_litellm_and_joins_choices(monkeypatch):
    """The public helper calls ``litellm.completion`` and joins choices."""

    # Replace prompt loader to keep this test self-contained
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    provider_loads = []
    monkeypatch.setattr(
        llm, "load_custom_providers", lambda: provider_loads.append(None)
    )

    seen_kwargs = {}
    prompt_models = []
    estimated = []
    compression_calls = []

    def fake_completion(messages, model, **kwargs):
        # return a mixture of object choice and dict/text choice
        seen_kwargs.update(model=model, messages=messages, **kwargs)
        return _Response(
            [
                _Choice(_Msg(" generated ")),
                {"text": ""},
                {"text": "  "},
                {"text": " more "},
            ]
        )

    # Monkeypatch the litellm completion function in the imported module
    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    def get_prompt_token_limit(model):
        prompt_models.append(model)
        return 7_000

    def estimate_prompt_tokens(model, messages):
        estimated.append((model, messages))
        return 42

    def compress_messages(model, messages, prompt_token_limit):
        compression_calls.append((model, messages, prompt_token_limit))
        return messages

    monkeypatch.setattr(llm, "_get_prompt_token_limit", get_prompt_token_limit)
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", estimate_prompt_tokens)
    monkeypatch.setattr(llm, "_compress_messages", compress_messages)

    result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")
    assert result == "generated\nmore"
    assert seen_kwargs["model"] == "mymodel"
    assert seen_kwargs["messages"][-1] == {
        "role": "user",
        "content": "diff-markdown",
    }
    assert seen_kwargs["max_tokens"] == 1_024
    assert seen_kwargs["drop_params"] is True
    assert seen_kwargs["extra_headers"] == {}
    assert prompt_models == ["mymodel"]
    assert estimated == [("mymodel", seen_kwargs["messages"])]
    assert provider_loads == [None]
    assert compression_calls == [("mymodel", seen_kwargs["messages"], 7_000)]


def test_get_commit_msg_untyped_instructs_model_after_default_prompt(
    monkeypatch, caplog
):
    """Only decision mode asks for an untyped description."""
    prompt_paths = []

    def load_prompt_messages(path):
        prompt_paths.append(path)
        return [
            {"role": "system", "content": "header"},
            {"role": "user", "content": "template"},
        ]

    monkeypatch.setattr(llm, "_load_prompt_messages", load_prompt_messages)
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)
    seen_messages = []

    def fake_completion(**kwargs):
        seen_messages.append(kwargs["messages"])
        return _Response([_Choice(_Msg("describe change"))])

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)
    with caplog.at_level("DEBUG", logger=llm.__name__):
        assert llm.get_commit_msg("model", "diff", "prompt.yml", untyped=True) == (
            "describe change"
        )
    assert seen_messages[0] == [
        {"role": "system", "content": "header"},
        {
            "role": "system",
            "content": (
                "Write the commit description and optional body. Do not include a "
                "Conventional Commit type, scope, !, or colon prefix on the first line. "
                "Keep any body and footers."
            ),
        },
        {"role": "user", "content": "template"},
        {"role": "user", "content": "diff"},
    ]

    with caplog.at_level("DEBUG", logger=llm.__name__):
        assert llm.get_commit_msg("model", "diff", "prompt.yml") == "describe change"
    assert seen_messages[1] == [
        {"role": "system", "content": "header"},
        {
            "role": "system",
            "content": (
                "Format the first line as a Conventional Commit: "
                "<type>[optional scope][!]: <description>. Choose the type that "
                "best describes the primary change from feat, fix, refactor, revert, "
                "style, docs, test, chore, build, ci, or perf. Use a scope only when "
                "supported by the diff and ! for breaking changes. Ensure valid "
                "Conventional Commit syntax and an accurate type and scope. "
                "See https://www.conventionalcommits.org/en/v1.0.0/."
            ),
        },
        {"role": "user", "content": "template"},
        {"role": "user", "content": "diff"},
    ]
    assert "Loaded 2 prompt messages from prompt.yml" in caplog.text
    assert prompt_paths == ["prompt.yml", "prompt.yml"]


def test_get_commit_msg_builds_default_instruction_without_prompt_messages(monkeypatch):
    """An empty prompt file still gets format instructions before the diff."""
    monkeypatch.setattr(llm, "_load_prompt_messages", lambda _path: [])
    monkeypatch.setattr(llm, "_get_prompt_token_limit", lambda _model: 7_000)
    monkeypatch.setattr(
        llm, "_compress_messages", lambda _model, messages, _limit: messages
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)
    seen_messages = []

    def complete(**kwargs):
        seen_messages.append(kwargs["messages"])
        return _Response([_Choice(_Msg("generated"))])

    monkeypatch.setattr(llm.litellm, "completion", complete)

    assert llm.get_commit_msg("model", "diff", "empty.yml") == "generated"
    assert seen_messages == [
        [
            {
                "role": "system",
                "content": (
                    "Format the first line as a Conventional Commit: "
                    "<type>[optional scope][!]: <description>. Choose the type that "
                    "best describes the primary change from feat, fix, refactor, revert, "
                    "style, docs, test, chore, build, ci, or perf. Use a scope only when "
                    "supported by the diff and ! for breaking changes. Ensure valid "
                    "Conventional Commit syntax and an accurate type and scope. "
                    "See https://www.conventionalcommits.org/en/v1.0.0/."
                ),
            },
            {"role": "user", "content": "diff"},
        ]
    ]


def test_default_prompt_leaves_type_selection_to_runtime():
    """The shared prompt must not contradict the untyped system instruction."""
    prompt_file = (
        llm.Path(__file__).parents[1] / "src/ai_prepare_commit_msg/prompts/default.yml"
    )
    system_prompt = llm._load_prompt_messages(prompt_file)[0]["content"]

    assert "<type>" not in system_prompt
    assert "Choose the type" not in system_prompt
    assert "conventionalcommits.org" not in system_prompt


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


@pytest.mark.parametrize("raw_headers", [None, "", " \t "])
def test_get_extra_headers_defaults_when_environment_is_empty(monkeypatch, raw_headers):
    """Unset or blank optional header configuration yields no headers."""
    if raw_headers is None:
        monkeypatch.delenv("LITELLM_EXTRA_HEADERS_JSON", raising=False)
    else:
        monkeypatch.setenv("LITELLM_EXTRA_HEADERS_JSON", raw_headers)

    assert llm._get_extra_headers() == {}


def test_get_extra_headers_rejects_non_string_values(monkeypatch):
    """Header configuration must contain only string values."""
    monkeypatch.setenv("LITELLM_EXTRA_HEADERS_JSON", '{"X-Retry": 1}')

    with pytest.raises(ValueError) as error:
        llm._get_extra_headers()
    assert str(error.value) == (
        "LITELLM_EXTRA_HEADERS_JSON must be a JSON object of strings"
    )


def test_get_extra_headers_rejects_malformed_json(monkeypatch):
    """Malformed JSON in the environment variable raises a clear error."""
    monkeypatch.setenv("LITELLM_EXTRA_HEADERS_JSON", "{not-valid-json")

    with pytest.raises(ValueError) as error:
        llm._get_extra_headers()
    assert str(error.value) == "LITELLM_EXTRA_HEADERS_JSON must be valid JSON"


def test_get_llm_timeout_defaults_when_unset(monkeypatch):
    """The default timeout is used when the environment variable is unset."""
    monkeypatch.delenv("LITELLM_REQUEST_TIMEOUT", raising=False)

    assert llm._get_llm_timeout() == 60


def test_get_llm_timeout_reads_environment_variable(monkeypatch):
    """A custom timeout is read from the environment as a float."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", " 12.5 ")

    assert llm._get_llm_timeout() == 12.5


def test_get_llm_timeout_rejects_non_numeric_value(monkeypatch):
    """A non-numeric timeout value raises a clear error."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", "not-a-number")

    with pytest.raises(ValueError) as error:
        llm._get_llm_timeout()
    assert str(error.value) == (
        "LITELLM_REQUEST_TIMEOUT must be a positive number of seconds"
    )


@pytest.mark.parametrize("timeout", ["0", "-2"])
def test_get_llm_timeout_rejects_non_positive_value(monkeypatch, timeout):
    """A zero or negative timeout value raises a clear error."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", timeout)

    with pytest.raises(ValueError) as error:
        llm._get_llm_timeout()
    assert str(error.value) == (
        "LITELLM_REQUEST_TIMEOUT must be a positive number of seconds"
    )


@pytest.mark.parametrize("timeout", ["nan", "inf", "-inf"])
def test_get_llm_timeout_rejects_non_finite_value(monkeypatch, timeout):
    """Non-finite values cannot disable or invalidate the request timeout."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", timeout)

    with pytest.raises(ValueError) as error:
        llm._get_llm_timeout()
    assert str(error.value) == (
        "LITELLM_REQUEST_TIMEOUT must be a positive number of seconds"
    )


@pytest.mark.parametrize(
    "message",
    [
        "prompt token count exceeded",
        "CONTEXT LENGTH exceeded",
        "maximum context length exceeded",
        "too many tokens",
        "request exceeds the limit",
    ],
)
def test_has_oversized_prompt_error_detects_all_markers(message):
    """Recognized provider phrases are matched case-insensitively."""
    assert llm._has_oversized_prompt_error(RuntimeError(message))


@pytest.mark.parametrize("message", ["provider unavailable", "context limit", ""])
def test_has_oversized_prompt_error_rejects_unrelated_messages(message):
    """Unrelated provider failures do not become oversized-prompt warnings."""
    assert not llm._has_oversized_prompt_error(RuntimeError(message))


def test_get_commit_msg_skips_oversized_diff_when_summarization_does_not_help(
    monkeypatch, caplog
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

    with caplog.at_level("WARNING", logger=llm.__name__):
        result = llm.get_commit_msg("mymodel", "very large diff", "prompt.yml")

    assert result == llm.OVERSIZED_DIFF_WARNING
    assert "Estimated prompt token count 7001 exceeds safe limit 7000" in caplog.text
    assert "Skipping LLM call: prompt still 7001 tokens" in caplog.text


def test_get_commit_msg_does_not_summarize_at_exact_prompt_limit(monkeypatch):
    """Only prompts strictly larger than the configured limit are summarized."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda _path: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_get_prompt_token_limit", lambda _model: 7_000)
    monkeypatch.setattr(
        llm, "_compress_messages", lambda _model, messages, _limit: messages
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 7_000)
    monkeypatch.setattr(
        llm,
        "_summarize_diff",
        lambda *_args: pytest.fail("An exactly-at-limit prompt must not be summarized"),
    )
    monkeypatch.setattr(
        llm.litellm,
        "completion",
        lambda **_kwargs: _Response([_Choice(_Msg("generated"))]),
    )

    assert llm.get_commit_msg("mymodel", "diff", "prompt.yml") == "generated"


def test_get_commit_msg_uses_summarization_chain_for_oversized_diff(
    monkeypatch, caplog
):
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

    with caplog.at_level("WARNING", logger=llm.__name__):
        result = llm.get_commit_msg("mymodel", "very large diff", "prompt.yml")

    assert summarize_calls == ["very large diff"]
    assert result == "generated from summary"
    assert seen_messages[-1][-1] == {"role": "user", "content": "summarized diff"}
    assert "Estimated prompt token count 7001 exceeds safe limit 7000" in caplog.text


def test_get_commit_msg_returns_empty_on_timeout(monkeypatch, caplog):
    """A slow provider call falls back to an empty message on timeout."""
    monkeypatch.setenv("LITELLM_REQUEST_TIMEOUT", "4.5")
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)
    observed_timeouts = []

    def fast_completion(**_kwargs):
        return SimpleNamespace(choices=[])

    def raise_timeout(self, timeout=None):
        observed_timeouts.append(timeout)
        raise llm.concurrent.futures.TimeoutError("future did not complete in time")

    monkeypatch.setattr(llm.litellm, "completion", fast_completion)
    monkeypatch.setattr(llm.concurrent.futures.Future, "result", raise_timeout)

    with caplog.at_level("ERROR", logger=llm.__name__):
        result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")

    assert result == ""
    assert observed_timeouts == [4.5]
    assert "LLM call timed out after 4.5 seconds" in caplog.text


def test_get_commit_msg_returns_empty_on_generic_provider_error(monkeypatch, caplog):
    """Non-oversized provider errors degrade to an empty commit message."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)

    def fake_completion(**_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    with caplog.at_level("ERROR", logger=llm.__name__):
        result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")

    assert result == ""
    assert "LLM call failed: provider unavailable" in caplog.text


def test_get_commit_msg_returns_warning_for_oversized_provider_error(
    monkeypatch, caplog
):
    """Provider token-limit failures degrade to a warning message."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(llm, "_estimate_prompt_tokens", lambda *_args: 42)

    def fake_completion(**_kwargs):
        raise RuntimeError("prompt token count of 287975 exceeds the limit of 128000")

    monkeypatch.setattr(llm.litellm, "completion", fake_completion)

    with caplog.at_level("WARNING", logger=llm.__name__):
        result = llm.get_commit_msg("mymodel", "diff-markdown", "prompt.yml")

    assert result == llm.OVERSIZED_DIFF_WARNING
    assert (
        "Skipping LLM call after oversized prompt rejection: prompt token count "
        "of 287975 exceeds the limit of 128000"
    ) in caplog.text


def test_compress_messages_records_savings(monkeypatch):
    """Headroom compression is applied and its token savings recorded."""
    compressed_result = SimpleNamespace(
        messages=[{"role": "system", "content": "x"}],
        tokens_before=1000,
        tokens_after=600,
        transforms_applied=["router:diff:0.6"],
    )

    llm.get_compression_stats().reset()
    observed = {}

    def compress(**kwargs):
        observed.update(kwargs)
        return compressed_result

    monkeypatch.setattr(llm, "headroom_compress", compress)

    messages = [{"role": "user", "content": "diff"}]

    assert (
        llm._compress_messages("mymodel", messages, 7_000) == compressed_result.messages
    )

    stats = llm.get_compression_stats()
    assert stats.requests == 1
    assert stats.tokens_saved == 400
    assert stats.savings_ratio == pytest.approx(0.4)
    assert "saved 400 (40.0%)" in stats.format_summary()
    assert observed == {
        "messages": messages,
        "model": "mymodel",
        "model_limit": 7_000,
        "compress_user_messages": True,
        "protect_recent": 0,
    }


def test_compress_messages_when_headroom_unavailable(monkeypatch, caplog):
    """Prompt messages pass through untouched when Headroom is missing."""
    llm.get_compression_stats().reset()
    monkeypatch.setattr(llm, "headroom_compress", None)

    messages = [{"role": "user", "content": "diff"}]

    with caplog.at_level("DEBUG", logger=llm.__name__):
        assert llm._compress_messages("mymodel", messages) == messages
    assert llm.get_compression_stats().requests == 0
    assert "Headroom is not installed; sending the prompt uncompressed." in caplog.text


def test_compress_messages_falls_back_when_headroom_raises(monkeypatch, caplog):
    """Compression failures degrade to the original prompt."""

    def boom(**_kwargs):
        raise RuntimeError("compression backend unavailable")

    llm.get_compression_stats().reset()
    monkeypatch.setattr(llm, "headroom_compress", boom)

    messages = [{"role": "user", "content": "diff"}]

    with caplog.at_level("WARNING", logger=llm.__name__):
        assert llm._compress_messages("mymodel", messages) == messages
    assert llm.get_compression_stats().requests == 0
    assert "Headroom compression failed; using original prompt: " in caplog.text
    assert "compression backend unavailable" in caplog.text


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
    observed = {}

    def token_counter(**kwargs):
        observed.update(kwargs)
        return 123

    monkeypatch.setattr(llm.litellm, "token_counter", token_counter)

    messages = [{"role": "user", "content": "x"}]
    result = llm._estimate_prompt_tokens("mymodel", messages)

    assert result == 123
    assert isinstance(result, int)
    assert observed == {"model": "mymodel", "messages": messages}


def test_estimate_prompt_tokens_returns_none_on_failure(monkeypatch):
    """Token estimation failures degrade to ``None`` instead of raising."""

    def boom(**_kwargs):
        raise RuntimeError("model not recognized")

    monkeypatch.setattr(llm.litellm, "token_counter", boom)

    assert (
        llm._estimate_prompt_tokens("mymodel", [{"role": "user", "content": "x"}])
        is None
    )


def test__load_prompt_messages_file_handling(tmp_path, monkeypatch):
    """Prompt YAML parsing and validation scenarios."""
    encodings = []
    original_read_text = llm.Path.read_text

    def read_text(path, *args, **kwargs):
        encodings.append(kwargs.get("encoding"))
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(llm.Path, "read_text", read_text)

    # non-existent file -> FileNotFoundError
    with pytest.raises(FileNotFoundError, match="not found or not a file"):
        llm._load_prompt_messages(tmp_path / "nope.yml")
    with pytest.raises(FileNotFoundError, match="not found or not a file"):
        llm._load_prompt_messages(tmp_path)

    # top-level not a mapping -> TypeError
    p = tmp_path / "bad.yml"
    p.write_text("- not: a mapping")
    with pytest.raises(TypeError, match="mapping at the top level"):
        llm._load_prompt_messages(p)

    empty = tmp_path / "empty-file.yml"
    empty.write_text("")
    with pytest.raises(TypeError, match="mapping at the top level"):
        llm._load_prompt_messages(empty)

    # no messages key -> empty list
    p2 = tmp_path / "empty.yml"
    p2.write_text("{}")
    assert not llm._load_prompt_messages(p2)

    empty_messages = tmp_path / "empty-messages.yml"
    empty_messages.write_text("messages: []")
    assert llm._load_prompt_messages(empty_messages) == []

    # messages not a list -> TypeError
    p3 = tmp_path / "notalist.yml"
    p3.write_text("messages: yes")
    with pytest.raises(TypeError, match="'messages' must be a list"):
        llm._load_prompt_messages(p3)

    # message item not a mapping -> TypeError
    p4 = tmp_path / "baditem.yml"
    p4.write_text("messages:\n  - role: system\n    content: valid\n  - not-a-mapping")
    with pytest.raises(TypeError, match="message at index 1 must be a mapping/dict"):
        llm._load_prompt_messages(p4)

    # Role and content are validated independently.
    p5 = tmp_path / "badrole.yml"
    p5.write_text("messages:\n  - role: 1\n    content: valid")
    with pytest.raises(TypeError, match="string 'role' and 'content'"):
        llm._load_prompt_messages(p5)

    p6 = tmp_path / "badcontent.yml"
    p6.write_text("messages:\n  - role: system\n    content: 2")
    with pytest.raises(TypeError, match="string 'role' and 'content'"):
        llm._load_prompt_messages(p6)

    for index, message in enumerate(("content: hi", "role: system")):
        missing_field = tmp_path / f"missing-field-{index}.yml"
        missing_field.write_text(f"messages:\n  - {message}")
        with pytest.raises(TypeError, match="string 'role' and 'content'"):
            llm._load_prompt_messages(missing_field)

    # valid file
    p7 = tmp_path / "good.yml"
    p7.write_text("messages:\n  - role: system\n    content: hi")
    assert llm._load_prompt_messages(p7) == [{"role": "system", "content": "hi"}]
    assert encodings and set(encodings) == {"utf-8"}


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


def test_load_custom_providers_ignores_malformed_existing_entries(monkeypatch):
    """Unexpected existing map entries do not prevent valid providers loading."""
    entry = SimpleNamespace(
        name="my_provider",
        value="mypkg.llm:Handler",
        load=lambda: _FakeHandler,
    )
    _patch_entry_points(monkeypatch, [entry])
    malformed_entry = object()
    monkeypatch.setattr(
        llm.litellm, "custom_provider_map", [malformed_entry], raising=False
    )

    llm.load_custom_providers()

    assert llm.litellm.custom_provider_map[0] is malformed_entry
    assert llm.litellm.custom_provider_map[1]["provider"] == "my_provider"


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
    assert [record.getMessage() for record in caplog.records] == [
        "Failed to load LiteLLM custom provider 'bad_provider' "
        "from 'badpkg.llm:Bad': missing dep"
    ]


def test_load_custom_providers_warns_on_handler_construction_failure(
    monkeypatch, caplog
):
    """A discovered provider whose handler cannot be constructed is skipped."""

    class BrokenHandler:
        def __init__(self):
            raise RuntimeError("handler initialization failed")

    entry = SimpleNamespace(
        name="broken_provider",
        value="brokenpkg.llm:Handler",
        load=lambda: BrokenHandler,
    )
    _patch_entry_points(monkeypatch, [entry])

    with caplog.at_level("WARNING", logger=llm.__name__):
        llm.load_custom_providers()

    assert llm.litellm.custom_provider_map == []
    assert [record.getMessage() for record in caplog.records] == [
        "Failed to load LiteLLM custom provider 'broken_provider' "
        "from 'brokenpkg.llm:Handler': handler initialization failed"
    ]


def test_load_custom_providers_without_entry_points(monkeypatch):
    """No providers registered means the map is left untouched."""
    _patch_entry_points(monkeypatch, [])
    monkeypatch.setattr(llm.litellm, "custom_provider_map", None, raising=False)

    llm.load_custom_providers()

    assert llm.litellm.custom_provider_map is None
