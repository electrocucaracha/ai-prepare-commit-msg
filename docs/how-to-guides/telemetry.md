---
title: Track usage and AI savings
parent: How-to guides
nav_order: 5
---

# Track usage and AI savings

Use this guide to send hook usage and savings metrics to an
OpenTelemetry Protocol over HTTP (OTLP/HTTP) receiver.
Telemetry is optional and disabled by default.

![Telemetry delivery from the AI commit-message hook to Rotel, with separate verification and reporting configurations](../assets/diagrams/telemetry-delivery.png)

Source: [Editable draw.io diagram](../assets/diagrams/telemetry-delivery.drawio).

The local verification setup prints and discards metrics.
For historical reports,
configure Rotel to forward them to a metrics backend instead.

## Prerequisites

- An [installed hook](how-to-install.md) and a configured model.
- A version of the package that includes telemetry support.
- An OTLP/HTTP metrics receiver, such as [Rotel](https://github.com/rotel-dev/rotel).
- Docker, only if you choose the container option below.

The receiver URL is not a dashboard URL or a Prometheus scrape endpoint.
Your receiver must accept binary OTLP metrics.

## 1. Prepare a receiver

For an existing receiver,
obtain its full metrics URL and any required authentication headers.
Use HTTPS for remote receivers.

For lightweight local collection,
use Rotel, a Rust-based OpenTelemetry collector with an OTLP/HTTP metrics receiver.
Choose the native binary to avoid a container runtime,
or use the Docker option below.

### Native binary

Download the binary for your operating system and architecture from the
[Rotel releases](https://github.com/rotel-dev/rotel/releases),
and make `rotel` available on your `PATH`.
These examples use Rotel `v0.2.6`.
Run the receiver in a separate terminal:

```bash
rotel start \
  --otlp-http-endpoint 127.0.0.1:4318 \
  --debug-log metrics \
  --debug-log-verbosity detailed \
  --exporter blackhole
```

### Docker

Alternatively,
run the same verification receiver with the prebuilt image:

```bash
docker run --rm --init --name commit-telemetry \
  -p 127.0.0.1:4318:4318 \
  public.ecr.aws/rotel-dev/rotel:v0.2.6 \
  --debug-log metrics \
  --debug-log-verbosity detailed \
  --exporter blackhole
```

Both examples expose the HTTP receiver on the host's loopback interface
and print received metrics through Rotel's detailed debug logging.
The `blackhole` exporter discards telemetry after processing;
these commands verify delivery but do not retain historical data or provide dashboards.
For ongoing reporting,
replace `blackhole` with a configured exporter.
See [Rotel's OTLP exporter configuration](https://github.com/rotel-dev/rotel#otlp-exporter-configuration)
to forward metrics to a backend that supports
OpenTelemetry delta metrics.

The [official OpenTelemetry Collector](https://opentelemetry.io/docs/collector/)
remains an alternative if you already operate it
or need components outside Rotel's supported receivers, processors, and exporters.
The hook uses the same endpoint variable with either collector.

## 2. Use the standard hook installation

OpenTelemetry dependencies are included in the standard package installation.
For `pre-commit`,
keep your existing hook entry unchanged.
No `entry` override, dependency overrides, or second hook are needed.
The model, gateway credentials, and telemetry settings are inherited
from the environment that launches Git.
The following example keeps the standard hook structure;
replace `<release-with-telemetry>` with a release tag that includes telemetry support:

```yaml
default_install_hook_types:
  - prepare-commit-msg
repos:
  - repo: https://github.com/electrocucaracha/ai-prepare-commit-msg
    rev: <release-with-telemetry>
    hooks:
      - id: ai-prepare-commit
        stages:
          - prepare-commit-msg
```

If the hook is already installed,
no reinstall is needed when changing environment variables.
For a new installation,
merge this configuration with any existing hooks and install the Git hook:

```bash
uvx pre-commit install --hook-type prepare-commit-msg
```

Pre-commit installs the package and its dependencies in its isolated environment.
Installing these dependencies alone does not enable telemetry;
only a non-empty `AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT` enables collection and export.
If it is unset or blank,
the hook runs normally without initializing or exporting telemetry,
even when the other telemetry variables are set.
If your current pin, such as `v20.3.7`, predates telemetry support,
update only `rev` to a release that includes it;
setting environment variables cannot add the feature to an older release.

### Environment variables

The hook's metrics configuration consists of four variables.
LiteLLM request tracing has separate settings,
described in [Configure LiteLLM request telemetry](#6-configure-litellm-request-telemetry).

| Variable                                 | Required                                     | Where to configure it                                                                                                            |
| ---------------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT`   | Yes, to enable export                        | Export the full OTLP/HTTP metrics URL before launching Git. Leave it unset or blank to disable telemetry.                        |
| `AI_PREPARE_COMMIT_MANUAL_SECONDS`       | No; defaults to `120`                        | Export the baseline before launching Git. Set `0` to disable time estimates. This variable alone does not enable telemetry.      |
| `OTEL_EXPORTER_OTLP_METRICS_HEADERS`     | Only for a receiver requiring authentication | Export the receiver's headers from a trusted environment or secret manager. Do not commit credentials to the hook configuration. |
| `OTEL_EXPORTER_OTLP_METRICS_CERTIFICATE` | Only for a receiver using a private CA       | Export the local path to the trusted CA certificate file. This must exist on each user's machine.                                |

For an authenticated receiver using a private CA,
set the optional variables before launching Git.
In this example,
`TELEMETRY_TOKEN` is supplied by your secret manager
and the certificate path must point to your actual CA file:

```bash
export OTEL_EXPORTER_OTLP_METRICS_HEADERS="Authorization=Bearer ${TELEMETRY_TOKEN}"
export OTEL_EXPORTER_OTLP_METRICS_CERTIFICATE="$HOME/.config/commit-telemetry/ca.pem"
```

Neither optional variable is needed for the local Rotel verification receiver.
Keep your existing exports for `LITELLM_PROXY_MODEL`,
`LITELLM_PROXY_API_BASE`, `LITELLM_PROXY_API_KEY`,
`LITELLM_EXTRA_HEADERS_JSON`, and `AI_PREPARE_COMMIT_AUTO_APPROVE` as they are.
Any provider-specific aliases required by your gateway remain unchanged.
For example,
add optional telemetry exports alongside your existing configuration in `~/.zshrc`,
then open a new terminal or reload that configuration before launching Git.
Do not put model-provider keys or telemetry authentication headers in committed YAML.
Pre-commit inherits exported variables;
it does not load `~/.zshrc` or a `.env` file itself,
and it does not support an `env:` key in hook configuration.
See the [configuration reference](../references/configuration.md#core-variables)
for provider-specific settings and other optional hook variables.

The Python pre-commit hook resolves dependencies from the package metadata;
it does not enforce this project's `uv.lock`.
Dependency constraints and the lockfile are maintained in this project,
not in each consuming repository's hook configuration.

### Standalone installations

For a source checkout using `uv`,
install the locked dependencies:

```bash
uv sync --locked
```

To run generation directly after configuring the endpoint,
use `uv run --locked prepare-commit --model "$LITELLM_PROXY_MODEL"`.
This command runs generation immediately if the checkout has staged changes.

For a package installed with `pip`,
use the standard installation in the environment that runs `prepare-commit`:

```bash
pip install ai-prepare-commit
```

## 3. Enable export

Export the endpoint in the environment that launches Git or the hook.
Your pre-commit configuration remains unchanged.
For the local receiver above:

```bash
export AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT=http://127.0.0.1:4318/v1/metrics
```

The URL includes the full metrics path;
the hook does not append `/v1/metrics`.
Setting `OTEL_EXPORTER_OTLP_ENDPOINT` alone does not enable telemetry.

![Telemetry opt-in flow: shell exports pass through Git and the unchanged pre-commit hook; an unset, blank, or invalid endpoint skips telemetry](../assets/diagrams/telemetry-opt-in.png)

Source: [Editable draw.io diagram](../assets/diagrams/telemetry-opt-in.drawio).

Both paths use the same hook configuration and normal generation flow.
Enabling telemetry adds measurements and best-effort export;
it does not change confirmation or approval behavior.

For a receiver that requires authentication,
set `OTEL_EXPORTER_OTLP_METRICS_HEADERS`
using the header names and values supplied by your receiver.
Do not embed credentials in the endpoint URL.
For a private certificate authority,
set `OTEL_EXPORTER_OTLP_METRICS_CERTIFICATE` to its trusted CA certificate file.
TLS certificate verification remains enabled.

## 4. Set a time-savings baseline

The default manual-writing baseline is 120 seconds per written AI suggestion.
To use a measured baseline for your workflow,
export it before launching Git:

```bash
export AI_PREPARE_COMMIT_MANUAL_SECONDS=90
```

The estimate subtracts hook duration,
including in-hook confirmation time,
from this baseline.
It can be negative when the hook takes longer than manual writing.
Set the value to `0` to disable time-savings estimates
without disabling other telemetry.

## 5. Verify delivery

Make your next intended commit with staged changes:

```bash
git commit
```

Review the generated message as usual.
The hook exports metrics when its command exits,
including when you reject a suggestion.
With the local receiver,
look for the `service.name` value `ai-prepare-commit-msg`
and metric names such as `commit_assistant.invocations` in Rotel's debug output.

Confirm that the attributes match the action you took:
an explicitly approved message has `outcome=written` and `approval=accepted`;
an auto-approved message has `approval=auto`;
a rejected message has `outcome=rejected` and `approval=rejected`.

## 6. Configure LiteLLM request telemetry

This project uses the LiteLLM Python SDK inside the hook process.
It measures `litellm.completion()` calls locally;
you do not need a LiteLLM server, server configuration,
or access to a gateway administrator to collect these measurements.

### Enable SDK request measurements

Keep your existing model selection, credentials, and pre-commit hook entry unchanged.
The same endpoint variable used for hook metrics also enables SDK request measurements:

```bash
export AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT=http://127.0.0.1:4318/v1/metrics
```

Export it in the shell that launches Git,
or add it alongside your existing exports in `~/.zshrc`.
The SDK measurements share the hook's OTLP/HTTP metrics export,
its `service.name=ai-prepare-commit-msg`,
and the optional authentication and CA variables listed above.
There is no second endpoint or separate LiteLLM telemetry service to configure.
If the endpoint is unset or blank,
the SDK calls still run normally but this integration does not collect or export metrics.

### What the SDK integration records

The hook wraps its SDK calls with `telemetry.request()`.
Both stages contribute to the same per-invocation metrics:

| SDK stage         | Calls covered                                                                                | Metric prefix                      |
| ----------------- | -------------------------------------------------------------------------------------------- | ---------------------------------- |
| Commit generation | Each SDK request for a generated message, including repeated attempts after empty responses. | `commit_assistant.generation.*`    |
| Summarization     | SDK calls for map-chunk summaries and reduce rounds when a diff is oversized.                | `commit_assistant.summarization.*` |

For each stage,
the integration counts attempted SDK calls,
records failures that raise exceptions,
and measures total elapsed request time.
When a response includes usage,
it records provider-reported input and output tokens.
When LiteLLM can price that response,
it contributes to `commit_assistant.cost_estimated`
and increments `commit_assistant.cost_priced_requests`.
Headroom compression measurements contribute to the separate compression-savings metrics.

One recorded request means one invocation of `litellm.completion()`,
not necessarily one upstream network attempt.
Retries or fallback routing internal to LiteLLM or your provider
are not separately counted by this wrapper.
The hook's `retries` metric counts its own repeated generation attempts after empty responses.
Missing usage or pricing remains unavailable data,
not evidence that a request consumed no tokens or incurred no cost.

Use the SDK measurements and hook outcomes together:

| Question                                      | Measurements                                                                                                        |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| How much AI work did a commit attempt use?    | Generation and summarization request and token totals, including rejected suggestions and retries.                  |
| What was the estimated AI cost?               | `cost_estimated`, with `cost_priced_requests` indicating pricing coverage. Both use the `commit_assistant.` prefix. |
| Did that work produce an accepted suggestion? | `invocations` grouped by `outcome` and `approval`.                                                                  |
| What did compression avoid?                   | `compression.tokens_saved` and `compression.cost_saved_estimated`, distinct from total AI consumption.              |

The SDK token and cost values are already included in the hook's totals.
Do not add a second copy of the same request's measurements from another integration
when calculating consumption or spend.

### Verify the SDK measurements with Rotel

Use the metrics-only Rotel command in [Prepare a receiver](#1-prepare-a-receiver).
After an intended commit that makes an SDK request,
look for `commit_assistant.generation.requests` in the receiver output.
Token and cost metrics appear when the provider supplies usage
and LiteLLM has pricing metadata.
Summarization metrics appear only when the oversized-diff path makes summary requests.
An invocation with no staged changes can produce hook metrics without any SDK request metrics.

### Native LiteLLM callbacks and traces

The integration described here is the project's own SDK instrumentation,
not LiteLLM's built-in OpenTelemetry callback.
The hook does not currently register `litellm.callbacks = ["otel"]`,
emit native `gen_ai.*` metrics,
or create and propagate tracing spans.
Setting `OTEL_EXPORTER`, `OTEL_ENDPOINT`, or `OTEL_SERVICE_NAME`
does not enable those features in this hook.
Use the documented `AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT` setting
for the SDK measurements supported by this implementation.

Native LiteLLM tracing would require additional SDK initialization,
callback lifecycle and shutdown handling,
and a separate review of which request attributes can leave the process.
It is not enabled by changing the pre-commit configuration.
See [LiteLLM's OpenTelemetry SDK integration](https://docs.litellm.ai/docs/observability/opentelemetry_integration)
for the library's separate callback API.

The current integration extracts numeric usage and pricing information;
it does not export SDK prompts, staged diffs, generated messages,
provider URLs, or provider credentials.
These content-free guarantees do not extend to independently installed
LiteLLM callbacks or other third-party instrumentation.

## Interpret usage and savings

Use the following measurements when building reports:

| Goal                         | Measurements and filters                                                                                                                                   |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Track frequency              | Sum `commit_assistant.invocations` over your reporting period. Separate `no_changes` and `error` outcomes from written suggestions.                        |
| Compare commit types         | Group written invocations by `commit.type`, such as `feat`, `fix`, or `docs`.                                                                              |
| Track explicit acceptance    | Compare `approval=accepted` with `approval=rejected`. Keep `approval=auto` separate.                                                                       |
| Track AI consumption         | Include generation and summarization input/output tokens, even for rejected suggestions and retries.                                                       |
| Track compression savings    | Sum `compression.tokens_saved` and compare it with `compression.tokens_before`. Both names have the `commit_assistant.` prefix.                            |
| Track AI spend               | Sum `commit_assistant.cost_estimated`. Use `cost_priced_requests` to identify how many responses contributed to that estimate.                             |
| Track avoided input cost     | Sum `commit_assistant.compression.cost_saved_estimated`. This is a gross compression estimate, not net savings after summarization costs.                  |
| Track estimated time savings | Sum `commit_assistant.time_saved_estimated` for written suggestions, separating explicit and automatic approvals. Divide seconds by 3,600 to report hours. |

Missing usage or pricing measurements mean unavailable data,
not zero consumption or free requests.
Pricing estimates depend on LiteLLM metadata
and do not account for negotiated prices or provider-specific cache discounts.
Decision-service consumption is not included.

Treat time savings as an estimate rather than measured developer productivity.
The hook does not observe later edits or review outside its confirmation prompt.
A written suggestion does not prove that the Git commit ultimately succeeded.
See the [telemetry reference](../references/configuration.md#optional-telemetry)
for the complete metric list and outcome definitions.

## Privacy and delivery limits

Hook metric payloads contain numeric measurements,
fixed outcome and approval categories,
and allowlisted Conventional Commit types.
They exclude commit text, scopes, diffs, paths, repository identifiers,
model names, user identities, and provider credentials.
These guarantees apply to `commit_assistant.*` metrics,
not to independently enabled LiteLLM traces or logs.
The receiver still sees your network address
and any authentication headers you configure.

Export is best-effort,
with a one-second exporter timeout and no background export thread.
Telemetry failures do not block commits.
Metrics are not queued or persisted for later delivery;
an unavailable receiver can therefore leave gaps in your reports.

## Troubleshoot missing metrics

| Symptom                                               | Action                                                                                                                                                                                         |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Nothing reaches the receiver                          | Confirm that `AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT` is set in the process launching Git. A graphical Git client might not inherit your shell's environment.                                    |
| The hook reports that telemetry export is unavailable | Confirm that the pinned hook release includes telemetry support, then check receiver reachability, authentication, and TLS configuration.                                                      |
| The receiver returns a not-found or protocol error    | Use the full binary OTLP/HTTP metrics URL, commonly ending in `/v1/metrics`. Do not use a dashboard URL or an OTLP/gRPC endpoint.                                                              |
| Token or cost measurements are absent                 | Check whether your provider returns usage and whether LiteLLM has pricing metadata for the model.                                                                                              |
| Time-savings measurements are absent                  | Check for a `written` outcome and a positive, finite manual-writing baseline. Rejected, oversized, no-change, and failed runs do not report time savings.                                      |
| Hook metrics arrive but SDK request metrics do not    | Confirm that staged changes actually trigger a generation request. Missing usage or pricing can omit token or cost measurements; native LiteLLM traces are not enabled by this implementation. |

## Disable telemetry

Unset the endpoint in the environment that launches the hook:

```bash
unset AI_PREPARE_COMMIT_TELEMETRY_ENDPOINT
```

If you added an endpoint export to `~/.zshrc` or another startup file,
remove it there too so new terminals do not re-enable telemetry.
No change to the pre-commit hook entry is needed.

This disables both hook-level and SDK request measurements from this integration.
It does not change model-provider credentials
or independently installed third-party instrumentation.

If you started the local receiver example,
stop it with `Ctrl+C` in its terminal.

## Related

- [How to install](how-to-install.md)
- [Configuration reference](../references/configuration.md#optional-telemetry)
- [Guides index](index.md)
