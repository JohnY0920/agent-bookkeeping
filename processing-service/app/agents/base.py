import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from app.models.llm import call_llm
from app.models.router import get_model_for_agent
from app.memory.lesson_store import get_relevant_lessons
from app.memory.client_profile import load_client_profile


class BaseAgent(ABC):
    """Base class for all processing agents.

    Stateless restart invariant: every call to run() creates a NEW processing_run
    and starts from scratch. Failed runs are marked FAILED; the next dispatch
    always begins with a clean slate — never resumes from prior run state.
    """

    agent_type: str = ""

    def __init__(self, engagement_id: str, client_id: str, firm_id: str):
        self.engagement_id = engagement_id
        self.client_id = client_id
        self.firm_id = firm_id
        self.tools = self._register_tools()
        self.system_prompt, self.prompt_version = self._load_prompt()
        self.model = get_model_for_agent(self.agent_type)

    @abstractmethod
    def _register_tools(self) -> list[dict]:
        """Return Claude API tool definitions this agent can call."""

    def _load_prompt(self) -> tuple[str, str | None]:
        """Load system prompt from prompts/ directory. Returns (content, version)."""
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / f"{self.agent_type}_agent.md"
        if not prompt_path.exists():
            return "", None
        raw = prompt_path.read_text()
        version = None
        content = raw
        if raw.startswith("---"):
            end = raw.find("---", 3)
            if end != -1:
                try:
                    meta = yaml.safe_load(raw[3:end])
                    version = str(meta.get("version", "")) or None
                except Exception:
                    pass
                content = raw[end + 3:].lstrip()
        return content, version

    async def run(self, task_description: str, context: dict | None = None) -> dict:
        """Execute the agent. Always starts from scratch — never resumes prior state."""
        from app.state_machine import create_processing_run, complete_processing_run, fail_processing_run
        run_id = await create_processing_run(
            engagement_id=self.engagement_id,
            firm_id=self.firm_id,
            agent_type=self.agent_type,
            task_description=task_description,
            prompt_version=self.prompt_version,
        )
        try:
            lessons = await get_relevant_lessons(
                agent_type=self.agent_type,
                client_id=self.client_id,
                task_description=task_description,
            )
            client_profile = await load_client_profile(self.client_id)
            messages = self._build_messages(task_description, context, lessons, client_profile)
            result = await self._agent_loop(messages, run_id=run_id)
            await complete_processing_run(run_id, result_summary=result.get("output", "")[:500])
            result["processing_run_id"] = run_id
            return result
        except Exception as e:
            await fail_processing_run(run_id, error_message=str(e))
            raise

    async def _agent_loop(self, messages: list[dict], run_id: str | None = None) -> dict:
        """Core loop: call LLM → execute tool calls → repeat until end_turn (max 25 iter)."""
        for _ in range(25):
            response = await call_llm(
                model=self.model,
                system=self.system_prompt,
                messages=messages,
                tools=self.tools or None,
                firm_id=self.firm_id,
            )

            if response.stop_reason == "end_turn":
                return self._extract_result(response)

            if response.stop_reason == "tool_use":
                tool_results = await self._execute_tool_calls(response.content)
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

        return {"status": "max_iterations_reached"}

    async def _execute_tool_calls(self, content: list) -> list[dict]:
        """Execute each tool_use block and return tool_result blocks."""
        results = []
        for block in content:
            if not hasattr(block, "type") or block.type != "tool_use":
                continue
            tool_fn = self._get_tool_function(block.name)
            try:
                result = await tool_fn(**block.input)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                })
            except Exception as e:
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": f"Error: {e}",
                    "is_error": True,
                })
        return results

    def _build_messages(
        self,
        task_description: str,
        context: dict | None,
        lessons: list[dict],
        client_profile: dict | None,
    ) -> list[dict]:
        parts = [f"## Task\n{task_description}\n"]

        if client_profile:
            parts.append(f"## Client profile\n{client_profile}\n")

        if lessons:
            lesson_lines = "\n".join(f"- {l['lesson_content']}" for l in lessons)
            parts.append(f"## Lessons from previous similar tasks\n{lesson_lines}\n")

        if context:
            parts.append(f"## Additional context\n{context}\n")

        return [{"role": "user", "content": "\n".join(parts)}]

    def _get_tool_function(self, tool_name: str):
        from app.tools import TOOL_REGISTRY
        if tool_name not in TOOL_REGISTRY:
            raise ValueError(f"Unknown tool: {tool_name}")
        return TOOL_REGISTRY[tool_name]

    def _extract_result(self, response) -> dict:
        text_blocks = [b.text for b in response.content if hasattr(b, "text")]
        return {"status": "complete", "output": "\n".join(text_blocks)}
