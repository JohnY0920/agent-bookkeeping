from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Run a read-only SQL query. Use to fetch GL entries and transactions.",
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
        "name": "calculate_gst",
        "description": "Calculate GST/HST on an amount. Returns tax amount and total.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "province": {"type": "string", "description": "Two-letter province code (ON, BC, AB, etc.)"},
                "is_included": {"type": "boolean", "description": "True if amount already includes tax"},
            },
            "required": ["amount", "province"],
        },
    },
    {
        "name": "calculate_itc",
        "description": "Calculate eligible ITC on an expense, applying ETA restrictions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "expense_type": {"type": "string", "description": "meals, vehicle, office, other"},
                "province": {"type": "string"},
                "is_included": {"type": "boolean"},
            },
            "required": ["amount", "expense_type", "province"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Search CRA/ITA/ETA knowledge base for ITC rules and GST guidance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "source": {"type": "string"},
                "top_k": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Flag an ITC violation or GST discrepancy for CPA review.",
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
        "description": "Write the GST/HST reconciliation report to working papers.",
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
        "name": "save_lesson",
        "description": "Save an ITC/GST lesson for future recall.",
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


class TaxReconAgent(BaseAgent):
    agent_type = "tax_recon"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
