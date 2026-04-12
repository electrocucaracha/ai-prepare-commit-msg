---
# GitHub Copilot Custom Instructions

# Repository-specific instructions for Copilot to follow when generating code
---

# General Guidelines

- Ensure all code changes adhere to Pythonic best practices, including PEP 8 compliance and idiomatic Python.
- Write clear and concise docstrings for all functions, classes, and modules using the Google style guide.
- Prioritize readability, maintainability, and modularity in the code.

## Pre-commit Requirements

- After making code changes, ensure the following commands pass successfully:
  1. `make fmt` - to check for formatting errors.
  1. `make test` - to verify all tests pass.
- Update or add new tests in the `tests/` directory to cover any new functionality or changes.
- Update the documentation in `docs/` if the changes affect the public API or usage.

## Specific Instructions

- Use type hints for all function signatures.
- Avoid redundant comments; let the code and docstrings speak for themselves.
- Follow the DRY (Don't Repeat Yourself) principle to avoid code duplication.
- Use meaningful variable and function names that convey intent.
- Ensure all YAML files in `src/ai_prepare_commit_msg/prompts/` are valid and properly formatted.

## Code Review Checklist

- Verify that all docstrings are up-to-date and accurately describe the functionality.
- Confirm that `make lint` and `make test` pass without errors.
- Check for adherence to Pythonic best practices and idiomatic code.
- Ensure that any changes to the `src/` directory are reflected in the corresponding tests in `tests/`.

## Additional Notes

- Use the `pyproject.toml` file for managing dependencies and configurations.
- If adding new dependencies, ensure they are added to `pyproject.toml` and documented in the `README.md`.
- Keep the `Makefile` updated with any new commands or workflows.
