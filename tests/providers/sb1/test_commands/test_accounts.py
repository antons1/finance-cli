"""Tests for account CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from finance.cli import cli

SAMPLE_ACCOUNTS = {
    "accounts": [
        {
            "key": "acc-1",
            "accountNumber": "12345678901",
            "iban": "NO5512345678901",
            "name": "Brukskonto",
            "description": "BRUKSKONTO",
            "balance": 15000.50,
            "availableBalance": 14500.00,
            "currencyCode": "NOK",
            "owner": {"name": "Ola Nordmann", "firstName": "Ola", "lastName": "Nordmann", "type": "personal"},
            "type": "USER",
        },
        {
            "key": "acc-2",
            "accountNumber": "98765432109",
            "iban": "NO7798765432109",
            "name": "Sparekonto",
            "description": "SPAREKONTO",
            "balance": 250000.00,
            "availableBalance": 250000.00,
            "currencyCode": "NOK",
            "owner": {"name": "Ola Nordmann", "firstName": "Ola", "lastName": "Nordmann", "type": "personal"},
            "type": "SAVING",
        },
    ],
    "errors": [],
}


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_client():
    with patch("finance.providers.sb1.commands.accounts.get_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestAccountsList:
    def test_outputs_json_array(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_ACCOUNTS
        result = runner.invoke(cli, ["accounts", "list"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    def test_includes_account_details(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_ACCOUNTS
        result = runner.invoke(cli, ["accounts", "list"])
        data = json.loads(result.output)
        assert data[0]["name"] == "Brukskonto"
        assert data[0]["accountNumber"] == "12345678901"
        assert data[0]["balance"] == 15000.50
        assert data[0]["key"] == "acc-1"
        assert data[0]["owner"] == "Ola Nordmann"

    def test_calls_correct_endpoint(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_ACCOUNTS
        runner.invoke(cli, ["accounts", "list"])
        mock_client.get.assert_called_once_with("/personal/banking/accounts")


class TestAccountsGet:
    def test_outputs_single_account(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_ACCOUNTS["accounts"][0]
        result = runner.invoke(cli, ["accounts", "get", "acc-1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["name"] == "Brukskonto"

    def test_calls_correct_endpoint(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_ACCOUNTS["accounts"][0]
        runner.invoke(cli, ["accounts", "get", "acc-1"])
        mock_client.get.assert_called_once_with("/personal/banking/accounts/acc-1")


class TestAccountsBalance:
    def test_outputs_balance_summary(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_ACCOUNTS
        result = runner.invoke(cli, ["accounts", "balance"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2
        assert data[0]["balance"] == 15000.50
        assert data[1]["balance"] == 250000.00


class TestErrorCases:
    def test_api_error_returns_exit_code_1(self, runner, mock_client):
        from finance.exceptions import ApiError
        mock_client.get.side_effect = ApiError(500, "Internal error")
        result = runner.invoke(cli, ["accounts", "list"])
        assert result.exit_code == 1

    def test_auth_error_returns_exit_code_1(self, runner, mock_client):
        from finance.exceptions import AuthError
        mock_client.get.side_effect = AuthError("Not authenticated")
        result = runner.invoke(cli, ["accounts", "list"])
        assert result.exit_code == 1
