---
title: Home
nav_order: 1
---

# AI Prepare Commit Message

A Git `prepare-commit-msg` hook that generates a commit message draft from your staged changes.
It uses a language model to summarize the work and propose a message you can review before committing.

## Why use it

**Start from a draft, not a blank page** —
You do not need to write a well-formed commit message from scratch for every change.
The hook creates a structured draft so you can refine it instead of staring at an empty editor.

**Keep commit history consistent** —
The generated output is aligned with Conventional Commits conventions,
which helps make your history easier to scan and your changelog more useful.

**Use the model provider you want** —
The hook delegates to LiteLLM,
so you can switch between OpenAI, Anthropic, GitHub Copilot,
and other supported providers by changing a single environment variable.
A plugin system also lets you add custom providers without modifying this project;
see [Add a custom LLM provider](how-to-guides/custom-providers.md).

**Keep setup simple** —
Installation is a single `pre-commit` block or a direct copy into `.git/hooks/`.
There is no background daemon, no persistent service, and no extra operational burden.

## What it does

When you stage a change and run `git commit`, the hook inspects the diff,
identifies the main change, and opens a draft commit message in your editor.
You stay in control:
review the suggestion, adjust it, and finalize only when it matches your intent.

## Get started

1. Read the [tutorials](tutorials/) for a guided first-time setup.
2. Follow the [how-to guides](how-to-guides/) for common workflows and customizations.
3. Use the [reference](references/) pages for environment variables and CLI options.
4. Read the [explanations](explanations/) pages for design rationale and architecture context.

## Documentation map

| Section                         | Contents                                                      |
| ------------------------------- | ------------------------------------------------------------- |
| [Tutorials](tutorials/)         | Guided first-run walkthrough and onboarding                   |
| [How-to guides](how-to-guides/) | Task-based recipes for installation and configuration         |
| [Reference](references/)        | Environment variables, CLI options, and details               |
| [Explanations](explanations/)   | Design rationale, architecture context, and deeper background |

## In one sentence

AI Prepare Commit Message helps you create higher-quality commit messages faster,
without taking control away from the developer.
