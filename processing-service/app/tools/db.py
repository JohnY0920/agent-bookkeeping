import asyncpg
import json
from app.config import settings

_pool: asyncpg.Pool | None = None


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Register codecs so asyncpg handles JSONB and pgvector natively."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=2,
            max_size=10,
            init=_init_connection,
        )
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def query_db(query: str, params: list | None = None) -> list[dict]:
    """Execute a SELECT query and return rows as dicts. Uses $1, $2... positional params."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *(params or []))
        return [dict(row) for row in rows]


async def write_db(table: str, data: dict) -> dict:
    """INSERT a row into table and return the inserted row."""
    pool = await get_pool()
    columns = list(data.keys())
    values = list(data.values())
    cols = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))
    query = f'INSERT INTO "{table}" ({cols}) VALUES ({placeholders}) RETURNING *'
    async with pool.acquire() as conn:
        row = await conn.fetchrow(query, *values)
        return dict(row)
