---
title: Home
nav_order: 1
---

# AI Prepare Commit Message

A Git `prepare-commit-msg` hook that uses a language model
to generate a commit message draft from staged changes.
You stay in control —
the draft appears in your editor and you finalize it before committing.

## What it solves

**No first-draft friction** —
Writing a well-formed commit message for every change takes time.
The hook generates a Conventional Commits-aligned draft automatically,
so you start from something instead of a blank buffer.

**Provider flexibility** —
The hook delegates to LiteLLM,
which means you can switch between OpenAI, Anthropic, GitHub Copilot,
and other providers by changing a single environment variable.
A plugin system also lets you add custom providers
without modifying this project;
see [Add a custom LLM provider](how-to-guides/custom-providers.md).

**Minimal integration surface** —
Installation is a single `pre-commit` block or a file copy into `.git/hooks/`.
No persistent processes, no sidecars, no daemon.

## Documentation sections

| Section                         | Contents                                  |
| ------------------------------- | ----------------------------------------- |
| [Tutorials](tutorials/)         | Guided first-run walkthrough              |
| [How-to guides](how-to-guides/) | Goal-oriented task recipes                |
| [Reference](references/)        | Environment variables and CLI options     |
| [Explanations](explanations/)   | Design rationale and architecture context |
