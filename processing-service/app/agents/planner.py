from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "create_plan_step",
        "description": "Add a step to the engagement task plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_id": {"type": "string"},
                "agent_type": {"type": "string"},
                "description": {"type": "string"},
                "sort_order": {"type": "integer"},
                "depends_on": {"type": "array", "items": {"type": "string"}},
                "requires_human": {"type": "boolean"},
            },
            "required": ["plan_id", "agent_type", "description", "sort_order"],
        },
    },
    {
        "name": "update_plan_step",
        "description": "Update the status of a plan step.",
        "input_schema": {
            "type": "object",
            "properties": {
                "step_id": {"type": "string"},
                "status": {"type": "string", "enum": ["PENDING", "RUNNING", "COMPLETE", "FAILED", "WAITING_HUMAN", "SKIPPED"]},
                "result_summary": {"type": "string"},
                "error_message": {"type": "string"},
            },
            "required": ["step_id", "status"],
        },
    },
    {
        "name": "dispatch_agent",
        "description": "Dispatch a specialized agent as a background task. Always include engagement_id, client_id, firm_id.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_type": {
                    "type": "string",
                    "enum": ["document", "transaction", "reconciliation", "tax_recon",
                             "yearend", "financial_stmt", "tax", "qc", "comms", "workpaper", "filing"],
                },
                "task_description": {"type": "string"},
                "engagement_id": {"type": "string"},
                "client_id": {"type": "string"},
                "firm_id": {"type": "string"},
                "context": {"type": "object"},
            },
            "required": ["agent_type", "task_description", "engagement_id", "client_id", "firm_id"],
        },
    },
    {
        "name": "query_db",
        "description": "Run a read-only SQL query.",
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
        "name": "check_completeness",
        "description": "Check if all required checklist items are received for an engagement.",
        "input_schema": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string"},
            },
            "required": ["engagement_id"],
        },
    },
]

class PlannerAgent(BaseAgent):
    agent_type = "planner"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
