"""
Xero API integration.

Tokens are encrypted with Fernet (AES-128-CBC) before DB storage.
Decrypt at read time; never log plaintext tokens.

OAuth flow:
  1. Frontend redirects user to Xero consent URL (GET /api/xero/auth-url)
  2. Xero redirects to callback (GET /api/xero/callback?code=...&state=...)
  3. Callback exchanges code for tokens, encrypts, stores in accounting_connections
  4. Subsequent pulls use stored tokens, auto-refreshing when expired
"""
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Any
import httpx
from app.config import settings
from app.tools.db import query_db, write_db, update_db

XERO_API_BASE = "https://api.xero.com/api.xro/2.0"
XERO_TOKEN_URL = "https://identity.xero.com/connect/token"
XERO_AUTH_URL = "https://login.xero.com/identity/connect/authorize"

XERO_SCOPES = "offline_access accounting.transactions.read accounting.accounts.read accounting.reports.read"


# --- Token encryption helpers ---

def _encrypt_token(plaintext: str) -> str:
    from cryptography.fernet import Fernet
    if not settings.TOKEN_ENCRYPTION_KEY:
        return plaintext  # dev mode: no encryption
    f = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    return f.encrypt(plaintext.encode()).decode()


def _decrypt_token(ciphertext: str) -> str:
    from cryptography.fernet import Fernet
    if not settings.TOKEN_ENCRYPTION_KEY:
        return ciphertext
    f = Fernet(settings.TOKEN_ENCRYPTION_KEY.encode())
    return f.decrypt(ciphertext.encode()).decode()


# --- OAuth helpers ---

def get_auth_url(state: str) -> str:
    """Return the Xero consent URL for the OAuth flow."""
    import urllib.parse
    params = {
        "response_type": "code",
        "client_id": settings.XERO_CLIENT_ID,
        "redirect_uri": f"{settings.XERO_CLIENT_ID}",  # overridden by caller
        "scope": XERO_SCOPES,
        "state": state,
    }
    return f"{XERO_AUTH_URL}?{urllib.parse.urlencode(params)}"


async def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """Exchange OAuth authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            XERO_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            auth=(settings.XERO_CLIENT_ID, settings.XERO_CLIENT_SECRET),
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()


async def _get_connection(client_id: str, firm_id: str) -> dict | None:
    rows = await query_db(
        "SELECT * FROM accounting_connections WHERE client_id = $1 AND firm_id = $2 AND platform = 'XERO' LIMIT 1",
        [client_id, firm_id],
    )
    return dict(rows[0]) if rows else None


async def _refresh_if_needed(conn: dict) -> str:
    """Return a valid access token, refreshing if expired."""
    expiry = conn.get("token_expiry")
    if expiry and datetime.now(timezone.utc) < expiry - timedelta(minutes=5):
        return _decrypt_token(conn["access_token"])

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            XERO_TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": _decrypt_token(conn["refresh_token"])},
            auth=(settings.XERO_CLIENT_ID, settings.XERO_CLIENT_SECRET),
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

    new_expiry = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    await update_db(
        "accounting_connections",
        {
            "access_token": _encrypt_token(data["access_token"]),
            "refresh_token": _encrypt_token(data.get("refresh_token", _decrypt_token(conn["refresh_token"]))),
            "token_expiry": new_expiry,
            "status": "CONNECTED",
        },
        {"id": str(conn["id"])},
    )
    return data["access_token"]


async def _xero_get(conn: dict, path: str, params: dict | None = None) -> Any:
    token = await _refresh_if_needed(conn)
    tenant_id = conn["tenant_id"]
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{XERO_API_BASE}{path}",
            headers={"Authorization": f"Bearer {token}", "Xero-Tenant-Id": tenant_id, "Accept": "application/json"},
            params=params or {},
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()


# --- Public tool functions ---

async def pull_transactions(
    client_id: str,
    firm_id: str,
    engagement_id: str,
    from_date: str,
    to_date: str,
    page: int = 1,
) -> dict:
    """
    Pull bank transactions from Xero for the given date range.
    Writes raw rows to the `transactions` table. Returns count + summary.
    """
    conn = await _get_connection(client_id, firm_id)
    if not conn:
        return {"error": "No Xero connection found for this client"}

    data = await _xero_get(
        conn,
        "/BankTransactions",
        params={"where": f'Date>=DateTime({from_date.replace("-", ",")})&Date<=DateTime({to_date.replace("-", ",")})', "page": page},
    )

    txns = data.get("BankTransactions", [])
    written = 0
    for txn in txns:
        existing = await query_db(
            "SELECT id FROM transactions WHERE xero_id = $1 AND engagement_id = $2 LIMIT 1",
            [txn.get("BankTransactionID"), engagement_id],
        )
        if existing:
            continue

        amount = float(txn.get("Total", 0))
        if txn.get("Type") in ("SPEND", "SPEND-OVERPAYMENT", "SPEND-PREPAYMENT"):
            amount = -abs(amount)
        else:
            amount = abs(amount)

        await write_db("transactions", {
            "engagement_id": engagement_id,
            "firm_id": firm_id,
            "xero_id": txn.get("BankTransactionID"),
            "bank_account_id": txn.get("BankAccount", {}).get("AccountID"),
            "date": txn.get("DateString", "")[:10],
            "amount": amount,
            "description": txn.get("Reference") or txn.get("Narration") or "",
            "contact_name": txn.get("Contact", {}).get("Name"),
            "reference": txn.get("Reference"),
            "source_chain": {"xero_id": txn.get("BankTransactionID"), "type": txn.get("Type")},
        })
        written += 1

    return {
        "status": "pulled",
        "written": written,
        "total_in_page": len(txns),
        "page": page,
        "from_date": from_date,
        "to_date": to_date,
    }


async def pull_chart_of_accounts(client_id: str, firm_id: str) -> dict:
    """Pull Xero chart of accounts and return as a list."""
    conn = await _get_connection(client_id, firm_id)
    if not conn:
        return {"error": "No Xero connection found"}

    data = await _xero_get(conn, "/Accounts", params={"where": "Status==\"ACTIVE\""})
    accounts = [
        {
            "code": a.get("Code"),
            "name": a.get("Name"),
            "type": a.get("Type"),
            "tax_type": a.get("TaxType"),
            "description": a.get("Description"),
        }
        for a in data.get("Accounts", [])
    ]
    return {"account_count": len(accounts), "accounts": accounts}


async def pull_bank_balances(client_id: str, firm_id: str) -> dict:
    """Pull current bank account balances from Xero."""
    conn = await _get_connection(client_id, firm_id)
    if not conn:
        return {"error": "No Xero connection found"}

    data = await _xero_get(conn, "/Accounts", params={"where": 'Type=="BANK"&Status=="ACTIVE"'})
    balances = [
        {
            "account_id": a.get("AccountID"),
            "code": a.get("Code"),
            "name": a.get("Name"),
            "balance": a.get("ReportingCodeUpdated"),
        }
        for a in data.get("Accounts", [])
    ]
    return {"balances": balances}


async def save_xero_connection(
    client_id: str,
    firm_id: str,
    access_token: str,
    refresh_token: str,
    expires_in: int,
    tenant_id: str,
) -> dict:
    """Store or update encrypted Xero tokens for a client."""
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    existing = await _get_connection(client_id, firm_id)

    data = {
        "access_token": _encrypt_token(access_token),
        "refresh_token": _encrypt_token(refresh_token),
        "token_expiry": expiry,
        "tenant_id": tenant_id,
        "status": "CONNECTED",
    }

    if existing:
        updated = await update_db("accounting_connections", data, {"id": str(existing["id"])})
        return {"connection_id": str(existing["id"]), "status": "updated"}
    else:
        row = await write_db("accounting_connections", {
            "client_id": client_id,
            "firm_id": firm_id,
            "platform": "XERO",
            **data,
        })
        return {"connection_id": str(row["id"]), "status": "created"}
