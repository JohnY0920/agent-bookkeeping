"""Xero OAuth flow endpoints."""
import urllib.parse
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from app.config import settings
from app.tools.xero import exchange_code_for_tokens, save_xero_connection, XERO_AUTH_URL, XERO_SCOPES

router = APIRouter(prefix="/xero", tags=["xero"])

# Simple in-memory state store for OAuth CSRF protection
# In production this should use Redis with TTL
_pending_states: dict[str, dict] = {}


class XeroConnectRequest(BaseModel):
    client_id: str
    firm_id: str
    redirect_base_url: str  # e.g. https://app.architectledger.com


@router.post("/connect")
async def start_xero_oauth(payload: XeroConnectRequest) -> dict:
    """Generate a Xero OAuth consent URL. Frontend should redirect the user to this URL."""
    import secrets
    state = secrets.token_urlsafe(32)
    _pending_states[state] = {
        "client_id": payload.client_id,
        "firm_id": payload.firm_id,
        "redirect_uri": f"{payload.redirect_base_url}/api/xero/callback",
    }
    params = {
        "response_type": "code",
        "client_id": settings.XERO_CLIENT_ID,
        "redirect_uri": f"{payload.redirect_base_url}/api/xero/callback",
        "scope": XERO_SCOPES,
        "state": state,
    }
    auth_url = f"{XERO_AUTH_URL}?{urllib.parse.urlencode(params)}"
    return {"auth_url": auth_url, "state": state}


@router.get("/callback")
async def xero_oauth_callback(code: str, state: str, error: str | None = None) -> dict:
    """Handle Xero OAuth callback. Exchange code for tokens and store encrypted."""
    if error:
        raise HTTPException(status_code=400, detail=f"Xero OAuth error: {error}")

    pending = _pending_states.pop(state, None)
    if not pending:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    token_data = await exchange_code_for_tokens(code, pending["redirect_uri"])

    # Get the tenant ID (first available Xero org)
    import httpx
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://api.xero.com/connections",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
            timeout=15,
        )
        resp.raise_for_status()
        connections = resp.json()

    if not connections:
        raise HTTPException(status_code=400, detail="No Xero organisations found")

    tenant_id = connections[0]["tenantId"]
    result = await save_xero_connection(
        client_id=pending["client_id"],
        firm_id=pending["firm_id"],
        access_token=token_data["access_token"],
        refresh_token=token_data["refresh_token"],
        expires_in=token_data.get("expires_in", 1800),
        tenant_id=tenant_id,
    )
    return {**result, "tenant_name": connections[0].get("tenantName")}


@router.get("/status")
async def xero_connection_status(client_id: str, firm_id: str) -> dict:
    """Check Xero connection status for a client."""
    from app.tools.db import query_db
    rows = await query_db(
        "SELECT id, status, token_expiry, tenant_id FROM accounting_connections WHERE client_id = $1 AND firm_id = $2 AND platform = 'XERO' LIMIT 1",
        [client_id, firm_id],
    )
    if not rows:
        return {"connected": False}
    conn = rows[0]
    return {
        "connected": conn["status"] == "CONNECTED",
        "status": conn["status"],
        "tenant_id": conn["tenant_id"],
        "token_expiry": conn["token_expiry"].isoformat() if conn["token_expiry"] else None,
    }
