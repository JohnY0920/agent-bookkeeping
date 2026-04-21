from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.schemas import WebhookEvent

router = APIRouter(prefix="/webhooks")


@router.post("/events")
async def receive_event(event: WebhookEvent, background_tasks: BackgroundTasks) -> dict:
    """
    Receive events from the frontend or n8n and dispatch to the planner agent.
    All agent execution is async via Celery.
    """
    if not event.engagement_id:
        raise HTTPException(status_code=422, detail="engagement_id is required")

    background_tasks.add_task(_dispatch_planner, event)
    return {"status": "accepted", "event_type": event.event_type}


async def _dispatch_planner(event: WebhookEvent) -> None:
    """Dispatch PlannerAgent as a Celery task for the incoming event."""
    try:
        from workers.celery_tasks import dispatch_agent

        dispatch_agent.delay(
            agent_type="planner",
            engagement_id=event.engagement_id,
            client_id=event.client_id or "",
            firm_id=event.firm_id,
            task_description=f"Handle event: {event.event_type}",
            context=event.payload,
        )
    except Exception as e:
        # Log error but don't crash the webhook response
        import logging
        logging.getLogger(__name__).error("Failed to dispatch planner: %s", e)
