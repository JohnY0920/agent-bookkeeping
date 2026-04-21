from pydantic import BaseModel, Field
from typing import Any
from enum import Enum
import uuid


class EngagementType(str, Enum):
    BOOKKEEPING = "BOOKKEEPING"
    T1 = "T1"
    T2 = "T2"


class EngagementMode(str, Enum):
    COLLECTION = "COLLECTION"
    PROCESSING = "PROCESSING"
    REVIEW = "REVIEW"
    COMPLETE = "COMPLETE"


class WebhookEventType(str, Enum):
    DOCUMENT_UPLOADED = "document.uploaded"
    ENGAGEMENT_CREATED = "engagement.created"
    CPA_ACTION = "cpa.action"
    XERO_SYNC = "xero.sync"
    TIMER_FIRED = "timer.fired"


class WebhookEvent(BaseModel):
    event_type: WebhookEventType
    firm_id: str
    engagement_id: str | None = None
    client_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class EngagementCreate(BaseModel):
    client_id: str
    firm_id: str
    period_label: str
    engagement_type: EngagementType
    assigned_user_id: str | None = None


class EngagementResponse(BaseModel):
    id: str
    client_id: str
    firm_id: str
    period_label: str
    engagement_type: EngagementType
    mode: EngagementMode
    current_summary: str | None = None


class AgentTaskRequest(BaseModel):
    agent_type: str
    engagement_id: str
    client_id: str
    firm_id: str
    task_description: str
    context: dict[str, Any] | None = None


class SourceChain(BaseModel):
    transaction: dict[str, Any] | None = None
    source_document: dict[str, Any] | None = None
    categorization: dict[str, Any] | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"
