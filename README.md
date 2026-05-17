# AI Prepare Commit Message

<!-- markdown-link-check-disable-next-line -->

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![GitHub Super-Linter](https://github.com/electrocucaracha/ai-prepare-commit-msg/workflows/Lint%20Code%20Base/badge.svg)](https://github.com/marketplace/actions/super-linter)

<!-- markdown-link-check-disable-next-line -->

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![visitors](https://visitor-badge.laobi.icu/badge?page_id=electrocucaracha.ai-prepare-commit-msg)
[![Scc Code Badge](https://sloc.xyz/github/electrocucaracha/ai-prepare-commit-msg?category=code)](https://github.com/boyter/scc/)
[![Scc COCOMO Badge](https://sloc.xyz/github/electrocucaracha/ai-prepare-commit-msg?category=cocomo)](https://github.com/boyter/scc/)

AI-powered Git hook that generates concise,
high-quality commit messages from your staged changes.

Messages follow the Conventional Commits format
and OpenStack commit-message best practices.

The hook integrates with Git's `prepare-commit-msg` flow
and uses LiteLLM to produce the text.

## Features

- Generates commit messages from staged diffs.
- Produces Conventional Commits-compliant messages.
- Integrates with the `prepare-commit-msg` Git hook and `pre-commit`.
- Configurable prompts to control tone and style.

## Documentation

Project documentation for GitHub Pages is available in the docs site:

- [Docs home](docs/index.md)
