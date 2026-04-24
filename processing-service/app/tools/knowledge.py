"""
CRA/ITA knowledge base search.
Uses pgvector cosine similarity to find relevant regulatory guidance.
"""
from app.tools.db import query_db, write_db


async def search_knowledge_base(query: str, source: str | None = None, top_k: int = 5) -> list[dict]:
    """
    Find knowledge base entries most similar to query using pgvector cosine distance.
    Optionally filter by source (ITA, ETA, CRA_GUIDE, ITC_RULES, CCA_CLASSES).
    """
    from app.models.llm import get_embedding
    embedding = await get_embedding(query)

    if source:
        rows = await query_db(
            """SELECT id, source, section, title, content,
                      1 - (embedding <=> $1::vector) AS similarity
               FROM knowledge_base
               WHERE source = $2 AND embedding IS NOT NULL
               ORDER BY embedding <=> $1::vector
               LIMIT $3""",
            [embedding, source, top_k],
        )
    else:
        rows = await query_db(
            """SELECT id, source, section, title, content,
                      1 - (embedding <=> $1::vector) AS similarity
               FROM knowledge_base
               WHERE embedding IS NOT NULL
               ORDER BY embedding <=> $1::vector
               LIMIT $2""",
            [embedding, top_k],
        )

    return [
        {
            "id": str(r["id"]),
            "source": r["source"],
            "section": r["section"],
            "title": r["title"],
            "content": r["content"],
            "similarity": float(r["similarity"]),
        }
        for r in rows
    ]


async def add_knowledge_entry(
    source: str,
    title: str,
    content: str,
    section: str | None = None,
) -> dict:
    """Add a CRA/ITA guidance entry to the knowledge base with its embedding."""
    from app.models.llm import get_embedding
    embedding = await get_embedding(f"{title}\n{content}")
    row = await write_db("knowledge_base", {
        "source": source,
        "section": section,
        "title": title,
        "content": content,
        "embedding": embedding,
    })
    return {"id": str(row["id"]), "status": "added"}
