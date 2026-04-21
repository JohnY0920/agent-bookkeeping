"""
Integration tests require a real PostgreSQL database with the schema applied.
They are skipped automatically if the DB is unreachable.

Run with:
    PYTHONPATH=. pytest tests/integration/ -v

Or from the processing-service directory after `docker compose -f ../docker-compose.dev.yml up -d`
"""
import os
import asyncio
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires real database and APIs")


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def db_pool():
    """Return a live DB pool, or skip the whole session if DB is unreachable."""
    import asyncpg
    import json

    url = os.environ.get("DATABASE_URL", "postgresql://dev:dev@localhost:5432/architect_ledger")
    try:
        async def init(conn):
            await conn.set_type_codec("jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")
            await conn.set_type_codec("json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog")

        pool = await asyncpg.create_pool(url, min_size=1, max_size=3, init=init, timeout=5)
        yield pool
        await pool.close()
    except Exception as e:
        pytest.skip(f"Database not reachable: {e}")


@pytest.fixture(scope="session")
async def seed_firm(db_pool):
    """Insert a test firm and return its id."""
    row = await db_pool.fetchrow(
        "INSERT INTO firms (name, contact_email) VALUES ($1, $2) RETURNING id",
        "Test Firm Inc.", "test@testfirm.ca"
    )
    return str(row["id"])


@pytest.fixture(scope="session")
async def seed_client(db_pool, seed_firm):
    """Insert a test client and return its id."""
    row = await db_pool.fetchrow(
        """INSERT INTO clients (firm_id, name, entity_type, industry_code)
           VALUES ($1, $2, $3, $4) RETURNING id""",
        seed_firm, "Acme Corp", "CORPORATION", "41"
    )
    return str(row["id"])


@pytest.fixture(scope="session")
async def seed_engagement(db_pool, seed_firm, seed_client):
    """Insert a test engagement and return its id."""
    row = await db_pool.fetchrow(
        """INSERT INTO engagements (client_id, firm_id, period_label, engagement_type, mode)
           VALUES ($1, $2, $3, $4, $5) RETURNING id""",
        seed_client, seed_firm, "FY2025", "BOOKKEEPING", "COLLECTION"
    )
    return str(row["id"])
