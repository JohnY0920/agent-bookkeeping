from app.tools.db import query_db, write_db
from app.models.llm import get_embedding


async def get_relevant_lessons(
    agent_type: str,
    client_id: str,
    task_description: str,
    limit: int = 5,
) -> list[dict]:
    """Retrieve relevant lessons using pgvector cosine similarity search."""
    embedding = await get_embedding(task_description)

    results = await query_db(
        """
        SELECT id, scenario_description, lesson_content,
               1 - (embedding <=> $1::vector) AS similarity
        FROM lessons
        WHERE agent_type = $2
          AND (client_id = $3 OR client_id IS NULL)
        ORDER BY embedding <=> $1::vector
        LIMIT $4
        """,
        params=[embedding, agent_type, client_id, limit],
    )

    return [r for r in results if r["similarity"] > 0.7]


async def save_lesson(
    agent_type: str,
    firm_id: str,
    client_id: str | None,
    scenario_description: str,
    lesson_content: str,
) -> dict:
    """Save a lesson learned from processing, with embedding for future recall."""
    embedding = await get_embedding(f"{scenario_description} {lesson_content}")

    return await write_db(
        "lessons",
        {
            "agent_type": agent_type,
            "firm_id": firm_id,
            "client_id": client_id,
            "scenario_description": scenario_description,
            "lesson_content": lesson_content,
            "embedding": embedding,
            "created_by": "AGENT",
        },
    )
