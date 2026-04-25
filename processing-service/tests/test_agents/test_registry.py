"""Verify agent registry completeness and evaluation module."""
import pytest
from unittest.mock import AsyncMock, patch


EXPECTED_AGENTS = [
    "document", "planner", "transaction", "reconciliation", "tax_recon",
    "yearend", "qc", "workpaper", "comms", "financial_stmt", "tax", "filing",
]


class TestAgentRegistry:
    def test_all_agents_registered(self):
        from app.agents import _AGENT_MAP
        for agent_type in EXPECTED_AGENTS:
            assert agent_type in _AGENT_MAP, f"'{agent_type}' missing from _AGENT_MAP"

    def test_get_agent_class_returns_correct_class(self):
        from app.agents import get_agent_class
        from app.agents.transaction_agent import TransactionAgent
        assert get_agent_class("transaction") is TransactionAgent

    def test_unknown_agent_raises_value_error(self):
        from app.agents import get_agent_class
        with pytest.raises(ValueError, match="Unknown agent type"):
            get_agent_class("nonexistent_agent")

    def test_all_registered_agents_have_correct_type(self):
        from app.agents import _AGENT_MAP
        for agent_type, AgentClass in _AGENT_MAP.items():
            agent = AgentClass.__new__(AgentClass)
            assert agent_type == AgentClass.agent_type, \
                f"_AGENT_MAP key '{agent_type}' doesn't match {AgentClass.__name__}.agent_type='{AgentClass.agent_type}'"

    def test_all_agents_have_prompts(self):
        """Every registered agent should have a prompt file in prompts/."""
        from pathlib import Path
        from app.agents import _AGENT_MAP
        prompts_dir = Path(__file__).parent.parent.parent / "prompts"
        for agent_type in _AGENT_MAP:
            if agent_type == "planner":
                prompt_file = prompts_dir / "planner.md"
            else:
                prompt_file = prompts_dir / f"{agent_type}_agent.md"
            assert prompt_file.exists(), f"Missing prompt file for '{agent_type}': {prompt_file}"


class TestCeleryTaskName:
    def test_run_agent_task_exists(self):
        from workers.celery_tasks import run_agent
        assert run_agent.name == "workers.celery_tasks.run_agent"

    def test_dispatch_tool_references_run_agent(self):
        """dispatch.py tool must import run_agent (not the old dispatch_agent name)."""
        import inspect
        from app.tools import dispatch
        src = inspect.getsource(dispatch)
        assert "run_agent" in src


class TestEvaluationModule:
    def test_check_field_exact_match(self):
        from app.memory.evaluation import _check_field
        assert _check_field({"status": "complete"}, "status", "complete") is None
        assert _check_field({"status": "failed"}, "status", "complete") is not None

    def test_check_field_missing(self):
        from app.memory.evaluation import _check_field
        result = _check_field({}, "status", "complete")
        assert "missing" in result

    def test_check_field_none_means_exists(self):
        from app.memory.evaluation import _check_field
        assert _check_field({"id": "abc"}, "id", None) is None
        assert _check_field({}, "id", None) is not None

    def test_check_field_tilde_contains(self):
        from app.memory.evaluation import _check_field
        assert _check_field({"output": "processed 50 transactions"}, "output", "~50 transactions") is None
        assert _check_field({"output": "processed 10 items"}, "output", "~50 transactions") is not None

    def test_check_field_nested_path(self):
        from app.memory.evaluation import _check_field
        data = {"result": {"count": 5}}
        assert _check_field(data, "result.count", 5) is None
        assert _check_field(data, "result.count", 10) is not None

    async def test_run_benchmark_case_passes(self):
        from app.memory.evaluation import BenchmarkCase, run_benchmark_case
        case = BenchmarkCase(
            description="basic pass test",
            task="do something",
            context={},
            expected_fields={"status": "complete"},
        )
        result = await run_benchmark_case("document", case)
        assert result.passed is True
        assert result.error is None

    async def test_run_benchmark_scores_correctly(self):
        from app.memory.evaluation import BenchmarkCase, run_benchmark
        cases = [
            BenchmarkCase("pass", "task", {}, {"status": "complete"}),
            BenchmarkCase("pass2", "task", {}, {"status": "complete"}),
        ]
        report = await run_benchmark("document", cases)
        assert report["total"] == 2
        assert report["passed"] == 2
        assert report["score"] == 1.0
