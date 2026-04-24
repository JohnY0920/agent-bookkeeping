from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Run a read-only SQL query. Use to fetch GL entries, transactions, and bank balances.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "params": {"type": "array", "items": {}},
            },
            "required": ["query"],
        },
    },
    {
        "name": "pull_bank_balances",
        "description": "Pull current bank account balances from Xero.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "firm_id": {"type": "string"},
            },
            "required": ["client_id", "firm_id"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Flag a reconciliation discrepancy for CPA review.",
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
        "description": "Write the completed reconciliation report to the working papers.",
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
        "name": "write_db",
        "description": "Insert a reconciliation summary or update engagement current_summary.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "data": {"type": "object"},
            },
            "required": ["table", "data"],
        },
    },
]


class ReconciliationAgent(BaseAgent):
    agent_type = "reconciliation"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
