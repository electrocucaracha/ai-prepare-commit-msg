---
title: Add a custom LLM provider
parent: How-to guides
nav_order: 3
---

This guide shows you how to register a custom LLM provider
so the hook routes model calls through your own backend
without any change to this project.

Use it when you need a provider that LiteLLM does not support natively,
such as a corporate AI gateway, a self-hosted inference server,
or an internal proxy.

## How provider discovery works

The hook discovers custom providers through
[Python entry points](https://packaging.python.org/en/latest/specifications/entry-points/).

Before the first model call,
it looks for every package installed in the active Python environment
that registers an entry point in the
`ai_prepare_commit_msg.litellm_providers` group.
Each discovered entry point is loaded and added to LiteLLM's
[custom provider map](https://docs.litellm.ai/docs/providers/custom_llm_server).

Your handler lives entirely in your own package,
so no gateway-specific code or credential material
ever needs to reach this repository.

## Prerequisites

- Python 3.12 or later.
- A LiteLLM-compatible handler class.
- A Python package you can install alongside `ai-prepare-commit`.

## Steps

### 1. Create a custom handler class

Your handler must implement the `CustomLLM` interface from LiteLLM.
At minimum, implement `completion`.

```python
# src/mypackage/llm.py
from litellm import CustomLLM
from litellm.types.utils import ModelResponse


class Handler(CustomLLM):
    def completion(self, model: str, messages: list, **kwargs) -> ModelResponse:
        # Route the request to your backend here.
        ...
```

See the
[LiteLLM custom provider documentation](https://docs.litellm.ai/docs/providers/custom_llm_server)
for the full interface, including async and streaming support.

### 2. Register the entry point

In your package's `pyproject.toml`,
declare the entry point in the `ai_prepare_commit_msg.litellm_providers` group.
The key is the provider prefix used in model strings.
The value is the dotted import path to your handler class.

```toml
[project.entry-points."ai_prepare_commit_msg.litellm_providers"]
my_provider = "mypackage.llm:Handler"
```

The key `my_provider` becomes the prefix in the model string,
so `my_provider/my-model-name` routes to your handler.

### 3. Install both packages

Install your package into the same Python environment as the hook.

```bash
uv pip install ai-prepare-commit ./path/to/your/package
```

If you install the hook through `pre-commit`,
add your package to `additional_dependencies`
so it lands in the same hook environment.

```yaml
repos:
  - repo: https://github.com/electrocucaracha/ai-prepare-commit-msg
    rev: v7.0.1
    hooks:
      - id: ai-prepare-commit
        additional_dependencies:
          - my-provider-package
```

### 4. Run with your provider

Pass your provider prefix and model name through `--model`:

```bash
prepare-commit --model my_provider/my-model-name
```

Or set the environment variable:

```bash
export LITELLM_PROXY_MODEL=my_provider/my-model-name
```

## Verify the registration

List the providers visible in the active environment:

```bash
python -c "from importlib.metadata import entry_points; \
  print(list(entry_points(group='ai_prepare_commit_msg.litellm_providers')))"
```

Your provider appears in the printed list
when the entry point is declared
and the package is installed.

Then stage a change and run `git commit` with debug logging enabled
to confirm the hook registers the handler:

```bash
prepare-commit --log-level DEBUG --model my_provider/my-model-name
```

The output contains
`Registered LiteLLM custom provider 'my_provider'`.

## Behavior details

**Registration is idempotent.**
A provider whose name is already in the custom provider map is not added again.

**Failed providers do not block the hook.**
If an entry point fails to load,
for example because a dependency is missing,
the hook logs a warning and continues with the remaining providers.

**Registration order.**
Entry points load in the order returned by `importlib.metadata.entry_points`,
which depends on package installation order.
If two packages register the same provider name,
the first one wins.

## Troubleshooting

**The hook uses a built-in provider instead of my handler.**
LiteLLM's native routing takes precedence for its built-in prefixes,
such as `openai/`, `anthropic/`, `ollama/`, and `azure/`.
Choose a prefix that does not collide with a LiteLLM built-in provider.

**My handler is not discovered.**
An empty list in the verification command
means no installed package registers a provider.
Check that your package is installed in the same environment as the hook,
and that the group name is spelled correctly.

**I see a warning about a failed provider.**
The warning names the entry point and the underlying error,
which is usually a missing dependency or an import error in your package.
Install the missing dependency,
then run the verification command again.

## Related

- [Configuration reference](../references/configuration.md)
- [How it works](../explanations/how-it-works.md)
- [Guides index](index.md)
