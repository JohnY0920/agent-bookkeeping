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


@celery_app.task(name="workers.celery_tasks.dispatch_agent", bind=True, max_retries=3)
def dispatch_agent(
    self,
    agent_type: str,
    engagement_id: str,
    client_id: str,
    firm_id: str,
    task_description: str,
    context: dict | None = None,
) -> dict:
    """Dispatch a specialized agent. Runs synchronously inside a Celery worker."""
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
        return asyncio.get_event_loop().run_until_complete(_run())
    except NotImplementedError:
        return {"status": "not_implemented", "agent_type": agent_type}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
