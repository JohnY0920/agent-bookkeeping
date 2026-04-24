from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Read plan_steps, review_items, engagement data for pre-filing validation.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {}}}, "required": ["query"]},
    },
    {
        "name": "update_db",
        "description": "Advance engagement to COMPLETE mode after successful filing.",
        "input_schema": {
            "type": "object",
            "properties": {"table": {"type": "string"}, "data": {"type": "object"}, "where": {"type": "object"}},
            "required": ["table", "data", "where"],
        },
    },
    {
        "name": "write_db",
        "description": "Write audit_log entry on engagement completion.",
        "input_schema": {
            "type": "object",
            "properties": {"table": {"type": "string"}, "data": {"type": "object"}},
            "required": ["table", "data"],
        },
    },
    {
        "name": "upload_file",
        "description": "Upload the e-filing XML package to S3.",
        "input_schema": {
            "type": "object",
            "properties": {"local_path": {"type": "string"}, "destination_path": {"type": "string"}},
            "required": ["local_path", "destination_path"],
        },
    },
    {
        "name": "write_workpaper_entry",
        "description": "Write e-filing package reference, invoice, and engagement_complete entries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string"},
                "entry_type": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "source_event": {"type": "object"},
            },
            "required": ["engagement_id", "entry_type", "title", "content"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Block filing if prerequisites not met.",
        "input_schema": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string"},
                "item_type": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "agent_reasoning": {"type": "object"},
            },
            "required": ["engagement_id", "item_type", "description"],
        },
    },
    {
        "name": "dispatch_agent",
        "description": "Dispatch comms_agent after filing to notify client.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_type": {"type": "string"},
                "task_description": {"type": "string"},
                "engagement_id": {"type": "string"},
                "client_id": {"type": "string"},
                "firm_id": {"type": "string"},
                "context": {"type": "object"},
            },
            "required": ["agent_type", "task_description", "engagement_id", "client_id", "firm_id"],
        },
    },
]


class FilingAgent(BaseAgent):
    agent_type = "filing"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
