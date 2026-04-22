import pytest
from unittest.mock import patch, MagicMock, AsyncMock


def _make_claude_response(text: str) -> MagicMock:
    """Build a fake Claude API messages response."""
    mock_resp = MagicMock()
    mock_block = MagicMock()
    mock_block.text = text
    mock_resp.content = [mock_block]
    return mock_resp


class TestExtractDocument:
    @pytest.fixture
    def sample_pdf(self, tmp_path):
        f = tmp_path / "test.pdf"
        f.write_bytes(b"%PDF-1.4 fake pdf content")
        return str(f)

    @pytest.fixture
    def sample_png(self, tmp_path):
        f = tmp_path / "test.png"
        f.write_bytes(b"\x89PNG\r\n\x1a\n fake png")
        return str(f)

    async def test_returns_extracted_text(self, sample_pdf):
        extracted = "## Bank Statement\nAccount: ****1234\n\nTotal: $5,000.00"
        mock_response = _make_claude_response(extracted)

        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("app.tools.ocr._get_client", return_value=mock_client):
            from app.tools.ocr import extract_document
            result = await extract_document(sample_pdf)

        assert "Bank Statement" in result["full_text"]
        assert "Total: $5,000.00" in result["full_text"]
        assert result["model"] == "claude-sonnet-4-6"

    async def test_page_structure(self, sample_pdf):
        mock_response = _make_claude_response("Single page content")
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("app.tools.ocr._get_client", return_value=mock_client):
            from app.tools.ocr import extract_document
            result = await extract_document(sample_pdf)

        assert result["page_count"] == 1
        assert result["pages"][0]["page"] == 0
        assert result["pages"][0]["text"] == "Single page content"
        assert result["full_text"] == "Single page content"

    async def test_file_path_in_result(self, sample_pdf):
        mock_response = _make_claude_response("text")
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("app.tools.ocr._get_client", return_value=mock_client):
            from app.tools.ocr import extract_document
            result = await extract_document(sample_pdf)

        assert result["file_path"] == sample_pdf

    async def test_uses_document_type_for_pdf(self, sample_pdf):
        """PDF files should use document content block type."""
        mock_response = _make_claude_response("content")
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("app.tools.ocr._get_client", return_value=mock_client):
            from app.tools.ocr import extract_document
            await extract_document(sample_pdf)

        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        content_block = messages[0]["content"][0]
        assert content_block["type"] == "document"
        assert content_block["source"]["media_type"] == "application/pdf"

    async def test_uses_image_type_for_png(self, sample_png):
        """Image files should use image content block type."""
        mock_response = _make_claude_response("content")
        mock_client = AsyncMock()
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with patch("app.tools.ocr._get_client", return_value=mock_client):
            from app.tools.ocr import extract_document
            await extract_document(sample_png)

        call_kwargs = mock_client.messages.create.call_args
        messages = call_kwargs.kwargs["messages"]
        content_block = messages[0]["content"][0]
        assert content_block["type"] == "image"
        assert content_block["source"]["media_type"] == "image/png"
