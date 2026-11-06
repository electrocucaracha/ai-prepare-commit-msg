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

To generate a message manually from Vim without installing a Git hook,
configure the optional shortcut below,
then follow [Use Vim without a Git hook](vim-integration.md).

## Configure Vim integration

You can run the command manually from Vim
without installing `pre-commit` or a Git hook.
Configure Git to use Vim or Neovim as its commit-message editor.
For Vim, set the editor globally:

```bash
git config --global core.editor "vim"
```

Use `nvim` instead of `vim` for Neovim.
To configure the editor for only one repository,
run the command there without `--global`.

Install `uv`,
and make sure `uvx` is on the shell `PATH` used by Vim.
The shortcut runs `uvx` as a child process of Vim,
so it inherits Vim's environment.
Set `LITELLM_PROXY_MODEL` and any provider-specific variables,
including credentials,
before launching Vim.
If you launch Vim from a graphical session,
make those variables available to that session as well.

Add this Vimscript to `~/.vimrc` or Neovim's `init.vim`:

```vim
function! s:GenerateCommitMessage()
  if &modified
    echoerr 'Save or discard buffer changes before generating a message.'
    return
  endif

  let l:original_message = getline(1, '$')
  let l:autoread = &autoread
  echo 'Generating commit message from staged changes...'
  redraw
  set autoread
  execute '!uvx --from ai-prepare-commit prepare-commit'
  let l:exit_code = v:shell_error
  let &autoread = l:autoread

  if l:exit_code != 0
    echoerr 'Generation failed or was declined; check the command output.'
  elseif getline(1, '$') ==# l:original_message
    echomsg 'Commit message unchanged; check staged changes and command output.'
  else
    echomsg 'Commit message updated. Review it before completing the commit.'
  endif
endfunction

augroup ai_prepare_commit_msg
  autocmd!
  autocmd BufRead,BufNewFile COMMIT_EDITMSG nnoremap <buffer> <leader>cg :call <SID>GenerateCommitMessage()<CR>
augroup END
```

The mapping applies when Vim opens Git's `COMMIT_EDITMSG` file.
By default, `<leader>` is the backslash key;
use your configured leader key if you have changed it.
The `cg` suffix is a mnemonic for “commit generate.”
The mapping temporarily enables Vim's `autoread` option
so it reloads the generated message without prompting to load the changed file.
It also shows progress and reports whether the message changed
or generation failed or was declined.

For a custom provider,
add its package to the `uvx` command in the function.
See [Add a custom LLM provider](custom-providers.md)
for provider configuration details.

See [Use Vim without a Git hook](vim-integration.md)
to generate a message or test the shortcut without committing.

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
