"""CLI commands for SpareBank 1 account operations."""

import json
import sys

import click

from finance.exceptions import FinanceError
from finance.formatting import format_table
from finance.providers.sb1.client import Sb1Client
from finance.token_store import TokenStore
from finance.config import CONFIG_DIR


def get_client() -> Sb1Client:
    """Create an authenticated Sb1Client."""
    store = TokenStore(config_dir=CONFIG_DIR)
    return Sb1Client(store)


def _output(ctx: click.Context, rows: list[dict], columns: list[str] | None = None, headers: dict[str, str] | None = None) -> None:
    """Output rows as JSON or table depending on --json flag."""
    if ctx.obj.get("json"):
        click.echo(json.dumps(rows, indent=2, ensure_ascii=False))
    else:
        click.echo(format_table(rows, columns=columns, headers=headers), nl=False)


@click.group()
@click.pass_context
def accounts(ctx):
    """Bank account operations."""


@accounts.command("list")
@click.pass_context
def list_accounts(ctx):
    """List all bank accounts."""
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
        _output(ctx, result,
                columns=["key", "name", "accountNumber", "balance", "availableBalance", "currency", "owner"],
                headers={"key": "Key", "accountNumber": "Account", "availableBalance": "Available", "balance": "Balance", "name": "Name", "currency": "Cur", "owner": "Owner"})
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@accounts.command("get")
@click.argument("account_key")
@click.pass_context
def get_account(ctx, account_key: str):
    """Get details for a specific account."""
    try:
        client = get_client()
        data = client.get(f"/personal/banking/accounts/{account_key}")
        if ctx.obj.get("json"):
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            _output(ctx, [data],
                    columns=["name", "accountNumber", "balance", "availableBalance", "currencyCode"],
                    headers={"accountNumber": "Account", "availableBalance": "Available", "balance": "Balance", "name": "Name", "currencyCode": "Cur"})
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@accounts.command("balance")
@click.pass_context
def balance(ctx):
    """Show balance summary for all accounts."""
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
        _output(ctx, result,
                columns=["name", "accountNumber", "balance", "availableBalance", "currency"],
                headers={"accountNumber": "Account", "availableBalance": "Available", "balance": "Balance", "name": "Name", "currency": "Cur"})
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)
