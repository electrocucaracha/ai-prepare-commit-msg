# How to Use AI Prepare Commit Message

This guide walks you through generating an AI-assisted commit message
with the hook in place.

## Prerequisites

- You installed the hook.
  See [How to install](how-to-install.md).
- You have changes ready to commit in your repository.
- You configured model and API settings.
  See the [Configuration reference](../reference/configuration.md).

## Generate a commit message

1. Stage your changes.

   ```bash
   git add <files>
   ```

2. Start a commit.

   ```bash
   git commit
   ```

3. Review the generated message in your editor.
4. Edit the message if needed, then save and close the editor.

## Tune prompt behavior

Prompt templates are in `src/ai_prepare_commit_msg/prompts/`.
Edit those files to adjust tone, length, and structure.

## Related

- [How to install](how-to-install.md)
- [Configuration reference](../reference/configuration.md)
- [Guides index](index.md)
