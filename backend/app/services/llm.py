"""One small place that talks to the optional AI service (OpenRouter).

The project works fully without it. When no key or model is configured, or when the
call fails for any reason, this returns None and the caller falls back to plain rules.
"""
from __future__ import annotations

import json
import urllib.request

from app.core.config import settings


def llm_configured() -> bool:
    return bool(settings.openrouter_api_key and settings.llm_model)


def ask_llm(system: str, user: str, temperature: float = 0.0, timeout: int = 20) -> str | None:
    if not llm_configured():
        return None
    payload = json.dumps({
        "model": settings.llm_model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": temperature,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=payload, method="POST",
        headers={"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json",
                 "HTTP-Referer": "http://localhost:5173", "X-Title": "KrishiAssist"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())["choices"][0]["message"]["content"].strip()
    except Exception:  # noqa: BLE001 - any failure simply means "no AI answer"
        return None
