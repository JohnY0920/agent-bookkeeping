from app.tools.db import query_db


async def load_client_profile(client_id: str) -> dict | None:
    """Load client info and their active engagement for agent context."""
    rows = await query_db(
        """
        SELECT c.id, c.name, c.entity_type, c.industry_code,
               e.id AS engagement_id, e.engagement_type, e.mode, e.period_label
        FROM clients c
        LEFT JOIN engagements e
               ON e.client_id = c.id AND e.mode != 'COMPLETE'
        WHERE c.id = $1
        LIMIT 1
        """,
        params=[client_id],
    )

    if not rows:
        return None

    row = rows[0]
    return {
        "client_id": str(row["id"]),
        "name": row["name"],
        "entity_type": row["entity_type"],
        "industry_code": row["industry_code"],
        "active_engagement": {
            "id": str(row["engagement_id"]),
            "type": row["engagement_type"],
            "mode": row["mode"],
            "period": row["period_label"],
        }
        if row["engagement_id"]
        else None,
    }
