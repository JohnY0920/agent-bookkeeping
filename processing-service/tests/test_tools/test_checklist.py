import pytest
from unittest.mock import AsyncMock, patch


class TestUpdateChecklistItem:
    async def test_marks_item_received(self):
        mock_row = {"id": "item-1", "status": "RECEIVED", "received_at": "2025-01-01"}
        with patch("app.tools.checklist.update_db", new_callable=AsyncMock) as mock_upd:
            mock_upd.return_value = mock_row
            from app.tools.checklist import update_checklist_item
            result = await update_checklist_item("item-1", "RECEIVED")

        assert result["status"] == "RECEIVED"
        assert result["updated"] is True
        # received_at should be set when marking RECEIVED
        call_data = mock_upd.call_args[0][1]
        assert "received_at" in call_data

    async def test_sets_document_id(self):
        with patch("app.tools.checklist.update_db", new_callable=AsyncMock) as mock_upd:
            mock_upd.return_value = {"id": "item-1", "status": "RECEIVED"}
            from app.tools.checklist import update_checklist_item
            await update_checklist_item("item-1", "RECEIVED", document_id="doc-999")

        call_data = mock_upd.call_args[0][1]
        assert call_data["document_id"] == "doc-999"

    async def test_not_applicable_no_received_at(self):
        with patch("app.tools.checklist.update_db", new_callable=AsyncMock) as mock_upd:
            mock_upd.return_value = {"id": "item-1", "status": "NOT_APPLICABLE"}
            from app.tools.checklist import update_checklist_item
            await update_checklist_item("item-1", "NOT_APPLICABLE")

        call_data = mock_upd.call_args[0][1]
        assert "received_at" not in call_data

    async def test_returns_error_when_not_found(self):
        with patch("app.tools.checklist.update_db", new_callable=AsyncMock) as mock_upd:
            mock_upd.return_value = None
            from app.tools.checklist import update_checklist_item
            result = await update_checklist_item("nonexistent", "RECEIVED")

        assert "error" in result


class TestCheckCompleteness:
    async def test_all_received(self):
        with patch("app.tools.checklist.query_db", new_callable=AsyncMock) as mock_q:
            mock_q.return_value = [{"total_required": 3, "completed": 3}]
            from app.tools.checklist import check_completeness
            result = await check_completeness("eng-001")

        assert result["is_complete"] is True
        assert result["completion_percentage"] == 100

    async def test_partially_complete(self):
        with patch("app.tools.checklist.query_db", new_callable=AsyncMock) as mock_q:
            mock_q.return_value = [{"total_required": 4, "completed": 2}]
            from app.tools.checklist import check_completeness
            result = await check_completeness("eng-001")

        assert result["is_complete"] is False
        assert result["completion_percentage"] == 50

    async def test_no_items(self):
        with patch("app.tools.checklist.query_db", new_callable=AsyncMock) as mock_q:
            mock_q.return_value = [{"total_required": 0, "completed": 0}]
            from app.tools.checklist import check_completeness
            result = await check_completeness("eng-001")

        assert result["is_complete"] is False
        assert result["completion_percentage"] == 0
