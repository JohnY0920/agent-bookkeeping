"""GL entries — read-only API with source_chain drill-down."""
from fastapi import APIRouter, HTTPException
from app.tools.db import query_db

router = APIRouter(prefix="/gl", tags=["gl"])


@router.get("")
async def list_gl_entries(
    engagement_id: str,
    firm_id: str,
    account_code: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """List GL entries for an engagement with optional account filter."""
    base = "SELECT * FROM gl_entries WHERE engagement_id = $1 AND firm_id = $2"
    params: list = [engagement_id, firm_id]
    if account_code:
        base += f" AND account_code = ${len(params) + 1}"
        params.append(account_code)
    base += f" ORDER BY entry_date DESC, created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
    params += [limit, offset]

    rows = await query_db(base, params)

    count_rows = await query_db(
        "SELECT COUNT(*) as total FROM gl_entries WHERE engagement_id = $1 AND firm_id = $2",
        [engagement_id, firm_id],
    )
    return {
        "total": count_rows[0]["total"],
        "limit": limit,
        "offset": offset,
        "entries": [dict(r) for r in rows],
    }


@router.get("/{entry_id}")
async def get_gl_entry(entry_id: str, firm_id: str) -> dict:
    """Get a single GL entry with its full source_chain."""
    rows = await query_db(
        "SELECT * FROM gl_entries WHERE id = $1 AND firm_id = $2 LIMIT 1",
        [entry_id, firm_id],
    )
    if not rows:
        raise HTTPException(status_code=404, detail="GL entry not found")
    return dict(rows[0])


@router.get("/summary/by-account")
async def gl_summary_by_account(engagement_id: str, firm_id: str) -> list[dict]:
    """Aggregate GL entries by account code — trial balance view."""
    rows = await query_db(
        """SELECT account_code, account_name,
                  SUM(CASE WHEN amount > 0 THEN amount ELSE 0 END) as total_debits,
                  SUM(CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END) as total_credits,
                  SUM(amount) as net_amount,
                  COUNT(*) as entry_count
           FROM gl_entries
           WHERE engagement_id = $1 AND firm_id = $2
           GROUP BY account_code, account_name
           ORDER BY account_code""",
        [engagement_id, firm_id],
    )
    return [dict(r) for r in rows]
