"""CLI commands for SpareBank 1 transaction operations."""

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
def transactions():
    """Transaction operations."""


@transactions.command("list")
@click.option("--account-key", required=True, help="Account key from 'accounts list'")
@click.option("--from", "from_date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", default=None, help="End date (YYYY-MM-DD)")
def list_transactions(account_key: str, from_date: str | None, to_date: str | None):
    """List transactions for an account."""
    try:
        client = get_client()
        params = {"accountKey": account_key}
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date

        data = client.get("/personal/banking/transactions", params=params)
        result = [
            {
                "id": t.get("id"),
                "date": t.get("accountingDate"),
                "description": t.get("description"),
                "amount": t["amount"]["amount"],
                "currency": t["amount"]["currencyCode"],
                "type": t.get("transactionType"),
            }
            for t in data.get("transactions", [])
        ]
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@transactions.command("details")
@click.argument("transaction_id")
def transaction_details(transaction_id: str):
    """Get details for a specific transaction."""
    try:
        client = get_client()
        data = client.get(f"/personal/banking/transactions/{transaction_id}/details")
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@transactions.command("export")
@click.option("--account-key", required=True, help="Account key from 'accounts list'")
def export_transactions(account_key: str):
    """Export transactions (CSV)."""
    try:
        client = get_client()
        data = client.get(
            "/personal/banking/transactions/export",
            params={"accountKey": account_key},
        )
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)
