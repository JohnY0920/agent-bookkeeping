from datetime import datetime, timezone
from app.tools.db import query_db, update_db


async def update_checklist_item(
    checklist_item_id: str,
    status: str,
    document_id: str | None = None,
) -> dict:
    """Update a checklist item status. Use 'RECEIVED' when a document is uploaded."""
    data: dict = {"status": status}
    if status == "RECEIVED":
        data["received_at"] = datetime.now(timezone.utc).isoformat()
    if document_id:
        data["document_id"] = document_id

    row = await update_db("checklist_items", data, {"id": checklist_item_id})
    if not row:
        return {"error": f"Checklist item {checklist_item_id} not found"}
    return {
        "checklist_item_id": checklist_item_id,
        "status": status,
        "updated": True,
    }


async def check_completeness(engagement_id: str) -> dict:
    """Return how many required checklist items are received vs total required."""
    rows = await query_db(
        """
        SELECT
            COUNT(*) FILTER (WHERE required = true)                                           AS total_required,
            COUNT(*) FILTER (WHERE required = true
                             AND status IN ('RECEIVED', 'VERIFIED', 'NOT_APPLICABLE'))        AS completed
        FROM checklist_items
        WHERE engagement_id = $1
        """,
        params=[engagement_id],
    )
    row = rows[0]
    total = int(row["total_required"])
    completed = int(row["completed"])
    return {
        "engagement_id": engagement_id,
        "total_required": total,
        "completed": completed,
        "is_complete": total > 0 and completed >= total,
        "completion_percentage": round(completed / total * 100) if total > 0 else 0,
    }
