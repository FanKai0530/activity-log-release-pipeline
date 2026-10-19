"""Exercise the exact archive downloaded from the build job."""

import hashlib
import os
from pathlib import Path
import stat
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
        test_env = os.environ.get("TEST_ENV")
        self.assertIn(test_env, {"staging", "prod"})
        with tempfile.TemporaryDirectory() as directory:
            with ZipFile(ARTIFACT) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"README.md", "scripts/update_readme.py", "VERSION"},
                )
                archive.extractall(directory)
                if test_env == "prod":
                    self.assertIsNone(archive.testzip(), "Production bundle has a corrupt member")
                    self.assertTrue(
                        all(not (member.flag_bits & 1) for member in archive.infolist()),
                        "Production bundle must not contain encrypted members",
                    )
                    self.assertTrue(
                        all(not stat.S_ISLNK(member.external_attr >> 16) for member in archive.infolist()),
                        "Production bundle must not contain symbolic links",
                    )
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
            if test_env == "staging":
                self.assertIn("Activity markers are valid", result.stdout)
            else:
                self.assertRegex(
                    (extracted / "VERSION").read_text(encoding="utf-8").strip(),
                    r"^\d+\.\d+\.\d+$",
                    "Production requires a final semantic version",
                )


if __name__ == "__main__":
    unittest.main()
