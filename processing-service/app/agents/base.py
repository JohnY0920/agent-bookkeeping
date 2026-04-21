from abc import ABC, abstractmethod
from app.models.llm import call_llm
from app.models.router import get_model_for_agent
from app.memory.lesson_store import get_relevant_lessons
from app.memory.client_profile import load_client_profile


class BaseAgent(ABC):
    """Base class for all processing agents."""

    agent_type: str = ""
    default_model: str = "sonnet"

    def __init__(self, engagement_id: str, client_id: str, firm_id: str):
        self.engagement_id = engagement_id
        self.client_id = client_id
        self.firm_id = firm_id
        self.tools = self._register_tools()
        self.system_prompt = self._load_prompt()
        self.model = get_model_for_agent(self.agent_type)

    @abstractmethod
    def _register_tools(self) -> list[dict]:
        """Return Claude API tool definitions this agent can call."""

    @abstractmethod
    def _load_prompt(self) -> str:
        """Load system prompt from prompts/ directory."""

    async def run(self, task_description: str, context: dict | None = None) -> dict:
        """Execute the agent with a task and optional context."""
        lessons = await get_relevant_lessons(
            agent_type=self.agent_type,
            client_id=self.client_id,
            task_description=task_description,
        )
        client_profile = await load_client_profile(self.client_id)
        messages = self._build_messages(task_description, context, lessons, client_profile)
        return await self._agent_loop(messages)

    async def _agent_loop(self, messages: list[dict]) -> dict:
        """Core loop: call LLM → execute tool calls → repeat until end_turn (max 25 iter)."""
        max_iterations = 25

        for _ in range(max_iterations):
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
