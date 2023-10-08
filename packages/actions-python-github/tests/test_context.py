import dataclasses
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from actions.github.context import Context
from tests.utils import capture_output


class ContextTestCase(unittest.TestCase):
    def setUp(self):
        env_vars = {
            "GITHUB_EVENT_PATH": str(Path(__file__).parent / "fixtures/payload.json"),
            "GITHUB_REPOSITORY": "actions-python/toolkit",
        }
        self.environ_mocked = patch.dict("os.environ", env_vars)
        self.environ_mocked.start()

    def tearDown(self):
        self.environ_mocked.stop()

    def test_returns_the_payload_object(self):
        content = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
        self.assertDictEqual(Context().payload, content)

    def test_returns_an_empty_payload_if_environment_variable_is_empty(self):
        del os.environ["GITHUB_EVENT_PATH"]
        self.assertDictEqual(Context().payload, {})

    def test_returns_stdout_if_environment_variable_is_invalid(self):
        os.environ["GITHUB_EVENT_PATH"] = "/foo/bar/baz"
        self.assertEqual(
            capture_output(Context),
            "GITHUB_EVENT_PATH /foo/bar/baz does not exist",
        )

    def test_returns_attributes_from_environment_variable(self):
        self.assertDictEqual(
            dataclasses.asdict(Context().repo),
            {"owner": "actions-python", "repo": "toolkit"},
        )

    def test_returns_attributes_from_the_repository_payload(self):
        del os.environ["GITHUB_REPOSITORY"]
        context = Context()
        context.payload = {"repository": {"name": "test", "owner": {"login": "user"}}}
        self.assertDictEqual(
            dataclasses.asdict(context.repo),
            {"owner": "user", "repo": "test"},
        )

    def test_return_error_for_context_repo_when_repository_is_empty(self):
        del os.environ["GITHUB_REPOSITORY"]
        context = Context()
        del context.payload["repository"]
        with self.assertRaisesRegex(
            Exception,
            (
                "context.repo requires a GITHUB_REPOSITORY environment variable "
                "like 'owner/repo'"
            ),
        ):
            context.repo  # noqa: B018

    def test_returns_issue_attributes_from_the_repository(self):
        self.assertDictEqual(
            dataclasses.asdict(Context().issue),
            {"owner": "actions-python", "repo": "toolkit", "number": 1},
        )

    def test_works_with_pull_request_payloads(self):
        del os.environ["GITHUB_REPOSITORY"]
        context = Context()
        context.payload = {
            "repository": {"owner": {"login": "user"}, "name": "test"},
            "pull_request": {"number": 2},
        }
        self.assertDictEqual(
            dataclasses.asdict(context.issue),
            {"owner": "user", "repo": "test", "number": 2},
        )

    def test_works_with_payload_number_payloads(self):
        del os.environ["GITHUB_REPOSITORY"]
        context = Context()
        context.payload = {
            "repository": {"owner": {"login": "user"}, "name": "test"},
            "number": 2,
        }
        self.assertDictEqual(
            dataclasses.asdict(context.issue),
            {"owner": "user", "repo": "test", "number": 2},
        )
