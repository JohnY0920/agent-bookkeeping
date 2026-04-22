"""Review queue — CPA approves, rejects, or modifies agent decisions."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.db import query_db
from app.tools.review import update_review_item
from app.state_machine import record_human_evaluation

router = APIRouter(prefix="/review", tags=["review"])


class ReviewDecision(BaseModel):
    decision: str  # APPROVED | REJECTED | MODIFIED
    resolution_note: str | None = None
    evaluator_user_id: str | None = None
    processing_run_id: str | None = None


@router.get("")
async def list_review_items(
    engagement_id: str,
    firm_id: str,
    status: str = "PENDING",
) -> list[dict]:
    """List review items filtered by status (default: PENDING)."""
    rows = await query_db(
        "SELECT * FROM review_items WHERE engagement_id = $1 AND firm_id = $2 AND status = $3 ORDER BY created_at DESC",
        [engagement_id, firm_id, status],
    )
    return [dict(r) for r in rows]


@router.get("/{item_id}")
async def get_review_item(item_id: str, firm_id: str) -> dict:
    rows = await query_db(
        "SELECT * FROM review_items WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [item_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Review item not found")
    return dict(rows[0])


@router.post("/{item_id}/decide")
async def decide_review_item(item_id: str, firm_id: str, payload: ReviewDecision) -> dict:
    """CPA submits a decision on a review item. Records human evaluation event."""
    rows = await query_db(
        "SELECT * FROM review_items WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [item_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Review item not found")
    item = rows[0]

    if item["status"] != "PENDING":
        raise HTTPException(status_code=409, detail=f"Item is already {item['status']}")

    # Map decision to review_items status
    status_map = {"APPROVED": "APPROVED", "REJECTED": "REJECTED", "MODIFIED": "APPROVED"}
    updated = await update_review_item(
        item_id,
        status_map[payload.decision],
        resolution_note=payload.resolution_note,
    )

    # Record human evaluation event for audit trail and analytics
    await record_human_evaluation(
        engagement_id=str(item["engagement_id"]),
        firm_id=firm_id,
        pipeline_stage=item["item_type"],
        decision=payload.decision,
        decision_note=payload.resolution_note,
        review_item_id=item_id,
        processing_run_id=payload.processing_run_id,
        evaluator_user_id=payload.evaluator_user_id,
    )

    return updated


@router.get("/analytics/summary")
async def review_analytics(engagement_id: str, firm_id: str) -> dict:
    """Summary of human evaluation touchpoints for an engagement."""
    rows = await query_db(
        """SELECT pipeline_stage, decision, COUNT(*) as count
           FROM human_evaluation_events
           WHERE engagement_id = $1 AND firm_id = $2
           GROUP BY pipeline_stage, decision
           ORDER BY pipeline_stage, decision""",
        [engagement_id, firm_id],
    )
    return {"engagement_id": engagement_id, "breakdown": [dict(r) for r in rows]}
