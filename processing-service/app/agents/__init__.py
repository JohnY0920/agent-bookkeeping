from app.agents.base import BaseAgent
from app.agents.document_agent import DocumentAgent
from app.agents.planner import PlannerAgent

_AGENT_MAP: dict[str, type[BaseAgent]] = {
    "document": DocumentAgent,
    "planner": PlannerAgent,
    # Phase 2+
    # "transaction": TransactionAgent,
    # "reconciliation": ReconciliationAgent,
    # "tax_recon": TaxReconAgent,
    # Phase 3+
    # "yearend": YearEndAgent,
    # "qc": QCAgent,
    # "workpaper": WorkpaperAgent,
    # "comms": CommsAgent,
    # Phase 4+
    # "financial_stmt": FinancialStmtAgent,
    # "tax": TaxAgent,
    # "filing": FilingAgent,
}


def get_agent_class(agent_type: str) -> type[BaseAgent]:
    if agent_type not in _AGENT_MAP:
        raise NotImplementedError(f"Agent '{agent_type}' not yet implemented")
    return _AGENT_MAP[agent_type]
