import asyncio
import json
import re
import anthropic
from app.config import settings

_client: anthropic.AsyncAnthropic | None = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
    return _client


async def call_llm(
    model: str,
    system: str,
    messages: list[dict],
    tools: list[dict] | None = None,
    firm_id: str | None = None,
) -> anthropic.types.Message:
    """Call Claude API with PII scrubbing, token logging, and exponential-backoff retry."""
    scrubbed_messages = _scrub_pii(messages)

    kwargs: dict = {
        "model": model,
        "max_tokens": 4096,
        "system": system,
        "messages": scrubbed_messages,
    }
    if tools:
        kwargs["tools"] = tools

    client = _get_client()
    last_error: Exception | None = None

    for attempt in range(3):
        try:
            response = await client.messages.create(**kwargs)
            _log_api_call(
                model=model,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                stop_reason=response.stop_reason,
                firm_id=firm_id,
            )
            return response
        except anthropic.RateLimitError as e:
            last_error = e
            await asyncio.sleep(2 ** attempt)
        except anthropic.APIError as e:
            last_error = e
            if attempt == 2:
                raise
            await asyncio.sleep(1)

    raise last_error  # type: ignore[misc]


async def get_embedding(text: str) -> list[float]:
    """Get 1024-dim text embedding via Mistral embeddings API."""
    from mistralai import Mistral

    mistral = Mistral(api_key=settings.MISTRAL_API_KEY)
    response = mistral.embeddings.create(
        model="mistral-embed",
        inputs=[text],
    )
    return response.data[0].embedding


def _scrub_pii(messages: list[dict]) -> list[dict]:
    """Deep-copy messages and redact PII before sending to LLM."""
    scrubbed = json.loads(json.dumps(messages))
    for msg in scrubbed:
        content = msg.get("content")
        if isinstance(content, str):
            msg["content"] = _scrub_text(content)
        elif isinstance(content, list):
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    block["text"] = _scrub_text(block.get("text", ""))
                elif block.get("type") == "tool_result":
                    if isinstance(block.get("content"), str):
                        block["content"] = _scrub_text(block["content"])
    return scrubbed


def _scrub_text(text: str) -> str:
    # SIN: 9 digits (XXX-XXX-XXX or XXXXXXXXX)
    text = re.sub(r"\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b", "[SIN_REDACTED]", text)
    # Bank account numbers (8-12 digits) — keep last 4
    text = re.sub(r"\b\d{8,12}\b", lambda m: "****" + m.group()[-4:], text)
    # Email addresses
    text = re.sub(
        r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
        "[EMAIL]",
        text,
    )
    # Phone numbers (North American)
    text = re.sub(
        r"\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "[PHONE]",
        text,
    )
    return text


def _log_api_call(
    model: str,
    input_tokens: int,
    output_tokens: int,
    stop_reason: str,
    firm_id: str | None,
) -> None:
    """Write token usage to api_call_logs. Fire-and-forget — errors are swallowed."""
    import asyncio

    async def _write() -> None:
        try:
            from app.tools.db import write_db

            await write_db(
                "api_call_logs",
                {
                    "firm_id": firm_id,
                    "model": model,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "stop_reason": stop_reason,
                },
            )
        except Exception:
            pass

    try:
        loop = asyncio.get_event_loop()
        loop.create_task(_write())
    except RuntimeError:
        pass
