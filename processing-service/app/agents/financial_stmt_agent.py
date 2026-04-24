from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Read GL entries and workpaper entries. Group by account code to build financial statements.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {}}}, "required": ["query"]},
    },
    {
        "name": "write_workpaper_entry",
        "description": "Write each financial statement (income statement, balance sheet, retained earnings) as a workpaper entry.",
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
        "description": "Flag if balance sheet doesn't balance or prerequisites are missing.",
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


class FinancialStmtAgent(BaseAgent):
    agent_type = "financial_stmt"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
