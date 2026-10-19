import unittest
from pathlib import Path
import tempfile
from unittest.mock import patch

from scripts.update_readme import END, START, main, recent_commits, render_activity, update, validate_markers


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

    def test_empty_activity_and_invalid_repository(self):
        self.assertEqual(render_activity([], "owner/repo"), "_No commits are available yet._")
        with self.assertRaises(ValueError):
            render_activity([], "bad repository")

    def test_invalid_commit_fields(self):
        for commit in [("bad", "2026-10-05", "subject"), ("a" * 40, "bad-date", "subject")]:
            with self.subTest(commit=commit), self.assertRaises(ValueError):
                render_activity([commit], "owner/repo")

    def test_recent_commits_skip_generated_updates(self):
        output = "a" * 40 + "\x1f2026-10-05\x1fdocs: update recent activity\x1e"
        output += "b" * 40 + "\x1f2026-10-06\x1fFix bug\x1e"
        with patch("scripts.update_readme.subprocess.run") as run:
            run.return_value.stdout = output
            self.assertEqual(recent_commits(1), [("b" * 40, "2026-10-06", "Fix bug")])

    def test_preserves_windows_newlines(self):
        original = f"Header\r\n{START}\r\nold\r\n{END}\r\n"
        self.assertEqual(update(original, "first\nsecond"), f"Header\r\n{START}\r\nfirst\r\nsecond\r\n{END}\r\n")

    def test_check_mode_validates_real_file(self):
        with tempfile.TemporaryDirectory() as directory:
            readme = Path(directory) / "README.md"
            readme.write_text(f"Header\n{START}\nold\n{END}\n", encoding="utf-8")
            with patch("sys.argv", ["update_readme.py", "--readme", str(readme), "--repository", "owner/repo", "--check"]):
                self.assertEqual(main(), 0)


if __name__ == "__main__":
    unittest.main()
