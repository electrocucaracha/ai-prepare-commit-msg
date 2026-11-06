---
title: Use Vim without a Git hook
parent: How-to guides
nav_order: 6
---

Use the shortcut configured in [How to install](how-to-install.md)
to generate a message during a commit
or test the shortcut without creating a commit.

## Generate a message

Review the staged changes you intend to include.
The command reads the staged diff and sends it to your configured model provider.
Then run `git commit`.
When Vim opens the commit-message buffer,
press `<leader>cg` and approve the generated message at the terminal prompt.
Vim displays a progress message while the command runs,
then reports whether it updated the message buffer.

The shortcut temporarily enables Vim's `autoread` option
to load the generated message without a file-change prompt.
Review the message,
then save and close the buffer with `:wq` to complete the commit.
Use `:cq` to abort the commit instead.

## Test without committing

From the repository root, inspect the staged diff and open Git's message file:

```bash
git diff --cached --stat
vim "$(git rev-parse --git-path COMMIT_EDITMSG)"
```

Press `<leader>cg` to test the mapping.
Because Vim was opened directly,
not by `git commit`, saving or quitting the buffer does not create a commit.
Quit with `:q!` when you finish.

If no changes are staged,
the command exits without calling the model provider;
this only checks that the mapping runs.
If changes are staged,
their diff is sent to the configured provider.

## Troubleshooting

If Vim still reports that the message file changed,
press `L` to load the generated message.
If the command reports no staged changes,
stage the changes you want included and try again.
