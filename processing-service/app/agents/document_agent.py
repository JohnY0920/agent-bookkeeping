from app.agents.base import BaseAgent

_TOOL_DEFS = [
    {
        "name": "extract_document",
        "description": "Extract text and structure from a document (PDF, image) using Claude Sonnet vision.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Local path to the document"},
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "update_checklist_item",
        "description": "Update the status of a checklist item (e.g. to RECEIVED after a document is processed).",
        "input_schema": {
            "type": "object",
            "properties": {
                "checklist_item_id": {"type": "string"},
                "status": {"type": "string", "enum": ["PENDING", "RECEIVED", "VERIFIED", "NOT_APPLICABLE"]},
                "document_id": {"type": "string", "description": "UUID of the associated document row"},
            },
            "required": ["checklist_item_id", "status"],
        },
    },
    {
        "name": "check_completeness",
        "description": "Check how many required checklist items are received for an engagement.",
        "input_schema": {
            "type": "object",
            "properties": {
                "engagement_id": {"type": "string"},
            },
            "required": ["engagement_id"],
        },
    },
    {
        "name": "create_review_item",
        "description": "Flag an item for CPA review. Use when classification confidence < 0.80.",
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
        "description": "Write a working paper entry summarising what was found for this document.",
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
        "name": "upload_file",
        "description": "Upload a local file to S3.",
        "input_schema": {
            "type": "object",
            "properties": {
                "local_path": {"type": "string"},
                "destination_path": {"type": "string", "description": "Path within the S3 bucket"},
            },
            "required": ["local_path", "destination_path"],
        },
    },
    {
        "name": "write_db",
        "description": "Insert a row into a database table.",
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
        "name": "get_lessons",
        "description": "Retrieve relevant lessons learned for this agent type and client.",
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
        "description": "Save a lesson learned for future recall.",
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


class DocumentAgent(BaseAgent):
    agent_type = "document"

    def _register_tools(self) -> list[dict]:
        return _TOOL_DEFS
