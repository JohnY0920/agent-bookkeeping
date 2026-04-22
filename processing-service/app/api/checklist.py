"""Checklist management — CPA can edit, re-upload, or remove items."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.db import query_db, write_db, update_db

router = APIRouter(prefix="/checklist", tags=["checklist"])


class ChecklistItemCreate(BaseModel):
    engagement_id: str
    firm_id: str
    item_type: str
    label: str
    required: bool = True


class ChecklistItemUpdate(BaseModel):
    status: str | None = None
    label: str | None = None
    required: bool | None = None
    notes: str | None = None


@router.get("")
async def list_checklist(engagement_id: str, firm_id: str) -> list[dict]:
    """List all checklist items for an engagement."""
    rows = await query_db(
        "SELECT * FROM checklist_items WHERE engagement_id = $1 AND firm_id = $2 ORDER BY created_at",
        [engagement_id, firm_id],
    )
    return [dict(r) for r in rows]


@router.post("", status_code=201)
async def create_checklist_item(payload: ChecklistItemCreate) -> dict:
    """Add a custom checklist item."""
    row = await write_db("checklist_items", {
        "engagement_id": payload.engagement_id,
        "firm_id": payload.firm_id,
        "item_type": payload.item_type,
        "label": payload.label,
        "required": payload.required,
        "status": "PENDING",
    })
    return dict(row)


@router.put("/{item_id}")
async def update_checklist_item(item_id: str, firm_id: str, payload: ChecklistItemUpdate) -> dict:
    """Update a checklist item's status, label, or notes. Supports re-upload workflow."""
    rows = await query_db(
        "SELECT * FROM checklist_items WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [item_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    updates: dict = {}
    if payload.status is not None:
        updates["status"] = payload.status
        if payload.status == "RECEIVED":
            from datetime import datetime, timezone
            updates["received_at"] = datetime.now(timezone.utc)
        elif payload.status == "PENDING":
            # Re-upload: clear received_at so the item is treated as new
            updates["received_at"] = None
    if payload.label is not None:
        updates["label"] = payload.label
    if payload.required is not None:
        updates["required"] = payload.required

    if not updates:
        return dict(rows[0])

    updated = await update_db("checklist_items", updates, {"id": item_id})
    return dict(updated)


@router.delete("/{item_id}", status_code=204)
async def delete_checklist_item(item_id: str, firm_id: str) -> None:
    """Remove a checklist item (CPA decides it is no longer required)."""
    rows = await query_db(
        "SELECT id FROM checklist_items WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [item_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    await update_db("checklist_items", {"status": "REMOVED"}, {"id": item_id})


@router.post("/{item_id}/request-reupload")
async def request_reupload(item_id: str, firm_id: str) -> dict:
    """Mark a checklist item as needing re-upload (resets status to PENDING)."""
    rows = await query_db(
        "SELECT * FROM checklist_items WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [item_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Checklist item not found")
    updated = await update_db(
        "checklist_items",
        {"status": "PENDING", "received_at": None},
        {"id": item_id},
    )
    return {"id": item_id, "status": "PENDING", "message": "Item reset — awaiting re-upload"}
