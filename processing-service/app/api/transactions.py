"""Transaction list and sync endpoints."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.tools.db import query_db

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.get("")
async def list_transactions(
    engagement_id: str,
    firm_id: str,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List transactions for an engagement with optional status filter."""
    base = "SELECT * FROM transactions WHERE engagement_id = $1 AND firm_id = $2"
    params: list = [engagement_id, firm_id]
    if status:
        base += f" AND categorization_status = ${len(params) + 1}"
        params.append(status)
    base += f" ORDER BY date DESC, created_at DESC LIMIT ${len(params)+1} OFFSET ${len(params)+2}"
    params += [limit, offset]

    rows = await query_db(base, params)
    count_rows = await query_db(
        "SELECT COUNT(*) as total FROM transactions WHERE engagement_id = $1 AND firm_id = $2",
        [engagement_id, firm_id],
    )
    return {
        "total": count_rows[0]["total"],
        "limit": limit,
        "offset": offset,
        "transactions": [dict(r) for r in rows],
    }


@router.get("/summary")
async def transaction_summary(engagement_id: str, firm_id: str) -> dict:
    """Categorization status breakdown for an engagement."""
    rows = await query_db(
        """SELECT categorization_status, COUNT(*) as count, SUM(ABS(amount)) as total_amount
           FROM transactions WHERE engagement_id = $1 AND firm_id = $2
           GROUP BY categorization_status ORDER BY categorization_status""",
        [engagement_id, firm_id],
    )
    return {"engagement_id": engagement_id, "breakdown": [dict(r) for r in rows]}


@router.get("/{transaction_id}")
async def get_transaction(transaction_id: str, firm_id: str) -> dict:
    rows = await query_db(
        "SELECT * FROM transactions WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [transaction_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return dict(rows[0])


class SyncRequest(BaseModel):
    client_id: str
    firm_id: str
    engagement_id: str
    from_date: str
    to_date: str


@router.post("/sync")
async def sync_transactions(payload: SyncRequest) -> dict:
    """Trigger a Xero transaction pull via Celery worker."""
    from workers.celery_tasks import run_agent
    run_agent.delay(
        agent_type="transaction",
        engagement_id=payload.engagement_id,
        firm_id=payload.firm_id,
        task_description=f"Pull and categorize Xero transactions from {payload.from_date} to {payload.to_date}",
        context={
            "client_id": payload.client_id,
            "from_date": payload.from_date,
            "to_date": payload.to_date,
        },
    )
    return {"status": "queued", "message": "Transaction sync dispatched"}
