import unittest

from scripts.update_readme import END, START, render_activity, update, validate_markers


class ReadmeUpdaterTests(unittest.TestCase):
    def test_rejects_missing_and_duplicate_markers(self):
        for text in ("plain README", f"{START}\n{START}\n{END}\n"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    validate_markers(text)

    def test_rejects_reversed_markers(self):
        with self.assertRaises(ValueError):
            validate_markers(f"{END}\n{START}\n")

    def test_update_is_idempotent_and_preserves_surrounding_text(self):
        original = f"Header\n{START}\nold\n{END}\nFooter\n"
        once = update(original, "new")
        self.assertEqual(once, f"Header\n{START}\nnew\n{END}\nFooter\n")
        self.assertEqual(update(once, "new"), once)

    def test_escapes_untrusted_commit_subject(self):
        result = render_activity([("a" * 40, "2026-10-05", "Fix [link] <tag>")], "owner/repo")
        self.assertIn("Fix &#91;link&#93; &lt;tag&gt;", result)
        self.assertIn("https://github.com/owner/repo/commit/", result)


if __name__ == "__main__":
    unittest.main()
