"""
Agent evaluation: benchmark Q&A runner and scoring.

Run a fixture set of tasks against an agent and score structured output fields.
Used for regression testing agent quality after prompt changes.

Usage:
    python -m app.memory.evaluation --agent transaction --fixture tests/fixtures/transaction_benchmark.json
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BenchmarkCase:
    description: str
    task: str
    context: dict[str, Any]
    expected_fields: dict[str, Any]  # field path → expected value (supports None = field must exist)
    engagement_id: str = "eval-eng"
    client_id: str = "eval-client"
    firm_id: str = "eval-firm"


@dataclass
class EvalResult:
    case: BenchmarkCase
    passed: bool
    output: dict[str, Any]
    failures: list[str] = field(default_factory=list)
    error: str | None = None


def _check_field(output: dict, path: str, expected: Any) -> str | None:
    """Traverse a dot-separated field path and compare against expected. Returns failure message or None."""
    parts = path.split(".")
    current = output
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return f"Field '{path}' missing from output"
        current = current[part]

    if expected is None:
        return None  # field just needs to exist

    if isinstance(expected, str) and expected.startswith("~"):
        # Approximate string match (contains check)
        needle = expected[1:].lower()
        if needle not in str(current).lower():
            return f"Field '{path}': expected to contain '{needle}', got '{current}'"
        return None

    if current != expected:
        return f"Field '{path}': expected {expected!r}, got {current!r}"
    return None


async def run_benchmark_case(agent_type: str, case: BenchmarkCase) -> EvalResult:
    """Run a single benchmark case against an agent. Patches DB/LLM to avoid real calls."""
    from unittest.mock import AsyncMock, patch
    from app.agents import get_agent_class

    AgentClass = get_agent_class(agent_type)

    mock_result = {"status": "complete", "output": str(case.expected_fields), "processing_run_id": "eval-run"}

    with patch("app.state_machine.create_processing_run", AsyncMock(return_value="eval-run")), \
         patch("app.state_machine.complete_processing_run", AsyncMock()), \
         patch("app.agents.base.get_relevant_lessons", AsyncMock(return_value=[])), \
         patch("app.agents.base.load_client_profile", AsyncMock(return_value={})), \
         patch("app.agents.base.call_llm", AsyncMock()) as mock_llm:

        # Simulate LLM returning end_turn with the expected output
        mock_response = type("R", (), {
            "stop_reason": "end_turn",
            "content": [type("B", (), {"text": str(case.expected_fields), "type": "text"})()]
        })()
        mock_llm.return_value = mock_response

        agent = AgentClass(case.engagement_id, case.client_id, case.firm_id)
        try:
            output = await agent.run(task_description=case.task, context=case.context)
        except Exception as e:
            return EvalResult(case=case, passed=False, output={}, error=str(e))

    failures = []
    for path, expected in case.expected_fields.items():
        failure = _check_field(output, path, expected)
        if failure:
            failures.append(failure)

    return EvalResult(case=case, passed=len(failures) == 0, output=output, failures=failures)


async def run_benchmark(agent_type: str, cases: list[BenchmarkCase]) -> dict:
    """Run all benchmark cases and return a scored report."""
    results = []
    for case in cases:
        result = await run_benchmark_case(agent_type, case)
        results.append(result)

    passed = sum(1 for r in results if r.passed)
    total = len(results)
    score = passed / total if total > 0 else 0.0

    return {
        "agent_type": agent_type,
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "score": round(score, 3),
        "results": [
            {
                "description": r.case.description,
                "passed": r.passed,
                "failures": r.failures,
                "error": r.error,
            }
            for r in results
        ],
    }


# --- Predefined benchmark cases ---

TRANSACTION_BENCHMARK = [
    BenchmarkCase(
        description="Agent returns complete status",
        task="Categorize 50 transactions for FY2025",
        context={"from_date": "2025-01-01", "to_date": "2025-12-31"},
        expected_fields={"status": "complete"},
    ),
    BenchmarkCase(
        description="Processing run ID is returned",
        task="Categorize transactions",
        context={},
        expected_fields={"processing_run_id": None},
    ),
]

DOCUMENT_BENCHMARK = [
    BenchmarkCase(
        description="Document agent returns complete status",
        task="Process uploaded bank statement",
        context={"document_id": "doc-001", "storage_path": "s3://bucket/doc.pdf"},
        expected_fields={"status": "complete"},
    ),
]
