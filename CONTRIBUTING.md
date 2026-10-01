# Contributing to AI Prepare Commit Message

Thank you for your interest in contributing.
This guide explains how to set up a development environment,
make changes,
and test them before you open a pull request.

## Prerequisites

You can work in one of two environments:

- **Dev Container (recommended)** —
  requires [Docker](https://docs.docker.com/get-docker/) or Podman
  and [Visual Studio Code](https://code.visualstudio.com/) with the
  [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)
  extension,
  or a [GitHub Codespace](https://github.com/features/codespaces).
- **Local machine** —
  requires Git, Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js,
  and Docker or Podman for linting.

## Set Up the Development Environment

### Option 1: Dev Container

1. Clone the repository:

   ```bash
   git clone https://github.com/electrocucaracha/ai-prepare-commit-msg.git
   cd ai-prepare-commit-msg
   ```

2. Open the folder in Visual Studio Code
   and select **Dev Containers: Reopen in Container** from the Command Palette.
3. Wait for the container to build.
   The `postCreateCommand` installs all dependency groups with `uv sync --all-groups`
   and registers the Git hooks with `pre-commit install`.

The container forwards `LITELLM_PROXY_MODEL`, `LITELLM_PROXY_API_BASE`,
`LITELLM_PROXY_API_KEY`, `OPENAI_API_KEY`, and `ANTHROPIC_API_KEY`
from your host environment.
See [Configuration](docs/references/configuration.md)
for the full list of variables.

By default,
the hook uses the local [Ollama](https://ollama.com/) server
that starts with the container on port `11434`:
`LITELLM_PROXY_MODEL` defaults to `ollama/llama3.2`
and `LITELLM_PROXY_API_BASE` defaults to `http://localhost:11434`.
On every start,
the container pulls the configured Ollama model in the background
and logs progress to `/tmp/ollama.log`.
To use a different model or a cloud provider,
export `LITELLM_PROXY_MODEL` on the host before you open the container.

### Option 2: Local Machine

1. Clone the repository as shown above.
2. Install the project and all dependency groups into `.venv`:

   ```bash
   uv sync --all-groups
   ```

3. Install the Git hooks:

   ```bash
   uvx pre-commit install
   ```

   This registers both the `pre-commit` checks
   and the `prepare-commit-msg` hook that runs `uv run prepare-commit`,
   so your own commits use the development version of the tool.

## Make Changes

1. Create a branch from `main`:

   ```bash
   git checkout -b my-feature
   ```

2. Make your changes:
   - Application code lives in `src/ai_prepare_commit_msg/`.
   - Unit tests live in `tests/`.
   - Behavior-driven scenarios live in `features/`.
   - Documentation lives in `docs/`
     and follows [Semantic Line Breaks](https://sembr.org/).
3. Add or update tests that cover the change.
4. Update the documentation when behavior or configuration changes.

## Test Your Changes

The `Makefile` wraps the [tox](https://tox.wiki/) environments
defined in `pyproject.toml`:

| Command         | Description                                                                      |
| --------------- | -------------------------------------------------------------------------------- |
| `make test`     | Run the unit tests with pytest.                                                  |
| `make coverage` | Run the unit tests with a coverage report.                                       |
| `make bdd`      | Run the Behave BDD scenarios in `features/`.                                     |
| `make mutation` | Run mutation tests with mutmut.                                                  |
| `make fmt`      | Format Python, Markdown, YAML, and shell sources.                                |
| `make lint`     | Run [Super-Linter](https://github.com/super-linter/super-linter) in a container. |

Pass extra arguments to pytest through tox, for example:

```bash
uvx tox -e test -- tests/test_git.py -k staged
```

To try the hook end-to-end,
stage a change and run the CLI directly:

```bash
git add <file>
uv run prepare-commit --log-level DEBUG
```

> [!NOTE]
> `make lint` uses the `ghcr.io/super-linter/super-linter` image,
> which only publishes `linux/amd64`.
> On Apple Silicon hosts it may fail
> unless you run it with `--platform=linux/amd64`.

## Submit a Pull Request

1. Run `make fmt`, `make lint`, and `make test` and fix any reported issues.
2. Commit your changes with the `prepare-commit-msg` hook installed by `pre-commit`.
   We encourage contributors to dogfood the project this way:
   the hook generates the commit message in the
   [Conventional Commits](https://www.conventionalcommits.org/) format for you,
   and using it on real changes helps us find bugs and improve the prompts.
   Review the draft before you accept it,
   and edit it if it does not describe the change accurately.
3. Push your branch and open a pull request against `main`.
4. Describe the motivation for the change
   and how you tested it.

## License

By contributing,
you agree that your contributions are licensed under the
[Apache License, Version 2.0](LICENSE).
