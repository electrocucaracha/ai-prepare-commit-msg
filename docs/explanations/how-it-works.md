---
title: How the hook works
parent: Explanations
nav_order: 1
---

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

## The Execution Flow

![Execution flow from staged changes to a generated commit message](../assets/diagrams/commit-flow.png)

The diagram shows the normal path,
including the no-change exit,
oversized-prompt guard,
and retry loop.

When you run `git commit`,
Git invokes the `prepare-commit-msg` hook,
which runs the AI command with your configured model.

The tool then:

1. **Detects staged changes** — Uses GitPython to fetch the cached diff (all staged changes awaiting commit).
   If no changes are staged, the tool exits silently without generating anything.

2. **Guards against oversized diffs** — Estimates token count using LiteLLM's token counter.
   If the prompt exceeds 120,000 tokens,
   the tool returns a warning message instead of calling the model,
   preventing context-window failures.

3. **Constructs the prompt** — Loads a YAML prompt file (default: `prompts/default.yml`)
   containing a system message and user message template.
   Your staged diff becomes the final user message.

4. **Calls the LLM** — Sends all prompt messages to your configured model via LiteLLM
   with a 10-second timeout.
   The request includes a low temperature (0.1) to favor consistency over creativity.

5. **Handles retries** — If the model returns an empty response,
   the tool retries up to 5 times (configurable) with a 3-second delay between attempts (configurable).
   This helps recover from transient API failures.

6. **Validates the output** — Extracts text from the model's response,
   supporting multiple response formats (objects with message attributes, dictionaries, strings).

7. **Confirms or auto-approves** — When running interactively, displays the generated message and prompts you to confirm.
   You can accept it (press Enter or Y), reject it (press N), or edit it in the editor.
   With `--auto-approve`, the message is written without confirmation.

8. **Writes to Git** — Persists the commit message to `.git/COMMIT_EDITMSG`,
   which Git displays in your editor when the hook completes.

## Why LiteLLM

LiteLLM provides a single abstraction over multiple model providers
(OpenAI, Anthropic, Azure, local models, etc.).
That means you can switch models by changing a single environment variable,
instead of rewriting hook logic for each provider's API.

The tool calls `litellm.completion()` with your model identifier,
and LiteLLM handles authentication, routing, and response parsing transparently.

## Prompt Strategy and Conventional Commits

The prompt file defines the writing constraints and quality expectations.
The default prompt enforces Conventional Commits format:
each message has a type (feat, fix, refactor, etc.),
optional scope,
a concise description,
and an optional body with semantic line breaks.

The prompt also instructs the model to:

- Write headers in imperative mood without trailing periods.
- Limit headers to 72 characters.
- Use semantic line breaks in the body (one sentence per line, split at natural clause boundaries).
- Include footers only when applicable (BREAKING CHANGE, references, etc.).
- Self-document the commit with enough context that readers understand the "why" without external bug trackers.

This shared prompt ensures consistent commit message quality
across all developers and time,
regardless of which LLM provider or model version you select.

## Safeguards and Error Handling

The tool includes multiple safety mechanisms:

- **Timeout protection** — LLM calls are wrapped in a 10-second timeout using Python's `concurrent.futures`.
  If the model takes longer, the tool falls back to an empty message,
  which can then be retried.

- **Oversized prompt detection** — Prompts exceeding 120,000 tokens are rejected before calling the model,
  with a clear message asking you to write the commit manually.
  This prevents context-window failures and wasted API calls.

- **Retry logic** — Empty responses trigger automatic retries (up to 5 attempts by default),
  which helps survive transient network errors or API hiccups.

- **Interactive confirmation** — Unless you use `--auto-approve`,
  every generated message is displayed and requires your explicit approval before being written.
  You retain full control.

- **No staged changes** — If no changes are staged,
  the tool silently returns without generating anything,
  letting Git proceed with an empty message buffer.

## Prompt Compression with Headroom

If the optional `headroom-ai` package is installed,
the tool compresses the prompt before sending it to LiteLLM.
This reduces token usage while preserving the added and removed diff lines,
allowing longer diffs to fit within token budgets.
After each run the tool prints a one-line summary of the tokens saved.
Headroom is optional;
the tool works fine without it.

## Operational Model

- **Input**: staged diff and context.
- **Processing**: prompt loading, token estimation, LLM inference with retries, and output extraction.
- **Output**: commit message draft inserted into Git's message buffer.

This model keeps the integration narrow and predictable,
which makes the hook easy to install,
reason about,
and replace with alternative implementations.

## Related

- [Configuration reference](../references/configuration.md)
- [Explanation index](index.md)
