from app.agents.base import BaseAgent


def get_agent_class(agent_type: str) -> type[BaseAgent]:
    """Return agent class by type. Extend this as agents are implemented."""
    # Phase 1+
    # from app.agents.document_agent import DocumentAgent
    # from app.agents.planner import PlannerAgent
    # map = {"document": DocumentAgent, "planner": PlannerAgent, ...}
    # if agent_type in map:
    #     return map[agent_type]
    raise NotImplementedError(f"Agent '{agent_type}' not yet implemented")
