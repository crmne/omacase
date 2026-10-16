# Omacase: installation and recovery guide

An opinionated, Omarchy-inspired macOS setup for development and persistent
agent work, including a full machine bootstrap.

## Why Omacase?

**Omacase** ("oh-mac-kah-say") is **Mac + omakase**: a thoughtfully chosen setup
instead of a pile of tools you have to assemble yourself. The name puts Mac
at the center of the omakase idea: let someone curate the starting point,
then make it your own.

That means a coordinated shell, terminal, tiling window manager, keyboard
shortcuts, local dictation and persistent agent workspaces. The goal is to
prepare a fresh Mac or bring an existing one into the same setup, with
repeatable updates and backups of the configurations it changes.

Omacase brings the parts of Omarchy that fit macOS while keeping deliberate
Mac conveniences, such as native find, save, tabs and address-bar shortcuts.
It is a configuration and bootstrap project, not a new operating system or
a promise that every Hyprland feature works on macOS.

This is an independent project, not DHH's Omamac and not affiliated with
Omarchy, Omacom, or Apple. It is under active development, not yet a stable
release. Repository: [crmne/omacase](https://github.com/crmne/omacase).

## Full bootstrap: fresh or existing Mac

Requirements: Apple Silicon, macOS 26+, internet access and a normal user
account. Some steps need administrator authentication. Intel is not supported
by this stack because OmniWM requires Apple Silicon. The full provisioning
flow is implemented but has not been validated on a freshly installed Mac.

From an extracted copy of this project, no Git, Python or Homebrew is needed:

```sh
bash bootstrap.sh          # preview, no changes or downloads
bash bootstrap.sh --apply  # install, upgrade, configure and activate
```

The same command is used for subsequent updates. It installs Homebrew with
the official installer when absent, then provisions Python and the packages
below. Homebrew can arrange its own required developer tools; do not run this
project as root. macOS prompts for passwords and security grants remain manual.

| Layer | Included |
| --- | --- |
| Shell | Fish, Starship, eza, zoxide, fzf, mise, direnv, bat, ripgrep, fd, jq |
| Development | Git, Git LFS, GitHub CLI, Neovim, tmux, lazygit, btop, Lua |
| Containers | Docker CLI, Colima, lazydocker |
| Desktop | Ghostty, OmniWM, Hammerspoon, Raycast, JetBrains Mono Nerd Font |
| Agent workspace | Herdr with Omarchy bindings |
| Dictation | Voxtype 1.1.1, verified SHA-256, local small.en model, app bundle |
| Menu bar | Thaw 2 on macOS 26; Thaw 3 beta on macOS 27 |
| Shortcut apps | Chrome, Obsidian, Signal; native Passwords; web fallbacks |

No paid app or agent subscription is installed. AI provider credentials,
personal Git identity, SSH keys and conversations are never copied. Voxtype
is pinned to the tested release (an existing newer binary is not downgraded);
Homebrew packages update to their registry versions, not a lockfile.

### Behavior on an existing Mac

- Already installed Homebrew packages are upgraded, not treated as errors.
  Only the listed packages are requested, plus their dependencies. No global
  cleanup, autoremove or blanket upgrade is performed.
- Running GUI apps are left alone and their upgrades are listed as deferred.
  Close the named apps and rerun to finish those upgrades.
- Manually installed app bundles are copied to a recovery directory before
  replacement with the current Homebrew cask. Identical font artifacts can be
  adopted. Unusual symlinked app paths require manual reconciliation.
- Managed configuration files are updated automatically, with original bytes
  and permissions backed up. This is replacement, not a semantic merge.
  Fish uses a separate conf.d file and a project-specific Starship profile;
  personal config.fish and the existing global starship.toml are preserved.
  Existing Fish plugins can still override or duplicate initialization and
  need review. Configuration symlinks are deliberately not followed.
- Persistent Herdr servers are not restarted. Their configuration is reloaded.
  Competing window managers are reported, not killed or uninstalled.
- Activation configures Fish as the login shell, adds desktop login items,
  selects the Hammerspoon configuration, opens the desktop utilities, and
  starts Colima only when no Docker daemon is available. Hammerspoon already
  running may need a manual reload. macOS permission prompts require you.
  Conflicting screenshot/input-source/workspace hotkeys are disabled with a preference
  backup; macOS may need a logout to recognize that change. Choose Raycast's
  launcher shortcut in its first-run setup.
  Missing preference entries inherit macOS defaults, so the bootstrap writes
  explicit disabled entries for screenshot shortcuts as well. Print Screen
  still invokes capture directly through Hammerspoon, not those system keys.

Use `--no-activate` to install/configure without changing shell preferences,
login items or starting apps/Colima. Use `--no-login-shell` to activate without
changing the account's login shell. Configuration changes can still be picked
up immediately by apps that watch their files, including OmniWM.

Recovery files live in `~/.local/state/omarchy-mac/`. Bootstrap directories
contain package results, previous manually installed apps, activation
preferences and the configuration transaction ID. Configuration rollback is
described below. App versions, Homebrew changes, login items, shell registration,
Colima state and activation preferences are not automatically rolled back.
Do not run concurrent bootstraps or a separate config installer at the same time.

Network access: Homebrew and its package download hosts, GitHub's official
Homebrew installer and Voxtype release, and Voxtype's model download host.
Colima can download a Linux VM image on first start. No telemetry is added by
this project; installed applications have their own network behavior.

## Status

Tested components on one Apple Silicon Mac running macOS 27: OmniWM 0.7.6,
Hammerspoon 1.1.1, Herdr 0.9.5, Ghostty 1.3.1, and Voxtype 1.1.1. Thaw
3.0.0-beta.2 handles menu-bar clutter. A preview-first configuration installer
is available for development testing, not a claim of compatibility with every
Mac. The live Mac still uses chezmoi as its source
of truth; this directory is an extracted development snapshot.

## Design

- OmniWM: tiling, ten numbered workspaces, a workspace strip overlapping the
  native menu-bar area without reserving another row. Its native hotkeys are
  disabled; Hammerspoon owns desktop bindings.
- Hammerspoon: Command acts as Omarchy's Super, with native Command+T and
  Command+W preserved. Command+O toggles floating. Command+K opens key help.
- Herdr: Omarchy's Ctrl+Space prefix, pane/tab/workspace bindings and terminal
  theme. Ctrl+Space then C creates a tab without prompting for a name.
- Voxtype: local dictation and a Hammerspoon recording status overlay.
- Thaw: optional, free menu-bar management. Keep iStat visible. No second
  menu-bar hider runs alongside it.
- agent-run: opt-in idle-sleep prevention for a specific overnight command.

No shell reset, app removal, permission bypass, paid dependency or replacement
of personal dotfiles should be part of the default installation.

## Source and tests

The `dot_config` layout is retained from the initial chezmoi extraction.
Runtime paths assume Apple Silicon Homebrew and Fish. Use the bootstrap to
provision dependencies first. The configuration-only installer below is a
lower-level tool for selected files, not the fresh-machine entry point.

Run from this directory:

```sh
lua tests/mac-shortcuts.lua
python3 tests/config.py
python3 -m unittest discover -s tests -p 'test_*.py'
```

## Configuration installer (experimental)

Python 3.11+ is required for the TOML tests. The installer uses only the Python
standard library. It never downloads software, grants permissions, adds login
items, quits apps, or restarts a Herdr server. Installing an actively watched
OmniWM configuration can still change the live desktop immediately.

Start with read-only checks and a plan:

```sh
python3 setup.py doctor
python3 setup.py install --component herdr
```

Select only the components you want: `herdr`, `omniwm`, `hammerspoon`, and
`agent-run`. Repeat `--component` to select more than one. Add `--apply` to
write files. Existing files require the additional `--replace` flag, which
replaces the selected files completely, not a merge. Back up or review custom
Hammerspoon code first. The installer rejects symlinked paths rather than
following them into another dotfiles checkout.

Each installation prints a transaction ID. Original bytes and permissions
are saved beneath `~/.local/state/omarchy-mac/<id>/`. Recovery is preview-first:

```sh
python3 setup.py rollback TRANSACTION_ID
python3 setup.py rollback TRANSACTION_ID --apply
```

Rollback restores previous files and removes only unchanged files created by
that transaction. It refuses the whole operation if a managed file was edited
after installation, or a backup checksum fails. Backups and empty directories
remain. Interrupted writes can be recovered with the same transaction ID.
Do not run concurrent installations or edit managed files during apply/rollback.

### Activation and permissions

After reviewing the plan and installing the selected configuration:

- Herdr: `herdr server reload-config`. Do not stop the server to apply bindings.
- OmniWM: the app watches its settings file. Grant Accessibility in macOS
  settings yourself. Quit other window managers before running it.
- Hammerspoon: this prototype uses `~/.config/hammerspoon/init.lua`, not the
  default `~/.hammerspoon/init.lua`. Inspect `defaults read org.hammerspoon.Hammerspoon
  MJConfigFile` first. If you choose to switch configuration, set it with
  `defaults write org.hammerspoon.Hammerspoon MJConfigFile
  "$HOME/.config/hammerspoon/init.lua"`, then reload Hammerspoon. This preference
  is not managed or rolled back by the installer. Record its previous value.
- Choose login items manually. Command replaces many native shortcuts; use
  Command+Control+Escape to toggle the bridge's native-key passthrough.
- Disable conflicting macOS input-source and workspace shortcuts manually.
  Accessibility, microphone and any Thaw grants must be approved by the user.
- The configuration-only installer does not provision the Voxtype binary or
  model; the full bootstrap does.

Installer/bootstrap tests use temporary homes and mock package runners:
preview, install-versus-upgrade, unmanaged apps, active-app deferral, consent,
idempotence, restore, symlinks, edited-file protection, backup integrity and
interrupted-install recovery, checksum rejection and repeat-run provisioning.
No clean macOS account installation has been
tested. The originating Mac remains managed by chezmoi.

The download wrapper is tested with fixture archives for default installation,
preview, forwarded options, download failure and incomplete downloads. An
additional test installs every bundled configuration in an empty temporary
home, verifies bytes and permissions, repeats installation, then rolls back.
This does real filesystem work, but is not a fresh macOS account or machine.

### Testing without logging out

A separate standard account can be created in System Settings > Users & Groups
with administrator authentication. Non-GUI configuration tests can run as that
user without ending the current session. A GUI test needs a login session for
the test user, which Fast User Switching can provide without logging out the
original user. Accessibility and microphone grants must be approved separately.

Homebrew and /Applications remain shared between accounts. Running the full
bootstrap in another account may update shared software, and a Homebrew tree
owned by the original account may not be writable. Do not change its ownership
to force the test. Validate first-machine package provisioning in a clean macOS
VM or separate Mac instead. A temporary HOME is not an account-isolation test.

The one-command entry point downloads the main-branch source archive from
GitHub, uses authenticated GitHub CLI when available, and removes only its
temporary download directory on exit. `bash install.sh --preview` downloads
the source but does not provision anything. The direct `bootstrap.sh` preview
does not download. Piped installation reconnects stdin to the terminal for
interactive administrator prompts. Anonymous downloads require a public repo.

The shortcut suite checks 246 audited chords, dispatch, queues, native-key
passthrough, and the dictation overlay using inert OS mocks. It does not prove
physical keyboard input or real windows work on another Mac. The full matrix
is in `tools/mac-shortcuts.tsv`: 121 mapped, 60 equivalents, 36 native,
23 unavailable, and 6 hardware-unverified.

## Before public use

1. Choose a name and license, and audit upstream attribution/licensing.
2. Add user-selectable app/package profiles beyond the complete default stack.
3. Harden the experimental installer with configuration merging, concurrent
   operation protection and a clean-account installation/rollback test.
4. Validate dependency/version checks and permission onboarding on a real
   fresh account. Extend automatic rollback to activation preferences.
5. Test a clean macOS account, multiple displays, restart, uninstall, and
   supported Intel/macOS versions before claiming support.
6. Add synthetic screenshots and a reproducible visual acceptance checklist.

## Remaining Omarchy differences

The native macOS menu bar has no configured centered clock/calendar here.
OmniWM 0.7.6 supplies workspace chips, not its unreleased full-width widget
shell. Evaluate a separate clock/calendar or a future stable OmniWM shell
without obscuring application menus, iStat, or Thaw.

Other gaps include Linux bar panels, arbitrary window transparency,
cross-workspace floating pinning, indexed window-group selection, webcam
overlay controls, and keyboard workspace-slide animation. Some hardware keys
need physical testing. Native Command+T/W are intentional differences.

## Attribution

Herdr's preset follows `omacom/omarchy` config/herdr/config.toml at commit
246f33a2fef66411c990860d88e0823ae83987fc. The shortcut fixture audits that
Omarchy revision plus the originating user's Hyprland overrides. These are
not a promise of exact upstream defaults. Personal service URLs have been
removed from this snapshot. Upstream applications retain their own licenses.
