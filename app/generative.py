"""Optional proprietary generative-AI call, via environment variable only.

No API key is hardcoded anywhere in this prototype. When no key is set,
call_generative() raises NotConfiguredError and the API returns a clear
message instead of failing. When a key IS set, the call uses the standard
library (urllib) against an OpenAI-compatible chat endpoint, with a
timeout, and any failure is surfaced as GenerativeServiceError so the
API can fall back to the RAG/template answer with a clear note.
"""
import json
import os
import urllib.error
import urllib.request


class NotConfiguredError(Exception):
    pass


class GenerativeServiceError(Exception):
    pass


def generative_configured() -> bool:
    return bool(os.environ.get("GENAI_API_KEY"))


def call_generative(prompt: str) -> str:
    """Call a proprietary model if GENAI_API_KEY is set, else raise."""
    api_key = os.environ.get("GENAI_API_KEY")
    if not api_key:
        raise NotConfiguredError(
            "Generative AI is not configured: GENAI_API_KEY is not set. "
            "Set it in the environment (never in source code) to enable it."
        )
    model = os.environ.get("GENAI_MODEL", "gpt-4o-mini")
    base_url = os.environ.get(
        "GENAI_BASE_URL", "https://api.openai.com/v1/chat/completions"
    )
    payload = json.dumps(
        {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        base_url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise GenerativeServiceError(
            "Generative AI service failed or timed out. "
            "The prototype fell back to its template/RAG answer."
        ) from exc
    try:
        return body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GenerativeServiceError(
            "Generative AI returned an unexpected response format."
        ) from exc
