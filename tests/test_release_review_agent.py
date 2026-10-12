"""Check that the agent stops reading before the production draft is written."""

from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from scripts import release_review_agent as agent


class AgentBudgetTests(unittest.TestCase):
    def test_four_tool_calls_then_forced_draft(self):
        sha = "a" * 40
        requests = []

        def fake_api(payload):
            requests.append(payload)
            if len(requests) <= 4:
                name = "list_commits" if len(requests) == 1 else "show_diff"
                arguments = "{}" if name == "list_commits" else f'{{"sha":"{sha}"}}'
                return {"output": [{"type": "function_call", "name": name,
                                    "arguments": arguments, "call_id": f"call-{len(requests)}"}]}
            return {"output": [{"type": "message", "content": [
                {"type": "output_text", "text": "## Risks\nHuman review required."}]}]}

        current = Path.cwd()
        with tempfile.TemporaryDirectory(dir=current) as folder, patch.object(agent, "api_call", fake_api), \
             patch.object(agent, "release_commits", return_value=("initial release", [{"sha": sha, "subject": "test"}])), \
             patch.object(agent, "git", return_value="diff --git a/x b/x\n"):
            try:
                os.chdir(folder)
                self.assertEqual(agent.main(), 0)
                self.assertIn("Human review required.", Path("agent-review.md").read_text(encoding="utf-8"))
            finally:
                os.chdir(current)

        self.assertEqual(len(requests), 5)
        self.assertEqual(requests[0]["tool_choice"], {"type": "function", "name": "list_commits"})
        self.assertEqual(requests[-1]["tool_choice"], "none")
        self.assertTrue(all(request["parallel_tool_calls"] is False for request in requests))


if __name__ == "__main__":
    unittest.main()
