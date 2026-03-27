"""CLI entry point for the finance tool."""

import click

from finance.providers.sb1.commands.accounts import accounts
from finance.providers.sb1.commands.auth_commands import auth
from finance.providers.sb1.commands.transactions import transactions


@click.group()
def cli():
    """Fetch personal financial data from bank APIs."""


cli.add_command(auth)
cli.add_command(accounts)
cli.add_command(transactions)
