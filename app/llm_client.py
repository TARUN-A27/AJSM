import os

import requests

import app.config  # noqa: F401 — loads .env before the os.getenv() calls below

OLLAMA_URL = os.getenv("OLLAMA_URL", "").rstrip("/")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:14b")


def get_embedding(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    response = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": OLLAMA_EMBED_MODEL, "prompt": text},
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    if "embedding" not in data:
        raise RuntimeError(f"No embedding returned: {data}")

    return data["embedding"]


def chat(
    system_prompt: str,
    user_prompt: str,
    *,
    think: bool | None = None,
    num_predict: int | None = None,
    temperature: float | None = None,
) -> str:
    """
    Single entry point for LLM calls. Swapping the model (e.g. qwen3:14b ->
    qwen2.5-coder:14b) is an OLLAMA_CHAT_MODEL env change, not a code change —
    don't hardcode a model name anywhere else.
    """
    options = {"temperature": 0.1 if temperature is None else temperature}
    if num_predict is not None:
        options["num_predict"] = num_predict
    payload = {
        "model": OLLAMA_CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": options,
    }
    if think is not None:
        payload["think"] = think

    response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=180)
    response.raise_for_status()
    data = response.json()

    content = data.get("message", {}).get("content")
    if not content:
        raise RuntimeError(f"No chat response returned: {data}")

    return content
