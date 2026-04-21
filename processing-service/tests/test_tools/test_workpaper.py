import pytest
from unittest.mock import AsyncMock, patch


class TestWriteWorkpaperEntry:
    async def test_returns_written_status(self):
        with patch("app.tools.workpaper.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "wp-001", "reference_id": "WP-BK-2025-001"}
            from app.tools.workpaper import write_workpaper_entry
            result = await write_workpaper_entry(
                engagement_id="eng-001",
                entry_type="document_processed",
                title="Bank Statement — Jan 2025",
                content="Processed TD bank statement. 87 transactions found.",
            )

        assert result["status"] == "written"
        assert result["workpaper_entry_id"] == "wp-001"

    async def test_created_by_is_agent(self):
        with patch("app.tools.workpaper.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "wp-001", "reference_id": None}
            from app.tools.workpaper import write_workpaper_entry
            await write_workpaper_entry("eng-001", "test", "Title", "Content")

        data = mock_w.call_args[0][1]
        assert data["created_by"] == "AGENT"

    async def test_source_event_defaults_to_empty_dict(self):
        with patch("app.tools.workpaper.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "wp-001", "reference_id": None}
            from app.tools.workpaper import write_workpaper_entry
            await write_workpaper_entry("eng-001", "test", "Title", "Content")

        data = mock_w.call_args[0][1]
        assert data["source_event"] == {}

    async def test_optional_source_event(self):
        with patch("app.tools.workpaper.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "wp-001", "reference_id": None}
            from app.tools.workpaper import write_workpaper_entry
            event = {"document_id": "doc-123", "action": "uploaded"}
            await write_workpaper_entry("eng-001", "doc", "T", "C", source_event=event)

        data = mock_w.call_args[0][1]
        assert data["source_event"] == event
