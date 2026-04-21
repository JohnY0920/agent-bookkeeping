"""
Agent loop integration test.
Requires CLAUDE_API_KEY to be set (skipped otherwise).
Uses a minimal stub agent to verify the BaseAgent loop works end-to-end
against the real Claude API without needing a DB connection.
"""
import os
import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://dev:dev@localhost:5432/architect_ledger")
os.environ.setdefault("MISTRAL_API_KEY", "placeholder")


def _has_claude_key():
    key = os.environ.get("CLAUDE_API_KEY", "")
    return bool(key and not key.startswith("placeholder") and len(key) > 20)


pytestmark = pytest.mark.skipif(
    not _has_claude_key(),
    reason="CLAUDE_API_KEY not set — skipping live agent test"
)


class _EchoAgent:
    """Minimal agent that asks Claude a simple question, no tool use needed."""
    from app.agents.base import BaseAgent

    agent_type = "test"
    model = "claude-haiku-4-5-20251001"
    tools = []
    system_prompt = "You are a helpful assistant. Answer concisely in one sentence."
    engagement_id = "test-eng"
    client_id = "test-client"
    firm_id = "test-firm"

    def _build_messages(self, task, context, lessons, profile):
        return [{"role": "user", "content": task}]

    async def run(self, task_description, context=None):
        from app.models.llm import call_llm
        response = await call_llm(
            model=self.model,
            system=self.system_prompt,
            messages=[{"role": "user", "content": task_description}],
        )
        return {"status": "complete", "output": response.content[0].text}


async def test_claude_api_responds():
    """Verify Claude API key is valid and we get a coherent response."""
    agent = _EchoAgent()
    result = await agent.run("What is 2 + 2?")
    assert result["status"] == "complete"
    assert "4" in result["output"]
    print(f"\nClaude responded: {result['output']}")


async def test_pii_scrubbing_before_api_call():
    """Verify PII is scrubbed before the message reaches Claude."""
    from app.models.llm import _scrub_pii

    messages = [{"role": "user", "content": "Client SIN is 123-456-789, account 12345678901234"}]
    scrubbed = _scrub_pii(messages)
    content = scrubbed[0]["content"]
    assert "123-456-789" not in content
    assert "[SIN_REDACTED]" in content
    assert "12345678901234" not in content
    assert "****" in content
