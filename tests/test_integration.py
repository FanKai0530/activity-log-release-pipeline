"""Exercise the exact archive downloaded from the build job."""

import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "release-bundle.zip"
MANIFEST = ROOT / "release-bundle.sha256"
VERSION = ROOT / "release-version.txt"


class ReleaseBundleTests(unittest.TestCase):
    def test_downloaded_bundle_checksum(self):
        self.assertTrue(ARTIFACT.is_file(), "Build artifact was not downloaded")
        digest, filename = MANIFEST.read_text(encoding="utf-8").strip().split(maxsplit=1)
        self.assertEqual(filename, "release-bundle.zip")
        self.assertEqual(hashlib.sha256(ARTIFACT.read_bytes()).hexdigest(), digest)

    def test_downloaded_bundle_runs_in_isolation(self):
        self.assertIn(os.environ.get("TEST_ENV"), {"staging", "prod"})
        with tempfile.TemporaryDirectory() as directory:
            with ZipFile(ARTIFACT) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"README.md", "scripts/update_readme.py", "VERSION"},
                )
                archive.extractall(directory)
            extracted = Path(directory)
            self.assertEqual(
                (extracted / "VERSION").read_text(encoding="utf-8"),
                VERSION.read_text(encoding="utf-8"),
            )
            result = subprocess.run(
                [sys.executable, "scripts/update_readme.py", "--repository", "FanKai0530/activity-log-release-pipeline", "--check"],
                cwd=extracted,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Activity markers are valid", result.stdout)


if __name__ == "__main__":
    unittest.main()
