#!/bin/bash
# Download a complete source snapshot, then use the normal bootstrap.
set -euo pipefail
apply=true
args=()
for arg in "$@"; do
  case "$arg" in
    --preview) apply=false ;;
    --no-activate|--no-login-shell) args+=("$arg") ;;
    *) echo 'Usage: bash install.sh [--preview] [--no-activate] [--no-login-shell]' >&2; exit 2 ;;
  esac
done
if "$apply"; then args+=(--apply); fi
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo 'Omacase requires Apple Silicon macOS.' >&2
  exit 1
fi
if (( EUID == 0 )); then
  echo 'Run as your normal user, not sudo.' >&2
  exit 1
fi
stage="$(mktemp -d "${TMPDIR:-/tmp}/omacase-install.XXXXXXXX")"
trap 'rm -rf -- "$stage"' EXIT
archive="$stage/source.tar.gz"
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  gh api repos/crmne/omacase/tarball/main > "$archive"
else
  /usr/bin/curl --fail --location --proto '=https' --tlsv1.2 \
    https://api.github.com/repos/crmne/omacase/tarball/main -o "$archive" || {
      echo 'Download failed. For a private repository, use authenticated GitHub CLI or download its ZIP from GitHub.' >&2
      exit 1
    }
fi
mkdir "$stage/source"
/usr/bin/tar -xzf "$archive" --strip-components=1 -C "$stage/source"
if [[ ! -f "$stage/source/bootstrap.sh" || ! -f "$stage/source/bootstrap.py" ]]; then
  echo 'Incomplete Omacase archive; refusing to install.' >&2
  exit 1
fi
# Keep stdin available for password prompts when this script is piped to bash.
if ( : < /dev/tty ) 2>/dev/null; then
  /bin/bash "$stage/source/bootstrap.sh" ${args[@]+"${args[@]}"} < /dev/tty
else
  /bin/bash "$stage/source/bootstrap.sh" ${args[@]+"${args[@]}"}
fi
