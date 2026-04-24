"""
Phase 3 agent registration tests.
Verifies each agent has the correct tool set and all tools exist in TOOL_REGISTRY.
"""
import pytest
from app.tools import TOOL_REGISTRY


def _get_tool_names(agent_class):
    agent = agent_class.__new__(agent_class)
    agent.agent_type = agent_class.agent_type
    return {t["name"] for t in agent._register_tools()}


class TestYearendAgent:
    def test_agent_type(self):
        from app.agents.yearend_agent import YearendAgent
        assert YearendAgent.agent_type == "yearend"

    def test_required_tools_registered(self):
        from app.agents.yearend_agent import YearendAgent
        names = _get_tool_names(YearendAgent)
        assert "calculate_cca" in names
        assert "calculate_amortization" in names
        assert "create_plan_step" in names
        assert "create_review_item" in names
        assert "write_workpaper_entry" in names
        assert "search_knowledge_base" in names

    def test_no_write_gl_entry_in_yearend(self):
        """Year-end agent must NOT have write_gl_entry — entries need CPA approval first."""
        from app.agents.yearend_agent import YearendAgent
        names = _get_tool_names(YearendAgent)
        assert "write_gl_entry" not in names

    def test_all_tools_in_registry(self):
        from app.agents.yearend_agent import YearendAgent
        for name in _get_tool_names(YearendAgent):
            assert name in TOOL_REGISTRY, f"{name} not in TOOL_REGISTRY"


class TestQCAgent:
    def test_required_tools(self):
        from app.agents.qc_agent import QCAgent
        names = _get_tool_names(QCAgent)
        assert "query_db" in names
        assert "check_completeness" in names
        assert "search_knowledge_base" in names
        assert "create_review_item" in names
        assert "write_workpaper_entry" in names

    def test_no_write_gl_entry(self):
        """QC is read-only — must not write GL entries."""
        from app.agents.qc_agent import QCAgent
        assert "write_gl_entry" not in _get_tool_names(QCAgent)

    def test_all_tools_in_registry(self):
        from app.agents.qc_agent import QCAgent
        for name in _get_tool_names(QCAgent):
            assert name in TOOL_REGISTRY, f"{name} not in TOOL_REGISTRY"


class TestWorkpaperAgent:
    def test_required_tools(self):
        from app.agents.workpaper_agent import WorkpaperAgent
        names = _get_tool_names(WorkpaperAgent)
        assert "query_db" in names
        assert "write_workpaper_entry" in names
        assert "get_signed_url" in names

    def test_all_tools_in_registry(self):
        from app.agents.workpaper_agent import WorkpaperAgent
        for name in _get_tool_names(WorkpaperAgent):
            assert name in TOOL_REGISTRY, f"{name} not in TOOL_REGISTRY"


class TestCommsAgent:
    def test_required_tools(self):
        from app.agents.comms_agent import CommsAgent
        names = _get_tool_names(CommsAgent)
        assert "send_email" in names
        assert "check_completeness" in names
        assert "write_db" in names

    def test_all_tools_in_registry(self):
        from app.agents.comms_agent import CommsAgent
        for name in _get_tool_names(CommsAgent):
            assert name in TOOL_REGISTRY, f"{name} not in TOOL_REGISTRY"


class TestToolRegistryCompleteness:
    def test_update_db_registered(self):
        assert "update_db" in TOOL_REGISTRY

    def test_send_email_registered(self):
        assert "send_email" in TOOL_REGISTRY

    def test_registry_size(self):
        """Sanity check: registry should have all Phase 0–3 tools."""
        assert len(TOOL_REGISTRY) >= 28
