---
title: Large diff summarization chain
parent: Explanations
nav_order: 3
---

# Large diff summarization chain

When the staged diff gets too large for a single model request,
the hook falls back to a deterministic summarization pipeline.
The goal is to keep the meaningful change set,
while avoiding context-window problems and noisy prompt bloat.

## Why this is needed

Large changesets are common in feature work and refactors.
If the raw diff is sent directly,
a model can miss important files,
lose signal in generated artifacts,
or fail outright when the prompt exceeds the configured budget.

The project therefore protects generation with two steps:

1. A token-budget check.
2. A summarized fallback when the raw diff is still too large.

![Summarization chain from the staged diff to the final commit message prompt](../assets/diagrams/summarization-chain.png)

## Deterministic preprocessing

Before the model ever sees the diff,
the pipeline filters and anchors it.

### Low-signal file handling

Generated or vendor-heavy files are marked as low-signal and skipped from semantic summarization.
Examples include lockfiles and vendored directories.
This keeps the prompt focused on the architecture and behavior changes,
not on generated noise.

### File-level anchoring

The diff is also inspected for exact file paths,
modification types,
and added or removed line counts.
This creates a ground-truth skeleton that the model can use without inventing missing file details.

## Map phase: summarize each meaningful file

The summarization pass works file by file.
It does the following:

- splits very large files into chunks when necessary
- isolates each file or chunk into its own request
- asks for a short summary of the actual change
- preserves function, class, and constant names when they are relevant

This avoids a single large file drowning out smaller but more important edits.

## Reduce phase: merge notes back together

Once the per-file summaries exist,
the pipeline merges them until they fit the allowed summarization budget.
It keeps unique changes,
removes duplicated observations,
and produces a compact report that keeps the essential intent of the diff.

The result is not a generic summary.
It is a structured view of what changed,
where it changed,
and which files matter most.

## Fallback behavior

If the summarization chain fails,
the hook falls back to the original diff.
If the resulting prompt still exceeds the budget,
the tool emits a safe oversized-diff warning and stops instead of sending a broken request.

That turn of behavior matters:
most commit-generation workflows prefer a controlled failure over a bad or blank message.

## Practical outcome

The final prompt reaches the model with a compact, grounded description of the staged change set.
The commit message then reflects the actual intent of the diff,
without overwhelming the model with unrelated churn or generated artifacts.

See [How the hook works](how-it-works.md) for the overall lifecycle,
and [Headroom prompt compression](headroom-integration.md) for the optional token-saving layer.
