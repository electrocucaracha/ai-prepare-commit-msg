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

"""Module that load the prompt messages from a file."""

import yaml


def load_prompt_messages(file_path: str) -> list[dict[str, str]]:
    """Load prompt messages from a YAML file.

    Args:
        file_path (str): Path to the YAML file containing prompt messages.
    Returns:
        list[dict[str, str]]: List of messages with roles and content.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data.get("messages", [])
