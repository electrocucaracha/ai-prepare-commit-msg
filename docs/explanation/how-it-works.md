# How the Hook Works

`ai-prepare-commit-msg` connects Git's `prepare-commit-msg` lifecycle
to a language model through LiteLLM.

The design goal is simple:
you keep your normal commit flow,
and the tool proposes a high-quality draft based on staged changes.

## Lifecycle Integration

Git runs `prepare-commit-msg` before the commit message editor opens.
This project uses that moment to inspect staged diffs,
send a prompt to the selected model,
and write a suggested commit message to the commit message file.

You stay in control.
The generated output is a draft,
and you can edit it before the commit is finalized.

## Why LiteLLM

LiteLLM provides a single abstraction over multiple providers.
That means you can switch models by changing environment variables,
instead of rewriting hook logic.

## Prompt Strategy

The prompt files define the writing constraints,
including Conventional Commits alignment and style expectations.
This keeps behavior consistent across model providers.

## Operational Model

- Input: staged diff and context.
- Processing: prompt rendering and model inference.
- Output: commit message draft inserted into Git's message buffer.

This model keeps the integration narrow,
which makes the hook easy to install,
reason about,
and replace.

## Related

- [How to use](../guides/how-to-use.md)
- [Configuration reference](../reference/configuration.md)
- [Explanation index](index.md)
