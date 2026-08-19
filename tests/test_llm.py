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


def test_get_commit_msg_skips_oversized_diff_before_llm_call(monkeypatch):
    """Oversized diffs return a warning without calling the provider."""
    monkeypatch.setattr(
        llm, "_load_prompt_messages", lambda p: [{"role": "system", "content": "x"}]
    )
    monkeypatch.setattr(
        llm, "_estimate_prompt_tokens", lambda *_args: llm.MAX_PROMPT_TOKENS + 1
    )

    def fail_completion(**_kwargs):
        raise AssertionError("litellm.completion should not be called")

    monkeypatch.setattr(llm.litellm, "completion", fail_completion)

    result = llm.get_commit_msg("mymodel", "very large diff", "prompt.yml")

    assert result == llm.OVERSIZED_DIFF_WARNING


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
