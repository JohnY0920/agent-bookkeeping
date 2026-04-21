# Agent type → Claude model mapping. Simple tasks use Haiku; reasoning tasks use Sonnet.
MODEL_MAP: dict[str, str] = {
    # Haiku: fast, cheap — formatting, filing, drafting
    "comms": "claude-haiku-4-5-20251001",
    "filing": "claude-haiku-4-5-20251001",
    "workpaper": "claude-haiku-4-5-20251001",
    # Sonnet: balanced reasoning
    "document": "claude-sonnet-4-6",
    "transaction": "claude-sonnet-4-6",
    "reconciliation": "claude-sonnet-4-6",
    "tax_recon": "claude-sonnet-4-6",
    "yearend": "claude-sonnet-4-6",
    "financial_stmt": "claude-sonnet-4-6",
    "tax": "claude-sonnet-4-6",
    "qc": "claude-sonnet-4-6",
    "planner": "claude-sonnet-4-6",
}


def get_model_for_agent(agent_type: str) -> str:
    return MODEL_MAP.get(agent_type, "claude-sonnet-4-6")
