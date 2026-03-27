"""Tests for transaction CLI commands — written before implementation."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from finance.cli import cli

SAMPLE_TRANSACTIONS = {
    "transactions": [
        {
            "id": "tx-1",
            "amount": {"amount": -150.00, "currencyCode": "NOK"},
            "accountingDate": "2026-03-25",
            "description": "REMA 1000 MIDTBYEN",
            "transactionType": "Varekjop",
        },
        {
            "id": "tx-2",
            "amount": {"amount": -89.00, "currencyCode": "NOK"},
            "accountingDate": "2026-03-24",
            "description": "SPOTIFY",
            "transactionType": "Varekjop",
        },
    ]
}

SAMPLE_DETAIL = {
    "id": "tx-1",
    "amount": {"amount": -150.00, "currencyCode": "NOK"},
    "accountingDate": "2026-03-25",
    "description": "REMA 1000 MIDTBYEN",
    "fullDescription": "REMA 1000 MIDTBYEN 7011 TRONDHEIM",
    "transactionType": "Varekjop",
    "archiveReference": "ref-123",
}


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def mock_client():
    with patch("finance.providers.sb1.commands.transactions.get_client") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestTransactionsList:
    def test_outputs_json_array(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_TRANSACTIONS
        result = runner.invoke(cli, ["transactions", "list", "--account-key", "acc-1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    def test_includes_transaction_details(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_TRANSACTIONS
        result = runner.invoke(cli, ["transactions", "list", "--account-key", "acc-1"])
        data = json.loads(result.output)
        assert data[0]["description"] == "REMA 1000 MIDTBYEN"
        assert data[0]["amount"] == -150.00
        assert data[0]["date"] == "2026-03-25"

    def test_requires_account_key(self, runner, mock_client):
        result = runner.invoke(cli, ["transactions", "list"])
        assert result.exit_code != 0

    def test_calls_correct_endpoint_with_params(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_TRANSACTIONS
        runner.invoke(cli, ["transactions", "list", "--account-key", "acc-1"])
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args
        assert "/personal/banking/transactions" in call_kwargs.args[0]
        assert call_kwargs.kwargs["params"]["accountKey"] == "acc-1"


class TestTransactionsDetails:
    def test_outputs_single_transaction(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_DETAIL
        result = runner.invoke(cli, ["transactions", "details", "tx-1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["fullDescription"] == "REMA 1000 MIDTBYEN 7011 TRONDHEIM"


class TestTransactionsExport:
    def test_calls_export_endpoint(self, runner, mock_client):
        mock_client.get.return_value = {"export": "csv-data"}
        runner.invoke(cli, ["transactions", "export", "--account-key", "acc-1"])
        call_args = mock_client.get.call_args
        assert "export" in call_args.args[0]
