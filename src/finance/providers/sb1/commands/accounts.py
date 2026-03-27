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


def _require_json(ctx: click.Context) -> None:
    """Require --json flag until human-readable format is implemented."""
    if not ctx.obj.get("json"):
        click.echo("Error: --json flag is required. Human-readable format is not yet implemented.", err=True)
        click.echo("Usage: finance --json accounts list", err=True)
        sys.exit(1)


@click.group()
@click.pass_context
def accounts(ctx):
    """Bank account operations."""


@accounts.command("list")
@click.pass_context
def list_accounts(ctx):
    """List all bank accounts."""
    _require_json(ctx)
    try:
        client = get_client()
        data = client.get("/personal/banking/accounts")
        result = [
            {
                "key": a["key"],
                "accountNumber": a["accountNumber"],
                "name": a["name"],
                "balance": a["balance"],
                "availableBalance": a["availableBalance"],
                "currency": a["currencyCode"],
                "type": a.get("type"),
                "owner": a.get("owner", {}).get("name"),
            }
            for a in data.get("accounts", [])
        ]
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@accounts.command("get")
@click.argument("account_key")
@click.pass_context
def get_account(ctx, account_key: str):
    """Get details for a specific account."""
    _require_json(ctx)
    try:
        client = get_client()
        data = client.get(f"/personal/banking/accounts/{account_key}")
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@accounts.command("balance")
@click.pass_context
def balance(ctx):
    """Show balance summary for all accounts."""
    _require_json(ctx)
    try:
        client = get_client()
        data = client.get("/personal/banking/accounts")
        result = [
            {
                "accountNumber": a["accountNumber"],
                "name": a["name"],
                "balance": a["balance"],
                "availableBalance": a["availableBalance"],
                "currency": a["currencyCode"],
            }
            for a in data.get("accounts", [])
        ]
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)
