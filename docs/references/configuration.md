---
title: Configuration reference
parent: Reference
nav_order: 1
---

# Configuration reference

This page describes the environment variables
and CLI options for `ai-prepare-commit-msg`.

The `--model` option is required.
You can provide it directly
or through `LITELLM_PROXY_MODEL`.
CLI values take precedence over values supplied by an environment variable.

## Environment Variables

### Core variables

| Variable                         | Description                                                                                                |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `LITELLM_PROXY_MODEL`            | LiteLLM model ID for commit generation. Used when `--model` is not provided.                               |
| `LITELLM_PROXY_API_BASE`         | LiteLLM proxy base URL.                                                                                    |
| `LITELLM_PROXY_API_KEY`          | LiteLLM proxy API key, if required.                                                                        |
| `AI_PREPARE_COMMIT_AUTO_APPROVE` | Enable automatic approval, which skips the `[Y/n]` confirmation and writes the generated message directly. |

### Provider-specific keys

LiteLLM reads provider credentials from these variables
when the selected model requires them.

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

| Option           | Accepted values / default                                                                             |
| ---------------- | ----------------------------------------------------------------------------------------------------- |
| `--model`        | LiteLLM model ID. Required unless `LITELLM_PROXY_MODEL` is set.                                       |
| `--prompt-file`  | YAML prompt file path. Default: `prompts/default.yml`, resolved relative to the installed package.    |
| `--log-level`    | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Default: `WARNING`.                               |
| `--retry`        | Integer of at least `1`. Maximum attempts when the generated message is empty. Default: `5`.          |
| `--retry-sleep`  | Non-negative number of seconds between retries. Default: `3.0`.                                       |
| `--auto-approve` | Boolean flag that skips confirmation. The environment equivalent is `AI_PREPARE_COMMIT_AUTO_APPROVE`. |

The command also accepts positional file arguments.
They are used to detect pre-commit mode
and do not change message generation.

Prompt files use YAML with a top-level `messages` sequence.
Each message contains a `role`
and `content` field,
following the message format accepted by LiteLLM.

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

## Related

- [How to install](../how-to-guides/how-to-install.md)
- [How it works](../explanations/how-it-works.md)
- [Reference index](index.md)
