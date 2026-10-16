"""Exercise the download wrapper without installing packages or touching desktop state."""
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import setup


class EntrypointTests(unittest.TestCase):
    def invoke(self, *args, incomplete=False, fail=False):
        with tempfile.TemporaryDirectory(prefix="omacase-entry-test-") as folder:
            directory = Path(folder)
            archive = directory / "fixture.tar.gz"
            with tarfile.open(archive, "w:gz") as tar:
                files = {"bootstrap.sh": b'printf "BOOTSTRAP %s\\n" "$@"\n'}
                if not incomplete:
                    files["bootstrap.py"] = b"# fixture\n"
                for name, data in files.items():
                    info = tarfile.TarInfo("snapshot/" + name)
                    info.size = len(data)
                    tar.addfile(info, io.BytesIO(data))
            mock = directory / "gh"
            mock.write_text('#!/bin/bash\nif [[ "$1" == auth ]]; then exit 0; fi\n'
                            + ('exit 1\n' if fail else 'cat "$TEST_ARCHIVE"\n'))
            mock.chmod(0o755)
            env = dict(os.environ, PATH=f"{directory}:/usr/bin:/bin", TMPDIR=folder,
                       TEST_ARCHIVE=str(archive))
            result = subprocess.run(["/bin/bash", str(ROOT / "install.sh"), *args],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(list(directory.glob("omacase-install.*")), [])
            return result

    def test_default_applies_and_forwards_options(self):
        result = self.invoke("--no-activate")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("BOOTSTRAP --apply", result.stdout)
        self.assertIn("BOOTSTRAP --no-activate", result.stdout)

    def test_preview_never_applies(self):
        result = self.invoke("--no-activate", "--preview")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("--apply", result.stdout)
        self.assertIn("--no-activate", result.stdout)

    def test_failed_download_does_not_bootstrap(self):
        result = self.invoke(fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("BOOTSTRAP", result.stdout)

    def test_incomplete_archive_does_not_bootstrap(self):
        result = self.invoke(incomplete=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Incomplete", result.stderr)

    def test_invalid_option_rejected(self):
        self.assertEqual(self.invoke("--bogus").returncode, 2)

    def test_all_configs_in_empty_home_repeat_and_rollback(self):
        # Real writes and rollback, no package mocks. This is NOT a new OS account.
        with tempfile.TemporaryDirectory(prefix="omacase-clean-home-") as directory:
            home = Path(directory).resolve()
            entries = setup.plan(home, list(setup.FILES))
            self.assertTrue(all(entry[3] == "create" for entry in entries))
            transaction = setup.install(home, entries)
            for relative, data, mode, _ in entries:
                target = home / relative
                self.assertEqual(target.read_bytes(), data)
                self.assertEqual(target.stat().st_mode & 0o777, mode)
            self.assertIsNone(setup.install(home, setup.plan(home, list(setup.FILES))))
            setup.rollback(home, transaction, apply=True)
            self.assertTrue(all(not (home / entry[0]).exists() for entry in entries))


if __name__ == "__main__":
    unittest.main()
