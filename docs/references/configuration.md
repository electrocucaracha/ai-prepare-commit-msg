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
| `LITELLM_EXTRA_HEADERS_JSON`     | Optional JSON object of string request headers passed to LiteLLM.                                          |
| `LITELLM_REQUEST_TIMEOUT`        | Optional LLM request timeout in seconds. Must be a positive number. Defaults to `60`.                      |
| `AI_PREPARE_COMMIT_AUTO_APPROVE` | Enable automatic approval, which skips the `[Y/n]` confirmation and writes the generated message directly. |

### Optional telemetry

Telemetry is disabled by default.
See [Track usage and AI savings](../how-to-guides/telemetry.md)
for receiver setup, hook installation, and delivery verification.
OpenTelemetry dependencies are included in the standard package installation.
The existing `ai-prepare-commit` hook needs no additional dependency entries.
Set `AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT` to enable export:

```bash
export AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT=http://127.0.0.1:4318/v1/metrics
```

For a source checkout using `uv`,
run the hook with the project's locked dependencies:

```bash
uv run --locked prepare-commit --model "$LITELLM_PROXY_MODEL"
```

The endpoint must accept binary OTLP/HTTP metrics,
such as an OpenTelemetry Collector HTTP receiver.
Use the full metrics URL,
including `/v1/metrics` when required by the receiver.
Use HTTPS for remote receivers;
HTTP is intended for a local collector.
Embedded credentials, query strings, and fragments are not accepted.
Unset the endpoint variable to disable telemetry.
Setting standard `OTEL_EXPORTER_OTLP_ENDPOINT` alone does not enable this feature.

| Variable                                 | Description                                                                                                                               |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT`   | Opt-in OTLP/HTTP metrics URL. No default.                                                                                                 |
| `AI_PREPARE_COMMIT_MANUAL_SECONDS`       | Estimated manual-writing baseline per written AI suggestion, in seconds. Defaults to `120`. Set to `0` to disable time-savings estimates. |
| `OTEL_EXPORTER_OTLP_METRICS_HEADERS`     | Optional standard OpenTelemetry authentication headers. Use environment-based credentials, not credentials embedded in the endpoint URL.  |
| `OTEL_EXPORTER_OTLP_METRICS_CERTIFICATE` | Optional trusted CA certificate file for the receiver. TLS verification remains enabled.                                                  |

Each invocation makes a best-effort export at exit,
with a one-second exporter timeout and no background export thread.
Invalid configuration or export failures
do not change the hook's result.
Metrics are not persisted locally or queued for a later invocation.

All metric names start with `commit_assistant.`:

| Metric suffix                                                                       | Meaning                                                                                                                     |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `invocations`                                                                       | Hook runs, grouped by outcome, commit type, and approval mode.                                                              |
| `attempts`, `retries`                                                               | Generation attempts and extra attempts after empty responses.                                                               |
| `duration`                                                                          | Hook duration in seconds, including in-hook confirmation but excluding telemetry export.                                    |
| `generation.requests`, `summarization.requests`                                     | AI requests attempted in each stage.                                                                                        |
| `generation.failures`, `summarization.failures`                                     | Requests that raised provider errors.                                                                                       |
| `generation.duration`, `summarization.duration`                                     | Total request time per stage per invocation, in seconds. Parallel request times are summed.                                 |
| `generation.input_tokens`, `generation.output_tokens`                               | Provider-reported tokens used for commit generation.                                                                        |
| `summarization.input_tokens`, `summarization.output_tokens`                         | Provider-reported tokens used for map-reduce summarization.                                                                 |
| `compression.tokens_before`, `compression.tokens_after`, `compression.tokens_saved` | Headroom token counts for compressed generation prompts that received a response. Discarded candidate prompts are excluded. |
| `cost_estimated`                                                                    | Estimated USD cost of all priced generation and summarization responses, including retries and rejected suggestions.        |
| `cost_priced_requests`                                                              | Responses for which cost estimation was available. Unpriced responses are not assumed free.                                 |
| `compression.cost_saved_estimated`                                                  | Estimated USD input cost avoided by Headroom compression, using LiteLLM model pricing.                                      |
| `manual_baseline`                                                                   | Configured manual-writing time for a written AI suggestion, in seconds.                                                     |
| `time_saved_estimated`                                                              | Manual baseline minus hook duration, in seconds. Can be negative.                                                           |

Counters use delta aggregation so short-lived hook processes can contribute
to totals in a compatible metrics backend.
Missing provider usage or model pricing omits the corresponding measurement;
it does not imply zero consumption or zero cost.
Compression cost savings are a gross estimate,
not net savings after summarization costs,
and do not account for provider-specific cache discounts or negotiated prices.
Decision-service consumption is not included because it is not reported by this integration.

The only metric attributes are `outcome`, `commit.type`, and `approval`.
Outcomes are `written`, `rejected`, `no_changes`, `oversized`, or `error`.
Approval values are `accepted`, `auto`, `rejected`, or `none`.
Commit types use the supported Conventional Commit types,
with `unknown` for unrecognized titles.
No message text, scope, diff, file path, repository identifier, model name,
user identity, or provider credential is collected.
The receiver still sees the client's network address
and any authentication headers you configure.

Time savings are estimates rather than observed developer productivity.
They are emitted only for written AI suggestions,
including auto-approved suggestions that can be filtered by approval mode.
They do not measure subsequent editor changes or review outside the hook.
An approved message being written does not establish that the Git commit succeeded.
Use `invocations` to track frequency,
and group written outcomes by `commit.type` for the generated commit-type distribution.

### Decision models

Set `TYPESAFE_BASE_URL` to the base URL of a TypeSafe-compatible
decision service to choose the Conventional Commit type with a decision model.
Without this URL, the existing LiteLLM-only flow is unchanged.
LiteLLM still generates the description and optional body first;
the decision service receives that text and chooses the type for the title.
An unavailable service or invalid decision stops the hook without writing a message.

| Variable            | Description                                                                        |
| ------------------- | ---------------------------------------------------------------------------------- |
| `TYPESAFE_BASE_URL` | API base URL. Jev: `https://api.typesafe.ai`; Ollaya: `http://127.0.0.1:11435`.    |
| `TYPESAFE_API_KEY`  | Required for Jev; optional for Ollaya. Sent to the configured URL as a bearer key. |
| `TYPESAFE_MODEL`    | Optional model override. Defaults to `jev-latest` for Jev or `laya` otherwise.     |

The decision URL is an HTTP(S) base URL without embedded credentials or a query.
Jev requires HTTPS and a TypeSafe API key.
The key is sent to whichever decision URL you configure;
do not point `TYPESAFE_BASE_URL` at an untrusted service while a cloud key is set.
For a service without authentication, the `typesafe-sdk` client sends `local` as a placeholder bearer key
because the SDK requires a non-empty key.
Requests go to `/v1/systemone` with a 15-second per-request timeout;
the SDK handles retries.
See [Choose commit types with a decision model](../how-to-guides/decision-models.md)
for setup instructions.

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

### Additional request headers

Use `LITELLM_EXTRA_HEADERS_JSON` when a provider or gateway requires
additional HTTP headers:

```bash
export LITELLM_EXTRA_HEADERS_JSON='{"X-Request-Source":"local"}'
```

The value must be a JSON object whose keys and values are strings.
Unset the variable when the provider does not require additional headers.

## GitHub Copilot models

GitHub Copilot models can be selected through LiteLLM
by using the `github_copilot/` provider prefix:

```text
github_copilot/<model-id>
```

For example:

```bash
export LITELLM_PROXY_MODEL=github_copilot/gpt-5-mini
```

### Model selection

The model is intentionally not fixed by `ai-prepare-commit-msg`.
Users can select any GitHub Copilot model supported by their
LiteLLM version and available to their GitHub Copilot account.

Examples include:

| LiteLLM model ID                   | Notes                                                            |
| ---------------------------------- | ---------------------------------------------------------------- |
| `github_copilot/gpt-5-mini`        | Small GPT-5-family model suitable for commit-message generation. |
| `github_copilot/gpt-5.2`           | GPT-5-family model with higher capability than smaller models.   |
| `github_copilot/claude-haiku-4.5`  | Small Claude model suitable for short code-oriented tasks.       |
| `github_copilot/claude-sonnet-4.5` | Larger Claude model for more capable code understanding.         |
| `github_copilot/gpt-4o`            | GPT-4o model available through supported Copilot integrations.   |

### Model token budget

The prompt limit is derived at runtime from LiteLLM model metadata.

| Condition                                     | Maximum input source                | Prompt limit                        |
| --------------------------------------------- | ----------------------------------- | ----------------------------------- |
| LiteLLM reports a positive `max_input_tokens` | `litellm.get_model_info(model)`     | Reported maximum minus 1,024 tokens |
| Model metadata is unavailable or invalid      | 8,192-token context-window fallback | 7,168 tokens                        |

The 1,024-token difference reserves space for the generated commit message.
The resolved prompt limit is also passed to Headroom
and determines the map-reduce summarization chunk size.
There is no separate CLI option or environment variable for this limit.

## Custom provider entry points

The package discovers additional LiteLLM providers
through the entry point group in the following table.

| Entry point group                         | Value                                                 |
| ----------------------------------------- | ----------------------------------------------------- |
| `ai_prepare_commit_msg.litellm_providers` | Dotted import path to a LiteLLM `CustomLLM` subclass. |

The entry point name is the provider prefix in a model ID,
so the entry point `my_provider` matches the model ID `my_provider/my-model`.
Each discovered handler is instantiated
and appended to `litellm.custom_provider_map` before the first model call.
A name already present in that map is not registered again,
and an entry point that fails to load is logged at `WARNING` level
without stopping the hook.

Custom provider registration does not automatically add model metadata to LiteLLM.
If LiteLLM cannot resolve `max_input_tokens` for the custom model ID,
the hook uses the fallback described in [Model token budget](#model-token-budget).

See [Add a custom LLM provider](../how-to-guides/custom-providers.md)
for the procedure.

## CLI Options

| Option             | Accepted values / default                                                                             |
| ------------------ | ----------------------------------------------------------------------------------------------------- |
| `--model`          | LiteLLM model ID. Required unless `LITELLM_PROXY_MODEL` is set.                                       |
| `--prompt-file`    | YAML prompt file path. Default: `prompts/default.yml`, resolved relative to the installed package.    |
| `--log-level`      | `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. Default: `WARNING`.                               |
| `--retry`          | Integer of at least `1`. Maximum attempts when the generated message is empty. Default: `5`.          |
| `--retry-sleep`    | Non-negative number of seconds between retries. Default: `3.0`.                                       |
| `--auto-approve`   | Boolean flag that skips confirmation. The environment equivalent is `AI_PREPARE_COMMIT_AUTO_APPROVE`. |
| `--decision-url`   | Decision API base URL. Overrides `TYPESAFE_BASE_URL`.                                                 |
| `--decision-model` | Decision model name. Overrides `TYPESAFE_MODEL`.                                                      |

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
- [Choose commit types with a decision model](../how-to-guides/decision-models.md)
- [Add a custom LLM provider](../how-to-guides/custom-providers.md)
- [How it works](../explanations/how-it-works.md)
- [Reference index](index.md)
