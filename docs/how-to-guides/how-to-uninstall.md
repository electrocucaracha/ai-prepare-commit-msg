---
title: How to uninstall
parent: How-to guides
nav_order: 2
---

This guide shows you how to remove the `ai-prepare-commit-msg` hook from your repository.
Choose the method that matches how you installed it.

## Quickest way: remove the Git hooks directly

Git hooks are executable scripts stored in `.git/hooks/`.
Removing the `prepare-commit-msg` and `pre-commit` files from that folder
stops Git from running `ai-prepare-commit-msg`,
regardless of how the hook was installed.

From the root of your repository, run:

```bash
rm -f .git/hooks/prepare-commit-msg .git/hooks/pre-commit
```

This only affects your local clone.
Other clones of the repository, and CI systems,
keep running the hook until they remove it too.

## Uninstall with pre-commit

If you installed the hook through `pre-commit`,
you can uninstall the managed hook types instead of deleting files by hand:

```bash
uvx pre-commit uninstall --hook-type prepare-commit-msg
```

If you also installed the `pre-commit` stage, remove it too:

```bash
uvx pre-commit uninstall --hook-type pre-commit
```

Then remove the `ai-prepare-commit` entry from your `.pre-commit-config.yaml`.

## Verify removal

Run a test commit in a repository with staged changes.
No commit message draft should be generated,
and no `[Y/n]` confirmation prompt should appear.

## Related

- [How to install](how-to-install.md)
- [Configuration reference](../references/configuration.md)
- [Guides index](index.md)
