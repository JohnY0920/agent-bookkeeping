"""Thin tool wrappers around lesson_store — these are what agents call via TOOL_REGISTRY."""
from app.memory.lesson_store import get_relevant_lessons, save_lesson as _save_lesson


async def get_lessons(
    agent_type: str,
    client_id: str,
    task_description: str,
    limit: int = 5,
) -> dict:
    """Retrieve relevant lessons from memory for this agent type and client."""
    lessons = await get_relevant_lessons(agent_type, client_id, task_description, limit)
    return {"lessons": lessons, "count": len(lessons)}


async def save_lesson(
    agent_type: str,
    firm_id: str,
    scenario_description: str,
    lesson_content: str,
    client_id: str | None = None,
) -> dict:
    """Save a lesson learned so future agents can recall it."""
    result = await _save_lesson(
        agent_type=agent_type,
        firm_id=firm_id,
        client_id=client_id,
        scenario_description=scenario_description,
        lesson_content=lesson_content,
    )
    return {"status": "saved", "lesson_id": str(result["id"])}
