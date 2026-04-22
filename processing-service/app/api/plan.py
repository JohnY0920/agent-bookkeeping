"""Task plan and plan step management."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.db import query_db, write_db, update_db

router = APIRouter(prefix="/plan", tags=["plan"])


class PlanStepDecision(BaseModel):
    status: str  # COMPLETE | SKIPPED | FAILED
    result_summary: str | None = None


@router.get("")
async def get_plan(engagement_id: str, firm_id: str) -> dict:
    """Get the active task plan and all steps for an engagement."""
    plans = await query_db(
        "SELECT * FROM task_plans WHERE engagement_id = $1 AND status = 'ACTIVE' ORDER BY created_at DESC LIMIT 1",
        [engagement_id],
    )
    if not plans:
        return {"plan": None, "steps": []}
    plan = dict(plans[0])
    steps = await query_db(
        "SELECT * FROM plan_steps WHERE plan_id = $1 ORDER BY sort_order",
        [str(plan["id"])],
    )
    return {"plan": plan, "steps": [dict(s) for s in steps]}


@router.get("/steps/{step_id}")
async def get_plan_step(step_id: str, firm_id: str) -> dict:
    rows = await query_db(
        """SELECT ps.* FROM plan_steps ps
           JOIN task_plans tp ON ps.plan_id = tp.id
           JOIN engagements e ON tp.engagement_id = e.id
           WHERE ps.id = $1 AND e.firm_id = $2 LIMIT 1""",
        [step_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Plan step not found")
    return dict(rows[0])


@router.post("/steps/{step_id}/complete")
async def complete_plan_step(step_id: str, firm_id: str, payload: PlanStepDecision) -> dict:
    """CPA completes a human-required plan step."""
    rows = await query_db(
        """SELECT ps.* FROM plan_steps ps
           JOIN task_plans tp ON ps.plan_id = tp.id
           JOIN engagements e ON tp.engagement_id = e.id
           WHERE ps.id = $1 AND e.firm_id = $2 LIMIT 1""",
        [step_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Plan step not found")
    step = rows[0]
    if not step["requires_human"]:
        raise HTTPException(status_code=400, detail="Step does not require human action")

    from datetime import datetime, timezone
    updated = await update_db(
        "plan_steps",
        {
            "status": payload.status,
            "result_summary": payload.result_summary,
            "completed_at": datetime.now(timezone.utc),
        },
        {"id": step_id},
    )
    return dict(updated)


@router.get("/processing-runs")
async def list_processing_runs(engagement_id: str, firm_id: str) -> list[dict]:
    """List all agent processing runs for an engagement (for monitoring)."""
    rows = await query_db(
        "SELECT * FROM processing_runs WHERE engagement_id = $1 AND firm_id = $2 ORDER BY started_at DESC",
        [engagement_id, firm_id],
    )
    return [dict(r) for r in rows]
