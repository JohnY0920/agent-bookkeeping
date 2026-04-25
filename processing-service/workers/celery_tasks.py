import asyncio
from celery import Celery
from app.config import settings

celery_app = Celery(
    "agent_processing",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)


@celery_app.task(name="workers.celery_tasks.run_agent", bind=True, max_retries=3)
def run_agent(
    self,
    agent_type: str,
    engagement_id: str,
    firm_id: str,
    task_description: str,
    client_id: str = "",
    context: dict | None = None,
) -> dict:
    """
    Run a specialized agent synchronously inside a Celery worker.
    Uses asyncio.run() to create a fresh event loop per task (safe for Celery workers).
    """
    from app.agents import get_agent_class

    async def _run():
        AgentClass = get_agent_class(agent_type)
        agent = AgentClass(
            engagement_id=engagement_id,
            client_id=client_id,
            firm_id=firm_id,
        )
        return await agent.run(task_description=task_description, context=context)

    try:
        return asyncio.run(_run())
    except ValueError as exc:
        # Unknown agent type — don't retry
        return {"status": "error", "detail": str(exc)}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
