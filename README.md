# Omacase

**Mac + omakase**: an opinionated, Omarchy-inspired Mac setup for development
and overnight agent work. Independent of DHH's Omamac and Omarchy.

Fish, Starship, eza and modern CLI tools; Ghostty; OmniWM tiling;
Omarchy-style shortcuts through Hammerspoon; Herdr with Ctrl+Space;
local Voxtype dictation; Raycast; and free menu-bar management with Thaw.

## Install

Apple Silicon, macOS 26+, internet and administrator access required.
Run as your normal user, not with sudo. Review [install.sh](install.sh) first.

Install or update with:

```sh
curl -fsSL https://raw.githubusercontent.com/crmne/omacase/main/install.sh | bash
```

Alternatively, download and extract the repository ZIP from GitHub,
then run `bash bootstrap.sh --apply` inside it. Homebrew and Python are
installed when absent. Existing packages are updated; running GUI app updates
are deferred until you close them and rerun.

Managed configs are replaced with backups, not merged. No apps are removed.
macOS permission prompts remain manual. Pass `--no-activate` to the bootstrap
to avoid starting apps or changing the login shell and login items.

## Everyday keys

- Command + arrows: focus; Command + Shift + arrows: move windows.
- Command + 1–9/0: workspace; add Shift to move the window and follow it.
- Command + O: floating; Command + K: shortcut help.
- Herdr: Ctrl + Space, then C creates a tab.
- Native Command + T/W/F/S/L and other selected Mac shortcuts stay native.

## Status and details

Experimental. Tested components on one macOS 27 Mac, not yet a complete
fresh-Mac installation. Workspace-slide animations and some Hyprland features
are not available. A fresh account shares system apps and Homebrew, so
it cannot prove first-machine provisioning.

[Installation, recovery and limitations](docs/guide.md) ·
[Shortcut conflicts](tools/NATIVE-CONFLICTS.md) ·
[Attribution](THIRD_PARTY_NOTICES)

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 tests/config.py
lua tests/mac-shortcuts.lua
```
