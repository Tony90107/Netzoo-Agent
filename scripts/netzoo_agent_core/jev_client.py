"""TypeSafe Jev decisions over OpenRouter (`typesafe/jev-1.13`, `/api/alpha/decisions`): one transport for every Jev
caller (the guard, the overlap read). A leaf module: it imports only the standard library, so any layer may use it.

`decide` sends a state and typed questions and returns the provider's JSON; it raises RuntimeError("no_key") without a
key and lets network errors through, so each caller decides what a failure leaves (always: the call as it came).
"""

from __future__ import annotations

import json
import os
import urllib.request

__all__ = ["MODEL", "URL", "decide"]

URL = "https://openrouter.ai/api/alpha/decisions"
MODEL = "typesafe/jev-1.13"


def decide(state: str, questions: dict, *, timeout: float) -> dict:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("no_key")
    body = json.dumps({"model": MODEL, "state": state, "questions": questions}).encode()
    url = os.environ.get("NETZOO_JEV_URL", "").strip() or URL  # a test can point it elsewhere (smoke: Jev down)
    request = urllib.request.Request(url, data=body, headers={"Authorization": f"Bearer {key}",
                                                              "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read())
