import unittest

from scripts.build_release import next_version


class VersionTests(unittest.TestCase):
    def test_initial_and_patch_bump(self):
        self.assertEqual(next_version([]), "1.0.0")
        self.assertEqual(next_version(["prod-v1.0.2", "dev-v1.0.3"]), "1.0.4")
        self.assertEqual(next_version(["dev-v1.0.0", "staging-v1.0.0"]), "1.0.1")

    def test_ignores_invalid_tags_and_uses_highest_semver(self):
        self.assertEqual(next_version(["prod-v1.2.8", "prod-v1.10.1", "prod-v1.2.bad"]), "1.10.2")


if __name__ == "__main__":
    unittest.main()
