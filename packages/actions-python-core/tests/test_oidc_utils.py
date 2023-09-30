import unittest

import httpx

from actions.core.oidc_utils import BearerAuth


class OidcUtilsTestCase(unittest.TestCase):
    def test_bearer_auth(self):
        auth = BearerAuth(token="TODO")
        request = httpx.Request("GET", "https://www.example.com")
        request = next(auth.sync_auth_flow(request))
        self.assertEqual(request.headers["Authorization"], "Bearer TODO")
