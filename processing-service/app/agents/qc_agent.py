from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Read-only SQL for GL entries, review items, checklist, workpaper entries.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {}}}, "required": ["query"]},
    },
    {
        "name": "check_completeness",
        "description": "Check if all required checklist items are received.",
        "input_schema": {"type": "object", "properties": {"engagement_id": {"type": "string"}}, "required": ["engagement_id"]},
    },
    {
        "name": "search_knowledge_base",
        "description": "Look up current CRA audit thresholds and NAICS benchmarks.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "source": {"type": "string"}, "top_k": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Flag a QC issue. Use item_type prefixed with 'qc_'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string"},
                "item_type": {"type": "string"},
                "description": {"type": "string"},
                "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                "confidence_score": {"type": "number"},
                "agent_reasoning": {"type": "object"},
            },
            "required": ["engagement_id", "item_type", "description"],
        },
    },
    {
        "name": "write_workpaper_entry",
        "description": "Write the QC report to working papers.",
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
]


class QCAgent(BaseAgent):
    agent_type = "qc"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
