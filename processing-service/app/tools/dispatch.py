"""Planner tool: dispatch a specialized agent as a Celery background task."""


async def dispatch_agent(
    agent_type: str,
    task_description: str,
    engagement_id: str,
    client_id: str,
    firm_id: str,
    context: dict | None = None,
) -> dict:
    """Enqueue a specialized agent task. Returns immediately with task_id."""
    from workers.celery_tasks import run_agent

    task = run_agent.delay(
        agent_type=agent_type,
        engagement_id=engagement_id,
        client_id=client_id,
        firm_id=firm_id,
        task_description=task_description,
        context=context or {},
    )
    return {
        "status": "dispatched",
        "task_id": task.id,
        "agent_type": agent_type,
    }
