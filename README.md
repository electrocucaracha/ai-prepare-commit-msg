# AI Prepare Commit Message

<!-- markdown-link-check-disable-next-line -->

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Super-Linter](https://github.com/electrocucaracha/ai-prepare-commit-msg/workflows/Lint%20Code%20Base/badge.svg)](https://github.com/marketplace/actions/super-linter)

<!-- markdown-link-check-disable-next-line -->

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![visitors](https://visitor-badge.laobi.icu/badge?page_id=electrocucaracha.ai-prepare-commit-msg)
[![Scc Code Badge](https://sloc.xyz/github/electrocucaracha/ai-prepare-commit-msg?category=code)](https://github.com/boyter/scc/)
[![Scc COCOMO Badge](https://sloc.xyz/github/electrocucaracha/ai-prepare-commit-msg?category=cocomo)](https://github.com/boyter/scc/)

An AI-powered Git hook that generates concise,
high-quality commit messages from your staged changes.
Messages follow the Conventional Commits format and
Google engineering best practices.
The hook integrates with Git's `prepare-commit-msg`
flow and uses LiteLLM to produce the text.

## Features

- Generates commit messages from staged diffs.
- Produces Conventional Commits-compliant messages.
- Integrates with the `prepare-commit-msg` Git hook and
  `pre-commit`.
- Configurable system prompts to control tone and style.

## Installation (recommended)

Add a local hook to your `.pre-commit-config.yaml`:

```yaml
- repo: local
  hooks:
    - id: ai-prepare-commit-msg
      name: AI prepare commit message
      entry: prepare-commit
      language: python
      stages:
        - prepare-commit-msg
```

Alternatively, install the hook directly in your repository's
`.git/hooks/prepare-commit-msg`.

## Configuration

This tool requires a LiteLLM-compatible proxy.
Provide configuration via environment variables (shell or
`.env`):

```bash
export LITELLM_PROXY_MODEL=litellm_proxy/mistral
export LITELLM_PROXY_API_BASE=https://your-litellm-proxy.example
export LITELLM_PROXY_API_KEY=<your-api-key>
```

- `LITELLM_PROXY_MODEL`: LiteLLM model identifier used to
  generate messages.
- `LITELLM_PROXY_API_BASE`: Base URL of the LiteLLM proxy
  service.
- `LITELLM_PROXY_API_KEY`: API key for the proxy (if
  required).

Ensure these variables are available in the environment
where the hook runs (CI, local shell, or `pre-commit`
environment).

## Usage

1. Stage your changes with `git add`.
1. Create a commit (e.g., `git commit`).
   The hook will run and suggest a commit message.
1. Review and edit the suggested message before finalizing
   the commit.

## Prompts

System prompts and templates are stored under the
`prompts/` directory.
Edit those files to customize tone, length, or
formatting.
