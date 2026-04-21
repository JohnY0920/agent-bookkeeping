import pytest
from unittest.mock import AsyncMock, patch
from app.tools.gl_writer import write_gl_entry


MOCK_DB_ROW = {"id": "test-gl-uuid-1234"}


@pytest.fixture
def mock_write_db():
    with patch("app.tools.gl_writer.write_db", new_callable=AsyncMock) as mock:
        mock.return_value = MOCK_DB_ROW
        yield mock


class TestWriteGLEntry:
    async def test_returns_written_status(self, mock_write_db):
        result = await write_gl_entry(
            engagement_id="eng-001",
            account_code="4000",
            account_name="Revenue",
            amount=1000.00,
            entry_date="2025-01-15",
            description="Service revenue",
        )
        assert result["status"] == "written"
        assert result["gl_entry_id"] == "test-gl-uuid-1234"

    async def test_empty_source_chain_when_no_sources(self, mock_write_db):
        result = await write_gl_entry(
            engagement_id="eng-001",
            account_code="5000",
            account_name="Expenses",
            amount=500.00,
            entry_date="2025-01-15",
            description="Office supplies",
        )
        # source_chain should be an empty dict, not None
        assert isinstance(result["source_chain"], dict)
        assert "transaction" not in result["source_chain"]

    async def test_source_chain_includes_transaction(self, mock_write_db):
        result = await write_gl_entry(
            engagement_id="eng-001",
            account_code="4000",
            account_name="Revenue",
            amount=1000.00,
            entry_date="2025-01-15",
            description="Payment",
            source_transaction={
                "xero_id": "xero-abc-123",
                "description": "CLIENT PAYMENT",
                "date": "2025-01-15",
                "amount": 1000.00,
            },
        )
        assert "transaction" in result["source_chain"]
        assert result["source_chain"]["transaction"]["xero_id"] == "xero-abc-123"
        assert result["source_chain"]["transaction"]["bank_description"] == "CLIENT PAYMENT"

    async def test_source_chain_includes_document(self, mock_write_db):
        result = await write_gl_entry(
            engagement_id="eng-001",
            account_code="4000",
            account_name="Revenue",
            amount=2500.00,
            entry_date="2025-01-15",
            description="Invoice payment",
            source_document={
                "document_id": "doc-999",
                "type": "invoice",
                "institution": "Acme Corp",
                "page": 1,
                "line": 7,
                "storage_path": "gs://bucket/invoices/inv-001.pdf",
            },
        )
        assert "source_document" in result["source_chain"]
        doc = result["source_chain"]["source_document"]
        assert doc["document_id"] == "doc-999"
        assert doc["page"] == 1
        assert doc["line"] == 7

    async def test_source_chain_includes_categorization(self, mock_write_db):
        result = await write_gl_entry(
            engagement_id="eng-001",
            account_code="6100",
            account_name="Office Supplies",
            amount=150.00,
            entry_date="2025-01-15",
            description="Staples purchase",
            categorization_method="three_dimensional_analysis",
            categorization_confidence=0.92,
            agent_type="transaction",
            processing_run_id="run-456",
        )
        assert "categorization" in result["source_chain"]
        cat = result["source_chain"]["categorization"]
        assert cat["confidence"] == pytest.approx(0.92)
        assert cat["agent"] == "transaction"
        assert cat["method"] == "three_dimensional_analysis"

    async def test_full_source_chain(self, mock_write_db):
        result = await write_gl_entry(
            engagement_id="eng-001",
            account_code="6100",
            account_name="Office Supplies",
            amount=150.00,
            entry_date="2025-01-15",
            description="Staples",
            source_transaction={"xero_id": "x-1", "description": "STAPLES", "date": "2025-01-15", "amount": 150.00},
            source_document={"document_id": "d-1", "type": "receipt", "institution": "Staples", "page": 1, "line": 1, "storage_path": "gs://b/r.pdf"},
            categorization_method="description_match",
            categorization_confidence=0.88,
            agent_type="transaction",
        )
        chain = result["source_chain"]
        assert "transaction" in chain
        assert "source_document" in chain
        assert "categorization" in chain

    async def test_write_db_called_with_correct_table(self, mock_write_db):
        await write_gl_entry(
            engagement_id="eng-001",
            account_code="4000",
            account_name="Revenue",
            amount=1000.00,
            entry_date="2025-01-15",
            description="Test",
        )
        call_args = mock_write_db.call_args
        assert call_args[0][0] == "gl_entries"  # table name

    async def test_write_db_data_includes_created_by_agent(self, mock_write_db):
        await write_gl_entry(
            engagement_id="eng-001",
            account_code="4000",
            account_name="Revenue",
            amount=1000.00,
            entry_date="2025-01-15",
            description="Test",
        )
        data = mock_write_db.call_args[0][1]
        assert data["created_by"] == "AGENT"
        assert data["source_chain"] is not None
