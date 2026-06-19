---
title: How to install
parent: How-to guides
nav_order: 1
---

This guide shows you how to add the `ai-prepare-commit-msg` hook to your repository.
Choose the method that fits your workflow.

## Prerequisites

- You have a Git repository.
- You can run `git` commands from your shell.
- For the `pre-commit` method, you have `pre-commit` installed.

## Install with pre-commit (recommended)

Add the repository to your `.pre-commit-config.yaml`:

```yaml
default_install_hook_types:
  - pre-commit
  - prepare-commit-msg
repos:
  - repo: https://github.com/electrocucaracha/ai-prepare-commit-msg
    rev: e1fda3d307234dd12d0eb9161007ab6bd89fba37
    hooks:
      - id: ai-prepare-commit
        stages:
          - prepare-commit-msg
```

Install the Git hook:

```bash
pre-commit install --hook-type prepare-commit-msg
```

## Install directly in .git/hooks

Copy or symlink the hook script into your local Git hooks directory:

```bash
cp <path-to-hook-script> .git/hooks/prepare-commit-msg
chmod +x .git/hooks/prepare-commit-msg
```

## Verify installation

Run a test commit in a repository with staged changes.
When your editor opens,
you should see a generated commit message draft.

## Related

- [How to use](how-to-use.md)
- [Configuration reference](../references/configuration.md)
- [Guides index](index.md)
