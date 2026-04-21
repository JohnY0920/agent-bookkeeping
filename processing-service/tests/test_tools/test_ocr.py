import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock


def _make_mock_ocr_response(pages: list[dict]) -> MagicMock:
    """Build a fake Mistral OCR response object."""
    mock_resp = MagicMock()
    mock_pages = []
    for p in pages:
        mp = MagicMock()
        mp.index = p["index"]
        mp.markdown = p["markdown"]
        mock_pages.append(mp)
    mock_resp.pages = mock_pages
    return mock_resp


class TestMistralOCR:
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        """Create a minimal temp file to simulate a PDF."""
        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4 fake pdf content")
        return str(f)

    async def test_returns_extracted_text(self, sample_pdf):
        mock_response = _make_mock_ocr_response([
            {"index": 0, "markdown": "## Bank Statement\nAccount: ****1234"},
            {"index": 1, "markdown": "Total: $5,000.00"},
        ])

        with patch("app.tools.ocr._get_mistral_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.ocr.process.return_value = mock_response
            mock_client_fn.return_value = mock_client

            from app.tools.ocr import mistral_ocr
            result = await mistral_ocr(sample_pdf)

        assert result["page_count"] == 2
        assert "Bank Statement" in result["full_text"]
        assert "Total: $5,000.00" in result["full_text"]
        assert result["model"] == "mistral-ocr-latest"

    async def test_pages_are_indexed(self, sample_pdf):
        mock_response = _make_mock_ocr_response([
            {"index": 0, "markdown": "Page 1 content"},
            {"index": 1, "markdown": "Page 2 content"},
        ])

        with patch("app.tools.ocr._get_mistral_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.ocr.process.return_value = mock_response
            mock_client_fn.return_value = mock_client

            from app.tools.ocr import mistral_ocr
            result = await mistral_ocr(sample_pdf)

        assert result["pages"][0]["page"] == 0
        assert result["pages"][1]["page"] == 1

    async def test_single_page_document(self, sample_pdf):
        mock_response = _make_mock_ocr_response([
            {"index": 0, "markdown": "Single page content"},
        ])

        with patch("app.tools.ocr._get_mistral_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.ocr.process.return_value = mock_response
            mock_client_fn.return_value = mock_client

            from app.tools.ocr import mistral_ocr
            result = await mistral_ocr(sample_pdf)

        assert result["page_count"] == 1
        assert result["full_text"] == "Single page content"

    async def test_file_path_in_result(self, sample_pdf):
        mock_response = _make_mock_ocr_response([{"index": 0, "markdown": "text"}])

        with patch("app.tools.ocr._get_mistral_client") as mock_client_fn:
            mock_client = MagicMock()
            mock_client.ocr.process.return_value = mock_response
            mock_client_fn.return_value = mock_client

            from app.tools.ocr import mistral_ocr
            result = await mistral_ocr(sample_pdf)

        assert result["file_path"] == sample_pdf
