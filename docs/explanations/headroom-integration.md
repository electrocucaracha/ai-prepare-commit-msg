---
title: Headroom prompt compression
parent: Explanations
nav_order: 2
---

# Headroom prompt compression

This project uses Headroom's inline Python API to optionally compress the prompt before it reaches LiteLLM.
The feature is not required for correctness,
but it can reduce the cost and context-window pressure of a large staged diff.

## Why this exists

The main request contains two things:
the prompt policy and the staged diff.
When the diff is large,
compression removes low-value context while keeping the actual change set intact.
The project still enforces its own token budget and rejects requests that remain too large.

Headroom is therefore an optimization layer,
not the core model interface.
This integration does not run Headroom as a proxy,
enable its MCP tools,
or depend on its Compress-Cache-Retrieve (CCR) retrieval flow.
If compression is unavailable or fails,
the hook continues with the original messages.

## What the project does

The project passes LiteLLM's message list to `headroom.compress.compress()`.
Headroom examines each message's content and routes recognized structures to an appropriate compressor.
For a unified staged diff,
that route is Headroom's diff compressor;
the same pipeline can also handle structured data such as JSON, logs, tables, configuration, and plain text.

The integration sets `compress_user_messages=True` and `protect_recent=0`.
These settings are essential here:
the staged diff is deliberately the final user message,
so the default protections for user and recent messages would otherwise make it ineligible for compression.
The configured model and the project's `120,000`-token guardrail are passed to Headroom,
allowing it to use the model-aware token accounting expected by the request.

Headroom's router applies safety gates before transforming content.
Small content, unrecognized content, and a transform that does not save tokens can pass through unchanged.
The upstream library also fails open when a structural transform cannot safely run.
The hook adds its own broader fail-open boundary around the Headroom call,
so an import or runtime failure cannot block a commit.

The request path is:

1. Build the LiteLLM message list.
2. Append the staged diff as the final user message.
3. Compress the complete message list when Headroom is available.
4. Estimate the resulting prompt length with LiteLLM.
5. When it still exceeds the guardrail, summarize the diff, compress again, and re-estimate.
6. Proceed only when the final prompt is within the project's guardrail.

![Headroom compression request flow from the Git hook to the generated commit message](../assets/diagrams/headroom-compression.png)

## What gets preserved

Headroom is a lossy compression layer,
not a byte-for-byte representation of the diff.
Its diff-aware route is designed to preserve the information most useful for understanding a patch.
In practice this includes:

- patch structure and file boundaries
- added and removed lines that carry change information
- relevant hunks and contextual signals

It can reduce surrounding context, repeated headers, and low-value boilerplate.
The exact result depends on the diff's size, redundancy, and shape;
the project should not treat a particular compression ratio or every individual line as guaranteed.

## Token metrics and fallback

The project records token counts before and after compression.
Those values are printed in the CLI output when available,
for example:

```console
Headroom: 2395 -> 2131 prompt tokens over 1 request(s); saved 264 (11.0%).
```

If compression is unavailable or throws an error,
the hook falls back to the original messages without failing the commit flow.
Likewise,
a result without a positive token baseline is discarded and the original message list is used.
This is intentional: compression is a cost-saving optimization, not a required dependency.

## Limits

Headroom does not replace the project's guardrails.
The final token check still enforces the maximum prompt budget,
and the system still stops on provider context-limit errors.

This keeps the project safe:
Headroom can reduce cost for large diffs,
but it cannot guarantee that an arbitrarily large diff will fit into any model context.

## Further reading

For Headroom's current compression pipeline,
including content routing and safety gates,
see [How compression works](https://docs.headroomlabs.ai/docs/how-compression-works).
For its supported entry points and the distinction between the inline library, proxy, and CCR flows,
see [Headroom architecture](https://docs.headroomlabs.ai/docs/architecture).
The project's dependency is published in the [Headroom repository](https://github.com/headroomlabs-ai/headroom).

## Related topic

For the larger diff-handling process,
see [Large diff summarization chain](summarization-chain.md).
