---
title: Headroom prompt compression
parent: Explanations
nav_order: 2
---

# Headroom prompt compression

This project uses Headroom's inline Python API to reduce the size of large prompts
before they reach LiteLLM.
The compression is optional.
It can lower token use and reduce pressure on the model's context window,
but it is not required to generate a commit message.

## Why the project uses it

The prompt contains the commit-message instructions and the staged Git diff.
Large diffs can repeat file headers,
context lines,
and other information that is less useful to the model.
Headroom removes some of that repetition while keeping the important shape of the change.

The project still owns the final size check.
Headroom reduces the prompt;
it does not guarantee that every prompt fits the model's context window.

This integration uses Headroom as an inline library.
It does not run Headroom as a proxy,
use its MCP tools,
or depend on its Compress-Cache-Retrieve (CCR) flow.

## How the integration works

The project loads the configured prompt messages and appends the staged diff as the last user message.
It passes the complete list to `headroom.compress.compress()`.

Headroom examines message content and chooses a suitable content-aware transform.
For a unified diff,
that can be the diff transform.
The same routing system supports other content types,
including JSON,
logs,
tables,
configuration,
and plain text.

The project sets `compress_user_messages=True` because the staged diff is a user message.
It sets `protect_recent=0` so the final diff message is eligible for compression.
The project asks LiteLLM for the configured model's maximum input size,
reserves space for the response,
and passes the resulting prompt limit to Headroom.
Models that are not present in LiteLLM's metadata use a conservative 8,192-token context-window fallback.

## How the prompt limit is resolved

The hook reads `max_input_tokens` from `litellm.get_model_info()`.
It does not use LiteLLM's `max_tokens` value,
because that value can describe the model's output limit rather than its input capacity.

The hook reserves 1,024 tokens for the generated response.
For example,
a model with a 128,000-token maximum input size receives a 126,976-token prompt limit.
An unmapped model uses the 8,192-token fallback
and therefore receives a 7,168-token prompt limit.

Metadata lookup is a safeguard,
not a dependency for successful generation.
If LiteLLM cannot identify the model or returns no positive input limit,
the fallback keeps compression and summarization available for custom gateways and proxy aliases.

Headroom returns the messages after transformation,
the token counts before and after compression,
and the transforms it applied.
The project records those counts only when Headroom provides a positive baseline.

See the [Headroom compression sequence diagram source](../assets/diagrams/headroom-sequence.drawio)
for the complete component and message flow.

The diagram shows the boundary between the project,
Headroom,
LiteLLM,
and the model provider.
Headroom performs the optional transformation;
LiteLLM estimates the resulting prompt;
the provider generates the commit message only after the size check passes.

If the estimate is still above the resolved prompt token limit,
the project replaces the diff with its map-reduce summary.
It compresses and measures the new prompt again.
If the prompt remains too large,
the project skips the model request and returns a warning.

## What compression preserves

Headroom is lossy.
The compressed result is not a byte-for-byte copy of the diff.
Its diff-aware transform is intended to preserve information that helps a model understand a patch,
including:

- file boundaries and patch structure
- meaningful added and removed lines
- relevant hunks and nearby context

It can remove repeated headers,
surrounding context,
and other low-value boilerplate.
The result depends on the size and shape of the diff,
so the project does not promise a fixed compression ratio or preservation of every line.

## Fallback behavior

The integration fails open.
If Headroom is not installed,
cannot be imported,
throws an exception,
or returns no usable token baseline,
the project keeps the original messages.
An unchanged result is also valid when the content is too small,
unrecognized,
unsafe to transform,
or unlikely to save tokens.

These fallbacks keep an optimization failure from blocking the Git hook.
The project still handles an oversized prompt separately:
it summarizes the diff,
checks the result again,
and stops safely when the prompt remains above the limit.

The CLI reports compression metrics when they are available:

```console
Headroom: 2395 -> 2131 prompt tokens over 1 request(s); saved 264 (11.0%).
```

The counts describe the compression calls made in the current process.
They are useful for observing savings,
not a promise about every diff.

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
