"""
State machine for engagement pipeline and processing run lifecycle.

Key invariant: agents always start from scratch — no state is resumed from a
previous run. If a run fails, a new run is created with a clean slate.
"""
from app.tools.db import write_db, query_db, update_db

ENGAGEMENT_TRANSITIONS = {
    "COLLECTION": "PROCESSING",
    "PROCESSING": "REVIEW",
    "REVIEW": "COMPLETE",
}


async def create_processing_run(
    engagement_id: str,
    firm_id: str,
    agent_type: str,
    task_description: str,
    prompt_version: str | None = None,
) -> str:
    """Create a new processing run record. Returns run_id."""
    row = await write_db("processing_runs", {
        "engagement_id": engagement_id,
        "firm_id": firm_id,
        "agent_type": agent_type,
        "task_description": task_description,
        "prompt_version": prompt_version,
        "status": "RUNNING",
    })
    return str(row["id"])


async def complete_processing_run(run_id: str, result_summary: str | None = None) -> None:
    from datetime import datetime, timezone
    await update_db(
        "processing_runs",
        {"status": "COMPLETE", "result_summary": result_summary, "completed_at": datetime.now(timezone.utc)},
        {"id": run_id},
    )


async def fail_processing_run(run_id: str, error_message: str | None = None) -> None:
    from datetime import datetime, timezone
    await update_db(
        "processing_runs",
        {"status": "FAILED", "error_message": error_message, "completed_at": datetime.now(timezone.utc)},
        {"id": run_id},
    )


async def pause_for_human(run_id: str, review_item_id: str | None = None) -> None:
    await update_db(
        "processing_runs",
        {"status": "WAITING_HUMAN"},
        {"id": run_id},
    )


async def record_human_evaluation(
    engagement_id: str,
    firm_id: str,
    pipeline_stage: str,
    decision: str,
    decision_note: str | None = None,
    review_item_id: str | None = None,
    processing_run_id: str | None = None,
    evaluator_user_id: str | None = None,
) -> dict:
    """Record a CPA decision at a human checkpoint."""
    from datetime import datetime, timezone
    row = await write_db("human_evaluation_events", {
        "engagement_id": engagement_id,
        "firm_id": firm_id,
        "pipeline_stage": pipeline_stage,
        "decision": decision,
        "decision_note": decision_note,
        "review_item_id": review_item_id,
        "processing_run_id": processing_run_id,
        "evaluator_user_id": evaluator_user_id,
        "occurred_at": datetime.now(timezone.utc),
    })
    return {"human_evaluation_id": str(row["id"]), "decision": decision}


async def advance_engagement_mode(engagement_id: str, expected_current_mode: str) -> dict:
    """Advance engagement to the next mode. Raises ValueError if not in expected mode."""
    rows = await query_db("SELECT mode FROM engagements WHERE id = $1", [engagement_id])
    if not rows:
        raise ValueError(f"Engagement {engagement_id} not found")
    current = rows[0]["mode"]
    if current != expected_current_mode:
        raise ValueError(f"Expected mode {expected_current_mode}, engagement is in {current}")
    next_mode = ENGAGEMENT_TRANSITIONS.get(current)
    if not next_mode:
        raise ValueError(f"No transition from mode {current}")
    updated = await update_db("engagements", {"mode": next_mode}, {"id": engagement_id})
    return {"previous_mode": current, "mode": next_mode, "engagement_id": engagement_id}


async def get_processing_runs(engagement_id: str, agent_type: str | None = None) -> list[dict]:
    """Return all processing runs for an engagement, most recent first."""
    if agent_type:
        return await query_db(
            "SELECT * FROM processing_runs WHERE engagement_id = $1 AND agent_type = $2 ORDER BY started_at DESC",
            [engagement_id, agent_type],
        )
    return await query_db(
        "SELECT * FROM processing_runs WHERE engagement_id = $1 ORDER BY started_at DESC",
        [engagement_id],
    )
