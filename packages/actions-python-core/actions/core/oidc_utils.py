import os
import typing
import urllib.parse

import httpx


class OidcClient:
    @classmethod
    def _create_http_client(cls) -> httpx.AsyncClient:
        return httpx.AsyncClient(auth=BearerAuth(token=cls._get_request_token()))

    @classmethod
    def _get_request_token(cls) -> str:
        token = os.getenv("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
        if not token:
            raise Exception("Unable to get ACTIONS_ID_TOKEN_REQUEST_TOKEN env variable")
        return token

    @classmethod
    def _get_id_token_url(cls) -> str:
        runtime_url = os.getenv("ACTIONS_ID_TOKEN_REQUEST_URL")
        if not runtime_url:
            raise Exception("Unable to get ACTIONS_ID_TOKEN_REQUEST_URL env variable")
        return runtime_url

    @classmethod
    async def _get_call(cls, id_token_url: str) -> str:
        http_client = cls._create_http_client()

        try:
            response = await http_client.get(id_token_url)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"Failed to get ID Token.\n"
                f"Error Code: {e.response.status_code}\n"
                f"Result: {e!s}"
            ) from e
        except httpx.HTTPError as e:
            raise Exception("Failed to get ID Token.") from e

        id_token = response.json().get("value")
        if not id_token:
            raise Exception("Response json body do not have ID Token field")
        return id_token

    @classmethod
    async def get_id_token(cls, audience: typing.Optional[str] = None) -> str:
        from actions.core.core import debug, set_secret

        try:
            # New ID Token is requested from action service
            id_token_url = cls._get_id_token_url()
            if audience:
                encoded_audience = urllib.parse.quote(audience)
                id_token_url = f"{id_token_url}&audience={encoded_audience}"

            debug(f"ID token url is {id_token_url}")

            id_token = await cls._get_call(id_token_url)
            set_secret(id_token)
            return id_token
        except Exception as e:
            raise Exception(f"Error message: {e!s}") from e


class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self._auth_header = self._build_auth_header(token)

    def auth_flow(
        self, request: httpx.Request
    ) -> typing.Generator[httpx.Request, httpx.Response, None]:
        request.headers["Authorization"] = self._auth_header
        yield request

    def _build_auth_header(self, token: str) -> str:
        return f"Bearer {token}"
