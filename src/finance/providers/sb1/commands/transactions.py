"""CLI commands for SpareBank 1 transaction operations."""

import json
import sys
from datetime import datetime, timezone
from urllib.parse import quote

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


def _epoch_ms_to_date(epoch_ms: int | None) -> str | None:
    """Convert epoch milliseconds to YYYY-MM-DD string."""
    if epoch_ms is None:
        return None
    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


@click.group()
@click.pass_context
def transactions(ctx):
    """Transaction operations."""


@transactions.command("list")
@click.option("--account-key", required=True, help="Account key from 'accounts list'")
@click.option("--from", "from_date", default=None, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", default=None, help="End date (YYYY-MM-DD)")
@click.pass_context
def list_transactions(ctx, account_key: str, from_date: str | None, to_date: str | None):
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
                "date": _epoch_ms_to_date(t.get("date")),
                "description": t.get("description"),
                "cleanedDescription": t.get("cleanedDescription"),
                "amount": t.get("amount"),
                "currency": t.get("currencyCode"),
                "type": t.get("typeText"),
                "typeCode": t.get("typeCode"),
                "remoteAccount": t.get("remoteAccountNumber"),
                "remoteAccountName": t.get("remoteAccountName"),
                "bookingStatus": t.get("bookingStatus"),
            }
            for t in data.get("transactions", [])
        ]
        _output(ctx, result,
                columns=["date", "description", "amount", "currency", "type", "remoteAccountName"],
                headers={"date": "Date", "description": "Description", "amount": "Amount", "currency": "Cur", "type": "Type", "remoteAccountName": "Counterparty"})
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


@transactions.command("details")
@click.argument("transaction_id")
@click.pass_context
def transaction_details(ctx, transaction_id: str):
    """Get details for a specific transaction."""
    try:
        client = get_client()
        encoded_id = quote(transaction_id, safe="")
        data = client.get(f"/personal/banking/transactions/{encoded_id}/details")
        if ctx.obj.get("json"):
            click.echo(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            _output(ctx, [data],
                    columns=["date", "description", "amount", "typeText", "remoteAccountNumber", "archiveReference"],
                    headers={"date": "Date", "description": "Description", "amount": "Amount", "typeText": "Type", "remoteAccountNumber": "Remote Account", "archiveReference": "Reference"})
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)


EXPORT_FIELDS = ["DATE", "DESCRIPTION", "INTEREST_DATE", "IN", "OUT", "TO_ACCOUNT", "FROM_ACCOUNT", "CATEGORY", "SUBCATEGORY"]


@transactions.command("export")
@click.option("--account-key", required=True, help="Account key from 'accounts list'")
@click.option("--from", "from_date", required=True, help="Start date (YYYY-MM-DD)")
@click.option("--to", "to_date", required=True, help="End date (YYYY-MM-DD)")
@click.option("--fields", default=None, help=f"Comma-separated fields: {','.join(EXPORT_FIELDS)}")
def export_transactions(account_key: str, from_date: str, to_date: str, fields: str | None):
    """Export transactions as CSV."""
    try:
        client = get_client()
        params = {"accountKey": account_key, "fromDate": from_date, "toDate": to_date}
        if fields:
            params["fields"] = fields
        data = client.get(
            "/personal/banking/transactions/export",
            params=params,
            accept="application/csv;charset=UTF-8",
            raw=True,
        )
        click.echo(data)
    except FinanceError as e:
        click.echo(json.dumps({"error": str(e)}), err=True)
        sys.exit(1)
