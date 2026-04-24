from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Run a read-only SQL query against the database.",
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
        "name": "write_db",
        "description": "Insert or update a database row.",
        "input_schema": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "data": {"type": "object"},
            },
            "required": ["table", "data"],
        },
    },
    {
        "name": "pull_transactions",
        "description": "Pull bank transactions from Xero for a date range. Writes raw rows to transactions table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string"},
                "firm_id": {"type": "string"},
                "engagement_id": {"type": "string"},
                "from_date": {"type": "string", "description": "YYYY-MM-DD"},
                "to_date": {"type": "string", "description": "YYYY-MM-DD"},
                "page": {"type": "integer", "default": 1},
            },
            "required": ["client_id", "firm_id", "engagement_id", "from_date", "to_date"],
        },
    },
    {
        "name": "pull_chart_of_accounts",
        "description": "Pull Xero chart of accounts for account code reference.",
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
        "name": "write_gl_entry",
        "description": "Write a GL entry. MUST include source_chain with xero_id. Never call directly on transactions table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string"},
                "account_code": {"type": "string"},
                "account_name": {"type": "string"},
                "amount": {"type": "number"},
                "entry_date": {"type": "string", "description": "YYYY-MM-DD"},
                "description": {"type": "string"},
                "source_transaction": {"type": "object"},
                "categorization_method": {"type": "string"},
                "categorization_confidence": {"type": "number"},
                "agent_type": {"type": "string"},
                "processing_run_id": {"type": "string"},
            },
            "required": ["engagement_id", "account_code", "account_name", "amount", "entry_date", "description"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Flag a transaction for CPA review.",
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
        "name": "search_knowledge_base",
        "description": "Search CRA/ITA knowledge base for relevant guidance (ITC rules, CCA classes, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "source": {"type": "string", "description": "ITA | ETA | CRA_GUIDE | ITC_RULES | CCA_CLASSES"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "write_workpaper_entry",
        "description": "Write a workpaper entry summarising the transaction batch processing result.",
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
        "name": "get_lessons",
        "description": "Retrieve categorization lessons for this client from prior periods.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_type": {"type": "string"},
                "client_id": {"type": "string"},
                "task_description": {"type": "string"},
            },
            "required": ["agent_type", "client_id", "task_description"],
        },
    },
    {
        "name": "save_lesson",
        "description": "Save a categorization lesson for future recall.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_type": {"type": "string"},
                "firm_id": {"type": "string"},
                "scenario_description": {"type": "string"},
                "lesson_content": {"type": "string"},
                "client_id": {"type": "string"},
            },
            "required": ["agent_type", "firm_id", "scenario_description", "lesson_content"],
        },
    },
]


class TransactionAgent(BaseAgent):
    agent_type = "transaction"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
