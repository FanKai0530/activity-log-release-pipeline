import unittest
from pathlib import Path
import os
import tempfile
from unittest.mock import patch
from zipfile import ZipFile

from scripts.build_release import main, next_version


class VersionTests(unittest.TestCase):
    def test_first_version(self):
        self.assertEqual(next_version([]), "1.0.0")

    def test_highest_version_across_environments(self):
        tags = ["dev-v1.0.8", "staging-v1.0.7", "prod-v1.0.6", "unrelated-v99.0.0"]
        self.assertEqual(next_version(tags), "1.0.9")

    def test_new_minor_and_major_versions(self):
        self.assertEqual(next_version(["prod-v1.9.99", "dev-v2.0.0"]), "2.0.1")

    def test_ignores_malformed_tags(self):
        self.assertEqual(next_version(["dev-v1.0.x", "prod-v1.2.3-extra"]), "1.0.0")

    def test_build_packages_exact_version_and_files(self):
        with tempfile.TemporaryDirectory() as directory:
            previous = Path.cwd()
            try:
                os.chdir(directory)
                Path("scripts").mkdir()
                Path("README.md").write_text("example", encoding="utf-8")
                Path("scripts/update_readme.py").write_text("print('ok')", encoding="utf-8")
                with patch("sys.argv", ["build_release.py"]), patch(
                    "scripts.build_release.subprocess.check_output", return_value="prod-v1.0.3\n"
                ):
                    main()
                self.assertEqual(Path("release-version.txt").read_text(encoding="utf-8"), "1.0.4\n")
                with ZipFile("release-bundle.zip") as archive:
                    self.assertEqual(set(archive.namelist()), {"README.md", "scripts/update_readme.py", "VERSION"})
                    self.assertEqual(archive.read("VERSION"), b"1.0.4\n")
            finally:
                os.chdir(previous)


if __name__ == "__main__":
    unittest.main()
