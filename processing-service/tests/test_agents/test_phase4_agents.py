"""Phase 4 agent registration and tool coverage tests."""
import pytest
from app.tools import TOOL_REGISTRY


def _get_tool_names(agent_class):
    agent = agent_class.__new__(agent_class)
    agent.agent_type = agent_class.agent_type
    return {t["name"] for t in agent._register_tools()}


class TestFinancialStmtAgent:
    def test_agent_type(self):
        from app.agents.financial_stmt_agent import FinancialStmtAgent
        assert FinancialStmtAgent.agent_type == "financial_stmt"

    def test_uses_sonnet(self):
        from app.models.router import get_model_for_agent
        assert get_model_for_agent("financial_stmt") == "claude-sonnet-4-6"

    def test_required_tools(self):
        from app.agents.financial_stmt_agent import FinancialStmtAgent
        names = _get_tool_names(FinancialStmtAgent)
        assert "query_db" in names
        assert "write_workpaper_entry" in names
        assert "create_review_item" in names

    def test_all_tools_in_registry(self):
        from app.agents.financial_stmt_agent import FinancialStmtAgent
        for name in _get_tool_names(FinancialStmtAgent):
            assert name in TOOL_REGISTRY

    def test_no_write_gl_entry(self):
        """Financial statements are read-only from GL."""
        from app.agents.financial_stmt_agent import FinancialStmtAgent
        assert "write_gl_entry" not in _get_tool_names(FinancialStmtAgent)


class TestTaxAgent:
    def test_agent_type(self):
        from app.agents.tax_agent import TaxAgent
        assert TaxAgent.agent_type == "tax"

    def test_required_tools(self):
        from app.agents.tax_agent import TaxAgent
        names = _get_tool_names(TaxAgent)
        assert "calculate_tax_payable" in names
        assert "calculate_sbd" in names
        assert "search_knowledge_base" in names
        assert "create_plan_step" in names
        assert "write_workpaper_entry" in names

    def test_requires_human_via_plan_step(self):
        """Tax agent must create plan_steps (requires_human), not bypass CPA."""
        from app.agents.tax_agent import TaxAgent
        names = _get_tool_names(TaxAgent)
        assert "create_plan_step" in names

    def test_all_tools_in_registry(self):
        from app.agents.tax_agent import TaxAgent
        for name in _get_tool_names(TaxAgent):
            assert name in TOOL_REGISTRY


class TestFilingAgent:
    def test_agent_type(self):
        from app.agents.filing_agent import FilingAgent
        assert FilingAgent.agent_type == "filing"

    def test_uses_haiku(self):
        from app.models.router import get_model_for_agent
        assert get_model_for_agent("filing") == "claude-haiku-4-5-20251001"

    def test_required_tools(self):
        from app.agents.filing_agent import FilingAgent
        names = _get_tool_names(FilingAgent)
        assert "query_db" in names
        assert "update_db" in names
        assert "upload_file" in names
        assert "write_workpaper_entry" in names
        assert "dispatch_agent" in names

    def test_all_tools_in_registry(self):
        from app.agents.filing_agent import FilingAgent
        for name in _get_tool_names(FilingAgent):
            assert name in TOOL_REGISTRY


class TestFlowDefinitions:
    def test_t1_flow_has_required_agents(self):
        from app.flows.t1_personal import T1_FLOW_STEPS
        agent_types = {s["agent"] for s in T1_FLOW_STEPS}
        assert "document" in agent_types
        assert "tax" in agent_types
        assert "filing" in agent_types

    def test_t1_tax_and_filing_require_human(self):
        from app.flows.t1_personal import T1_FLOW_STEPS
        human_required = {s["agent"] for s in T1_FLOW_STEPS if s.get("requires_human")}
        assert "tax" in human_required
        assert "filing" in human_required

    def test_t2_flow_has_all_phases(self):
        from app.flows.t2_corporate import T2_FLOW_STEPS
        modes = {s["mode"] for s in T2_FLOW_STEPS}
        assert "COLLECTION" in modes
        assert "PROCESSING" in modes
        assert "REVIEW" in modes

    def test_t2_yearend_requires_human(self):
        from app.flows.t2_corporate import T2_FLOW_STEPS
        yearend_steps = [s for s in T2_FLOW_STEPS if s["agent"] == "yearend"]
        assert all(s.get("requires_human") for s in yearend_steps)

    def test_bookkeeping_flow_is_subset_of_t2(self):
        from app.flows.bookkeeping import FLOW_STEPS
        from app.flows.t2_corporate import T2_FLOW_STEPS
        bk_agents = {s["agent"] for steps in FLOW_STEPS.values() for s in steps}
        t2_agents = {s["agent"] for s in T2_FLOW_STEPS}
        # All BK agents should appear in the T2 flow
        assert bk_agents.issubset(t2_agents | {"comms"})


class TestRegistryFinalState:
    def test_total_tool_count(self):
        """Final registry should have all Phase 0-4 tools."""
        assert len(TOOL_REGISTRY) >= 29

    def test_all_calculation_tools_present(self):
        for tool in ["calculate_cca", "calculate_amortization", "calculate_gst",
                     "calculate_itc", "calculate_tax_payable", "calculate_sbd"]:
            assert tool in TOOL_REGISTRY, f"{tool} missing"

    def test_all_phase2_tools_present(self):
        for tool in ["pull_transactions", "pull_chart_of_accounts",
                     "pull_bank_balances", "search_knowledge_base"]:
            assert tool in TOOL_REGISTRY, f"{tool} missing"
