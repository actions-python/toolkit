import typing
import unittest
from unittest.mock import patch

import pytest

from actions.github.github import get_github, get_githubkit


@pytest.mark.filterwarnings("ignore:datetime.datetime.utcfromtimestamp()")
class GitHubTestCase(unittest.TestCase):
    def setUp(self):
        self.environ_mocked = patch.dict(
            "os.environ",
            {"GITHUB_TOKEN": "", "INPUT_GITHUB-TOKEN": "", "INPUT_TOKEN": ""},
        )
        self.environ_mocked.start()

    def tearDown(self):
        self.environ_mocked.stop()

    def test_github_with_explicit_token(self):
        with get_github(token="TOKEN") as github:
            github: typing.Any  # type: ignore[annotation-unchecked]
            self.assertEqual(github._Github__requester._Requester__auth._token, "TOKEN")

    def test_github_with_environment_variable(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "TOKEN"}):
            with get_github() as github:
                github: typing.Any  # type: ignore[annotation-unchecked]
                self.assertEqual(
                    github._Github__requester._Requester__auth._token, "TOKEN"
                )

    def test_github_with_input(self):
        with patch.dict("os.environ", {"INPUT_GITHUB-TOKEN": "TOKEN"}):
            with get_github() as github:
                github: typing.Any  # type: ignore[annotation-unchecked]
                self.assertEqual(
                    github._Github__requester._Requester__auth._token, "TOKEN"
                )

        with patch.dict("os.environ", {"INPUT_TOKEN": "TOKEN"}):
            with get_github() as github:
                github: typing.Any  # type: ignore[annotation-unchecked]
                self.assertEqual(
                    github._Github__requester._Requester__auth._token, "TOKEN"
                )

    def test_github_without_token(self):
        with patch.dict("os.environ", {}):
            with get_github() as github:
                github: typing.Any  # type: ignore[annotation-unchecked]
                self.assertIsNone(github._Github__requester._Requester__auth)


class GitHubKitTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.environ_mocked = patch.dict(
            "os.environ",
            {"GITHUB_TOKEN": "", "INPUT_GITHUB-TOKEN": "", "INPUT_TOKEN": ""},
        )
        self.environ_mocked.start()

    async def asyncTearDown(self):
        self.environ_mocked.stop()

    async def test_githubkit_with_explicit_token(self):
        async with get_githubkit(token="TOKEN") as github:
            self.assertEqual(getattr(github.auth, "token", None), "TOKEN")

    async def test_githubkit_with_environment_variable(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "TOKEN"}):
            async with get_githubkit() as github:
                self.assertEqual(getattr(github.auth, "token", None), "TOKEN")

    async def test_githubkit_with_input(self):
        with patch.dict("os.environ", {"INPUT_GITHUB-TOKEN": "TOKEN"}):
            async with get_githubkit() as github:
                self.assertEqual(getattr(github.auth, "token", None), "TOKEN")

        with patch.dict("os.environ", {"INPUT_TOKEN": "TOKEN"}):
            async with get_githubkit() as github:
                self.assertEqual(getattr(github.auth, "token", None), "TOKEN")

    async def test_githubkit_without_token(self):
        with patch.dict("os.environ", {}):
            async with get_githubkit() as github:
                self.assertIsNone(getattr(github.auth, "token", None))
