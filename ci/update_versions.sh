#!/bin/bash
# SPDX-license-identifier: Apache-2.0
##############################################################################
# Copyright (c) 2025
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

set -o errexit
set -o pipefail
if [[ ${DEBUG:-false} == "true" ]]; then
    set -o xtrace
fi

REPO="https://github.com/electrocucaracha/gh-workflows/tree/main/.github/agents"
RAW="https://raw.githubusercontent.com/electrocucaracha/gh-workflows/main/.github/agents"

trap "make fmt" EXIT

if ! command -v uv >/dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi
uv sync --upgrade --all-extras
uvx pre-commit autoupdate
uv run --no-project --with git+https://github.com/electrocucaracha/gh-updater.git gh-updater .

curl -fsSL "$REPO" |
    grep -oE 'href="/electrocucaracha/gh-workflows/blob/main/\.github/agents/[^"]+"' |
    cut -d '"' -f 2 |
    sed 's|.*/||' |
    sort -u |
    while IFS= read -r file; do
        curl -fsSL "$RAW/$file" -o ".github/agents/$file"
        echo "Updated: $file"
    done
