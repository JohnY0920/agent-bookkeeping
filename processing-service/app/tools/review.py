from app.tools.db import write_db, update_db


async def create_review_item(
    engagement_id: str,
    item_type: str,
    description: str,
    severity: str = "medium",
    confidence_score: float | None = None,
    agent_reasoning: dict | None = None,
    processing_run_id: str | None = None,
) -> dict:
    """
    Flag an item for CPA review. Agents call this when:
    - Classification confidence < 0.80
    - Transaction confidence 0.50–0.85
    - Any year-end adjustment (requires_human always True for yearend_agent)
    - Reconciliation variance > $100
    """
    row = await write_db(
        "review_items",
        {
            "engagement_id": engagement_id,
            "processing_run_id": processing_run_id,
            "item_type": item_type,
            "description": description,
            "severity": severity,
            "confidence_score": confidence_score,
            "agent_reasoning": agent_reasoning or {},
            "status": "PENDING",
        },
    )
    return {
        "review_item_id": str(row["id"]),
        "item_type": item_type,
        "severity": severity,
        "status": "PENDING",
    }


async def update_review_item(
    review_item_id: str,
    status: str,
    resolved_by: str | None = None,
    resolution_note: str | None = None,
) -> dict:
    """Mark a review item as APPROVED, REJECTED, or ADJUSTED."""
    from datetime import datetime, timezone

    data: dict = {"status": status}
    if resolved_by:
        data["resolved_by"] = resolved_by
        data["resolved_at"] = datetime.now(timezone.utc).isoformat()
    if resolution_note:
        data["resolution_note"] = resolution_note

    row = await update_db("review_items", data, {"id": review_item_id})
    if not row:
        return {"error": f"Review item {review_item_id} not found"}
    return {"review_item_id": review_item_id, "status": status, "updated": True}
