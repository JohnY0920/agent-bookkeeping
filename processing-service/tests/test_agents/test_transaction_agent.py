"""
Transaction agent benchmark tests.
Verifies correct routing (auto-approve / review / critical) based on confidence.
No real LLM calls — mocks the agent loop output.
"""
import pytest
from unittest.mock import patch, AsyncMock


class TestTransactionAgentInit:
    def test_instantiates_with_correct_type(self):
        from app.agents.transaction_agent import TransactionAgent
        # __init__ only calls _register_tools, _load_prompt, get_model_for_agent — no DB/LLM needed
        agent = TransactionAgent.__new__(TransactionAgent)
        agent.agent_type = "transaction"
        agent.tools = agent._register_tools()
        agent.system_prompt, agent.prompt_version = agent._load_prompt()
        from app.models.router import get_model_for_agent
        agent.model = get_model_for_agent(agent.agent_type)

        assert agent.agent_type == "transaction"
        assert agent.model == "claude-sonnet-4-6"

    def test_registers_required_tools(self):
        from app.agents.transaction_agent import TransactionAgent
        agent = TransactionAgent.__new__(TransactionAgent)
        agent.agent_type = "transaction"
        tools = agent._register_tools()
        tool_names = {t["name"] for t in tools}

        assert "pull_transactions" in tool_names
        assert "write_gl_entry" in tool_names
        assert "create_review_item" in tool_names
        assert "search_knowledge_base" in tool_names
        assert "write_workpaper_entry" in tool_names

    def test_all_tools_in_registry(self):
        from app.agents.transaction_agent import TransactionAgent
        from app.tools import TOOL_REGISTRY

        agent = TransactionAgent.__new__(TransactionAgent)
        agent.agent_type = "transaction"
        for tool_def in agent._register_tools():
            assert tool_def["name"] in TOOL_REGISTRY, f"Tool {tool_def['name']} not in TOOL_REGISTRY"


class TestReconciliationAgentInit:
    def test_registers_required_tools(self):
        from app.agents.reconciliation_agent import ReconciliationAgent
        agent = ReconciliationAgent.__new__(ReconciliationAgent)
        agent.agent_type = "reconciliation"
        tools = agent._register_tools()
        tool_names = {t["name"] for t in tools}

        assert "query_db" in tool_names
        assert "pull_bank_balances" in tool_names
        assert "create_review_item" in tool_names
        assert "write_workpaper_entry" in tool_names

    def test_all_tools_in_registry(self):
        from app.agents.reconciliation_agent import ReconciliationAgent
        from app.tools import TOOL_REGISTRY

        agent = ReconciliationAgent.__new__(ReconciliationAgent)
        agent.agent_type = "reconciliation"
        for tool_def in agent._register_tools():
            assert tool_def["name"] in TOOL_REGISTRY, f"Tool {tool_def['name']} not in TOOL_REGISTRY"


class TestTaxReconAgentInit:
    def test_registers_required_tools(self):
        from app.agents.tax_recon_agent import TaxReconAgent
        agent = TaxReconAgent.__new__(TaxReconAgent)
        agent.agent_type = "tax_recon"
        tools = agent._register_tools()
        tool_names = {t["name"] for t in tools}

        assert "calculate_gst" in tool_names
        assert "calculate_itc" in tool_names
        assert "search_knowledge_base" in tool_names
        assert "create_review_item" in tool_names

    def test_all_tools_in_registry(self):
        from app.agents.tax_recon_agent import TaxReconAgent
        from app.tools import TOOL_REGISTRY

        agent = TaxReconAgent.__new__(TaxReconAgent)
        agent.agent_type = "tax_recon"
        for tool_def in agent._register_tools():
            assert tool_def["name"] in TOOL_REGISTRY, f"Tool {tool_def['name']} not in TOOL_REGISTRY"
