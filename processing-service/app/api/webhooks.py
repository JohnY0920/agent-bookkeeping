import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.models.schemas import WebhookEvent, WebhookEventType

router = APIRouter(prefix="/webhooks")
log = logging.getLogger(__name__)

# Event type → agent type that should handle it
_EVENT_AGENT_MAP = {
    WebhookEventType.DOCUMENT_UPLOADED: "document",
    WebhookEventType.ENGAGEMENT_CREATED: "planner",
    WebhookEventType.CPA_ACTION:         "planner",
    WebhookEventType.XERO_SYNC:          "transaction",
    WebhookEventType.TIMER_FIRED:        "planner",
}


@router.post("/events")
async def receive_event(event: WebhookEvent, background_tasks: BackgroundTasks) -> dict:
    """
    Receive events from frontend or n8n and dispatch to the appropriate agent.
    All agent execution is async via Celery — this endpoint returns immediately.
    """
    if not event.engagement_id:
        raise HTTPException(status_code=422, detail="engagement_id is required")

    agent_type = _EVENT_AGENT_MAP.get(event.event_type, "planner")
    background_tasks.add_task(_dispatch, event, agent_type)
    return {"status": "accepted", "event_type": event.event_type, "agent": agent_type}


async def _dispatch(event: WebhookEvent, agent_type: str) -> None:
    try:
        from workers.celery_tasks import run_agent
        run_agent.delay(
            agent_type=agent_type,
            engagement_id=event.engagement_id,
            client_id=event.client_id or "",
            firm_id=event.firm_id,
            task_description=f"Handle event: {event.event_type}",
            context=event.payload,
        )
    except Exception as e:
        log.error("Failed to dispatch %s for event %s: %s", agent_type, event.event_type, e)
