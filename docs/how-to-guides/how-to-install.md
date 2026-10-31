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

Add the repository to your `.pre-commit-config.yaml`.
Pin `rev` to a released tag, such as `v7.0.1`.
See the [releases page](https://github.com/electrocucaracha/ai-prepare-commit-msg/releases) for the latest version.

```yaml
default_install_hook_types:
  - pre-commit
  - prepare-commit-msg
repos:
  - repo: https://github.com/electrocucaracha/ai-prepare-commit-msg
    rev: v7.0.1
    hooks:
      - id: ai-prepare-commit
        stages:
          - prepare-commit-msg
```

The hook works alongside other `pre-commit` hooks in the same config.
Only the `prepare-commit-msg` stage is required for `ai-prepare-commit`.

`default_install_hook_types` tells `pre-commit` which Git hooks to wire up.
Install them with:

```bash
uvx pre-commit install
```

If your config omits `default_install_hook_types`,
install the `prepare-commit-msg` hook explicitly:

```bash
uvx pre-commit install --hook-type prepare-commit-msg
```

## Configure a model

The hook requires a configured LiteLLM model.
For GitHub Copilot,
export:

```bash
export LITELLM_PROXY_MODEL=github_copilot/gpt-4
```

See the [Configuration reference](../references/configuration.md)
for other providers and required API keys.

## Verify installation

Run a test commit in a repository with staged changes.
When your editor opens,
you should see a generated commit message draft,
followed by a `[Y/n]` prompt in your terminal to accept it.

If you commit from an environment without a controlling terminal,
such as CI or a script,
the confirmation prompt has no terminal to read from and the commit fails.
Set `AI_PREPARE_COMMIT_AUTO_APPROVE=1`
in that environment to skip the prompt and write the message directly.
See the [Configuration reference](../references/configuration.md).

## Troubleshooting

### Slow installation or execution after upgrading

The hook now requires Python 3.12 or later,
and the default pre-commit configuration uses Python 3.12.
When you upgrade from a version that used an older Python interpreter,
pre-commit must create a new hook environment and reinstall its dependencies.
This can delay your first commit after upgrading.

Make Python 3.12 available on your `PATH`,
then run this command from your repository before committing:

```bash
uvx pre-commit install --install-hooks --hook-type prepare-commit-msg
```

The command installs the Git hook and prepares its Python environment immediately.
Wait for installation to finish before committing.
Subsequent commits reuse the environment,
so you do not need to reinstall before every commit.
This moves environment setup out of the commit workflow;
it does not reduce AI message generation time.

## Related

- [Configuration reference](../references/configuration.md)
- [Guides index](index.md)
