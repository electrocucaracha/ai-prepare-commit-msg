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
- `uv` or `uvx` for running Python tools.
- `pre-commit` installed through `uvx pre-commit` or another package manager.
- A custom provider package that can be installed by `pip`.

You do not modify the `ai-prepare-commit-msg` source code
to use a custom provider.
The hook loads providers from packages installed into the same environment.

## Steps

### 1. Add the provider to pre-commit

Add the custom provider package to `additional_dependencies`.
This installs the provider into the isolated environment
that `pre-commit` creates for the hook.

```yaml
repos:
  - repo: https://github.com/electrocucaracha/ai-prepare-commit-msg
    rev: v7.0.1
    hooks:
      - id: ai-prepare-commit
        additional_dependencies:
          - my-provider-package
```

For a local gateway provider package,
use the package path.

```yaml
repos:
  - repo: https://github.com/electrocucaracha/ai-prepare-commit-msg
    rev: v7.0.1
    hooks:
      - id: ai-prepare-commit
        additional_dependencies:
          - /path/to/litellm-llm-gateway
```

Use a package index or Git URL instead of a local path
when the same configuration must work on multiple machines.

If you change `additional_dependencies`,
reinstall or refresh the hook environment:

```bash
uvx pre-commit clean
uvx pre-commit install --hook-type prepare-commit-msg
```

### 2. Configure the model

Set `LITELLM_PROXY_MODEL` to the provider prefix
and model name exposed by the provider package.

For example,
if the provider package registers the prefix `gateway`,
configure:

```bash
export LITELLM_PROXY_MODEL=gateway/your-model-name
```

You can also pass the model directly when you run the console script outside
of `pre-commit`:

```bash
uvx --from ai-prepare-commit --with my-provider-package prepare-commit \
  --model gateway/your-model-name
```

### 3. Configure the provider

Configure provider-specific values with the environment variables
that your provider package expects.
For example,
a gateway provider might read a base URL,
an API key,
and audit metadata from environment variables:

```bash
export BASE_URL=https://llm-gateway.example.com/api
export API_KEY="your-api-key"
export USER_TYPE=developer
export USER_NAME="your-user-id"
export LITELLM_PROXY_MODEL=gateway/your-model-name
```

Do not put secrets in `.pre-commit-config.yaml`.
Load them from your shell,
your secret manager,
or the environment used to run `git commit`.

### 4. Commit normally

Stage your changes and run `git commit`.
`pre-commit` runs the `prepare-commit-msg` hook,
installs the configured provider dependency,
and passes the selected model to LiteLLM.

```bash
git add README.md
git commit
```

## Use provider configuration files

Some gateway provider packages read configuration from files
before falling back to environment variables.
If your provider supports this pattern,
keep the files outside the repository
and pass their paths through the provider constructor defaults
or provider-specific environment variables.

For example,
a provider package might read this JSON shape:

```json
{
  "configResolution": {
    "resolved": {
      "base_url": "https://llm-gateway.example.com/api",
      "model": "your-model-name"
    }
  }
}
```

The commit hook still receives the LiteLLM model ID
through `--model` or `LITELLM_PROXY_MODEL`.
The provider decides how to combine that model ID
with its own backend configuration.

## Verify the registration

Check the provider package in an environment managed by `uvx`:

```bash
uv run --with ai-prepare-commit --with my-provider-package python -c "from importlib.metadata import entry_points; \
  print(list(entry_points(group='ai_prepare_commit_msg.litellm_providers')))"
```

Your provider appears in the printed list
when the entry point is declared
and the package is installed.

Then stage a change and run `git commit` with debug logging enabled
to confirm the hook registers the handler:

```bash
uvx --from ai-prepare-commit --with my-provider-package prepare-commit \
  --log-level DEBUG \
  --model gateway/your-model-name
```

The output contains
`Registered LiteLLM custom provider 'gateway'`.

## Provider package requirements

This section is for authors of custom provider packages.
Consumers who receive a ready-made package only need the `pre-commit`
configuration above.

Your provider package must expose a LiteLLM `CustomLLM` handler.
At minimum,
implement `completion`.

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

In the provider package's `pyproject.toml`,
declare the entry point in the `ai_prepare_commit_msg.litellm_providers` group.
The key is the provider prefix used in model strings.
The value is the dotted import path to the handler class.

```toml
[project.entry-points."ai_prepare_commit_msg.litellm_providers"]
gateway = "mypackage.llm:Handler"
```

The provider prefix should be short,
stable,
and unique.
Avoid names that collide with LiteLLM built-in providers.

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
