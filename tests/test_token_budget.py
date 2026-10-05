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

"""Tests for model-aware prompt token budgets."""

import pytest

from ai_prepare_commit_msg import token_budget


def test_get_prompt_token_limit_uses_litellm_model_metadata(monkeypatch):
    """Known models use their reported input limit minus response headroom."""
    observed = []

    def get_model_info(**kwargs):
        observed.append(kwargs)
        return {"max_input_tokens": 16_384}

    monkeypatch.setattr(
        token_budget.litellm,
        "get_model_info",
        get_model_info,
    )

    assert token_budget.get_prompt_token_limit("known-model") == 15_360
    assert observed == [{"model": "known-model"}]


def test_get_prompt_token_limit_uses_conservative_fallback(monkeypatch):
    """Unknown models fall back to an 8K context window."""

    def fail(**_kwargs):
        raise RuntimeError("model is not mapped")

    monkeypatch.setattr(token_budget.litellm, "get_model_info", fail)

    assert token_budget.get_prompt_token_limit("custom/model") == 7_168


@pytest.mark.parametrize(
    "reported_limit",
    [None, True, False, 0, -1, 16.0, "16384"],
)
def test_get_prompt_token_limit_ignores_invalid_metadata(monkeypatch, reported_limit):
    """Invalid metadata types and non-positive values use the fallback budget."""
    monkeypatch.setattr(
        token_budget.litellm,
        "get_model_info",
        lambda **_kwargs: {"max_input_tokens": reported_limit},
    )

    assert token_budget.get_prompt_token_limit("custom/model") == 7_168


@pytest.mark.parametrize("reported_limit", [1, 1_024])
def test_get_prompt_token_limit_keeps_at_least_one_input_token(
    monkeypatch, reported_limit
):
    """A context smaller than the response reserve still allows one input token."""
    monkeypatch.setattr(
        token_budget.litellm,
        "get_model_info",
        lambda **_kwargs: {"max_input_tokens": reported_limit},
    )

    assert token_budget.get_prompt_token_limit("small-model") == 1
