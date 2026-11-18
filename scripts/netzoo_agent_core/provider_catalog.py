"""Every model the saved provider serves, for the desktop's "All models" browser.

OpenRouter's ``/models`` list is public and carries what NetZoo needs to show:
price per token, context length, and whether the model takes function calls
(``supported_parameters`` names ``tools``). Every NetZoo role calls its model
through a forced function call, so a model without tool calling cannot run a
session. OpenAI and other OpenAI-compatible endpoints list only ids; for them
tool support and price are unknown (``None``). A model whose listed endpoints
leave out chat completions (OpenRouter's ``:batch`` variants serve only its
batch API) cannot hold a conversation and is left out.

The list is fetched by the daemon (the key never reaches the desktop) and kept
for ten minutes per provider URL.
"""

from __future__ import annotations

import json
import time
import urllib.request
from urllib.error import HTTPError, URLError

from . import provider_config

__all__ = ["CatalogError", "fetch_catalog"]

_CACHE_SECONDS = 600
_cache: dict[str, tuple[float, list[dict]]] = {}


class CatalogError(RuntimeError):
    """The provider's model list could not be read."""


def _per_million(value) -> float | None:
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    # OpenRouter uses -1 for "varies" (its auto router).
    return round(price * 1_000_000, 4) if price >= 0 else None


def _normalize(item: dict) -> dict | None:
    model_id = str(item.get("id") or "").strip()
    if not model_id:
        return None
    endpoints = item.get("endpoints")
    if isinstance(endpoints, list) and endpoints and not any(
            str(path).endswith("/chat/completions") for path in endpoints):
        return None
    pricing = item.get("pricing")
    params = item.get("supported_parameters")
    prompt = _per_million(pricing.get("prompt")) if isinstance(pricing, dict) else None
    completion = _per_million(pricing.get("completion")) if isinstance(pricing, dict) else None
    return {
        "id": model_id,
        "name": str(item.get("name") or model_id),
        "context_length": item.get("context_length") if isinstance(item.get("context_length"), int) else None,
        "prompt_per_million": prompt,
        "completion_per_million": completion,
        "free": model_id.endswith(":free") or (prompt == 0 and completion == 0),
        "tools": ("tools" in params) if isinstance(params, list) else None,
        "created": item.get("created") if isinstance(item.get("created"), int) else None,
    }


def _download(base_url: str, api_key: str, timeout: float) -> list[dict]:
    request = urllib.request.Request(base_url.rstrip("/") + "/models", headers={"Accept": "application/json"})
    if api_key and api_key != "not-needed":
        request.add_header("Authorization", f"Bearer {api_key}")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - http(s) checked on save
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise CatalogError(f"The provider refused the model list (HTTP {error.code}).") from error
    except (URLError, TimeoutError, OSError) as error:
        raise CatalogError(f"Could not reach the provider's model list: {error}") from error
    except ValueError as error:
        raise CatalogError("The provider's model list was not JSON.") from error
    items = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        raise CatalogError("The provider's model list had no data.")
    return [model for model in (_normalize(item) for item in items if isinstance(item, dict)) if model]


def fetch_catalog(config: dict | None = None, *, timeout: float = 15.0, refresh: bool = False,
                  download=_download) -> dict:
    """The provider's models, newest first, with which are recommended or added."""
    config = config or provider_config.load()
    base_url = config["base_url"]
    api_key = config["api_key"]
    if config["provider"] == "openrouter" and not api_key:
        import os
        api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    cached = _cache.get(base_url)
    if cached and not refresh and time.monotonic() - cached[0] < _CACHE_SECONDS:
        models = cached[1]
    else:
        models = download(base_url, api_key, timeout)
        models.sort(key=lambda model: (-(model["created"] or 0), model["id"]))
        _cache[base_url] = (time.monotonic(), models)
    return {
        "provider": config["provider"],
        "models": models,
        "recommended": provider_config.recommended_models(config),
        "added": list(config["models"]),
        "max_added": provider_config.MAX_MODELS,
    }
