import unittest

import httpx

from actions.http_client.auth import BearerAuth


class AuthTestCase(unittest.TestCase):
    def test_bearer_auth(self):
        auth = BearerAuth(token="TODO")
        request = httpx.Request("GET", "https://www.example.com")
        flow = auth.sync_auth_flow(request)
        request = next(flow)
        self.assertEqual(request.headers["Authorization"], "Bearer TODO")
