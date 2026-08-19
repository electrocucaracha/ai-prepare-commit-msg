---
title: Configuration reference
parent: Reference
nav_order: 1
---

# Configuration reference

This page describes environment variables
and CLI options for `ai-prepare-commit-msg`.

The hook reads only environment variables.
Set variables in the environment where the hook runs:
your shell,
`pre-commit`,
or CI.

## Environment Variables

### Core variables

| Variable                         | Description                                                                                                                                                       |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `LITELLM_PROXY_MODEL`            | LiteLLM model ID for commit generation.                                                                                                                           |
| `LITELLM_PROXY_API_BASE`         | LiteLLM proxy base URL.                                                                                                                                           |
| `LITELLM_PROXY_API_KEY`          | LiteLLM proxy API key, if required.                                                                                                                               |
| `AI_PREPARE_COMMIT_AUTO_APPROVE` | Skip the `[Y/n]` confirmation and write the generated message directly. Required for commits made without a controlling terminal, such as CI or scripted commits. |

### Provider-specific keys

When you use a provider through the proxy,
set the matching API key:

| Variable             | Provider    |
| -------------------- | ----------- |
| `OPENAI_API_KEY`     | OpenAI      |
| `ANTHROPIC_API_KEY`  | Anthropic   |
| `XAI_API_KEY`        | xAI         |
| `REPLICATE_API_KEY`  | Replicate   |
| `TOGETHERAI_API_KEY` | Together AI |

### Azure OpenAI

| Variable            | Description                                     |
| ------------------- | ----------------------------------------------- |
| `AZURE_API_BASE`    | Azure OpenAI endpoint URL.                      |
| `AZURE_API_VERSION` | Azure OpenAI API version, such as `2023-05-15`. |
| `AZURE_API_TYPE`    | Set this value to `azure`.                      |

### Custom OpenAI base URL

| Variable          | Description                                            |
| ----------------- | ------------------------------------------------------ |
| `OPENAI_BASE_URL` | Base URL for a self-hosted OpenAI-compatible endpoint. |

## CLI Options

| Option           | Description                                                                                                |
| ---------------- | ---------------------------------------------------------------------------------------------------------- |
| `--model`        | Model ID. Overrides `LITELLM_PROXY_MODEL`.                                                                 |
| `--prompt-file`  | YAML prompt file path. Default is `prompts/default.yml`.                                                   |
| `--log-level`    | Logging level. Default is `WARNING`.                                                                       |
| `--retry`        | Maximum attempts when the generated message is empty. Default is `5`.                                      |
| `--retry-sleep`  | Seconds to wait between retries. Default is `3.0`.                                                         |
| `--auto-approve` | Skip confirmation and write the generated message immediately. Overrides `AI_PREPARE_COMMIT_AUTO_APPROVE`. |

The package exposes a `prepare-commit` console script:

```bash
prepare-commit --model "$LITELLM_PROXY_MODEL"
```

## Examples

### LiteLLM proxy

```bash
export LITELLM_PROXY_MODEL=litellm_proxy/mistral
export LITELLM_PROXY_API_BASE=https://your-litellm-proxy.example
export LITELLM_PROXY_API_KEY="your-proxy-api-key"
```

### GitHub Copilot

```bash
export LITELLM_PROXY_MODEL=github_copilot/gpt-4
```

### OpenAI GPT-4

```bash
export LITELLM_PROXY_MODEL=openai/gpt-4
export OPENAI_API_KEY="your-openai-api-key"
```

### Custom OpenAI base URL example

```bash
export OPENAI_BASE_URL="https://your_host/v1"
```

## Related

- [How to install](../how-to-guides/how-to-install.md)
- [Reference index](index.md)
