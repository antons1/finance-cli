"""Tests for transaction CLI commands."""

import json
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from finance.cli import cli

SAMPLE_TRANSACTIONS = {
    "transactions": [
        {
            "id": "tx-1-long-id",
            "nonUniqueId": "722041731687042571",
            "description": "REMA 1000 MIDTBYEN",
            "cleanedDescription": "REMA 1000 MIDTBYEN",
            "accountNumber": {"value": "18138922606", "formatted": "1813 89 22606", "unformatted": "18138922606"},
            "remoteAccountNumber": "60050608460",
            "remoteAccountName": "Rema 1000",
            "amount": -150,
            "date": 1774393200000,  # epoch ms
            "typeCode": "R_156",
            "typeText": "Varekjøp",
            "currencyCode": "NOK",
            "canShowDetails": True,
            "source": "HISTORIC",
            "isConfidential": False,
            "bookingStatus": "BOOKED",
            "accountName": "Regningskonto",
            "accountKey": "acc-1",
            "accountCurrency": "NOK",
            "isFromCurrencyAccount": False,
        },
        {
            "id": "tx-2-long-id",
            "nonUniqueId": "524402095889632571",
            "description": "SPOTIFY",
            "cleanedDescription": "SPOTIFY",
            "accountNumber": {"value": "18138922606", "formatted": "1813 89 22606", "unformatted": "18138922606"},
            "amount": -89,
            "date": 1774306800000,
            "typeCode": "R_714",
            "typeText": "Visa/Mastercard",
            "currencyCode": "NOK",
            "canShowDetails": True,
            "source": "HISTORIC",
            "isConfidential": False,
            "bookingStatus": "BOOKED",
            "accountName": "Regningskonto",
            "accountKey": "acc-1",
            "accountCurrency": "NOK",
            "isFromCurrencyAccount": False,
        },
    ]
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
        result = runner.invoke(cli, ["--json", "transactions", "list", "--account-key", "acc-1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2

    def test_includes_transaction_details(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_TRANSACTIONS
        result = runner.invoke(cli, ["--json", "transactions", "list", "--account-key", "acc-1"])
        data = json.loads(result.output)
        assert data[0]["description"] == "REMA 1000 MIDTBYEN"
        assert data[0]["amount"] == -150
        assert data[0]["date"] == "2026-03-24"  # epoch 1774393200000 -> date
        assert data[0]["type"] == "Varekjøp"
        assert data[0]["remoteAccountName"] == "Rema 1000"

    def test_requires_account_key(self, runner, mock_client):
        result = runner.invoke(cli, ["transactions", "list"])
        assert result.exit_code != 0

    def test_calls_correct_endpoint_with_params(self, runner, mock_client):
        mock_client.get.return_value = SAMPLE_TRANSACTIONS
        runner.invoke(cli, ["--json", "transactions", "list", "--account-key", "acc-1"])
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args
        assert "/personal/banking/transactions" in call_kwargs.args[0]
        assert call_kwargs.kwargs["params"]["accountKey"] == "acc-1"


class TestTransactionsDetails:
    def test_outputs_raw_response(self, runner, mock_client):
        detail = {"id": "tx-1", "description": "REMA", "fullDescription": "REMA 1000 MIDTBYEN 7011"}
        mock_client.get.return_value = detail
        result = runner.invoke(cli, ["--json", "transactions", "details", "tx-1"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["fullDescription"] == "REMA 1000 MIDTBYEN 7011"


class TestTransactionsExport:
    def test_calls_export_endpoint(self, runner, mock_client):
        mock_client.get.return_value = "Dato;Beskrivelse;Inn;Ut\n"
        result = runner.invoke(cli, ["transactions", "export", "--account-key", "acc-1", "--from", "2026-03-01", "--to", "2026-03-27"])
        assert result.exit_code == 0
        call_args = mock_client.get.call_args
        assert "export" in call_args.args[0]
        assert call_args.kwargs["accept"] == "application/csv;charset=UTF-8"
        assert call_args.kwargs["params"]["fromDate"] == "2026-03-01"

    def test_export_requires_dates(self, runner, mock_client):
        result = runner.invoke(cli, ["transactions", "export", "--account-key", "acc-1"])
        assert result.exit_code != 0
