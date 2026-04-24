import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestEncryptDecrypt:
    def test_encrypt_decrypt_roundtrip(self):
        from cryptography.fernet import Fernet
        key = Fernet.generate_key().decode()

        with patch("app.tools.xero.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = key
            from app.tools.xero import _encrypt_token, _decrypt_token
            encrypted = _encrypt_token("my-secret-token")
            assert encrypted != "my-secret-token"
            decrypted = _decrypt_token(encrypted)
            assert decrypted == "my-secret-token"

    def test_no_encryption_key_passes_through(self):
        with patch("app.tools.xero.settings") as mock_settings:
            mock_settings.TOKEN_ENCRYPTION_KEY = ""
            from app.tools.xero import _encrypt_token, _decrypt_token
            assert _encrypt_token("plain") == "plain"
            assert _decrypt_token("plain") == "plain"


class TestPullTransactions:
    async def test_writes_transactions_to_db(self):
        mock_txn = {
            "BankTransactionID": "xero-001",
            "Type": "SPEND",
            "DateString": "2025-01-15",
            "Total": "250.00",
            "Reference": "Office supplies",
            "Contact": {"Name": "Staples Canada"},
            "BankAccount": {"AccountID": "ba-001"},
        }
        xero_response = {"BankTransactions": [mock_txn]}

        mock_conn = {
            "id": "conn-001",
            "tenant_id": "tenant-001",
            "access_token": "encrypted-token",
            "refresh_token": "encrypted-refresh",
            "token_expiry": None,
        }

        with patch("app.tools.xero._get_connection", AsyncMock(return_value=mock_conn)), \
             patch("app.tools.xero._refresh_if_needed", AsyncMock(return_value="valid-token")), \
             patch("app.tools.xero._xero_get", AsyncMock(return_value=xero_response)), \
             patch("app.tools.xero.query_db", AsyncMock(return_value=[])), \
             patch("app.tools.xero.write_db", AsyncMock(return_value={"id": "t-001"})) as mock_write:

            from app.tools.xero import pull_transactions
            result = await pull_transactions(
                client_id="client-001",
                firm_id="firm-001",
                engagement_id="eng-001",
                from_date="2025-01-01",
                to_date="2025-01-31",
            )

        assert result["written"] == 1
        assert result["total_in_page"] == 1
        call_data = mock_write.call_args[0][1]
        assert call_data["xero_id"] == "xero-001"
        assert float(call_data["amount"]) == -250.0  # SPEND → negative

    async def test_skips_already_imported_transactions(self):
        xero_response = {"BankTransactions": [{"BankTransactionID": "xero-dup", "Type": "RECEIVE", "DateString": "2025-01-15", "Total": "100", "Contact": {}, "BankAccount": {}}]}

        with patch("app.tools.xero._get_connection", AsyncMock(return_value={"id": "conn-001", "tenant_id": "t1", "access_token": "enc", "refresh_token": "enc", "token_expiry": None})), \
             patch("app.tools.xero._refresh_if_needed", AsyncMock(return_value="token")), \
             patch("app.tools.xero._xero_get", AsyncMock(return_value=xero_response)), \
             patch("app.tools.xero.query_db", AsyncMock(return_value=[{"id": "existing"}])), \
             patch("app.tools.xero.write_db", AsyncMock()) as mock_write:

            from app.tools.xero import pull_transactions
            result = await pull_transactions("c", "f", "e", "2025-01-01", "2025-01-31")

        assert result["written"] == 0
        mock_write.assert_not_called()

    async def test_receive_transactions_are_positive(self):
        xero_response = {"BankTransactions": [{"BankTransactionID": "xero-r1", "Type": "RECEIVE", "DateString": "2025-01-10", "Total": "500", "Contact": {}, "BankAccount": {}, "Reference": "Client payment"}]}

        with patch("app.tools.xero._get_connection", AsyncMock(return_value={"id": "c", "tenant_id": "t", "access_token": "e", "refresh_token": "r", "token_expiry": None})), \
             patch("app.tools.xero._refresh_if_needed", AsyncMock(return_value="token")), \
             patch("app.tools.xero._xero_get", AsyncMock(return_value=xero_response)), \
             patch("app.tools.xero.query_db", AsyncMock(return_value=[])), \
             patch("app.tools.xero.write_db", AsyncMock(return_value={"id": "t-001"})) as mock_write:

            from app.tools.xero import pull_transactions
            await pull_transactions("c", "f", "e", "2025-01-01", "2025-01-31")

        call_data = mock_write.call_args[0][1]
        assert float(call_data["amount"]) == 500.0  # RECEIVE → positive

    async def test_no_connection_returns_error(self):
        with patch("app.tools.xero._get_connection", AsyncMock(return_value=None)):
            from app.tools.xero import pull_transactions
            result = await pull_transactions("c", "f", "e", "2025-01-01", "2025-01-31")

        assert "error" in result


class TestPullChartOfAccounts:
    async def test_returns_accounts_list(self):
        xero_resp = {"Accounts": [
            {"Code": "4000", "Name": "Sales Revenue", "Type": "REVENUE", "TaxType": "OUTPUT"},
            {"Code": "5100", "Name": "Wages", "Type": "EXPENSE", "TaxType": "NONE"},
        ]}

        with patch("app.tools.xero._get_connection", AsyncMock(return_value={"id": "c", "tenant_id": "t", "access_token": "e", "refresh_token": "r", "token_expiry": None})), \
             patch("app.tools.xero._refresh_if_needed", AsyncMock(return_value="token")), \
             patch("app.tools.xero._xero_get", AsyncMock(return_value=xero_resp)):

            from app.tools.xero import pull_chart_of_accounts
            result = await pull_chart_of_accounts("client-001", "firm-001")

        assert result["account_count"] == 2
        assert result["accounts"][0]["code"] == "4000"
