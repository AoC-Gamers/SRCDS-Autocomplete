#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ENV_FILE="${ENV_FILE:-$ROOT_DIR/.env}"

load_dotenv() {
  local env_file="$1"
  if [[ ! -f "$env_file" ]]; then
    return
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    [[ "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || continue

    local name="${line%%=*}"
    local value="${line#*=}"
    value="${value#"${value%%[![:space:]]*}"}"
    value="${value%"${value##*[![:space:]]}"}"
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi
    if [[ -z "${!name+x}" ]]; then
      export "$name=$value"
    fi
  done < "$env_file"
}

load_dotenv "$ENV_FILE"

DEPS_DIR="${DEPS_DIR:-$ROOT_DIR/.deps}"
BUILD_DIR="${BUILD_DIR:-$ROOT_DIR/.build/linux-l4d2}"
HL2SDK_DIR="${HL2SDK_DIR:-$DEPS_DIR/hl2sdk-l4d2}"
SOURCEMOD_DIR="${SOURCEMOD_DIR:-$DEPS_DIR/sourcemod-1.12}"
MMSOURCE_DIR="${MMSOURCE_DIR:-$DEPS_DIR/mmsource-1.12}"
VENV_DIR="${VENV_DIR:-$DEPS_DIR/.venv-linux}"
AMBUILD_DIR="${AMBUILD_DIR:-$DEPS_DIR/ambuild}"
export HL2SDK_DIR SOURCEMOD_DIR MMSOURCE_DIR AMBUILD_DIR
CONFIGURE_SCRIPT="${CONFIGURE_SCRIPT:-$ROOT_DIR/configure.py}"

# Validate before invalidating receipts or removing an existing directory.
BUILD_DIR="$("${PYTHON:-python3}" "$ROOT_DIR/scripts/tools/output_paths.py" "$ROOT_DIR" "$BUILD_DIR" \
  "$DEPS_DIR" "$HL2SDK_DIR" "$SOURCEMOD_DIR" "$MMSOURCE_DIR" "$AMBUILD_DIR" "$VENV_DIR")"

# Invalidate prior success before any preflight can fail.
rm -f "$BUILD_DIR/build-receipt.json"

case "$(uname -s)" in
  Linux)
    ;;
  *)
    echo "This build script must be run in a Linux environment (native Linux or WSL)." >&2
    exit 1
    ;;
esac

if [[ ! -x "$VENV_DIR/bin/python" ]]; then
  echo "Missing Python venv at $VENV_DIR. Run make deps-exts-linux first." >&2
  exit 1
fi

if [[ ! -x "$VENV_DIR/bin/ambuild" ]]; then
  echo "Missing AMBuild in $VENV_DIR. Run make deps-exts-linux first." >&2
  exit 1
fi

for required_dir in "$HL2SDK_DIR" "$SOURCEMOD_DIR" "$MMSOURCE_DIR"; do
  if [[ ! -d "$required_dir" ]]; then
    echo "Missing required directory: $required_dir" >&2
    exit 1
  fi
done

# Resolve source directories before changing cwd; the receipt records these paths.
HL2SDK_DIR="$(cd "$HL2SDK_DIR" && pwd -P)"
SOURCEMOD_DIR="$(cd "$SOURCEMOD_DIR" && pwd -P)"
MMSOURCE_DIR="$(cd "$MMSOURCE_DIR" && pwd -P)"

rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

pushd "$BUILD_DIR" > /dev/null
"$VENV_DIR/bin/python" "$CONFIGURE_SCRIPT" \
  --sdks l4d2 \
  --hl2sdk-root "$DEPS_DIR" \
  --hl2sdk-path "$HL2SDK_DIR" \
  --mms-path "$MMSOURCE_DIR" \
  --sm-path "$SOURCEMOD_DIR" \
  --enable-optimize

# AMBuild can report a configuration failure with a successful process exit.
test -f "$BUILD_DIR/.ambuild2/vars"

"$VENV_DIR/bin/ambuild"
popd > /dev/null

PACKAGE_DIR="$BUILD_DIR/package/addons/sourcemod/extensions"
EXT_BIN="$PACKAGE_DIR/autocomplete.ext.2.l4d2.so"
AUTOLOAD_FILE="$PACKAGE_DIR/autocomplete.autoload"
GAMEDATA_FILE="$BUILD_DIR/package/addons/sourcemod/gamedata/autocomplete.games.txt"

if [[ ! -f "$EXT_BIN" ]]; then
  echo "Build completed but no autocomplete.ext.2.l4d2.so was found in $PACKAGE_DIR." >&2
  exit 1
fi

cat <<EOF
Build complete.
BUILD_DIR=$BUILD_DIR
EXTENSION=$EXT_BIN
AUTOLOAD=$AUTOLOAD_FILE
GAMEDATA=$GAMEDATA_FILE
EOF

"$VENV_DIR/bin/python" "$ROOT_DIR/scripts/build/export-compile-commands.py" "$BUILD_DIR"
"$VENV_DIR/bin/python" "$ROOT_DIR/scripts/package/build-receipt.py" "$ROOT_DIR" "$BUILD_DIR" linux
