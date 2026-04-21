from fastapi import APIRouter, HTTPException
from app.models.schemas import EngagementCreate, EngagementResponse
from app.tools.db import write_db, query_db

router = APIRouter(prefix="/engagements")


@router.post("", response_model=EngagementResponse, status_code=201)
async def create_engagement(payload: EngagementCreate) -> EngagementResponse:
    row = await write_db(
        "engagements",
        {
            "client_id": payload.client_id,
            "firm_id": payload.firm_id,
            "period_label": payload.period_label,
            "engagement_type": payload.engagement_type,
            "mode": "COLLECTION",
            "assigned_user_id": payload.assigned_user_id,
        },
    )
    return EngagementResponse(
        id=str(row["id"]),
        client_id=str(row["client_id"]),
        firm_id=str(row["firm_id"]),
        period_label=row["period_label"],
        engagement_type=row["engagement_type"],
        mode=row["mode"],
        current_summary=row.get("current_summary"),
    )


@router.get("/{engagement_id}", response_model=EngagementResponse)
async def get_engagement(engagement_id: str) -> EngagementResponse:
    rows = await query_db(
        "SELECT * FROM engagements WHERE id = $1 LIMIT 1",
        params=[engagement_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Engagement not found")
    row = rows[0]
    return EngagementResponse(
        id=str(row["id"]),
        client_id=str(row["client_id"]),
        firm_id=str(row["firm_id"]),
        period_label=row["period_label"],
        engagement_type=row["engagement_type"],
        mode=row["mode"],
        current_summary=row.get("current_summary"),
    )
