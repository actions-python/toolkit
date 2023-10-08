import contextlib
import io
import unittest
from unittest.mock import patch

import httpx
import pytest

from actions.core.oidc_utils import BearerAuth, OidcClient


class TestOidcUtils(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.stream = contextlib.redirect_stdout(io.StringIO())
        self.stream.__enter__()

    async def asyncTearDown(self):
        self.stream.__exit__(None, None, None)

    async def test_raises_get_id_token_without_url(self):
        with patch.dict(
            "os.environ",
            {
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "github-token",
            },
        ):
            with self.assertRaisesRegex(
                Exception,
                "Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable",
            ):
                await OidcClient.get_id_token()

    async def test_raises_get_id_token_without_token(self):
        with patch.dict(
            "os.environ",
            {
                "ACTIONS_ID_TOKEN_REQUEST_URL": "https://actions-token.url",
            },
        ):
            with self.assertRaisesRegex(
                Exception,
                "Unable to get ACTIONS_ID_TOKEN_REQUEST_TOKEN env variable",
            ):
                await OidcClient.get_id_token()

    @pytest.mark.vcr()
    async def test_get_id_token(self):
        with patch.dict(
            "os.environ",
            {
                "ACTIONS_ID_TOKEN_REQUEST_URL": "https://actions-token.url",
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "github-token",
            },
        ):
            self.assertEqual(await OidcClient.get_id_token(), "result-token")

    @pytest.mark.vcr()
    async def test_get_id_token_with_audience(self):
        with patch.dict(
            "os.environ",
            {
                "ACTIONS_ID_TOKEN_REQUEST_URL": "https://actions-token.url",
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "github-token",
            },
        ):
            self.assertEqual(
                await OidcClient.get_id_token("test-audience"), "result-token"
            )

    def test_bearer_auth(self):
        auth = BearerAuth(token="TODO")
        request = httpx.Request("GET", "https://www.example.com")
        request = next(auth.sync_auth_flow(request))
        self.assertEqual(request.headers["Authorization"], "Bearer TODO")
