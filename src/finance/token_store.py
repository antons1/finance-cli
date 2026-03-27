"""Encrypted file-based token storage using Fernet (AES-128-CBC).

Works on both macOS and Linux. Tokens are never stored in plaintext.
"""

import json
import os
import stat
import time
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from finance.config import CONFIG_DIR, TOKEN_EXPIRY_MARGIN


def _set_file_permissions(path: Path) -> None:
    """Set file to owner-only read/write (chmod 600)."""
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


class TokenStore:
    """Encrypted key-value store for tokens and credentials.

    Data is stored as a Fernet-encrypted JSON blob in tokens.enc.
    The encryption key is stored separately in a key file with 600 permissions.
    """

    def __init__(self, config_dir: Path = CONFIG_DIR):
        self._config_dir = config_dir
        self._key_file = config_dir / "key"
        self._tokens_file = config_dir / "tokens.enc"
        self._fernet = self._load_or_create_key()

    def _load_or_create_key(self) -> Fernet:
        """Load existing key or generate a new one."""
        self._config_dir.mkdir(parents=True, exist_ok=True)

        if self._key_file.exists():
            raw = self._key_file.read_bytes().strip()
            try:
                return Fernet(raw)
            except (ValueError, Exception):
                raise ValueError(
                    f"Invalid encryption key in {self._key_file}. "
                    "Delete the file to generate a new one (this will lose stored tokens)."
                )

        key = Fernet.generate_key()
        self._key_file.write_bytes(key)
        _set_file_permissions(self._key_file)
        return Fernet(key)

    def _read_data(self) -> dict:
        """Read and decrypt the token store. Returns empty dict on any failure."""
        if not self._tokens_file.exists():
            return {}
        try:
            encrypted = self._tokens_file.read_bytes()
            decrypted = self._fernet.decrypt(encrypted)
            return json.loads(decrypted)
        except (InvalidToken, json.JSONDecodeError, Exception):
            return {}

    def _write_data(self, data: dict) -> None:
        """Encrypt and write the token store."""
        payload = json.dumps(data).encode()
        encrypted = self._fernet.encrypt(payload)
        self._tokens_file.write_bytes(encrypted)
        _set_file_permissions(self._tokens_file)

    def save(self, key: str, value: str) -> None:
        """Store a key-value pair."""
        data = self._read_data()
        data[key] = value
        self._write_data(data)

    def load(self, key: str) -> str | None:
        """Retrieve a value by key. Returns None if not found or on decryption failure."""
        data = self._read_data()
        return data.get(key)

    def save_token(self, key: str, value: str, expiry: float) -> None:
        """Store a token with its expiry timestamp."""
        data = self._read_data()
        data[key] = value
        data[f"{key}_expiry"] = expiry
        self._write_data(data)

    def get_access_token(self) -> str | None:
        """Return the access token if it exists and is not expired (with safety margin).

        Returns None if the token is missing, expired, or within the safety margin.
        """
        data = self._read_data()
        token = data.get("access_token")
        expiry = data.get("access_token_expiry")
        if token is None or expiry is None:
            return None
        if time.time() >= expiry - TOKEN_EXPIRY_MARGIN:
            return None
        return token

    def is_authenticated(self) -> bool:
        """Check if a refresh token exists (indicates an active session)."""
        return self.load("refresh_token") is not None

    def clear_all(self) -> None:
        """Remove all stored data."""
        if self._tokens_file.exists():
            self._tokens_file.unlink()
