import pytest
from unittest.mock import AsyncMock, patch


class TestGetLessons:
    async def test_returns_lessons_list(self):
        mock_lessons = [
            {"id": "l-1", "lesson_content": "COSTCO = Office Supplies", "similarity": 0.92},
            {"id": "l-2", "lesson_content": "Q4 advertising is seasonal", "similarity": 0.81},
        ]
        with patch("app.tools.lesson.get_relevant_lessons", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = mock_lessons
            from app.tools.lesson import get_lessons
            result = await get_lessons("transaction", "client-001", "categorize COSTCO purchase")

        assert result["count"] == 2
        assert len(result["lessons"]) == 2
        mock_fn.assert_called_once_with("transaction", "client-001", "categorize COSTCO purchase", 5)

    async def test_empty_lessons(self):
        with patch("app.tools.lesson.get_relevant_lessons", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = []
            from app.tools.lesson import get_lessons
            result = await get_lessons("document", "client-001", "process T4 slip")

        assert result["count"] == 0
        assert result["lessons"] == []


class TestSaveLesson:
    async def test_saves_and_returns_id(self):
        with patch("app.tools.lesson._save_lesson", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"id": "lesson-999"}
            from app.tools.lesson import save_lesson
            result = await save_lesson(
                agent_type="transaction",
                firm_id="firm-001",
                scenario_description="COSTCO transaction categorization",
                lesson_content="COSTCO WHOLESALE transactions should be categorized as Office Supplies",
                client_id="client-001",
            )

        assert result["status"] == "saved"
        assert result["lesson_id"] == "lesson-999"

    async def test_client_id_is_optional(self):
        with patch("app.tools.lesson._save_lesson", new_callable=AsyncMock) as mock_fn:
            mock_fn.return_value = {"id": "lesson-888"}
            from app.tools.lesson import save_lesson
            result = await save_lesson(
                agent_type="document",
                firm_id="firm-001",
                scenario_description="General rule",
                lesson_content="T4 slips are always in the same format for this firm",
            )

        assert result["status"] == "saved"
        # client_id defaults to None (firm-wide lesson)
        call_kwargs = mock_fn.call_args[1]
        assert call_kwargs.get("client_id") is None
