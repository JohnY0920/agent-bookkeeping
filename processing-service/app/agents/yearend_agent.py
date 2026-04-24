from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Read-only SQL queries for GL entries, plan steps, and engagement data.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {}}}, "required": ["query"]},
    },
    {
        "name": "calculate_cca",
        "description": "Calculate Capital Cost Allowance per ITA. Returns deduction and closing UCC.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cca_class": {"type": "integer"},
                "ucc_opening": {"type": "number"},
                "additions": {"type": "number"},
                "dispositions": {"type": "number"},
                "is_first_year": {"type": "boolean", "description": "True for AIIP-eligible additions"},
            },
            "required": ["cca_class", "ucc_opening"],
        },
    },
    {
        "name": "calculate_amortization",
        "description": "Calculate straight-line amortization for Class 14 assets.",
        "input_schema": {
            "type": "object",
            "properties": {
                "cost": {"type": "number"},
                "useful_life_years": {"type": "integer"},
                "year": {"type": "integer"},
            },
            "required": ["cost", "useful_life_years"],
        },
    },
    {
        "name": "create_plan_step",
        "description": "Create a CPA approval step. ALWAYS set requires_human=true for year-end entries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "agent_type": {"type": "string"},
                "description": {"type": "string"},
                "sort_order": {"type": "integer"},
                "requires_human": {"type": "boolean"},
            },
            "required": ["plan_id", "agent_type", "description", "sort_order"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Flag a year-end issue for CPA review (shareholder loans, AIIP questions, etc.).",
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
        "description": "Write proposed adjustments to working papers. NOT the same as writing GL entries.",
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
        "name": "search_knowledge_base",
        "description": "Look up ITA rules for CCA, AIIP, shareholder loans, and other year-end topics.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "source": {"type": "string"}, "top_k": {"type": "integer"}},
            "required": ["query"],
        },
    },
]


class YearendAgent(BaseAgent):
    agent_type = "yearend"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
