import asyncio
import base64
from app.config import settings

_mistral_client = None


def _get_mistral_client():
    global _mistral_client
    if _mistral_client is None:
        from mistralai import Mistral
        _mistral_client = Mistral(api_key=settings.MISTRAL_API_KEY)
    return _mistral_client


async def mistral_ocr(file_path: str) -> dict:
    """
    Extract text and layout from a document using Mistral OCR.
    Accepts local file paths (PDF, PNG, JPEG).
    Returns extracted text per page plus raw markdown.
    """
    with open(file_path, "rb") as f:
        raw = f.read()

    ext = file_path.lower().rsplit(".", 1)[-1]
    mime_types = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}
    mime = mime_types.get(ext, "application/pdf")
    b64 = base64.b64encode(raw).decode()
    data_url = f"data:{mime};base64,{b64}"

    client = _get_mistral_client()

    def _call_ocr():
        return client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "document_url", "document_url": data_url},
            include_image_base64=False,
        )

    response = await asyncio.to_thread(_call_ocr)

    pages = []
    full_text = []
    for page in response.pages:
        pages.append({"page": page.index, "text": page.markdown})
        full_text.append(page.markdown)

    return {
        "file_path": file_path,
        "page_count": len(pages),
        "pages": pages,
        "full_text": "\n\n".join(full_text),
        "model": "mistral-ocr-latest",
    }
