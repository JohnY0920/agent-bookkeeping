from app.tools.db import write_db


async def write_workpaper_entry(
    engagement_id: str,
    entry_type: str,
    title: str,
    content: str,
    source_event: dict | None = None,
    reference_id: str | None = None,
) -> dict:
    """
    Write a working paper entry. Called continuously throughout processing —
    not just at end-of-engagement. Every significant agent action should generate one.
    """
    row = await write_db(
        "workpaper_entries",
        {
            "engagement_id": engagement_id,
            "entry_type": entry_type,
            "title": title,
            "content": content,
            "source_event": source_event or {},
            "reference_id": reference_id,
            "created_by": "AGENT",
        },
    )
    return {
        "workpaper_entry_id": str(row["id"]),
        "reference_id": row.get("reference_id"),
        "status": "written",
    }
