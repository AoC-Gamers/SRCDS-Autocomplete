#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLATFORM="${EXTS_PLATFORM:-linux}"
PYTHON_BIN="${PYTHON:-python3}"
"$PYTHON_BIN" "$ROOT_DIR/scripts/ci/validate-artifact.py" \
  --artifact-dir "${EXTS_ARTIFACT_DIR:-$ROOT_DIR/dist/$PLATFORM/artifact}" \
  --platform "$PLATFORM" --zip "${EXTS_ZIP:-$ROOT_DIR/dist/release/srcds-autocomplete-local-$PLATFORM.zip}"
