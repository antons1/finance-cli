"""CLI entry point for the finance tool."""

import click

from finance.providers.sb1.commands.accounts import accounts
from finance.providers.sb1.commands.auth_commands import auth
from finance.providers.sb1.commands.transactions import transactions


@click.group()
@click.option("--json", "use_json", is_flag=True, help="Output in JSON format (required until human-readable format is implemented).")
@click.pass_context
def cli(ctx, use_json: bool):
    """Fetch personal financial data from bank APIs."""
    ctx.ensure_object(dict)
    ctx.obj["json"] = use_json


cli.add_command(auth)
cli.add_command(accounts)
cli.add_command(transactions)
