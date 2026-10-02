"""A session's chosen model runs every role (2026-10-02).

The desktop's model picker used to set only the reply model. Routing and
semantic interpretation make most of the calls, so a session started on a free
model still spent the default model's credits on them.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from netzoo_agent_core.server.session_worker import apply_session_request  # noqa: E402


def _defaults():
    return SimpleNamespace(task="x", session=None, resume=None, profile="default", model="openai/gpt-4o-mini",
                           router_model="openai/gpt-4o-mini", semantic_model=None)


def test_the_chosen_model_runs_reply_routing_and_interpretation():
    args = apply_session_request(_defaults(), {"session_id": "abc", "model": "qwen/qwen3.8-27b:free"})
    assert (args.model, args.router_model, args.semantic_model) == ("qwen/qwen3.8-27b:free",) * 3
    assert args.session == "abc" and args.task is None


def test_a_request_without_a_model_keeps_the_daemon_defaults():
    args = apply_session_request(_defaults(), {"resume": "abc"})
    assert (args.model, args.router_model, args.semantic_model) == ("openai/gpt-4o-mini", "openai/gpt-4o-mini", None)
    assert args.resume == "abc"


def test_a_free_model_gets_room_to_reason_and_a_paid_one_keeps_its_caps():
    from netzoo_agent_core.cli.bootstrap import _widen_limits_for_free_models

    caps = dict(router_max_tokens=1_200, response_max_tokens=800, max_task_tokens=30_000, llm_timeout=30.0)
    paid = SimpleNamespace(model="openai/gpt-4o-mini", router_model="openai/gpt-4o-mini", semantic_model=None, **caps)
    _widen_limits_for_free_models(paid)
    assert (paid.router_max_tokens, paid.response_max_tokens, paid.max_task_tokens, paid.llm_timeout) == (1_200, 800, 30_000, 30.0)
    free = apply_session_request(SimpleNamespace(**vars(paid)), {"model": "nvidia/nemotron-3-super-120b-a12b:free"})
    _widen_limits_for_free_models(free)
    assert (free.router_max_tokens, free.response_max_tokens, free.max_task_tokens, free.llm_timeout) == (6_000, 6_000, 150_000, 180.0)
