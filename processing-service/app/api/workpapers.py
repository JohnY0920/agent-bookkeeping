"""Workpaper entries — read-only listing for CPA review."""
from fastapi import APIRouter, HTTPException
from app.tools.db import query_db
from app.tools.storage import get_signed_url

router = APIRouter(prefix="/workpapers", tags=["workpapers"])


@router.get("")
async def list_workpaper_entries(
    engagement_id: str,
    firm_id: str,
    entry_type: str | None = None,
) -> list[dict]:
    """List workpaper entries for an engagement."""
    base = "SELECT * FROM workpaper_entries WHERE engagement_id = $1 AND firm_id = $2"
    params: list = [engagement_id, firm_id]
    if entry_type:
        base += f" AND entry_type = ${len(params) + 1}"
        params.append(entry_type)
    base += " ORDER BY created_at DESC"
    rows = await query_db(base, params)
    return [dict(r) for r in rows]


@router.get("/{entry_id}")
async def get_workpaper_entry(entry_id: str, firm_id: str) -> dict:
    rows = await query_db(
        "SELECT * FROM workpaper_entries WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [entry_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Workpaper entry not found")
    entry = dict(rows[0])
    # Attach signed URLs for any referenced documents
    if entry.get("source_event", {}).get("storage_path"):
        url = await get_signed_url(entry["source_event"]["storage_path"], expiration_minutes=30)
        entry["document_signed_url"] = url["signed_url"]
    return entry
