#!/usr/bin/env python3
"""Preview-first, local configuration installer. Never downloads or stops apps."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import tempfile
import uuid

ROOT = Path(__file__).resolve().parent
FILES = {
    "shell": {
        "dot_config/fish/conf.d/00-omacase.fish": ".config/fish/conf.d/00-omacase.fish",
        "dot_config/fish/conf.d/zz-omarchy-mac.fish": ".config/fish/conf.d/zz-omarchy-mac.fish",
        "dot_config/omarchy-mac/starship.toml": ".config/omarchy-mac/starship.toml",
    },
    "ghostty": {"dot_config/ghostty/config": ".config/ghostty/config"},
    "voxtype": {"dot_config/voxtype/config.toml": ".config/voxtype/config.toml"},
    "herdr": {"dot_config/herdr/config.toml": ".config/herdr/config.toml"},
    "omniwm": {"dot_config/omniwm/settings.toml": ".config/omniwm/settings.toml"},
    "hammerspoon": {
        f"dot_config/hammerspoon/{name}": f".config/hammerspoon/{name}"
        for name in ("init.lua", "bindings.lua", "omarchy.lua", "voxtype-osd.lua")
    },
    "agent-run": {"dot_local/bin/executable_agent-run": ".local/bin/agent-run"},
}
TARGETS = {target for files in FILES.values() for target in files.values()}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def checked(home, relative):
    """Reject symlinked ancestors as well as symlinked destination files."""
    path = home
    rel = Path(relative)
    if rel.is_absolute() or ".." in rel.parts:
        raise ValueError("Unsafe relative path")
    for part in rel.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"Refusing symlink: {path}")
    if path.exists() and not path.is_file():
        raise ValueError(f"Not a regular file: {path}")
    return path


def atomic_write(path, data, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".omarchy-mac-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def plan(home, components, source=ROOT):
    result = []
    for component in components:
        for src, relative in FILES[component].items():
            target = checked(home, relative)
            data = (source / src).read_bytes()
            previous = target.read_bytes() if target.exists() else None
            mode = 0o755 if component == "agent-run" else (
                stat.S_IMODE(target.stat().st_mode) if previous is not None else 0o600)
            same = previous == data and stat.S_IMODE(target.stat().st_mode) == mode
            result.append((relative, data, mode, "unchanged" if same else
                           "replace" if previous is not None else "create"))
    return result


def install(home, entries, replace=False):
    changed = [entry for entry in entries if entry[3] != "unchanged"]
    if not changed:
        return None
    # Recheck the complete plan before writing anything.
    for relative, data, mode, action in changed:
        target = checked(home, relative)
        if target.exists() and not replace:
            raise ValueError(f"Existing file needs --replace: {target}")
    transaction = uuid.uuid4().hex
    manifest_path = checked(home, f".local/state/omarchy-mac/{transaction}/manifest.json")
    records = []
    for index, (relative, data, mode, action) in enumerate(changed):
        target = checked(home, relative)
        old = target.read_bytes() if target.exists() else None
        record = {"target": relative, "installed_sha256": digest(data),
                  "installed_mode": mode, "existed": old is not None}
        if old is not None:
            record.update(old_sha256=digest(old), old_mode=stat.S_IMODE(target.stat().st_mode))
            atomic_write(manifest_path.parent / f"{index}.bak", old)
        records.append(record)
    manifest = {"version": 1, "home": str(home), "status": "prepared", "files": records}
    atomic_write(manifest_path, json.dumps(manifest, indent=2).encode())
    print(f"Recovery transaction: {transaction}")
    # Journal exists before mutation, including if a write is interrupted.
    for relative, data, mode, _ in changed:
        atomic_write(checked(home, relative), data, mode)
    manifest["status"] = "installed"
    atomic_write(manifest_path, json.dumps(manifest, indent=2).encode())
    return transaction


def rollback(home, transaction, apply=False):
    if not re.fullmatch(r"[0-9a-f]{32}", transaction):
        raise ValueError("Use the exact transaction ID printed by install")
    path = checked(home, f".local/state/omarchy-mac/{transaction}/manifest.json")
    manifest = json.loads(path.read_text())
    if manifest.get("version") != 1 or manifest.get("home") != str(home):
        raise ValueError("Backup does not belong to this home/schema")
    if manifest["status"] == "restored":
        return []
    restores = []
    seen = set()
    for index, record in enumerate(manifest["files"]):
        relative = record["target"]
        if relative not in TARGETS or relative in seen:
            raise ValueError("Unknown/duplicate backup target")
        seen.add(relative)
        target = checked(home, relative)
        current = target.read_bytes() if target.exists() else None
        old = None
        if record["existed"]:
            backup = checked(home, str(path.parent.relative_to(home) / f"{index}.bak"))
            old = backup.read_bytes()
            if digest(old) != record["old_sha256"]:
                raise ValueError(f"Backup checksum failed: {relative}")
        # Already restored or not yet written after an interrupted install.
        if current == old and (old is None or stat.S_IMODE(target.stat().st_mode) == record["old_mode"]):
            continue
        if current is None or digest(current) != record["installed_sha256"] or stat.S_IMODE(target.stat().st_mode) != record["installed_mode"]:
            raise ValueError(f"Changed since installation; preserve and reconcile manually: {relative}")
        restores.append((target, old, record.get("old_mode", 0o600)))
    if apply:
        for target, old, mode in restores:
            if old is None:
                target.unlink()  # Only an exact, unchanged installed file.
            else:
                atomic_write(target, old, mode)
        manifest["status"] = "restored"
        atomic_write(path, json.dumps(manifest, indent=2).encode())
    return restores


def doctor():
    ok = platform.system() == "Darwin" and platform.machine() == "arm64"
    print(f"Platform: {platform.system()} {platform.machine()} (Apple Silicon macOS prototype)")
    for app in ("OmniWM", "Hammerspoon", "Ghostty"):
        exists = Path(f"/Applications/{app}.app").is_dir()
        print(f"{'OK' if exists else 'MISSING'}: {app}")
        ok &= exists
    for binary in ("/opt/homebrew/bin/omniwmctl", "/opt/homebrew/bin/fish"):
        exists = os.access(binary, os.X_OK)
        print(f"{'OK' if exists else 'MISSING'}: {binary}")
        ok &= exists
    for binary in ("herdr", "lua", "hs"):
        print(f"{'OK' if shutil.which(binary) else 'MISSING'}: {binary}")
        if binary == "herdr":
            ok &= bool(shutil.which(binary))
    vox = Path.home() / ".local/bin/voxtype"
    print(f"{'OK' if os.access(vox, os.X_OK) else 'MISSING (dictation)'}: {vox}")
    print("UNVERIFIED: dependency versions, microphone model and live accessibility grants.")
    print("MANUAL: Accessibility for OmniWM/Hammerspoon; microphone for Voxtype.")
    print("MANUAL: disable competing window managers and macOS workspace hotkeys.")
    print("MANUAL: Hammerspoon must load ~/.config/hammerspoon/init.lua.")
    print("No grants, login items, app processes or system settings were changed.")
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor")
    install_parser = sub.add_parser("install")
    install_parser.add_argument("--component", choices=FILES, action="append", required=True)
    install_parser.add_argument("--apply", action="store_true")
    install_parser.add_argument("--replace", action="store_true", help="explicit consent to replace selected existing files")
    restore_parser = sub.add_parser("rollback")
    restore_parser.add_argument("transaction")
    restore_parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    home = Path.home().resolve()
    try:
        if args.command == "doctor":
            return 0 if doctor() else 1
        if args.command == "rollback":
            changes = rollback(home, args.transaction, args.apply)
            for target, old, _ in changes:
                print(f"{'restore' if old is not None else 'remove installed file'}: {target}")
            print("Restored; backups retained." if args.apply else "Preview only. Add --apply to restore.")
        else:
            entries = plan(home, list(dict.fromkeys(args.component)))
            for relative, _, _, action in entries:
                print(f"{action}: {home / relative}")
            if args.apply:
                if platform.system() != "Darwin" or platform.machine() != "arm64":
                    raise ValueError("Installation currently supports Apple Silicon macOS only")
                install(home, entries, args.replace)
                print("Files installed. No apps restarted. Follow README activation steps.")
            else:
                print("Preview only. Add --apply; existing files also require --replace.")
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"STOP: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
