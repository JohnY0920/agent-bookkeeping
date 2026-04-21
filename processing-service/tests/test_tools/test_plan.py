import pytest
from unittest.mock import AsyncMock, patch


class TestCreatePlanStep:
    async def test_creates_pending_step(self):
        with patch("app.tools.plan.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "step-001", "status": "PENDING", "requires_human": False}
            from app.tools.plan import create_plan_step
            result = await create_plan_step(
                plan_id="plan-001",
                agent_type="document",
                description="Process uploaded bank statement",
                sort_order=1,
            )

        assert result["status"] == "PENDING"
        assert result["plan_step_id"] == "step-001"

    async def test_human_required_flag(self):
        with patch("app.tools.plan.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "step-002", "status": "PENDING", "requires_human": True}
            from app.tools.plan import create_plan_step
            result = await create_plan_step(
                plan_id="plan-001",
                agent_type="yearend",
                description="CCA adjustments — requires CPA approval",
                sort_order=5,
                requires_human=True,
            )

        assert result["requires_human"] is True
        data = mock_w.call_args[0][1]
        assert data["requires_human"] is True

    async def test_depends_on_defaults_to_empty_list(self):
        with patch("app.tools.plan.write_db", new_callable=AsyncMock) as mock_w:
            mock_w.return_value = {"id": "step-001", "status": "PENDING", "requires_human": False}
            from app.tools.plan import create_plan_step
            await create_plan_step("plan-001", "document", "Process doc", 1)

        data = mock_w.call_args[0][1]
        assert data["depends_on"] == []


class TestUpdatePlanStep:
    async def test_marks_complete(self):
        with patch("app.tools.plan.update_db", new_callable=AsyncMock) as mock_u:
            mock_u.return_value = {"id": "step-001", "status": "COMPLETE"}
            from app.tools.plan import update_plan_step
            result = await update_plan_step("step-001", "COMPLETE", result_summary="Done")

        assert result["status"] == "COMPLETE"
        data = mock_u.call_args[0][1]
        assert "completed_at" in data
        assert data["result_summary"] == "Done"

    async def test_running_sets_started_at(self):
        with patch("app.tools.plan.update_db", new_callable=AsyncMock) as mock_u:
            mock_u.return_value = {"id": "step-001", "status": "RUNNING"}
            from app.tools.plan import update_plan_step
            await update_plan_step("step-001", "RUNNING")

        data = mock_u.call_args[0][1]
        assert "started_at" in data
        assert "completed_at" not in data

    async def test_returns_error_when_not_found(self):
        with patch("app.tools.plan.update_db", new_callable=AsyncMock) as mock_u:
            mock_u.return_value = None
            from app.tools.plan import update_plan_step
            result = await update_plan_step("bad-id", "COMPLETE")

        assert "error" in result
