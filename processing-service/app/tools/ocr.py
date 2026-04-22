import asyncio
import base64
import anthropic
from app.config import settings

_client = None


def _get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)
    return _client


async def extract_document(file_path: str) -> dict:
    """
    Extract text and structure from a document using Claude Sonnet vision.
    Accepts local file paths (PDF, PNG, JPEG).
    Returns extracted text per page plus raw markdown.
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    ext = file_path.lower().rsplit(".", 1)[-1]
    mime_map = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    mime = mime_map.get(ext, "application/pdf")
    b64 = base64.standard_b64encode(raw).decode()

    if mime == "application/pdf":
        content_block = {
            "type": "document",
            "source": {"type": "base64", "media_type": mime, "data": b64},
        }
    else:
        content_block = {
            "type": "image",
            "source": {"type": "base64", "media_type": mime, "data": b64},
        }

    client = _get_client()
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=(
            "You are a document extraction assistant. Extract all text and structure from the document. "
            "Preserve tables, labels, amounts, and dates exactly as they appear. "
            "Format your response as clean markdown."
        ),
        messages=[{
            "role": "user",
            "content": [
                content_block,
                {"type": "text", "text": "Extract all text and structure from this document. Preserve all numbers, dates, and labels exactly."},
            ],
        }],
    )

    extracted = response.content[0].text
    return {
        "file_path": file_path,
        "page_count": 1,
        "pages": [{"page": 0, "text": extracted}],
        "full_text": extracted,
        "model": "claude-sonnet-4-6",
    }
