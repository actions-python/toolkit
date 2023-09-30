import unittest
from pathlib import Path
from unittest.mock import patch

from actions.github.context import Context


class ContextTestCase(unittest.TestCase):
    def test_new_with_event_payload(self):
        environ = {
            "GITHUB_EVENT_PATH": str(Path(__file__).parent / "fixtures/payload.json"),
            "GITHUB_REPOSITORY": "actions-python/toolkit",
        }

        with patch.dict("os.environ", environ):
            context = Context.new()
            self.assertEqual(context.issue.number, 1)
            self.assertEqual(context.repo.owner, "actions-python")
            self.assertEqual(context.repo.repo, "toolkit")

    def test_new_without_event_payload(self):
        environ = {
            "GITHUB_REPOSITORY": "actions-python/toolkit",
        }

        with patch.dict("os.environ", environ):
            context = Context.new()
            self.assertIsNone(context.issue.number)
            self.assertEqual(context.repo.owner, "actions-python")
            self.assertEqual(context.repo.repo, "toolkit")
