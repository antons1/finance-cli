"""Tests for SpareBank 1 OAuth2 + PKCE authentication — written before implementation."""

import base64
import hashlib
import os
import time
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from finance.providers.sb1.auth import (
    Sb1Auth,
    build_authorization_url,
    exchange_code_for_tokens,
    generate_pkce_pair,
    is_headless,
    parse_callback_url,
)
from finance.token_store import TokenStore


class TestPkceGeneration:
    def test_code_verifier_is_base64url(self):
        verifier, _ = generate_pkce_pair()
        # base64url uses only these characters
        allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_=")
        assert set(verifier).issubset(allowed)

    def test_code_verifier_length_between_43_and_128(self):
        verifier, _ = generate_pkce_pair()
        assert 43 <= len(verifier) <= 128

    def test_code_challenge_is_sha256_of_verifier(self):
        verifier, challenge = generate_pkce_pair()
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")
        assert challenge == expected

    def test_each_call_produces_unique_pair(self):
        v1, _ = generate_pkce_pair()
        v2, _ = generate_pkce_pair()
        assert v1 != v2


class TestBuildAuthorizationUrl:
    def test_contains_required_params(self):
        url = build_authorization_url(
            client_id="test-client",
            code_challenge="test-challenge",
            state="test-state",
        )
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        assert params["client_id"] == ["test-client"]
        assert params["code_challenge"] == ["test-challenge"]
        assert params["code_challenge_method"] == ["S256"]
        assert params["response_type"] == ["code"]
        assert params["state"] == ["test-state"]
        assert "redirect_uri" in params

    def test_includes_bank_when_specified(self):
        url = build_authorization_url(
            client_id="test-client",
            code_challenge="test-challenge",
            state="test-state",
            bank="fid-smn",
        )
        params = parse_qs(urlparse(url).query)
        assert params["finInst"] == ["fid-smn"]

    def test_no_bank_param_when_not_specified(self):
        url = build_authorization_url(
            client_id="test-client",
            code_challenge="test-challenge",
            state="test-state",
        )
        params = parse_qs(urlparse(url).query)
        assert "finInst" not in params

    def test_uses_https(self):
        url = build_authorization_url(
            client_id="c", code_challenge="c", state="s"
        )
        assert url.startswith("https://")


class TestParseCallbackUrl:
    def test_extracts_code_and_state(self):
        url = "http://localhost:11737/callback?code=abc123&state=xyz789"
        code, state = parse_callback_url(url)
        assert code == "abc123"
        assert state == "xyz789"

    def test_raises_on_missing_code(self):
        url = "http://localhost:11737/callback?state=xyz789"
        with pytest.raises(ValueError, match="code"):
            parse_callback_url(url)

    def test_raises_on_missing_state(self):
        url = "http://localhost:11737/callback?code=abc123"
        with pytest.raises(ValueError, match="state"):
            parse_callback_url(url)

    def test_raises_on_error_response(self):
        url = "http://localhost:11737/callback?error=access_denied&error_description=User+cancelled"
        with pytest.raises(ValueError, match="access_denied"):
            parse_callback_url(url)


class TestExchangeCodeForTokens:
    @patch("finance.providers.sb1.auth.requests.post")
    def test_successful_exchange(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "at-new",
                "refresh_token": "rt-new",
                "expires_in": 300,
                "token_type": "Bearer",
            },
        )
        result = exchange_code_for_tokens(
            code="auth-code",
            code_verifier="verifier",
            client_id="cid",
            client_secret="csecret",
        )
        assert result["access_token"] == "at-new"
        assert result["refresh_token"] == "rt-new"
        assert result["expires_in"] == 300

    @patch("finance.providers.sb1.auth.requests.post")
    def test_exchange_sends_correct_params(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "at",
                "refresh_token": "rt",
                "expires_in": 300,
            },
        )
        exchange_code_for_tokens(
            code="the-code",
            code_verifier="the-verifier",
            client_id="cid",
            client_secret="csecret",
        )
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["data"]["grant_type"] == "authorization_code"
        assert call_kwargs.kwargs["data"]["code"] == "the-code"
        assert call_kwargs.kwargs["data"]["code_verifier"] == "the-verifier"

    @patch("finance.providers.sb1.auth.requests.post")
    def test_exchange_failure_raises(self, mock_post):
        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {"error": "invalid_grant"},
            text="invalid_grant",
        )
        from finance.exceptions import AuthError

        with pytest.raises(AuthError):
            exchange_code_for_tokens(
                code="bad-code",
                code_verifier="v",
                client_id="c",
                client_secret="s",
            )


class TestIsHeadless:
    @patch.dict("os.environ", {"SSH_CONNECTION": "1.2.3.4 5678 5.6.7.8 22"}, clear=False)
    def test_ssh_connection_is_headless(self):
        assert is_headless() is True

    def test_not_headless_with_display_and_tty(self):
        env = {"DISPLAY": ":0"}
        # Remove SSH_CONNECTION if present, set DISPLAY
        with patch.dict("os.environ", env, clear=False):
            os.environ.pop("SSH_CONNECTION", None)
            with patch("sys.stdout") as mock_stdout:
                mock_stdout.isatty.return_value = True
                assert is_headless() is False


class TestSb1Auth:
    @pytest.fixture
    def auth(self, tmp_path):
        store = TokenStore(config_dir=tmp_path)
        store.save("client_id", "test-cid")
        store.save("client_secret", "test-csecret")
        return Sb1Auth(store)

    @patch("finance.providers.sb1.auth.requests.post")
    def test_refresh_access_token(self, mock_post, auth):
        auth._store.save("refresh_token", "rt-old")
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "at-refreshed",
                "refresh_token": "rt-rotated",
                "expires_in": 300,
            },
        )
        token = auth.refresh_access_token()
        assert token == "at-refreshed"
        assert auth._store.load("refresh_token") == "rt-rotated"

    @patch("finance.providers.sb1.auth.requests.post")
    def test_refresh_failure_raises_token_expired(self, mock_post, auth):
        auth._store.save("refresh_token", "rt-expired")
        mock_post.return_value = MagicMock(
            status_code=400,
            json=lambda: {"error": "invalid_grant"},
            text="invalid_grant",
        )
        from finance.exceptions import TokenExpiredError

        with pytest.raises(TokenExpiredError):
            auth.refresh_access_token()

    def test_ensure_access_token_returns_valid_token(self, auth):
        expiry = time.time() + 300
        auth._store.save_token("access_token", "at-valid", expiry)
        assert auth.ensure_access_token() == "at-valid"

    @patch("finance.providers.sb1.auth.requests.post")
    def test_ensure_access_token_refreshes_when_expired(self, mock_post, auth):
        # Access token expired, refresh token valid
        auth._store.save_token("access_token", "at-old", time.time() - 10)
        auth._store.save("refresh_token", "rt-valid")
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {
                "access_token": "at-new",
                "refresh_token": "rt-new",
                "expires_in": 300,
            },
        )
        assert auth.ensure_access_token() == "at-new"
