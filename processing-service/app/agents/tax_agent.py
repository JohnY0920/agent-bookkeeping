from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "query_db",
        "description": "Read GL entries, extracted T-slip data (documents.extracted_data), and workpaper entries.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}, "params": {"type": "array", "items": {}}}, "required": ["query"]},
    },
    {
        "name": "calculate_tax_payable",
        "description": "Calculate federal and provincial income tax. Returns breakdown by jurisdiction.",
        "input_schema": {
            "type": "object",
            "properties": {
                "taxable_income": {"type": "number"},
                "province": {"type": "string"},
                "entity_type": {"type": "string", "enum": ["INDIVIDUAL", "CORPORATION"]},
                "is_ccpc": {"type": "boolean"},
            },
            "required": ["taxable_income", "province", "entity_type"],
        },
    },
    {
        "name": "calculate_sbd",
        "description": "Calculate Small Business Deduction (ITA s.125) for Canadian-Controlled Private Corporations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "active_business_income": {"type": "number"},
                "taxable_income": {"type": "number"},
                "province": {"type": "string"},
                "associated_corporations_abi": {"type": "number"},
            },
            "required": ["active_business_income", "taxable_income", "province"],
        },
    },
    {
        "name": "search_knowledge_base",
        "description": "Look up tax provisions, SBD association rules, loss carryover rules.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}, "source": {"type": "string"}, "top_k": {"type": "integer"}},
            "required": ["query"],
        },
    },
    {
        "name": "create_plan_step",
        "description": "Create CPA approval step for tax return sign-off. Always requires_human=true.",
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
        "name": "write_workpaper_entry",
        "description": "Write the tax return computation as a workpaper entry.",
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
        "description": "Flag items requiring CPA judgment (loss carryovers, SR&ED credits, instalment discrepancies).",
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


class TaxAgent(BaseAgent):
    agent_type = "tax"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
