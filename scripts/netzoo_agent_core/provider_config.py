"""Which LLM provider a session talks to, and with whose key.

The project's ``.env`` stays the default: OpenRouter with ``OPENROUTER_API_KEY``
and the model allowlists the container starts with. A person can instead save
their own provider in the desktop Settings view:

* ``openrouter`` with their own key (the allowlists still apply; the curated
  free models below are added, because they cost nothing). Models the person
  picks from OpenRouter's full catalog are added too: choosing one is the
  person's own decision to pay for it,
* ``openai`` (api.openai.com) or ``custom`` -- any OpenAI-compatible endpoint
  (Groq, DeepSeek, a local Ollama via host.docker.internal, ...). Their model
  ids are not OpenRouter ids, so the models the person lists for the provider
  become that provider's allowlist; the person is paying for those calls.

The saved file is owner-only, outside git (``.netzoo/`` is ignored), and its key
is never returned by ``public_view``. A worker applies the file to its own
process environment (one session, one process), so nothing here changes the
daemon's environment or another session's.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlparse

from .memory.storage import _exclusive_file_lock, _write_json_atomic
from .settings import DEFAULT_ROUTER_MODEL, PROJECT_ROOT

__all__ = [
    "FREE_OPENROUTER_MODELS",
    "OPENROUTER_BASE_URL",
    "PROVIDERS",
    "ProviderError",
    "apply_to_environment",
    "load",
    "llm_api_key",
    "llm_base_url",
    "add_model",
    "model_choices",
    "public_view",
    "recommended_models",
    "remove_model",
    "save",
]

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
PROVIDERS = {
    "openrouter": OPENROUTER_BASE_URL,
    "openai": "https://api.openai.com/v1",
    "custom": "",
}

#: OpenRouter free models offered in the desktop's model menus, best first.
#: Picked 2026-11-14 from the 14 ":free" models OpenRouter listed: each answered
#: one forced function call (the way every NetZoo role calls its model)
#: correctly on a per-sample PANDA/LIONESS routing question. Left out:
#: gemma-4-31b/26b (rate-limited upstream), inkling-2-small (403, restricted to
#: named agent harnesses), ling-3.2-flash (31 s for one call), and the small
#: coding models. One call each is a smoke test, not a routing measurement.
FREE_OPENROUTER_MODELS = (
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "baidu/ernie-5.5-flash-preview:free",
    "nvidia/nemotron-3.5-super-vl:free",
    "dots-studio/dots-3-note-preview:free",
)

PROVIDER_PATH = PROJECT_ROOT / ".netzoo" / "provider" / "provider.json"
MAX_MODELS = 12
_MANAGED_ENV = (
    "NETZOO_LLM_BASE_URL", "NETZOO_LLM_API_KEY", "OPENROUTER_API_KEY",
    "NETZOO_RESPONSE_MODEL_ALLOWLIST", "NETZOO_ROUTER_MODEL_ALLOWLIST",
    "OPENROUTER_MODEL", "OPENROUTER_ROUTER_MODEL", "OPENROUTER_SEMANTIC_MODEL",
    "OPENROUTER_CAPABILITY_MODEL",
)
_ORIGINAL_ENV: dict[int, dict] = {}


class ProviderError(ValueError):
    """A provider setting that cannot be saved as given."""


def _clean_models(models) -> list[str]:
    seen: list[str] = []
    for item in models or []:
        name = str(item).strip()
        if name and len(name) <= 200 and name not in seen:
            seen.append(name)
    return seen[:MAX_MODELS]


def load(path: Path | None = None) -> dict:
    """The saved provider, or the ``.env`` default when nothing is saved."""
    path = path or PROVIDER_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        payload = {}
    provider = payload.get("provider") if payload.get("provider") in PROVIDERS else "openrouter"
    base_url = str(payload.get("base_url") or "").strip() or PROVIDERS[provider]
    return {
        "provider": provider,
        "base_url": base_url,
        "api_key": str(payload.get("api_key") or "").strip(),
        "models": _clean_models(payload.get("models")),
    }


def save(update: dict, path: Path | None = None) -> dict:
    """Validate and store a provider; an empty ``api_key`` keeps the saved one.

    ``clear_key`` removes the saved key (OpenRouter then falls back to ``.env``).
    """
    path = path or PROVIDER_PATH
    provider = str(update.get("provider") or "openrouter")
    if provider not in PROVIDERS:
        raise ProviderError(f"Unknown provider {provider!r}; choose one of {', '.join(PROVIDERS)}.")
    base_url = str(update.get("base_url") or "").strip() or PROVIDERS[provider]
    parsed = urlparse(base_url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ProviderError("The base URL must be an http(s) URL, e.g. https://api.groq.com/openai/v1.")
    if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "host.docker.internal"}:
        raise ProviderError("A plain-http base URL is only allowed for a local server; use https.")
    models = _clean_models(update.get("models"))
    if provider != "openrouter" and not models:
        raise ProviderError("List at least one model id this provider serves, e.g. gpt-4o-mini.")
    with _exclusive_file_lock(path.with_suffix(".lock")):
        current = load(path)
        key = str(update.get("api_key") or "").strip()
        if update.get("clear_key"):
            key = ""
        elif not key and current["provider"] == provider:
            key = current["api_key"]
        if provider != "openrouter" and not key and not _is_local(parsed.hostname):
            raise ProviderError("This provider needs an API key.")
        _write_json_atomic(path, {"provider": provider, "base_url": base_url,
                                  "api_key": key, "models": models})
    return public_view(path)


def _is_local(host: str | None) -> bool:
    return host in {"localhost", "127.0.0.1", "host.docker.internal"}


def _env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.environ.get(name, default).split(",")
            if item.strip() and item.strip() != "(unset)"]


def _start_env_list(name: str, default: str = "") -> list[str]:
    """``_env_list`` as the process started, before a provider widened it."""
    original = _ORIGINAL_ENV.get(id(os.environ))
    if original is None or name not in original:
        return _env_list(name, default)
    value = original[name]
    return [item.strip() for item in (default if value is None else value).split(",")
            if item.strip() and item.strip() != "(unset)"]


def recommended_models(config: dict | None = None) -> list[str]:
    """The models NetZoo has been checked on under this provider, default first.

    OpenRouter: what both ``.env`` allowlists permit, then the curated free
    models. Any other provider: none -- NetZoo has not been checked there, so
    only the models the person listed are offered.
    """
    config = config or load()
    if config["provider"] != "openrouter":
        return []
    router = set(_start_env_list("NETZOO_ROUTER_MODEL_ALLOWLIST", DEFAULT_ROUTER_MODEL))
    allowed = [name for name in _start_env_list("NETZOO_RESPONSE_MODEL_ALLOWLIST", DEFAULT_ROUTER_MODEL)
               if name in router]
    # A free model the .env still names but OpenRouter retired (the
    # nemotron-3-super that 404s since 2026-10-20) is not offered again.
    allowed = [name for name in allowed if not name.endswith(":free") or name in FREE_OPENROUTER_MODELS]
    return allowed + [name for name in FREE_OPENROUTER_MODELS if name not in allowed]


def model_choices(config: dict | None = None) -> list[str]:
    """Models a whole session may run on under this provider, default first.

    OpenRouter: the recommended models, then the ones the person added from
    the catalog. Any other provider: exactly the models the person listed.
    """
    config = config or load()
    recommended = recommended_models(config)
    return recommended + [name for name in config["models"] if name not in recommended]


def _with_models(change, path: Path | None = None) -> dict:
    """Rewrite only the saved model list, keeping provider, URL and key."""
    path = path or PROVIDER_PATH
    with _exclusive_file_lock(path.with_suffix(".lock")):
        current = load(path)
        models = change(list(current["models"]), current)
        _write_json_atomic(path, {"provider": current["provider"], "base_url": current["base_url"],
                                  "api_key": current["api_key"], "models": models})
    return public_view(path)


def add_model(model: str, path: Path | None = None) -> dict:
    """Add one model (picked from the catalog) to the saved provider's list."""
    model = str(model or "").strip()
    if not model or len(model) > 200 or any(ch.isspace() for ch in model):
        raise ProviderError("Give one model id, e.g. anthropic/claude-haiku-5.5.")

    def change(models: list[str], current: dict) -> list[str]:
        if model in models or model in recommended_models(current):
            return models
        if len(models) >= MAX_MODELS:
            raise ProviderError(f"At most {MAX_MODELS} added models; remove one in Settings first.")
        return models + [model]

    return _with_models(change, path)


def remove_model(model: str, path: Path | None = None) -> dict:
    """Remove one added model; another provider keeps at least one."""
    model = str(model or "").strip()

    def change(models: list[str], current: dict) -> list[str]:
        kept = [name for name in models if name != model]
        if not kept and current["provider"] != "openrouter":
            raise ProviderError("This provider needs at least one model.")
        return kept

    return _with_models(change, path)


def llm_base_url() -> str:
    return os.environ.get("NETZOO_LLM_BASE_URL", "").strip() or OPENROUTER_BASE_URL


def llm_api_key() -> str:
    return (os.environ.get("NETZOO_LLM_API_KEY", "").strip()
            or os.environ.get("OPENROUTER_API_KEY", "").strip())


def apply_to_environment(config: dict | None = None, environ=None) -> dict:
    """Point this process's model calls at the saved provider.

    Called by a session worker before it reads its arguments, and again when
    the person switches model mid-conversation. Returns the config applied.
    """
    environ = os.environ if environ is None else environ
    config = config or load()
    # Start from the environment the process began with, so switching from
    # one provider to another mid-session leaves nothing of the first behind.
    original = _ORIGINAL_ENV.setdefault(id(environ), {name: environ.get(name) for name in _MANAGED_ENV})
    for name, value in original.items():
        if value is None:
            environ.pop(name, None)
        else:
            environ[name] = value
    environ["NETZOO_LLM_BASE_URL"] = config["base_url"]
    if config["provider"] == "openrouter":
        if config["api_key"]:
            # Their own OpenRouter account pays for everything, Jev included.
            environ["OPENROUTER_API_KEY"] = config["api_key"]
            environ["NETZOO_LLM_API_KEY"] = config["api_key"]
        else:
            environ.pop("NETZOO_LLM_API_KEY", None)
        # The free models, and the ones the person added from the catalog.
        extra = list(FREE_OPENROUTER_MODELS) + config["models"]
        for name in ("NETZOO_RESPONSE_MODEL_ALLOWLIST", "NETZOO_ROUTER_MODEL_ALLOWLIST"):
            current = _env_list(name, DEFAULT_ROUTER_MODEL)
            environ[name] = ",".join(current + [m for m in dict.fromkeys(extra) if m not in current])
        return config
    # Another provider: OpenRouter ids mean nothing there. Its own models are
    # the allowlist and the defaults; the capability check, which normally
    # runs on its own OpenRouter model, uses the session's model instead.
    # OPENROUTER_API_KEY is left alone, so Jev keeps working when .env has it.
    environ["NETZOO_LLM_API_KEY"] = config["api_key"] or "not-needed"
    models = ",".join(config["models"])
    environ["NETZOO_RESPONSE_MODEL_ALLOWLIST"] = models
    environ["NETZOO_ROUTER_MODEL_ALLOWLIST"] = models
    for name in ("OPENROUTER_MODEL", "OPENROUTER_ROUTER_MODEL", "OPENROUTER_SEMANTIC_MODEL"):
        environ[name] = config["models"][0]
    environ.pop("OPENROUTER_CAPABILITY_MODEL", None)
    return config


def public_view(path: Path | None = None) -> dict:
    """The saved provider without its key: whether one is set and its last four characters."""
    config = load(path)
    key = config["api_key"]
    using_env = config["provider"] == "openrouter" and not key
    return {
        "provider": config["provider"],
        "base_url": config["base_url"],
        "models": config["models"],
        "key_saved": bool(key),
        "key_hint": f"…{key[-4:]}" if len(key) >= 8 else "",
        "key_source": "saved" if key else ("env" if using_env and os.environ.get("OPENROUTER_API_KEY") else "none"),
        "presets": dict(PROVIDERS),
        "model_choices": model_choices(config),
        "recommended_models": recommended_models(config),
        "free_models": list(FREE_OPENROUTER_MODELS),
    }
