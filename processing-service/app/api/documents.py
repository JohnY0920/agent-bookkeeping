"""Document upload, list, and management endpoints."""
import os
import uuid
import tempfile
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.tools.db import write_db, query_db, update_db
from app.tools.storage import upload_file, delete_file, get_signed_url

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentResponse(BaseModel):
    id: str
    engagement_id: str
    firm_id: str
    file_name: str
    document_type: str | None
    status: str
    storage_path: str | None
    classification_confidence: float | None


@router.post("", status_code=201)
async def upload_document(
    engagement_id: str = Form(...),
    firm_id: str = Form(...),
    file: UploadFile = File(...),
) -> dict:
    """Upload a document file and create a DB record. Triggers document agent via worker."""
    suffix = os.path.splitext(file.filename or "")[1] or ".pdf"
    dest_path = f"{firm_id}/{engagement_id}/{uuid.uuid4()}{suffix}"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        upload_result = await upload_file(tmp_path, dest_path)
    finally:
        os.unlink(tmp_path)

    row = await write_db("documents", {
        "engagement_id": engagement_id,
        "firm_id": firm_id,
        "file_name": file.filename,
        "storage_path": upload_result["storage_path"],
        "status": "UPLOADED",
        "uploaded_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
    })

    # Dispatch document agent via Celery
    from workers.celery_tasks import run_agent
    run_agent.delay(
        agent_type="document",
        engagement_id=engagement_id,
        firm_id=firm_id,
        task_description=f"Process uploaded document: {file.filename}",
        context={"document_id": str(row["id"]), "storage_path": upload_result["storage_path"]},
    )

    return {"id": str(row["id"]), "storage_path": upload_result["storage_path"], "status": "UPLOADED"}


@router.get("")
async def list_documents(engagement_id: str, firm_id: str) -> list[dict]:
    """List all documents for an engagement."""
    rows = await query_db(
        "SELECT * FROM documents WHERE engagement_id = $1 AND firm_id = $2 ORDER BY created_at DESC",
        [engagement_id, firm_id],
    )
    return [dict(r) for r in rows]


@router.get("/{document_id}")
async def get_document(document_id: str, firm_id: str) -> dict:
    """Get document details and a fresh signed URL for viewing."""
    rows = await query_db(
        "SELECT * FROM documents WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [document_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = dict(rows[0])
    if doc.get("storage_path"):
        url_result = await get_signed_url(doc["storage_path"], expiration_minutes=30)
        doc["signed_url"] = url_result["signed_url"]
    return doc


@router.delete("/{document_id}", status_code=204)
async def delete_document(document_id: str, firm_id: str) -> None:
    """Delete a document record and its S3 file."""
    rows = await query_db(
        "SELECT storage_path FROM documents WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [document_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Document not found")
    storage_path = rows[0]["storage_path"]
    if storage_path:
        await delete_file(storage_path)
    await update_db("documents", {"status": "DELETED"}, {"id": document_id})
