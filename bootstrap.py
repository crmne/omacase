#!/usr/bin/env python3
"""Complete rerunnable provisioning. Invoke through bootstrap.sh on a fresh Mac."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import platform
import plistlib
import pwd
import re
import shutil
import subprocess
import urllib.request
import uuid

import setup

FORMULAE = (
    "fish", "starship", "eza", "zoxide", "fzf", "mise", "direnv", "bat",
    "ripgrep", "fd", "jq", "git", "git-lfs", "gh", "neovim", "tmux",
    "lazygit", "lazydocker", "btop", "lua", "herdr", "docker", "colima",
)
CASKS = {
    "ghostty": "Ghostty.app", "hammerspoon": "Hammerspoon.app",
    "omniwm": "OmniWM.app", "raycast": "Raycast.app",
    "google-chrome": "Google Chrome.app", "obsidian": "Obsidian.app",
    "signal": "Signal.app", "font-jetbrains-mono-nerd-font": None,
}
VOX_VERSION = "1.1.1"
VOX_SHA256 = "4886b3dbcd3a2b96ddc5087f2b477c45254a7d407acaf114b6bbdbbda6efde0e"
BREW = "/opt/homebrew/bin/brew"


def run(argv, check=True, capture=False):
    print("+", " ".join(map(str, argv)), flush=True)
    env = dict(os.environ, HOMEBREW_NO_INSTALL_CLEANUP="1", HOMEBREW_NO_AUTO_UPDATE="1")
    return subprocess.run(list(map(str, argv)), check=check, text=True,
                          capture_output=capture, env=env)


def is_running(app):
    # Exact app bundle executable path, not a loose name matching other apps.
    return run(["/usr/bin/pgrep", "-f", re.escape(f"/Applications/{app}/Contents/MacOS/")],
               check=False, capture=True).returncode == 0


def ensure_package(name, cask=False, app=None, backup=None):
    kind = "--cask" if cask else "--formula"
    installed = run([BREW, "list", kind, name], check=False, capture=True).returncode == 0
    if app and is_running(app):
        print(f"DEFERRED: {name} is running. Close it and rerun to upgrade safely.")
        return "deferred"
    if installed:
        command = [BREW, "upgrade", kind]
        if cask:
            command.append("--greedy")
        run(command + [name])
        return "upgraded-or-current"
    command = [BREW, "install", kind]
    if cask and not app:
        command.append("--adopt")
    # A manually installed older version is not identical, so --adopt alone
    # cannot handle it. Preserve the exact app bundle before --force replaces it.
    existing = Path("/Applications") / app if app else None
    if existing and existing.exists():
        if existing.is_symlink() or not existing.is_dir():
            raise ValueError(f"Unusual app path needs manual reconciliation: {existing}")
        destination = backup / app
        run(["/usr/bin/ditto", existing, destination])
        command.append("--force")
    run(command + [name])
    return "installed"


def provision_voxtype(home, backup):
    target = setup.checked(home, ".local/bin/voxtype")
    if target.exists():
        version = run([target, "--version"], capture=True).stdout
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
        if match and tuple(map(int, match.groups())) >= (1, 1, 1):
            print("Voxtype already meets the tested version; not downgrading.")
            return target
    url = f"https://github.com/peteonrails/voxtype/releases/download/v{VOX_VERSION}/voxtype-{VOX_VERSION}-macos-universal"
    print(f"Downloading pinned Voxtype {VOX_VERSION} from its official release.")
    with urllib.request.urlopen(url, timeout=120) as response:
        data = response.read()
    if setup.digest(data) != VOX_SHA256:
        raise ValueError("Voxtype checksum mismatch; refusing to install")
    if target.exists():
        shutil.copy2(target, backup / "voxtype.previous")
    setup.atomic_write(target, data, 0o755)
    return target


def preference_snapshot(backup):
    previous = run(["/usr/bin/defaults", "read", "org.hammerspoon.Hammerspoon", "MJConfigFile"],
                   check=False, capture=True)
    shell = run(["/usr/bin/dscl", ".", "-read", f"/Users/{pwd.getpwuid(os.getuid()).pw_name}", "UserShell"],
                check=False, capture=True)
    setup.atomic_write(backup / "activation-before.json", json.dumps({
        "hammerspoon_config": previous.stdout.strip() if previous.returncode == 0 else None,
        "login_shell": shell.stdout.strip(),
    }, indent=2).encode())


def disable_conflicting_shortcuts(backup):
    result = run(["/usr/bin/defaults", "export", "com.apple.symbolichotkeys", "-"],
                 check=False, capture=True)
    if result.returncode != 0:
        print("MANUAL: disable Control+Space input-source and conflicting workspace shortcuts in System Settings.")
        return
    original = result.stdout.encode()
    prefs = plistlib.loads(original)
    shortcuts = prefs.setdefault("AppleSymbolicHotKeys", {})
    changed = False
    # Missing entries inherit enabled system defaults, not disabled bindings.
    # 28..31: screen/selection to file/clipboard. 184: Screenshot controls.
    for key in ["28", "29", "30", "31", "184", "60"] + [str(n) for n in range(118, 127)]:
        entry = shortcuts.setdefault(key, {})
        if entry.get("enabled") is not False:
            entry["enabled"] = False
            changed = True
    if changed:
        setup.atomic_write(backup / "symbolichotkeys-before.plist", original)
        updated = backup / "symbolichotkeys-after.plist"
        setup.atomic_write(updated, plistlib.dumps(prefs))
        run(["/usr/bin/defaults", "import", "com.apple.symbolichotkeys", updated])
        refresh = Path("/System/Library/PrivateFrameworks/SystemAdministration.framework/Resources/activateSettings")
        if refresh.exists():
            run([refresh, "-u"], check=False, capture=True)
        print("Screenshot/input-source/workspace conflicts disabled. If still active, log out and back in.")


def activate(home, backup, login_shell=True):
    preference_snapshot(backup)
    disable_conflicting_shortcuts(backup)
    run(["/usr/bin/defaults", "write", "org.hammerspoon.Hammerspoon", "MJConfigFile",
         str(home / ".config/hammerspoon/init.lua")])
    if login_shell:
        fish = "/opt/homebrew/bin/fish"
        if fish not in Path("/etc/shells").read_text().splitlines():
            # Constant path only. macOS may request the user's administrator password.
            run(["/usr/bin/sudo", "/bin/sh", "-c", "printf '\\n/opt/homebrew/bin/fish\\n' >> /etc/shells"])
        current = run(["/usr/bin/dscl", ".", "-read", f"/Users/{pwd.getpwuid(os.getuid()).pw_name}", "UserShell"], capture=True).stdout
        if fish not in current:
            run(["/usr/bin/chsh", "-s", fish])
    # Idempotent login entries. Does not grant Accessibility or Microphone.
    for app in ("OmniWM", "Hammerspoon", "Thaw", "Raycast"):
        script = f'''tell application "System Events"
if not (exists login item "{app}") then
make login item at end with properties {{name:"{app}",path:"/Applications/{app}.app",hidden:false}}
end if
end tell'''
        run(["/usr/bin/osascript", "-e", script])
    conflicts = []
    for process in ("AeroSpace", "yabai", "Rectangle", "Rectangle Pro"):
        if run(["/usr/bin/pgrep", "-x", process], check=False, capture=True).returncode == 0:
            conflicts.append(process)
    if conflicts:
        print("DEFERRED: quit competing window managers before opening OmniWM:", ", ".join(conflicts))
    else:
        run(["/usr/bin/open", "-a", "OmniWM"])
    run(["/usr/bin/open", "-a", "Hammerspoon"])
    run(["/usr/bin/open", "-a", "Thaw"])
    run(["/usr/bin/open", "-a", "Raycast"])
    if run(["/opt/homebrew/bin/docker", "info"], check=False, capture=True).returncode != 0:
        run(["/opt/homebrew/bin/colima", "start"])
    # Never stop or restart persistent Herdr sessions.
    status = run(["/opt/homebrew/bin/herdr", "status", "server", "--json"], check=False, capture=True)
    if status.returncode == 0 and json.loads(status.stdout).get("running"):
        run(["/opt/homebrew/bin/herdr", "server", "reload-config"])
    print("If Hammerspoon was already open, reload its config from its menu after reviewing the changes.")
    print("Grant Accessibility to OmniWM/Hammerspoon, and Microphone to Voxtype when prompted.")
    print("Thaw also needs Accessibility and macOS 27 Menu Bar Layout Access.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-activate", action="store_true")
    parser.add_argument("--no-login-shell", action="store_true")
    args = parser.parse_args()
    if not args.apply:
        print("Formulae:", ", ".join(FORMULAE))
        print("Casks:", ", ".join(CASKS), "+ OS-appropriate Thaw")
        print("Also: verified Voxtype binary + small.en model; all bundled configuration.")
        print("Preview only. Use bootstrap.sh --apply to provision.")
        return 0
    if platform.system() != "Darwin" or platform.machine() != "arm64" or os.geteuid() == 0:
        raise ValueError("Run as a regular user on Apple Silicon macOS 26+")
    major = int(platform.mac_ver()[0].split(".")[0])
    if major < 26:
        raise ValueError("OmniWM requires macOS 26+")
    home = Path.home().resolve()
    # Fail on path conflicts before package or config changes.
    setup.plan(home, list(setup.FILES))
    state = setup.checked(home, ".local/state/omarchy-mac/bootstrap.lock")
    state.parent.mkdir(parents=True, exist_ok=True)
    with state.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        backup = state.parent / ("bootstrap-" + uuid.uuid4().hex)
        backup.mkdir(mode=0o700)
        print(f"Bootstrap recovery files: {backup}")
        report = {}
        errors = []
        packages = [(name, False, None) for name in FORMULAE]
        packages += [(name, True, app) for name, app in CASKS.items()]
        packages.append(("thaw@beta" if major >= 27 else "thaw", True, "Thaw.app"))
        for name, cask, app in packages:
            try:
                report[name] = ensure_package(name, cask, app, backup)
            except (subprocess.CalledProcessError, OSError, ValueError) as error:
                report[name] = "failed"
                errors.append(f"{name}: {error}")
        setup.atomic_write(backup / "packages.json", json.dumps(report, indent=2).encode())
        if errors:
            print("Package errors (successful steps are reusable on rerun):\n" + "\n".join(errors))
            return 1
        vox = provision_voxtype(home, backup)
        transaction = setup.install(home, setup.plan(home, list(setup.FILES)), replace=True)
        setup.atomic_write(backup / "config-transaction.json", json.dumps(transaction).encode())
        run([vox, "setup", "--download", "--model", "small.en", "--no-post-install"])
        if not args.no_activate:
            # Avoid rewriting a live audio app bundle.
            if not is_running("Voxtype.app"):
                if Path("/Applications/Voxtype.app").exists():
                    run(["/usr/bin/ditto", "/Applications/Voxtype.app", backup / "Voxtype.app"])
                run([vox, "setup", "app-bundle"])
                run(["/usr/bin/open", "-a", "Voxtype"])
            activate(home, backup, not args.no_login_shell)
        print("Provisioning completed. Deferred app upgrades:", [k for k, v in report.items() if v == "deferred"])
        print("No agent conversations or credentials were configured. No existing packages were removed.")
        return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print(f"STOP: {error}. Correct the issue and rerun; completed package steps are retained.")
        raise SystemExit(1)
