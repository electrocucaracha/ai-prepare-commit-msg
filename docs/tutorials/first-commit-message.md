# Tutorial: Generate Your First Commit Message

In this tutorial,
you will configure the hook and complete a commit with an AI-generated message.

When you finish, you will know the complete happy-path workflow.

## Before You Begin

- You can run shell commands in a local Git repository.
- You have Python and `pre-commit` available.
- You can access your configured LiteLLM provider.

## Step 1: Install the Hook

Follow [How to install](../guides/how-to-install.md)
using the `pre-commit` method.

## Step 2: Configure Environment Variables

Set the model and provider values you want to use.
For example:

```bash
export LITELLM_PROXY_MODEL=github_copilot/gpt-4
```

If your provider needs additional variables,
set them now.
See [Configuration reference](../reference/configuration.md).

## Step 3: Create a Small Change

Edit any file in your repository,
then stage the change:

```bash
git add <file>
```

## Step 4: Start the Commit

Run:

```bash
git commit
```

Your editor opens with a generated commit message draft.

## Step 5: Review and Finish

Check that the message matches your change intent.
Adjust wording if needed,
then save and close the editor.

## What You Learned

- How to install the `prepare-commit-msg` hook.
- How configuration values affect generation.
- How the generated draft fits into your normal commit flow.

## Next Step

Continue with [How to use](../guides/how-to-use.md)
to learn repeatable daily usage.
