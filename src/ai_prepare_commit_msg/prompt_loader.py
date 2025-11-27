# Copyright (c) 2025
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Module that loads prompt messages from a YAML file.

This module provides a small helper to read and validate the prompt
messages structure expected by the CLI.
"""

from pathlib import Path
from typing import Dict, List

import yaml


def load_prompt_messages(file_path: str | Path) -> List[Dict[str, str]]:
    """Load prompt messages from a YAML file.

    Args:
        file_path: Path to the YAML file containing prompt messages.

    Returns:
        A list of message dictionaries with `role` and `content` keys.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the YAML structure is not as expected.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError("Prompt file must contain a mapping at the top level")

    messages = data.get("messages", [])
    if messages is None:
        return []
    if not isinstance(messages, list):
        raise ValueError("'messages' must be a list in the prompt file")

    return [m for m in messages if isinstance(m, dict)]
