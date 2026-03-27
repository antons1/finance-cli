"""Configuration constants. No secrets — only public URLs and paths."""

from pathlib import Path

# SpareBank 1 API
API_BASE_URL = "https://api.sparebank1.no"
AUTHORIZE_URL = f"{API_BASE_URL}/oauth/authorize"
TOKEN_URL = f"{API_BASE_URL}/oauth/token"

# Local callback server for OAuth
CALLBACK_PORT = 11737
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}/callback"

# Default bank
DEFAULT_BANK = "fid-ostlandet"

# Token storage
CONFIG_DIR = Path.home() / ".config" / "finance"
TOKENS_FILE = CONFIG_DIR / "tokens.enc"
KEY_FILE = CONFIG_DIR / "key"
KEYRING_SERVICE = "finance-cli"

# API header versions
ACCEPT_HEADERS = {
    "accounts": "application/vnd.sparebank1.v5+json; charset=utf-8",
    "default": "application/vnd.sparebank1.v1+json; charset=utf-8",
}

# Rate limits
RATE_LIMIT_PER_HOUR = 60

# Token safety margin (seconds before expiry to trigger refresh)
TOKEN_EXPIRY_MARGIN = 30
