"""SpareBank 1 OAuth2 + PKCE authentication.

Supports two login modes:
1. Interactive: Opens browser, runs local callback server
2. Headless: Prints auth URL, user pastes redirect URL back
"""

import base64
import hashlib
import os
import secrets
import sys
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from finance.config import AUTHORIZE_URL, CALLBACK_PORT, REDIRECT_URI, TOKEN_URL
from finance.exceptions import AuthError, TokenExpiredError
from finance.token_store import TokenStore


def generate_pkce_pair() -> tuple[str, str]:
    """Generate a PKCE code_verifier and code_challenge (S256).

    Returns (code_verifier, code_challenge).
    """
    verifier_bytes = secrets.token_bytes(64)
    code_verifier = base64.urlsafe_b64encode(verifier_bytes).rstrip(b"=").decode("ascii")

    challenge_digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(challenge_digest).rstrip(b"=").decode("ascii")

    return code_verifier, code_challenge


def build_authorization_url(
    client_id: str,
    code_challenge: str,
    state: str,
    bank: str | None = None,
) -> str:
    """Build the OAuth2 authorization URL with PKCE parameters."""
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    if bank:
        params["finInst"] = bank
    return f"{AUTHORIZE_URL}?{urlencode(params)}"


def parse_callback_url(url: str) -> tuple[str, str]:
    """Extract code and state from a callback URL.

    Raises ValueError if the URL contains an error or is missing required params.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    if "error" in params:
        error = params["error"][0]
        desc = params.get("error_description", [""])[0]
        raise ValueError(f"Authorization error: {error} — {desc}")

    if "code" not in params:
        raise ValueError("Missing 'code' parameter in callback URL")
    if "state" not in params:
        raise ValueError("Missing 'state' parameter in callback URL")

    return params["code"][0], params["state"][0]


def exchange_code_for_tokens(
    code: str,
    code_verifier: str,
    client_id: str,
    client_secret: str,
) -> dict:
    """Exchange an authorization code for tokens.

    Returns the token response dict with access_token, refresh_token, expires_in.
    Raises AuthError on failure.
    """
    response = requests.post(
        TOKEN_URL,
        auth=(client_id, client_secret),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "code_verifier": code_verifier,
            "redirect_uri": REDIRECT_URI,
        },
    )

    if response.status_code != 200:
        raise AuthError(f"Token exchange failed: {response.text}")

    return response.json()


def is_headless() -> bool:
    """Detect if we're running in a headless environment (no browser available)."""
    if os.environ.get("SSH_CONNECTION"):
        return True
    if not sys.stdout.isatty():
        return True
    if sys.platform == "linux" and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return True
    return False


class _CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback."""

    callback_url: str | None = None

    def do_GET(self):
        _CallbackHandler.callback_url = f"http://localhost:{CALLBACK_PORT}{self.path}"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(
            b"<html><body><h1>Authentication successful</h1>"
            b"<p>You can close this tab.</p></body></html>"
        )

    def log_message(self, format, *args):
        pass  # Suppress server logs


class Sb1Auth:
    """Manages SpareBank 1 OAuth2 authentication."""

    def __init__(self, store: TokenStore):
        self._store = store

    def login(self, bank: str | None = None, headless: bool = False) -> str:
        """Run the full OAuth2 login flow. Returns the access token.

        In headless mode, prints the auth URL and reads the redirect URL from stdin.
        In interactive mode, opens a browser and runs a local callback server.
        """
        client_id = self._store.load("client_id")
        client_secret = self._store.load("client_secret")
        if not client_id or not client_secret:
            raise AuthError("Run 'finance auth setup' first to configure client credentials.")

        code_verifier, code_challenge = generate_pkce_pair()
        state = str(uuid.uuid4())
        auth_url = build_authorization_url(client_id, code_challenge, state, bank)

        if headless or is_headless():
            code, returned_state = self._headless_flow(auth_url)
        else:
            code, returned_state = self._interactive_flow(auth_url)

        if returned_state != state:
            raise AuthError("State mismatch — possible CSRF attack. Aborting.")

        token_data = exchange_code_for_tokens(code, code_verifier, client_id, client_secret)
        self._save_tokens(token_data)
        return token_data["access_token"]

    def _headless_flow(self, auth_url: str) -> tuple[str, str]:
        """Headless login: print URL, read redirect URL from stdin."""
        print(f"Open this URL in a browser:\n\n  {auth_url}\n", file=sys.stderr)
        print("After authenticating, paste the full redirect URL here:", file=sys.stderr)
        redirect_url = input().strip()
        return parse_callback_url(redirect_url)

    def _interactive_flow(self, auth_url: str) -> tuple[str, str]:
        """Interactive login: open browser, run local callback server."""
        _CallbackHandler.callback_url = None
        server = HTTPServer(("127.0.0.1", CALLBACK_PORT), _CallbackHandler)
        server.timeout = 120

        print("Opening browser for BankID authentication...", file=sys.stderr)
        webbrowser.open(auth_url)

        while _CallbackHandler.callback_url is None:
            server.handle_request()

        server.server_close()
        return parse_callback_url(_CallbackHandler.callback_url)

    def refresh_access_token(self) -> str:
        """Refresh the access token using the stored refresh token.

        Returns the new access token. Raises TokenExpiredError if refresh fails.
        """
        client_id = self._store.load("client_id")
        client_secret = self._store.load("client_secret")
        refresh_token = self._store.load("refresh_token")

        if not refresh_token:
            raise TokenExpiredError("No refresh token available. Re-login required.")

        response = requests.post(
            TOKEN_URL,
            auth=(client_id, client_secret),
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
        )

        if response.status_code != 200:
            raise TokenExpiredError(f"Refresh token expired or invalid: {response.text}")

        token_data = response.json()
        self._save_tokens(token_data)
        return token_data["access_token"]

    def ensure_access_token(self) -> str:
        """Return a valid access token, refreshing if necessary.

        Raises TokenExpiredError if both access and refresh tokens are invalid.
        """
        token = self._store.get_access_token()
        if token:
            return token
        return self.refresh_access_token()

    def _save_tokens(self, token_data: dict) -> None:
        """Persist tokens from a token response."""
        expiry = time.time() + token_data["expires_in"]
        self._store.save_token("access_token", token_data["access_token"], expiry)
        if "refresh_token" in token_data:
            self._store.save("refresh_token", token_data["refresh_token"])
