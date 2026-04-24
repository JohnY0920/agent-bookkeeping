import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestSendEmail:
    async def test_sends_via_sendgrid(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 202

        with patch("app.tools.email.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_class:
            mock_settings.SENDGRID_API_KEY = "SG.test-key"
            mock_settings.EMAIL_FROM = "noreply@firm.ca"

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            from app.tools.email import send_email
            result = await send_email(
                to_email="client@example.com",
                subject="Document request",
                body="Please upload your bank statement.",
                cc_emails=["accountant@firm.ca"],
            )

        assert result["status"] == "sent"
        assert result["to"] == "client@example.com"

    async def test_skips_when_no_api_key(self):
        with patch("app.tools.email.settings") as mock_settings:
            mock_settings.SENDGRID_API_KEY = ""
            from app.tools.email import send_email
            result = await send_email("a@b.com", "subject", "body")

        assert result["status"] == "skipped"

    async def test_returns_error_on_http_failure(self):
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"

        with patch("app.tools.email.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_class:
            mock_settings.SENDGRID_API_KEY = "SG.bad-key"
            mock_settings.EMAIL_FROM = "noreply@firm.ca"

            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_class.return_value = mock_client

            from app.tools.email import send_email
            result = await send_email("a@b.com", "subject", "body")

        assert result["status"] == "error"
        assert result["http_status"] == 401
