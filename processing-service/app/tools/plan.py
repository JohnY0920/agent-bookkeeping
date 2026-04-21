from app.tools.db import write_db, update_db


async def create_plan_step(
    plan_id: str,
    agent_type: str,
    description: str,
    sort_order: int,
    depends_on: list[str] | None = None,
    requires_human: bool = False,
) -> dict:
    """Add a step to a task plan."""
    row = await write_db(
        "plan_steps",
        {
            "plan_id": plan_id,
            "agent_type": agent_type,
            "description": description,
            "sort_order": sort_order,
            "depends_on": depends_on or [],
            "requires_human": requires_human,
            "status": "PENDING",
        },
    )
    return {
        "plan_step_id": str(row["id"]),
        "agent_type": agent_type,
        "status": "PENDING",
        "requires_human": requires_human,
    }


async def update_plan_step(
    step_id: str,
    status: str,
    result_summary: str | None = None,
    error_message: str | None = None,
) -> dict:
    """Update the status of a plan step."""
    from datetime import datetime, timezone

    data: dict = {"status": status}
    now = datetime.now(timezone.utc).isoformat()

    if status == "RUNNING":
        data["started_at"] = now
    elif status in ("COMPLETE", "FAILED", "WAITING_HUMAN", "SKIPPED"):
        data["completed_at"] = now

    if result_summary:
        data["result_summary"] = result_summary
    if error_message:
        data["error_message"] = error_message

    row = await update_db("plan_steps", data, {"id": step_id})
    if not row:
        return {"error": f"Plan step {step_id} not found"}
    return {"plan_step_id": step_id, "status": status, "updated": True}
