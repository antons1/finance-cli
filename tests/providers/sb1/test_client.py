"""Tests for SpareBank 1 API client — written before implementation."""

import time
from unittest.mock import MagicMock, patch

import pytest

from finance.exceptions import ApiError, RateLimitError
from finance.providers.sb1.client import Sb1Client
from finance.token_store import TokenStore


@pytest.fixture
def store(tmp_path):
    store = TokenStore(config_dir=tmp_path)
    store.save("client_id", "test-cid")
    store.save("client_secret", "test-csecret")
    store.save("refresh_token", "rt-valid")
    store.save_token("access_token", "at-valid", time.time() + 300)
    return store


@pytest.fixture
def client(store):
    return Sb1Client(store)


class TestHeaders:
    def test_accounts_endpoint_uses_v5_header(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(status_code=200, json=lambda: {"accounts": []})
            client.get("/personal/banking/accounts")
            call_kwargs = mock_req.call_args.kwargs
            assert "v5" in call_kwargs["headers"]["Accept"]

    def test_transactions_endpoint_uses_v1_header(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(status_code=200, json=lambda: {"transactions": []})
            client.get("/personal/banking/transactions", params={"accountKey": "abc"})
            call_kwargs = mock_req.call_args.kwargs
            assert "v1" in call_kwargs["headers"]["Accept"]

    def test_bearer_token_in_authorization_header(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(status_code=200, json=lambda: {})
            client.get("/personal/banking/accounts")
            call_kwargs = mock_req.call_args.kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer at-valid"


class TestErrorHandling:
    def test_401_triggers_refresh_and_retry(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            # First call returns 401, second (after refresh) returns 200
            mock_req.side_effect = [
                MagicMock(status_code=401, text="Unauthorized"),
                MagicMock(status_code=200, json=lambda: {"data": "ok"}),
            ]
            with patch.object(client._auth, "refresh_access_token", return_value="at-refreshed"):
                result = client.get("/personal/banking/accounts")
                assert result == {"data": "ok"}
                assert mock_req.call_count == 2

    def test_401_only_retries_once(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(status_code=401, text="Unauthorized")
            with patch.object(client._auth, "refresh_access_token", return_value="at-new"):
                with pytest.raises(ApiError) as exc_info:
                    client.get("/personal/banking/accounts")
                assert exc_info.value.status_code == 401
                assert mock_req.call_count == 2

    def test_429_raises_rate_limit_error_with_retry_after(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            response = MagicMock(
                status_code=429,
                headers={"Retry-After": "45"},
                text="Rate limit exceeded",
            )
            mock_req.return_value = response
            with pytest.raises(RateLimitError) as exc_info:
                client.get("/personal/banking/accounts")
            assert exc_info.value.retry_after == 45

    def test_500_raises_api_error(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(
                status_code=500,
                json=lambda: {"errors": [{"message": "Internal error"}]},
                text='{"errors": [{"message": "Internal error"}]}',
            )
            with pytest.raises(ApiError) as exc_info:
                client.get("/personal/banking/accounts")
            assert exc_info.value.status_code == 500

    def test_404_raises_api_error(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(
                status_code=404,
                json=lambda: {"errors": [{"message": "Not found"}]},
                text='{"errors": [{"message": "Not found"}]}',
            )
            with pytest.raises(ApiError) as exc_info:
                client.get("/personal/banking/accounts/nonexistent")
            assert exc_info.value.status_code == 404


class TestRequestConstruction:
    def test_get_with_params(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(status_code=200, json=lambda: {})
            client.get("/personal/banking/transactions", params={"accountKey": "abc123"})
            call_kwargs = mock_req.call_args.kwargs
            assert call_kwargs["params"] == {"accountKey": "abc123"}

    def test_post_with_json_body(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(status_code=200, json=lambda: {})
            client.post("/personal/banking/accounts/balance", json={"accountNumber": "12345"})
            call_kwargs = mock_req.call_args.kwargs
            assert call_kwargs["json"] == {"accountNumber": "12345"}

    def test_base_url_is_https(self, client):
        with patch("finance.providers.sb1.client.requests.request") as mock_req:
            mock_req.return_value = MagicMock(status_code=200, json=lambda: {})
            client.get("/personal/banking/accounts")
            call_args = mock_req.call_args
            url = call_args.kwargs.get("url") or call_args.args[1]
            assert url.startswith("https://")
