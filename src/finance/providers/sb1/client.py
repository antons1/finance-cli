"""SpareBank 1 API HTTP client with automatic auth, header versioning, and error handling."""

import requests

from finance.config import ACCEPT_HEADERS, API_BASE_URL
from finance.exceptions import ApiError, RateLimitError
from finance.providers.sb1.auth import Sb1Auth
from finance.token_store import TokenStore


class Sb1Client:
    """HTTP client for the SpareBank 1 personal banking API."""

    def __init__(self, store: TokenStore):
        self._store = store
        self._auth = Sb1Auth(store)

    def _accept_header(self, path: str) -> str:
        """Select the correct Accept header version based on endpoint path."""
        if "/banking/accounts" in path and "/credit/" not in path:
            return ACCEPT_HEADERS["accounts"]
        return ACCEPT_HEADERS["default"]

    def _request(self, method: str, path: str, retry_on_401: bool = True, **kwargs) -> dict:
        """Make an authenticated API request.

        Handles token refresh on 401, rate limiting on 429, and error responses.
        """
        token = self._auth.ensure_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": self._accept_header(path),
        }
        if method in ("POST", "PUT", "PATCH"):
            headers["Content-Type"] = ACCEPT_HEADERS["default"]

        url = f"{API_BASE_URL}{path}"

        response = requests.request(
            method,
            url=url,
            headers=headers,
            **kwargs,
        )

        if response.status_code == 401 and retry_on_401:
            self._auth.refresh_access_token()
            return self._request(method, path, retry_on_401=False, **kwargs)

        if response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(int(retry_after) if retry_after else None)

        if response.status_code >= 400:
            try:
                body = response.json()
            except Exception:
                body = response.text
            raise ApiError(response.status_code, body)

        return response.json()

    def get(self, path: str, **kwargs) -> dict:
        """GET request."""
        return self._request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> dict:
        """POST request."""
        return self._request("POST", path, **kwargs)
