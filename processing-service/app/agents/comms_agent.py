from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Read engagement, client, and user data. Always scope by firm_id.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {}}}, "required": ["query"]},
    },
    {
        "name": "check_completeness",
        "description": "Check which checklist items are still pending before sending reminder.",
        "input_schema": {"type": "object", "properties": {"engagement_id": {"type": "string"}}, "required": ["engagement_id"]},
    },
    {
        "name": "send_email",
        "description": "Send email to client. ALWAYS include assigned accountant in cc_emails.",
        "input_schema": {
            "type": "object",
            "properties": {
                "to_email": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
                "cc_emails": {"type": "array", "items": {"type": "string"}},
                "reply_to": {"type": "string"},
            },
            "required": ["to_email", "subject", "body"],
        },
    },
    {
        "name": "write_db",
        "description": "Write communication_logs entry after sending email.",
        "input_schema": {
            "type": "object",
            "properties": {"table": {"type": "string"}, "data": {"type": "object"}},
            "required": ["table", "data"],
        },
    },
    {
        "name": "update_db",
        "description": "Update last_reminder_at on engagement after sending a reminder.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "data": {"type": "object"},
                "where": {"type": "object"},
            },
            "required": ["table", "data", "where"],
        },
    },
]


class CommsAgent(BaseAgent):
    agent_type = "comms"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
