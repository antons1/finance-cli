"""CLI commands for SpareBank 1 account operations."""

import json
import sys

import click

from finance.exceptions import FinanceError
from finance.providers.sb1.client import Sb1Client
from finance.token_store import TokenStore
from finance.config import CONFIG_DIR


def get_client() -> Sb1Client:
    """Create an authenticated Sb1Client."""
    store = TokenStore(config_dir=CONFIG_DIR)
    return Sb1Client(store)


@click.group()
def accounts():
    """Bank account operations."""


@accounts.command("list")
def list_accounts():
    """List all bank accounts."""
    try:
        client = get_client()
        data = client.get("/personal/banking/accounts")
        result = [
            {
                "id": a["id"],
                "accountNumber": a["accountNumber"]["formatted"],
                "name": a["name"],
                "balance": a["balance"]["amount"],
                "currency": a["balance"]["currencyCode"],
                "availableBalance": a["availableBalance"]["amount"],
            }
            for a in data.get("accounts", [])
        ]
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@accounts.command("get")
@click.argument("account_key")
def get_account(account_key: str):
    """Get details for a specific account."""
    try:
        client = get_client()
        data = client.get(f"/personal/banking/accounts/{account_key}")
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@accounts.command("balance")
def balance():
    """Show balance summary for all accounts."""
    try:
        client = get_client()
        data = client.get("/personal/banking/accounts")
        result = [
            {
                "accountNumber": a["accountNumber"]["formatted"],
                "name": a["name"],
                "balance": a["balance"]["amount"],
                "currency": a["balance"]["currencyCode"],
            }
            for a in data.get("accounts", [])
        ]
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)
