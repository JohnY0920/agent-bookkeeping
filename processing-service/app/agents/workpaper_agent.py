from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Read GL entries, workpaper entries, review items, plan steps, and engagement data.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {}}}, "required": ["query"]},
    },
    {
        "name": "write_workpaper_entry",
        "description": "Write an assembled schedule or complete working paper section.",
        "input_schema": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string"},
                "entry_type": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "source_event": {"type": "object"},
                "reference_id": {"type": "string"},
            },
            "required": ["engagement_id", "entry_type", "title", "content"],
        },
    },
    {
        "name": "get_signed_url",
        "description": "Generate a signed URL for a document stored in S3.",
        "input_schema": {
            "type": "object",
            "properties": {
                "storage_path": {"type": "string"},
                "expiration_minutes": {"type": "integer"},
            },
            "required": ["storage_path"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Flag incomplete prerequisites before assembly (unresolved plan_steps, etc.).",
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
]


class WorkpaperAgent(BaseAgent):
    agent_type = "workpaper"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
