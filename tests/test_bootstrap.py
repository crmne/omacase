"""Provisioning tests use fake command runners, never Homebrew or live apps."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import plistlib
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap


def completed(code=0, out=""):
    return subprocess.CompletedProcess([], code, stdout=out, stderr="")


class BootstrapTests(unittest.TestCase):
    def test_shortcut_changes_preserve_other_preferences(self):
        prefs = {"other": "keep", "AppleSymbolicHotKeys": {
            "60": {"enabled": True, "value": {"type": "standard"}},
            "61": {"enabled": True}, "118": {"enabled": True}}}
        with tempfile.TemporaryDirectory() as directory:
            backup = Path(directory)
            with patch.object(bootstrap, "run", side_effect=[completed(out=plistlib.dumps(prefs).decode()), completed(), completed()]):
                bootstrap.disable_conflicting_shortcuts(backup)
            updated = plistlib.loads((backup / "symbolichotkeys-after.plist").read_bytes())
            self.assertFalse(updated["AppleSymbolicHotKeys"]["60"]["enabled"])
            for key in ("28", "29", "30", "31", "184", "119"):
                self.assertIs(updated["AppleSymbolicHotKeys"][key]["enabled"], False,
                              "Absent system defaults must be explicitly disabled")
            self.assertTrue(updated["AppleSymbolicHotKeys"]["61"]["enabled"])
            self.assertEqual(updated["other"], "keep")
            self.assertEqual(plistlib.loads((backup / "symbolichotkeys-before.plist").read_bytes()), prefs)

    def test_missing_package_installs(self):
        with patch.object(bootstrap, "run", side_effect=[completed(1), completed()]) as run:
            bootstrap.ensure_package("fish")
            self.assertEqual(run.call_args.args[0], [bootstrap.BREW, "install", "--formula", "fish"])

    def test_existing_package_upgrades_not_reinstalls(self):
        with patch.object(bootstrap, "run", side_effect=[completed(), completed()]) as run:
            bootstrap.ensure_package("fish")
            self.assertEqual(run.call_args.args[0], [bootstrap.BREW, "upgrade", "--formula", "fish"])

    def test_cask_upgrades_auto_updating_apps(self):
        with patch.object(bootstrap, "run", return_value=completed()) as run:
            with patch.object(bootstrap, "is_running", return_value=False):
                bootstrap.ensure_package("ghostty", True, "Ghostty.app")
            self.assertEqual(run.call_args.args[0], [bootstrap.BREW, "upgrade", "--cask", "--greedy", "ghostty"])

    def test_active_app_never_killed_or_upgraded(self):
        with patch.object(bootstrap, "run", return_value=completed()) as run:
            with patch.object(bootstrap, "is_running", return_value=True):
                self.assertEqual(bootstrap.ensure_package("ghostty", True, "Ghostty.app"), "deferred")
            self.assertEqual(run.call_count, 1)

    def test_unmanaged_app_backed_up_before_replacement(self):
        with patch.object(bootstrap, "run", side_effect=[completed(1), completed(), completed()]) as run:
            with patch.object(bootstrap, "is_running", return_value=False), \
                 patch.object(Path, "exists", return_value=True), \
                 patch.object(Path, "is_symlink", return_value=False), \
                 patch.object(Path, "is_dir", return_value=True):
                bootstrap.ensure_package("ghostty", True, "Ghostty.app", Path("/backup"))
            self.assertEqual(run.call_args_list[1].args[0][0], "/usr/bin/ditto")
            self.assertIn("--force", run.call_args_list[2].args[0])

    def test_voxtype_checksum_mismatch_never_installed(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.object(bootstrap.urllib.request, "urlopen") as request:
                request.return_value.__enter__.return_value.read.return_value = b"bad payload"
                with self.assertRaisesRegex(ValueError, "checksum"):
                    bootstrap.provision_voxtype(home, home)
            self.assertFalse((home / ".local/bin/voxtype").exists())

    def test_clean_then_used_home_provisioning_is_repeatable(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.object(Path, "home", return_value=home), \
                 patch.object(bootstrap.platform, "system", return_value="Darwin"), \
                 patch.object(bootstrap.platform, "machine", return_value="arm64"), \
                 patch.object(bootstrap.platform, "mac_ver", return_value=("27.0", (), "")), \
                 patch.object(bootstrap.os, "geteuid", return_value=501), \
                 patch.object(sys, "argv", ["bootstrap.py", "--apply", "--no-activate"]), \
                 patch.object(bootstrap, "ensure_package", return_value="upgraded-or-current"), \
                 patch.object(bootstrap, "provision_voxtype", return_value=home / ".local/bin/voxtype"), \
                 patch.object(bootstrap, "provision_omafish"), \
                 patch.object(bootstrap, "run", return_value=completed()):
                self.assertEqual(bootstrap.main(), 0)
                content = (home / ".config/herdr/config.toml").read_bytes()
                self.assertEqual(bootstrap.main(), 0)
                self.assertEqual((home / ".config/herdr/config.toml").read_bytes(), content)
                self.assertTrue((home / ".config/fish/conf.d/zz-omarchy-mac.fish").exists())

    def test_preview_does_not_execute_commands(self):
        with patch.object(sys, "argv", ["bootstrap.py"]), patch.object(bootstrap, "run") as run:
            self.assertEqual(bootstrap.main(), 0)
            run.assert_not_called()

    def test_omafish_installs_and_updates_through_fisher(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            with patch.object(bootstrap, "run", side_effect=[completed(), completed(out="crmne/omafish\n")]) as run:
                bootstrap.provision_omafish(home, home)
            self.assertEqual(run.call_args_list[0].args[0][-1], "fisher install crmne/omafish")

    def test_omafish_missing_registration_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(bootstrap, "run", return_value=completed()):
                with self.assertRaisesRegex(ValueError, "not registered"):
                    bootstrap.provision_omafish(Path(directory), Path(directory))


if __name__ == "__main__":
    unittest.main()
