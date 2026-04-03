# AI Prepare Commit Message

<!-- markdown-link-check-disable-next-line -->

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Super-Linter](https://github.com/electrocucaracha/ai-prepare-commit-msg/workflows/Lint%20Code%20Base/badge.svg)](https://github.com/marketplace/actions/super-linter)

<!-- markdown-link-check-disable-next-line -->

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![visitors](https://visitor-badge.laobi.icu/badge?page_id=electrocucaracha.ai-prepare-commit-msg)
[![Scc Code Badge](https://sloc.xyz/github/electrocucaracha/ai-prepare-commit-msg?category=code)](https://github.com/boyter/scc/)
[![Scc COCOMO Badge](https://sloc.xyz/github/electrocucaracha/ai-prepare-commit-msg?category=cocomo)](https://github.com/boyter/scc/)

AI-powered Git hook that generates concise, high-quality commit
messages from your staged changes.

Messages follow the Conventional Commits format and Google engineering
best practices.

The hook integrates with Git's `prepare-commit-msg` flow and uses
LiteLLM to produce the text.

## Features

- Generates commit messages from staged diffs.
- Produces Conventional Commits-compliant messages.
- Integrates with the `prepare-commit-msg` Git hook and `pre-commit`.
- Configurable prompts to control tone and style.

## Installation

Add this repository to your `.pre-commit-config.yaml` to enable the
`prepare-commit-msg` hook:

```yaml
default_install_hook_types:
  - pre-commit
  - prepare-commit-msg
repos:
  - repo: https://github.com/electrocucaracha/ai-prepare-commit-msg
    rev: e1fda3d307234dd12d0eb9161007ab6bd89fba37
    hooks:
      - id: ai-prepare-commit
        stages:
          - prepare-commit-msg
```

Or install the hook directly in your repository at
`.git/hooks/prepare-commit-msg`.

## Configuration

This tool requires a LiteLLM-compatible proxy.

Configure it with environment variables.

At a minimum you should set the model identifier and the proxy base URL.

Common environment variables:

- `LITELLM_PROXY_MODEL` — LiteLLM model identifier used to generate
  messages.
- `LITELLM_PROXY_API_BASE` — Base URL of the LiteLLM proxy service.
- `LITELLM_PROXY_API_KEY` — API key for the proxy (if required).
- Provider-specific keys (when using a provider directly via the proxy):
  `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `XAI_API_KEY`, `REPLICATE_API_KEY`,
  `TOGETHERAI_API_KEY`, etc.

Examples:

```bash
# LiteLLM proxy
export LITELLM_PROXY_MODEL=litellm_proxy/mistral
export LITELLM_PROXY_API_BASE=https://your-litellm-proxy.example
export LITELLM_PROXY_API_KEY="your-proxy-api-key"
```

Azure example (when using Azure OpenAI endpoints):

```bash
export AZURE_API_BASE="https://your-azure-openai-endpoint/"
export AZURE_API_VERSION="2023-05-15"
export AZURE_API_TYPE="azure"
```

Custom OpenAI base URL (self-hosted / proxy):

```bash
export OPENAI_BASE_URL="https://your_host/v1"
```

> Note: The hook reads only environment variables.
>
> Make sure the variables you need are exported in the environment
> where the hook runs (your shell, `pre-commit`, or CI).

### Using with GitHub Copilot or GPT-4

To use this application with GitHub Copilot or GPT-4 models, configure the `LITELLM_PROXY_MODEL` environment variable to point to the desired model. For example:

```bash
# GitHub Copilot model
export LITELLM_PROXY_MODEL=github_copilot

# GPT-4 model
export LITELLM_PROXY_MODEL=openai/gpt-4
```

Ensure that the `LITELLM_PROXY_API_BASE` and any required API keys (e.g., `OPENAI_API_KEY`) are properly set to connect to the respective service. Refer to the Configuration section for more details.

## Usage

1. Stage your changes: `git add`.
1. Create a commit: `git commit` (the `prepare-commit-msg` hook will
   run).
1. A suggested commit message is inserted; review and edit it before
   finalizing the commit.

## Prompts

System prompts and templates live in the `prompts/` directory.

Edit those files to adjust tone, length, or formatting.

## Configuration and CLI

| Aspect                           | Details                                                                                                                                                              |
| -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Model selection**              | Requires a LiteLLM model identifier via `--model` option or `LITELLM_PROXY_MODEL` environment variable                                                               |
| **Prompt file**                  | Loads `prompts/default.yml` by default; use `--prompt-file` to specify a different YAML file                                                                         |
| **Entrypoint / script**          | Package exposes `prepare-commit` console script; reference in `pre-commit` config or call directly: `prepare-commit --model "$LITELLM_PROXY_MODEL"`                  |
| **litellm client configuration** | Requires `litellm` Python library; may need additional environment variables like `LITELLM_PROXY_API_BASE` and `LITELLM_PROXY_API_KEY` depending on proxy deployment |

If you're using `pre-commit`, ensure the environment variables you need
are available to the hook process (see your CI or local shell setup).
