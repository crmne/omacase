"""Run: python3 -m unittest discover -s tests -p 'test_*.py'."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("setup", Path(__file__).resolve().parents[1] / "setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="omarchy-mac-test-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    def test_preview_makes_no_files(self):
        self.assertEqual(setup.plan(self.home, ["herdr"])[0][3], "create")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_create_idempotence_and_rollback(self):
        entries = setup.plan(self.home, ["herdr", "agent-run"])
        transaction = setup.install(self.home, entries)
        self.assertTrue(all(e[3] == "unchanged" for e in setup.plan(self.home, ["herdr", "agent-run"])))
        self.assertIsNone(setup.install(self.home, setup.plan(self.home, ["herdr"])))
        changes = setup.rollback(self.home, transaction)
        self.assertEqual(len(changes), 2)
        self.assertTrue(changes[0][0].exists())
        setup.rollback(self.home, transaction, apply=True)
        self.assertFalse(changes[0][0].exists())
        self.assertEqual(setup.rollback(self.home, transaction, apply=True), [])

    def test_replace_requires_consent_restores_bytes_and_mode(self):
        target = self.home / ".config/herdr/config.toml"
        setup.atomic_write(target, b"# mine\n", 0o640)
        entries = setup.plan(self.home, ["herdr"])
        with self.assertRaises(ValueError):
            setup.install(self.home, entries)
        self.assertFalse((self.home / ".local").exists())
        transaction = setup.install(self.home, entries, replace=True)
        setup.rollback(self.home, transaction, apply=True)
        self.assertEqual(target.read_bytes(), b"# mine\n")
        self.assertEqual(target.stat().st_mode & 0o777, 0o640)

    def test_modified_file_blocks_entire_rollback(self):
        transaction = setup.install(self.home, setup.plan(self.home, ["herdr", "agent-run"]))
        target = self.home / ".local/bin/agent-run"
        target.write_bytes(b"user edit")
        with self.assertRaises(ValueError):
            setup.rollback(self.home, transaction, apply=True)
        self.assertTrue((self.home / ".config/herdr/config.toml").exists())
        self.assertEqual(target.read_bytes(), b"user edit")

    def test_symlink_file_and_ancestor_rejected(self):
        outside = self.home / "outside"
        outside.mkdir()
        (self.home / ".config").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            setup.plan(self.home, ["herdr"])
        (self.home / ".config").unlink()
        target = self.home / ".local/bin/agent-run"
        target.parent.mkdir(parents=True)
        target.symlink_to(outside / "missing")
        with self.assertRaises(ValueError):
            setup.plan(self.home, ["agent-run"])

    def test_tampered_backup_rejected(self):
        target = self.home / ".config/herdr/config.toml"
        setup.atomic_write(target, b"old")
        transaction = setup.install(self.home, setup.plan(self.home, ["herdr"]), replace=True)
        backup = self.home / f".local/state/omarchy-mac/{transaction}/0.bak"
        backup.write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            setup.rollback(self.home, transaction, apply=True)

    def test_interrupted_install_recoverable(self):
        original_write = setup.atomic_write

        def fail_second(path, data, mode=0o600):
            if path == self.home / ".local/bin/agent-run":
                raise OSError("simulated interruption")
            original_write(path, data, mode)

        with patch.object(setup, "atomic_write", side_effect=fail_second):
            with self.assertRaises(OSError):
                setup.install(self.home, setup.plan(self.home, ["herdr", "agent-run"]))
        transaction = next((self.home / ".local/state/omarchy-mac").iterdir()).name
        setup.rollback(self.home, transaction, apply=True)
        self.assertFalse((self.home / ".config/herdr/config.toml").exists())

    def test_transaction_path_traversal_rejected(self):
        with self.assertRaises(ValueError):
            setup.rollback(self.home, "../../elsewhere")


if __name__ == "__main__":
    unittest.main()
