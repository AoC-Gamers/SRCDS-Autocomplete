SHELL := /usr/bin/env bash

ROOT_DIR := $(shell cd "$$(dirname "$(MAKEFILE_LIST)")" && pwd)
.DEFAULT_GOAL := help
ifeq ($(OS),Windows_NT)
PYTHON ?= python
else
PYTHON ?= $(shell command -v python3 >/dev/null 2>&1 && echo python3 || echo python)
endif
LINUX_DEPS_DIR ?= $(ROOT_DIR)/.deps/exts-linux
WINDOWS_DEPS_DIR ?= $(ROOT_DIR)/.deps/exts-windows
LINUX_BUILD_DIR ?= $(ROOT_DIR)/.build/linux-l4d2
WINDOWS_BUILD_DIR ?= $(ROOT_DIR)/.build/windows-l4d2
LINUX_PACKAGE_DIR ?= $(ROOT_DIR)/.build/package-exts-linux
WINDOWS_PACKAGE_DIR ?= $(ROOT_DIR)/.build/package-exts-windows
LINUX_ARTIFACT_DIR ?= $(ROOT_DIR)/dist/linux/artifact
WINDOWS_ARTIFACT_DIR ?= $(ROOT_DIR)/dist/windows/artifact
LINUX_RELEASE_BASENAME ?= srcds-autocomplete-local-linux
WINDOWS_RELEASE_BASENAME ?= srcds-autocomplete-local-windows

.PHONY: help deps-exts-linux deps-exts-windows build-exts-linux build-exts-windows package-exts-linux package-exts-windows release-linux release-windows clean-linux clean-windows clean-all

help:
	@printf '%s\n' \
		'Available targets:' \
		'  make test TEST_OUTPUT=<new-dir>  Run package and interface regressions' \
		'  make test-ci TEST_OUTPUT=<new-dir>  Run product checks without Sonar' \
		'  make check-ci             Lint GitHub Actions (actionlint required)' \
		'  make validate-artifact-linux|validate-artifact-windows  Validate tree and ZIP' \
		'  make release-identity-linux|release-identity-windows  Resolve identity from AOC_REF_*' \
		'  make sonar-cppcheck       Analyze locally with the real build database' \
		'  make sonar                Explicit configured Sonar analysis; waits for gate' \
		'  make sonar-tooling-test   Offline analyzer tests (local only)' \
		'  make help                 Show this help message' \
		'  make deps-exts-linux      Fetch Linux extension dependencies into .deps/exts-linux/' \
		'  make deps-exts-windows    Fetch Windows extension dependencies into .deps/exts-windows/' \
		'  make build-exts-linux     Build the Linux extension package' \
		'  make build-exts-windows   Build the Windows extension package' \
		'  make package-exts-linux   Stage the Linux package tree' \
		'  make package-exts-windows Stage the Windows package tree' \
		'  make release-linux        Create the Linux release zip' \
		'  make release-windows      Create the Windows release zip' \
		'  make clean-linux          Remove Linux build outputs' \
		'  make clean-windows        Remove Windows build outputs' \
		'  make clean-all            Remove all build outputs and dependencies'

deps-exts-linux:
	DEPS_DIR="$(LINUX_DEPS_DIR)" bash "$(ROOT_DIR)/scripts/deps/fetch-linux-deps.sh"

deps-exts-windows:
	DEPS_DIR="$(WINDOWS_DEPS_DIR)" pwsh -File "$(ROOT_DIR)/scripts/deps/fetch-windows-deps.ps1"

build-exts-linux:
	DEPS_DIR="$(LINUX_DEPS_DIR)" BUILD_DIR="$(LINUX_BUILD_DIR)" bash "$(ROOT_DIR)/scripts/build/build-linux-l4d2.sh"

build-exts-windows:
	DEPS_DIR="$(WINDOWS_DEPS_DIR)" BUILD_DIR="$(WINDOWS_BUILD_DIR)" pwsh -File "$(ROOT_DIR)/scripts/build/build-windows-l4d2.ps1"

package-exts-linux:
	$(PYTHON) "$(ROOT_DIR)/scripts/package/stage-artifact.py" "$(ROOT_DIR)" "$(LINUX_BUILD_DIR)/package" "$(LINUX_PACKAGE_DIR)" --platform linux

package-exts-windows:
	$(PYTHON) "$(ROOT_DIR)/scripts/package/stage-artifact.py" "$(ROOT_DIR)" "$(WINDOWS_BUILD_DIR)/package" "$(WINDOWS_PACKAGE_DIR)" --platform windows

release-linux:
	$(PYTHON) "$(ROOT_DIR)/scripts/package/stage-artifact.py" "$(ROOT_DIR)" "$(LINUX_PACKAGE_DIR)" "$(LINUX_ARTIFACT_DIR)" --platform linux
	$(PYTHON) "$(ROOT_DIR)/scripts/package/package-release.py" --root "$(ROOT_DIR)" --artifact-dir "$(LINUX_ARTIFACT_DIR)" --basename "$(or $(RELEASE_BASENAME),$(LINUX_RELEASE_BASENAME))" --platform linux

release-windows:
	$(PYTHON) "$(ROOT_DIR)/scripts/package/stage-artifact.py" "$(ROOT_DIR)" "$(WINDOWS_PACKAGE_DIR)" "$(WINDOWS_ARTIFACT_DIR)" --platform windows
	$(PYTHON) "$(ROOT_DIR)/scripts/package/package-release.py" --root "$(ROOT_DIR)" --artifact-dir "$(WINDOWS_ARTIFACT_DIR)" --basename "$(or $(RELEASE_BASENAME),$(WINDOWS_RELEASE_BASENAME))" --platform windows

clean-linux:
	$(PYTHON) "$(ROOT_DIR)/scripts/tools/clean.py" "$(ROOT_DIR)" "$(LINUX_BUILD_DIR)" "$(LINUX_PACKAGE_DIR)" "$(ROOT_DIR)/dist/linux"

clean-windows:
	$(PYTHON) "$(ROOT_DIR)/scripts/tools/clean.py" "$(ROOT_DIR)" "$(WINDOWS_BUILD_DIR)" "$(WINDOWS_PACKAGE_DIR)" "$(ROOT_DIR)/dist/windows"

clean-all:
	$(PYTHON) "$(ROOT_DIR)/scripts/tools/clean.py" "$(ROOT_DIR)" "$(ROOT_DIR)/.build" "$(ROOT_DIR)/dist" "$(ROOT_DIR)/.deps"

validate-artifact-linux:
	$(PYTHON) "$(ROOT_DIR)/scripts/ci/validate-artifact.py" --artifact-dir "$(LINUX_ARTIFACT_DIR)" --platform linux --zip "$(ROOT_DIR)/dist/release/$(or $(RELEASE_BASENAME),$(LINUX_RELEASE_BASENAME)).zip"

validate-artifact-windows:
	$(PYTHON) "$(ROOT_DIR)/scripts/ci/validate-artifact.py" --artifact-dir "$(WINDOWS_ARTIFACT_DIR)" --platform windows --zip "$(ROOT_DIR)/dist/release/$(or $(RELEASE_BASENAME),$(WINDOWS_RELEASE_BASENAME)).zip"

.PHONY: test test-ci sonar sonar-cppcheck sonar-tooling-test check-ci release-identity-linux release-identity-windows validate-artifact-linux validate-artifact-windows
TEST_OUTPUT ?=
test:
	$(PYTHON) "$(ROOT_DIR)/tests/runners/test.py" --output "$(TEST_OUTPUT)"

test-ci: test

sonar:
	@$(PYTHON) "$(ROOT_DIR)/scripts/tools/make_sonar.py" analyze --compile-commands "$(LINUX_BUILD_DIR)/compile_commands.json"

sonar-cppcheck:
	@$(PYTHON) "$(ROOT_DIR)/scripts/tools/make_sonar.py" cppcheck --compile-commands "$(LINUX_BUILD_DIR)/compile_commands.json"

sonar-tooling-test:
	$(PYTHON) "$(ROOT_DIR)/tests/python/sonar_tooling_test.py"

check-ci:
	actionlint "$(ROOT_DIR)/.github/workflows/build.yml"

release-identity-linux:
	@$(PYTHON) "$(ROOT_DIR)/scripts/package/release-identity.py" --name srcds-autocomplete --platform linux

release-identity-windows:
	@$(PYTHON) "$(ROOT_DIR)/scripts/package/release-identity.py" --name srcds-autocomplete --platform windows
