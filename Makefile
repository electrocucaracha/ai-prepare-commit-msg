# SPDX-license-identifier: Apache-2.0
##############################################################################
# Copyright (c) 2025
# All rights reserved. This program and the accompanying materials
# are made available under the terms of the Apache License, Version 2.0
# which accompanies this distribution, and is available at
# http://www.apache.org/licenses/LICENSE-2.0
##############################################################################

DOCKER_CMD ?= $(shell which docker 2> /dev/null || which podman 2> /dev/null || echo docker)
PYTHON_VERSIONS := 3.12 3.13 3.14
TOX_TEST_ENVS := test coverage mutation bdd

.PHONY: cleanup cleanup-node-modules
cleanup: cleanup-node-modules
	rm -rf .tox/ .venv/

cleanup-node-modules:
	rm -rf node_modules

# Biome has no JS/TS application sources to lint or format in this repo, and the
# pre-commit hooks include a local "uv run prepare-commit" hook that the
# super-linter container can't execute, so both validators are disabled
# via the overrides below.
.PHONY: lint
lint: cleanup-node-modules
	$(DOCKER_CMD) run --rm -v $$(pwd):/tmp/lint \
	-e RUN_LOCAL=true \
	-e LINTER_RULES_PATH=/ \
	-e EDITORCONFIG_FILE_NAME=.editorconfig-checker.json \
	-e VALIDATE_BIOME_LINT=false \
	-e VALIDATE_BIOME_FORMAT=false \
	-e VALIDATE_PRE_COMMIT=false \
	-e PYTHON_ISORT_CONFIG_FILE=pyproject.toml \
	-e PYTHON_RUFF_FORMAT_CONFIG_FILE=pyproject.toml \
	-e DEFAULT_BRANCH=main \
	ghcr.io/super-linter/super-linter

.PHONY: fmt
fmt: cleanup
	command -v textlint > /dev/null && npm list --global --depth=0 textlint-rule-terminology > /dev/null 2>&1 || sudo npm install --global textlint textlint-rule-terminology
	textlint . --fix
	command -v shfmt > /dev/null || curl -s "https://i.jpillora.com/mvdan/sh!!?as=shfmt" | bash
	shfmt -l -w -s -i 4 .
	command -v yamlfmt > /dev/null || curl -s "https://i.jpillora.com/google/yamlfmt!!" | bash
	yamlfmt -dstar **/*.{yaml,yml}
	npx -y prettier . --write --ignore-path .gitignore
	npx -y markdownlint-cli2 --fix .
	command -v uvx > /dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
	uvx tox -e fmt

define tox-version-target
.PHONY: $(1)-py$(subst .,,$(2))
$(1)-py$(subst .,,$(2)):
	uvx tox -e $(1) \
		--override tox.env.$(1).base_python=python$(2) \
		--override tox.env.$(1).package_env=.pkg-$(1)-py$(subst .,,$(2)) \
		--override tox.env.$(1).env_dir=.tox/$(1)-py$(subst .,,$(2)) \
		--override tox.env.$(1).set_env.COVERAGE_FILE=.coverage-$(1)-py$(subst .,,$(2)) \
		--override tox.env.$(1).set_env.PYTEST_ADDOPTS=--cache-dir=.pytest_cache/$(1)-py$(subst .,,$(2))
endef

$(foreach env,$(TOX_TEST_ENVS),$(foreach version,$(PYTHON_VERSIONS),$(eval $(call tox-version-target,$(env),$(version)))))

define tox-matrix-target
.PHONY: $(1)
$(1): $(foreach version,$(PYTHON_VERSIONS),$(1)-py$(subst .,,$(version)))
endef

$(foreach env,test coverage bdd,$(eval $(call tox-matrix-target,$(env))))

# Mutmut writes shared cache and report files, so run its Python versions serially.
mutation-py313: mutation-py312
mutation-py314: mutation-py313
.PHONY: mutation
mutation: mutation-py314
