"""Choose a Conventional Commit type with a TypeSafe-compatible decision API."""

import os
import re
from urllib.parse import urlsplit

from typesafe_sdk import Choice, TypeSafeClient, TypeSafeError

TYPES = {
    "feat": "Introduces a new feature or capability",
    "fix": "Corrects a bug or incorrect behavior",
    "refactor": "Restructures code without changing behavior",
    "revert": "Reverts an earlier change",
    "style": "Changes formatting or whitespace only",
    "docs": "Changes documentation only",
    "test": "Adds or changes tests only",
    "chore": "Changes maintenance work not covered by another type",
    "build": "Changes build tooling or dependencies",
    "ci": "Changes continuous integration configuration",
    "perf": "Improves performance",
}


def add_commit_type(message: str, base_url: str, model: str | None = None) -> str:
    """Add the selected Conventional Commit type to a generated message.

    Args:
        message: Generated description and optional body or footers.
        base_url: Base URL of the decision API.
        model: Optional decision model override.

    Returns:
        The message with its chosen type prepended.

    Raises:
        ValueError: When the description is empty or the decision is invalid.
        RuntimeError: When the decision service cannot answer.
    """
    title, separator, body = message.partition("\n")
    title = re.sub(r"^(?:[a-z]+(?:\([^\n)]*\))?!?: )", "", title)
    if not title.strip():
        raise ValueError("Generated commit description is empty.")
    description = f"{title}{separator}{body}"
    return f"{choose_type(description, base_url, model)}: {description}"


def choose_type(description: str, base_url: str, model: str | None = None) -> str:
    """Classify a generated description via a TypeSafe-compatible endpoint.

    Args:
        description: Generated commit description and optional body.
        base_url: Base URL of the Jev or Ollaya decision API.
        model: Optional decision model override.

    Returns:
        A supported Conventional Commit type.

    Raises:
        ValueError: When credentials or the decision answer are invalid.
        RuntimeError: When the service cannot answer the decision.
    """
    parsed_url = urlsplit(base_url)
    if (
        parsed_url.scheme not in {"http", "https"}
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise ValueError(
            "Decision URL must be an HTTP(S) base URL without credentials or query"
        )

    is_jev = parsed_url.hostname == "api.typesafe.ai"
    if is_jev and parsed_url.scheme != "https":
        raise ValueError("Jev decision URL must use HTTPS")
    api_key = os.getenv("TYPESAFE_API_KEY")
    if is_jev and not api_key:
        raise ValueError("TYPESAFE_API_KEY is required for Jev decisions")

    try:
        with TypeSafeClient(
            base_url=base_url.rstrip("/"),
            api_key=api_key or "local",
            model=model or ("jev-latest" if is_jev else "laya"),
            timeout=15,
        ) as client:
            response = client.system_one(
                state=description,
                questions={
                    "commit_type": Choice(
                        instructions="Which Conventional Commit type best describes the primary change?",
                        criteria=TYPES,
                    )
                },
            )
        answer = response.choices["commit_type"].choice
    except (TypeSafeError, KeyError) as error:
        raise RuntimeError(f"Decision request failed: {error}") from error

    if not isinstance(answer, str) or answer not in TYPES:
        raise ValueError(
            f"Decision service returned an unsupported commit type: {answer!r}"
        )
    return answer
