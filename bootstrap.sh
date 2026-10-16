#!/bin/bash
# The entry point deliberately needs only tools shipped with macOS.
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
apply=false
for arg in "$@"; do
  case "$arg" in
    --apply) apply=true ;;
    --no-activate|--no-login-shell) ;;
    *) echo "Usage: bash bootstrap.sh [--apply] [--no-activate] [--no-login-shell]"; exit 2 ;;
  esac
done
if ! "$apply"; then
  echo 'Preview: provision Homebrew and Python, then install/update the shell and desktop stack.'
  echo 'Configure Fish, Starship, eza, Ghostty, Herdr, OmniWM, Hammerspoon and Voxtype with backups.'
  echo 'Download the local speech model; configure startup and Fish login shell unless disabled.'
  echo 'No changes made. Run: bash bootstrap.sh --apply'
  exit 0
fi
if [[ "$(uname -s)" != Darwin || "$(uname -m)" != arm64 ]]; then
  echo 'This stack requires Apple Silicon macOS (OmniWM requirement).'; exit 1
fi
mac_major="$(sw_vers -productVersion | cut -d. -f1)"
if (( mac_major < 26 )); then
  echo 'This stack requires macOS 26 or later (OmniWM requirement).'; exit 1
fi
if (( EUID == 0 )); then echo 'Run as your normal user, not sudo.'; exit 1; fi
if [[ ! -x /opt/homebrew/bin/brew ]]; then
  echo 'Installing Homebrew using its official installer. It may request your administrator password.'
  brew_installer="$(mktemp -t omarchy-mac-homebrew)"
  trap 'rm -f -- "$brew_installer"' EXIT
  /usr/bin/curl --fail --location --proto '=https' --tlsv1.2 \
    https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh -o "$brew_installer"
  /bin/bash "$brew_installer"
fi
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
export HOMEBREW_NO_INSTALL_CLEANUP=1
brew update
brew install python
exec /opt/homebrew/bin/python3 "$project_dir/bootstrap.py" "$@"
