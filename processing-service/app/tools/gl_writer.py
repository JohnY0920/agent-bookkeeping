from datetime import datetime, timezone
from app.tools.db import write_db


async def write_gl_entry(
    engagement_id: str,
    account_code: str,
    account_name: str,
    amount: float,
    entry_date: str,
    description: str,
    source_transaction: dict | None = None,
    source_document: dict | None = None,
    categorization_method: str | None = None,
    categorization_confidence: float | None = None,
    agent_type: str | None = None,
    processing_run_id: str | None = None,
) -> dict:
    """
    Write a GL entry with a deterministic source_chain citation.

    The agent decides WHAT to write; this tool guarantees the citation format.
    Never insert into gl_entries directly — always use this function.

    Returns: { gl_entry_id, source_chain, status }
    """
    source_chain: dict = {}

    if source_transaction:
        source_chain["transaction"] = {
            "xero_id": source_transaction.get("xero_id"),
            "bank_description": source_transaction.get("description"),
            "date": source_transaction.get("date"),
            "original_amount": source_transaction.get("amount"),
        }

    if source_document:
        source_chain["source_document"] = {
            "document_id": source_document.get("document_id"),
            "type": source_document.get("type"),
            "institution": source_document.get("institution"),
            "page": source_document.get("page"),
            "line": source_document.get("line"),
            "storage_path": source_document.get("storage_path"),
        }

    if categorization_method:
        source_chain["categorization"] = {
            "processing_run_id": processing_run_id,
            "agent": agent_type,
            "confidence": categorization_confidence,
            "method": categorization_method,
        }

    entry = await write_db(
        "gl_entries",
        {
            "engagement_id": engagement_id,
            "account_code": account_code,
            "account_name": account_name,
            "amount": amount,
            "entry_date": entry_date,
            "description": description,
            "source_chain": source_chain,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "AGENT",
        },
    )

    return {
        "gl_entry_id": str(entry["id"]),
        "source_chain": source_chain,
        "status": "written",
    }
