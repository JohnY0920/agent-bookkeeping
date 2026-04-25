from app.agents.base import BaseAgent
from app.agents.document_agent import DocumentAgent
from app.agents.planner import PlannerAgent
from app.agents.transaction_agent import TransactionAgent
from app.agents.reconciliation_agent import ReconciliationAgent
from app.agents.tax_recon_agent import TaxReconAgent
from app.agents.yearend_agent import YearendAgent
from app.agents.qc_agent import QCAgent
from app.agents.workpaper_agent import WorkpaperAgent
from app.agents.comms_agent import CommsAgent
from app.agents.financial_stmt_agent import FinancialStmtAgent
from app.agents.tax_agent import TaxAgent
from app.agents.filing_agent import FilingAgent

_AGENT_MAP: dict[str, type[BaseAgent]] = {
    "document":       DocumentAgent,
    "planner":        PlannerAgent,
    "transaction":    TransactionAgent,
    "reconciliation": ReconciliationAgent,
    "tax_recon":      TaxReconAgent,
    "yearend":        YearendAgent,
    "qc":             QCAgent,
    "workpaper":      WorkpaperAgent,
    "comms":          CommsAgent,
    "financial_stmt": FinancialStmtAgent,
    "tax":            TaxAgent,
    "filing":         FilingAgent,
}


def get_agent_class(agent_type: str) -> type[BaseAgent]:
    if agent_type not in _AGENT_MAP:
        raise ValueError(f"Unknown agent type: '{agent_type}'. Valid: {list(_AGENT_MAP)}")
    return _AGENT_MAP[agent_type]
