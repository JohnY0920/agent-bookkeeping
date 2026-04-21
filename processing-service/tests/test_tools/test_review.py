import pytest
from unittest.mock import AsyncMock, patch


class TestCreateReviewItem:
    async def test_creates_pending_item(self):
        with patch("app.tools.review.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "rev-001", "status": "PENDING"}
            from app.tools.review import create_review_item
            result = await create_review_item(
                engagement_id="eng-001",
                item_type="classification_uncertain",
                description="Document could not be classified with confidence >= 0.80",
                severity="medium",
                confidence_score=0.65,
            )

        assert result["status"] == "PENDING"
        assert result["review_item_id"] == "rev-001"
        assert result["severity"] == "medium"

    async def test_agent_reasoning_defaults_to_empty_dict(self):
        with patch("app.tools.review.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "rev-001", "status": "PENDING"}
            from app.tools.review import create_review_item
            await create_review_item("eng-001", "test", "desc")

        data = mock_w.call_args[0][1]
        assert data["agent_reasoning"] == {}

    async def test_passes_confidence_score(self):
        with patch("app.tools.review.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "rev-001", "status": "PENDING"}
            from app.tools.review import create_review_item
            await create_review_item("eng-001", "type", "desc", confidence_score=0.72)

        data = mock_w.call_args[0][1]
        assert data["confidence_score"] == pytest.approx(0.72)

    async def test_critical_severity(self):
        with patch("app.tools.review.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "rev-001", "status": "PENDING"}
            from app.tools.review import create_review_item
            result = await create_review_item("eng-001", "type", "desc", severity="critical")

        assert result["severity"] == "critical"


class TestUpdateReviewItem:
    async def test_marks_approved(self):
        with patch("app.tools.review.update_db", new_callable=AsyncMock) as mock_u:
            mock_u.return_value = {"id": "rev-001", "status": "APPROVED"}
            from app.tools.review import update_review_item
            result = await update_review_item(
                "rev-001", "APPROVED",
                resolved_by="user-123",
                resolution_note="Confirmed as bank statement",
            )

        assert result["status"] == "APPROVED"
        data = mock_u.call_args[0][1]
        assert data["resolution_note"] == "Confirmed as bank statement"
        assert "resolved_at" in data

    async def test_returns_error_when_not_found(self):
        with patch("app.tools.review.update_db", new_callable=AsyncMock) as mock_u:
            mock_u.return_value = None
            from app.tools.review import update_review_item
            result = await update_review_item("bad-id", "APPROVED")

        assert "error" in result
