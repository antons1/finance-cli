"""CLI commands for SpareBank 1 authentication."""

import json
import sys
import time

import click

from finance.config import CONFIG_DIR
from finance.exceptions import FinanceError
from finance.providers.sb1.auth import Sb1Auth
from finance.token_store import TokenStore


@click.group("auth")
def auth():
    """Authentication management."""


@auth.command("setup")
def setup():
    """Store client credentials (client_id and client_secret)."""
    client_id = click.prompt("Client ID", hide_input=False)
    client_secret = click.prompt("Client Secret", hide_input=True)

    store = TokenStore(config_dir=CONFIG_DIR)
    store.save("client_id", client_id)
    store.save("client_secret", client_secret)
    click.echo(json.dumps({"status": "credentials_stored"}), err=True)


@auth.command("login")
@click.option("--bank", default=None, help="Bank ID (e.g. fid-smn). Omit for bank picker.")
@click.option("--headless", is_flag=True, help="Use paste-flow (for headless/SSH environments).")
def login(bank: str | None, headless: bool):
    """Authenticate with BankID via OAuth2."""
    try:
        store = TokenStore(config_dir=CONFIG_DIR)
        sb1_auth = Sb1Auth(store)
        sb1_auth.login(bank=bank, headless=headless)
        click.echo(json.dumps({"status": "authenticated"}), err=True)
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@auth.command("logout")
def logout():
    """Clear all stored tokens."""
    store = TokenStore(config_dir=CONFIG_DIR)
    store.clear_all()
    click.echo(json.dumps({"status": "logged_out"}), err=True)


@auth.command("status")
def status():
    """Show authentication status (JSON)."""
    store = TokenStore(config_dir=CONFIG_DIR)
    authenticated = store.is_authenticated()
    data = store._read_data()

    result = {"authenticated": authenticated}

    expiry = data.get("access_token_expiry")
    if expiry:
        remaining = int(expiry - time.time())
        result["access_token_expires_in"] = max(0, remaining)

    click.echo(json.dumps(result, indent=2))
