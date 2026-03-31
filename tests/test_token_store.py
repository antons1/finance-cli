"""Tests for token_store.py — written before implementation (TDD)."""

import time

import pytest

from finance.token_store import TokenStore


@pytest.fixture
def store(tmp_path):
    """Create a TokenStore using a temporary directory."""
    return TokenStore(config_dir=tmp_path)


class TestKeyGeneration:
    def test_init_creates_key_file(self, store, tmp_path):
        key_file = tmp_path / "key"
        assert key_file.exists()

    def test_key_file_not_world_readable(self, store, tmp_path):
        key_file = tmp_path / "key"
        mode = key_file.stat().st_mode & 0o777
        assert mode == 0o600

    def test_key_is_stable_across_loads(self, tmp_path):
        store1 = TokenStore(config_dir=tmp_path)
        store1.save("client_id", "test")
        store2 = TokenStore(config_dir=tmp_path)
        assert store2.load("client_id") == "test"


class TestSaveAndLoad:
    def test_save_and_load_client_id(self, store):
        store.save("client_id", "my-client-id")
        assert store.load("client_id") == "my-client-id"

    def test_save_and_load_client_secret(self, store):
        store.save("client_secret", "super-secret")
        assert store.load("client_secret") == "super-secret"

    def test_save_and_load_access_token(self, store):
        store.save("access_token", "at-123")
        assert store.load("access_token") == "at-123"

    def test_save_and_load_refresh_token(self, store):
        store.save("refresh_token", "rt-456")
        assert store.load("refresh_token") == "rt-456"

    def test_load_missing_key_returns_none(self, store):
        assert store.load("nonexistent") is None

    def test_save_overwrites_existing(self, store):
        store.save("client_id", "old")
        store.save("client_id", "new")
        assert store.load("client_id") == "new"

    def test_multiple_keys_independent(self, store):
        store.save("client_id", "id-1")
        store.save("client_secret", "secret-1")
        assert store.load("client_id") == "id-1"
        assert store.load("client_secret") == "secret-1"


class TestTokenExpiry:
    def test_save_token_with_expiry(self, store):
        expiry = time.time() + 300  # 5 min from now
        store.save_token("access_token", "at-123", expiry)
        assert store.load("access_token") == "at-123"

    def test_get_access_token_returns_valid_token(self, store):
        expiry = time.time() + 300
        store.save_token("access_token", "at-123", expiry)
        assert store.get_access_token() == "at-123"

    def test_get_access_token_returns_none_when_expired(self, store):
        expiry = time.time() - 10  # already expired
        store.save_token("access_token", "at-expired", expiry)
        assert store.get_access_token() is None

    def test_get_access_token_returns_none_within_safety_margin(self, store):
        expiry = time.time() + 20  # 20s left, within 30s margin
        store.save_token("access_token", "at-almost", expiry)
        assert store.get_access_token() is None

    def test_get_access_token_returns_none_when_no_token(self, store):
        assert store.get_access_token() is None


class TestIsAuthenticated:
    def test_not_authenticated_initially(self, store):
        assert store.is_authenticated() is False

    def test_authenticated_with_refresh_token(self, store):
        store.save("refresh_token", "rt-valid")
        assert store.is_authenticated() is True

    def test_not_authenticated_after_clear(self, store):
        store.save("refresh_token", "rt-valid")
        store.clear_all()
        assert store.is_authenticated() is False


class TestClearAll:
    def test_clear_removes_all_data(self, store):
        store.save("client_id", "id")
        store.save("client_secret", "secret")
        store.save("refresh_token", "rt")
        store.save_token("access_token", "at", time.time() + 300)
        store.clear_all()
        assert store.load("client_id") is None
        assert store.load("client_secret") is None
        assert store.load("refresh_token") is None
        assert store.get_access_token() is None


class TestTokenFilePermissions:
    def test_tokens_file_not_world_readable(self, store, tmp_path):
        store.save("client_id", "test")
        tokens_file = tmp_path / "tokens.enc"
        mode = tokens_file.stat().st_mode & 0o777
        assert mode == 0o600


class TestWriteFailureFallback:
    def test_data_available_in_memory_after_write_failure(self, store, tmp_path):
        """Token saved to cache even when disk write fails."""
        store.save("client_id", "id-before-failure")
        # Make the tokens file read-only to force a write failure
        tokens_file = tmp_path / "tokens.enc"
        tokens_file.chmod(0o444)
        try:
            store.save("client_id", "id-after-failure")
        except Exception:
            pass  # write failure is swallowed
        assert store.load("client_id") == "id-after-failure"
        tokens_file.chmod(0o600)

    def test_access_token_available_after_write_failure(self, store, tmp_path):
        """Refreshed access token usable in-memory when disk write fails."""
        expiry = time.time() + 300
        store.save_token("access_token", "at-original", expiry)
        tokens_file = tmp_path / "tokens.enc"
        tokens_file.chmod(0o444)
        try:
            store.save_token("access_token", "at-refreshed", expiry)
        except Exception:
            pass
        assert store.get_access_token() == "at-refreshed"
        tokens_file.chmod(0o600)

    def test_clear_all_also_clears_cache(self, store):
        """clear_all wipes in-memory cache so cached tokens don't linger."""
        expiry = time.time() + 300
        store.save_token("access_token", "at-123", expiry)
        store.clear_all()
        assert store.get_access_token() is None
        assert store.load("access_token") is None


class TestCorruptData:
    def test_corrupt_tokens_file_returns_none(self, store, tmp_path):
        tokens_file = tmp_path / "tokens.enc"
        tokens_file.write_bytes(b"not-valid-encrypted-data")
        assert store.load("client_id") is None

    def test_corrupt_key_file_raises_on_init(self, tmp_path):
        key_file = tmp_path / "key"
        key_file.write_bytes(b"not-a-valid-key")
        with pytest.raises(Exception):
            TokenStore(config_dir=tmp_path)
