"""A person's own provider and key, and switching model mid-conversation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core import provider_config  # noqa: E402
from netzoo_agent_core.cli import bootstrap  # noqa: E402
from netzoo_agent_core.session_meta import load_meta  # noqa: E402

from test_server_driver import _Harness, _planning_mode  # noqa: E402,F401
from test_cli_lifecycle import _fake_cli_runtime  # noqa: E402

FREE = provider_config.FREE_OPENROUTER_MODELS[0]
ENV = {
    "OPENROUTER_API_KEY": "sk-or-env-0000",
    "NETZOO_RESPONSE_MODEL_ALLOWLIST": "openai/gpt-4o-mini,nvidia/nemotron-3-super-120b-a12b:free",
    "NETZOO_ROUTER_MODEL_ALLOWLIST": "openai/gpt-4o-mini,nvidia/nemotron-3-super-120b-a12b:free,openai/gpt-4o-mini-2024-07-18",
    "OPENROUTER_MODEL": "openai/gpt-4o-mini",
    "OPENROUTER_ROUTER_MODEL": "openai/gpt-4o-mini",
    "OPENROUTER_SEMANTIC_MODEL": "openai/gpt-4o-mini",
    "OPENROUTER_CAPABILITY_MODEL": "openai/gpt-4o-mini-2024-07-18",
}


@pytest.fixture
def provider_file(tmp_path, monkeypatch):
    path = tmp_path / "provider" / "provider.json"
    monkeypatch.setattr(provider_config, "PROVIDER_PATH", path)
    for name in provider_config._MANAGED_ENV:
        monkeypatch.delenv(name, raising=False)
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    provider_config._ORIGINAL_ENV.clear()
    yield path
    provider_config._ORIGINAL_ENV.clear()


def test_nothing_saved_means_openrouter_with_the_env_key(provider_file):
    view = provider_config.public_view()
    assert view["provider"] == "openrouter"
    assert view["key_source"] == "env" and not view["key_saved"]
    assert provider_config.llm_base_url() == provider_config.OPENROUTER_BASE_URL
    assert provider_config.llm_api_key() == "sk-or-env-0000"


def test_model_choices_offer_the_free_models_but_not_a_retired_one(provider_file):
    choices = provider_config.model_choices()
    assert choices[0] == "openai/gpt-4o-mini"
    assert "nvidia/nemotron-3-super-120b-a12b:free" not in choices
    assert set(provider_config.FREE_OPENROUTER_MODELS) <= set(choices)


def test_a_saved_key_is_owner_only_and_never_read_back(provider_file):
    view = provider_config.save({"provider": "openrouter", "api_key": "sk-or-mine-12345678"})
    assert view["key_saved"] and view["key_hint"] == "…5678"
    assert "sk-or-mine" not in json.dumps(view)
    assert provider_file.stat().st_mode & 0o777 == 0o600
    # Saving again without a key keeps it; clear_key removes it.
    assert provider_config.save({"provider": "openrouter"})["key_saved"]
    assert not provider_config.save({"provider": "openrouter", "clear_key": True})["key_saved"]


def test_another_provider_needs_its_models_a_key_and_https(provider_file):
    with pytest.raises(provider_config.ProviderError, match="model"):
        provider_config.save({"provider": "openai", "api_key": "sk-x-12345678"})
    with pytest.raises(provider_config.ProviderError, match="key"):
        provider_config.save({"provider": "openai", "models": ["gpt-4o-mini"]})
    with pytest.raises(provider_config.ProviderError, match="https"):
        provider_config.save({"provider": "custom", "base_url": "http://example.com/v1",
                              "api_key": "k-12345678", "models": ["m"]})
    # A local server (Ollama) may be plain http and keyless.
    view = provider_config.save({"provider": "custom", "base_url": "http://host.docker.internal:11434/v1",
                                 "models": ["llama3.1"]})
    assert view["model_choices"] == ["llama3.1"]


def test_applying_a_provider_then_switching_back_leaves_nothing_behind(provider_file):
    import os

    provider_config.save({"provider": "openai", "api_key": "sk-proj-abcdefgh", "models": ["gpt-4o-mini", "gpt-4.1-mini"]})
    provider_config.apply_to_environment()
    assert os.environ["NETZOO_LLM_BASE_URL"] == "https://api.openai.com/v1"
    assert provider_config.llm_api_key() == "sk-proj-abcdefgh"
    assert os.environ["NETZOO_ROUTER_MODEL_ALLOWLIST"] == "gpt-4o-mini,gpt-4.1-mini"
    assert os.environ["OPENROUTER_MODEL"] == "gpt-4o-mini"
    assert "OPENROUTER_CAPABILITY_MODEL" not in os.environ
    assert os.environ["OPENROUTER_API_KEY"] == "sk-or-env-0000"  # Jev keeps the .env key

    provider_config.save({"provider": "openrouter"})
    provider_config.apply_to_environment()
    assert provider_config.llm_base_url() == provider_config.OPENROUTER_BASE_URL
    assert provider_config.llm_api_key() == "sk-or-env-0000"
    assert os.environ["OPENROUTER_MODEL"] == "openai/gpt-4o-mini"
    assert os.environ["OPENROUTER_CAPABILITY_MODEL"] == "openai/gpt-4o-mini-2024-07-18"
    assert FREE in os.environ["NETZOO_RESPONSE_MODEL_ALLOWLIST"].split(",")


def _switch_args():
    return SimpleNamespace(model="openai/gpt-4o-mini", router_model="openai/gpt-4o-mini",
                           semantic_model="openai/gpt-4o-mini", router_max_tokens=1200,
                           response_max_tokens=800, max_task_tokens=25_000, llm_timeout=60.0,
                           temperature=0.0,
                           _parsed_limits={"router_max_tokens": 1200, "response_max_tokens": 800,
                                           "max_task_tokens": 25_000, "llm_timeout": 60.0})


def test_switching_rebuilds_only_the_model_layer_and_records_it(provider_file, tmp_path, monkeypatch):
    from netzoo_agent_core import session as session_store

    monkeypatch.setattr(session_store, "SESSION_ROOT", tmp_path / "sessions")
    built = []
    monkeypatch.setattr(bootstrap, "build_model_layer",
                        lambda args, *rest: built.append(args.model) or (f"app:{args.model}", f"resolver:{args.model}"))
    args = _switch_args()
    runtime = SimpleNamespace(session_id="s1", app="old", reply_resolver="old", memory=None,
                              project_policy=None, recorder=None, conversation=["kept"],
                              session_models={"response": "openai/gpt-4o-mini"})

    switched = bootstrap.switch_session_model(args, runtime, FREE)
    assert switched["models"] == {"response": FREE, "router": FREE, "semantic": FREE}
    assert runtime.app == f"app:{FREE}" and runtime.conversation == ["kept"]
    assert args.router_max_tokens >= 6000  # a free reasoning model gets the wider caps
    meta = load_meta("s1", sessions_root=session_store.SESSION_ROOT)
    assert meta["current_models"]["response"] == FREE
    assert meta["model_switches"][-1]["provider"] == "openrouter"

    # Back to the billed model: its caps come back too.
    bootstrap.switch_session_model(args, runtime, "openai/gpt-4o-mini")
    assert args.router_max_tokens == 1200 and args.max_task_tokens == 25_000
    assert built == [FREE, "openai/gpt-4o-mini"]


def test_a_model_outside_the_allowlist_changes_nothing(provider_file, monkeypatch):
    monkeypatch.setattr(bootstrap, "build_model_layer", lambda *a: pytest.fail("must not rebuild"))
    args = _switch_args()
    runtime = SimpleNamespace(session_id="s2", app="old", reply_resolver="old", memory=None,
                              project_policy=None, recorder=None, session_models={})
    with pytest.raises(ValueError):
        bootstrap.switch_session_model(args, runtime, "openai/gpt-4o")
    assert args.model == "openai/gpt-4o-mini" and runtime.app == "old"


def test_the_window_can_switch_model_between_turns(monkeypatch):
    calls = []

    def fake_switch(args, runtime, model):
        if model == "bad":
            raise ValueError("Response model 'bad' is not in NETZOO_RESPONSE_MODEL_ALLOWLIST")
        calls.append(model)
        return {"models": {"response": model}, "provider": "openrouter"}

    monkeypatch.setattr(bootstrap, "switch_session_model", fake_switch)
    runtime = _fake_cli_runtime(invoke_error=AssertionError("graph must not run"))
    with _Harness(runtime) as harness:
        assert harness.next("view").payload["prompt_kind"] == "main"
        harness.send("set_model", model=FREE)
        assert harness.next("model_changed").payload["models"]["response"] == FREE
        harness.send("set_model", model="bad")
        assert harness.next("error").payload["error_type"] == "ModelNotAllowed"
        # The prompt is still open: the conversation carries on.
        harness.answer("exit")
        assert harness.next("stopped").payload["exit_code"] == 0
    assert calls == [FREE]


def test_a_catalog_model_is_offered_after_the_recommended_and_allowed(provider_file):
    from netzoo_agent_core.llm import validate_response_model, validate_router_model

    recommended = provider_config.recommended_models()
    view = provider_config.add_model("anthropic/claude-haiku-5.5")
    assert view["recommended_models"] == recommended
    assert view["model_choices"] == recommended + ["anthropic/claude-haiku-5.5"]
    provider_config.add_model("anthropic/claude-haiku-5.5")  # twice is once
    provider_config.add_model(recommended[0])  # a recommended one is not added
    assert provider_config.load()["models"] == ["anthropic/claude-haiku-5.5"]
    provider_config.apply_to_environment()
    validate_response_model("anthropic/claude-haiku-5.5")
    validate_router_model("anthropic/claude-haiku-5.5")
    view = provider_config.remove_model("anthropic/claude-haiku-5.5")
    assert view["model_choices"] == recommended
    provider_config.apply_to_environment()
    with pytest.raises(ValueError):
        validate_router_model("anthropic/claude-haiku-5.5")


def test_adding_a_model_keeps_the_saved_key_and_has_a_cap(provider_file):
    provider_config.save({"provider": "openrouter", "api_key": "sk-or-mine-1234"})
    provider_config.add_model("google/gemini-3-flash")
    assert provider_config.load()["api_key"] == "sk-or-mine-1234"
    with pytest.raises(provider_config.ProviderError):
        provider_config.add_model("two words")
    for index in range(provider_config.MAX_MODELS - 1):
        provider_config.add_model(f"vendor/model-{index}")
    with pytest.raises(provider_config.ProviderError):
        provider_config.add_model("vendor/one-too-many")


def test_another_provider_keeps_at_least_one_model(provider_file):
    provider_config.save({"provider": "openai", "api_key": "sk-openai-1234", "models": ["gpt-4o-mini"]})
    assert provider_config.recommended_models() == []
    with pytest.raises(provider_config.ProviderError):
        provider_config.remove_model("gpt-4o-mini")


def test_the_catalog_marks_tool_support_price_and_caches(provider_file):
    from netzoo_agent_core import provider_catalog

    provider_catalog._cache.clear()
    calls = []

    def download(base_url, api_key, timeout):
        calls.append((base_url, api_key))
        return [model for model in map(provider_catalog._normalize, [
            {"id": "old/tools", "created": 1, "supported_parameters": ["tools"],
             "pricing": {"prompt": "0.00000015", "completion": "0.0000006"}, "context_length": 128000},
            {"id": "new/no-tools:free", "created": 2, "supported_parameters": ["max_tokens"],
             "pricing": {"prompt": "0", "completion": "0"}},
            {"id": "bare-id"},
            {"id": "old/tools:batch", "endpoints": ["/api/v1/batches"]},
        ]) if model]

    catalog = provider_catalog.fetch_catalog(download=download)
    assert [model["id"] for model in catalog["models"]] == ["new/no-tools:free", "old/tools", "bare-id"]
    old = catalog["models"][1]
    assert old["tools"] is True and old["prompt_per_million"] == 0.15 and old["completion_per_million"] == 0.6
    assert catalog["models"][0]["tools"] is False and catalog["models"][0]["free"]
    assert catalog["models"][2]["tools"] is None and catalog["models"][2]["prompt_per_million"] is None
    assert calls == [(provider_config.OPENROUTER_BASE_URL, "sk-or-env-0000")]
    provider_catalog.fetch_catalog(download=download)
    assert len(calls) == 1
    provider_catalog._cache.clear()


def test_the_daemon_serves_the_catalog_and_adds_models(provider_file, monkeypatch):
    from starlette.testclient import TestClient
    from netzoo_agent_core import provider_catalog
    from netzoo_agent_core.server.app import create_app

    def broken(refresh=False):
        raise provider_catalog.CatalogError("offline")

    auth = {"Authorization": "Bearer catalog-token"}
    with TestClient(create_app(token="catalog-token")) as client:
        monkeypatch.setattr(provider_catalog, "fetch_catalog", lambda refresh=False: {"models": [], "refresh": refresh})
        assert client.get("/v1/provider/catalog", params={"refresh": "true"}, headers=auth).json() == {
            "models": [], "refresh": True}
        monkeypatch.setattr(provider_catalog, "fetch_catalog", broken)
        assert client.get("/v1/provider/catalog", headers=auth).status_code == 502
        added = client.post("/v1/provider/models", json={"model": "anthropic/claude-haiku-5.5"}, headers=auth)
        assert added.status_code == 200 and added.json()["model_choices"][-1] == "anthropic/claude-haiku-5.5"
        assert "api_key" not in added.json()
        removed = client.post("/v1/provider/models", json={"model": "anthropic/claude-haiku-5.5", "remove": True},
                              headers=auth)
        assert "anthropic/claude-haiku-5.5" not in removed.json()["model_choices"]
        assert client.post("/v1/provider/models", json={"model": "a b"}, headers=auth).status_code == 422
        assert client.get("/v1/provider/catalog").status_code in {401, 403}
