"""Argument parsing for the NetZoo command-line adapter."""

from __future__ import annotations

import argparse
import os

from ..contracts import (
    DEFAULT_EPISODE_MAX_BYTES,
    DEFAULT_EPISODE_MAX_COUNT,
    DEFAULT_EPISODE_RETENTION_DAYS,
    DEFAULT_LLM_TIMEOUT_SECONDS,
    DEFAULT_RESPONSE_MAX_TOKENS,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_ROUTER_MAX_TOKENS,
    DEFAULT_ROUTER_MODEL,
    DEFAULT_SESSION_HARD_RETENTION_DAYS,
    DEFAULT_TASK_TOKEN_BUDGET,
    DEFAULT_TOOL_TIMEOUT_SECONDS,
)

__all__ = ["parse_args"]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "LangGraph Planner/Executor/Evaluator agent for PANDA, PUMA, "
            "LIONESS, and CONDOR workflows."
        )
    )
    parser.add_argument(
        "--task",
        help="Task written in natural language. If omitted, ask interactively.",
    )
    parser.add_argument(
        "--web-url",
        metavar="QUERY",
        help="Search through Websearch MCP and print only the first result URL; no LLM call.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run NetZooPy/CONDOR commands after validation.",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        help=(
            "OpenRouter response model name; it must be listed in "
            "NETZOO_RESPONSE_MODEL_ALLOWLIST."
        ),
    )
    parser.add_argument(
        "--router-model",
        default=os.environ.get("OPENROUTER_ROUTER_MODEL", DEFAULT_ROUTER_MODEL),
        help=(
            "Cheap allow-listed OpenRouter model used only for routing. "
            "Configure NETZOO_ROUTER_MODEL_ALLOWLIST to permit alternatives."
        ),
    )
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument(
        "--router-max-tokens",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_ROUTER_MAX_TOKENS",
                DEFAULT_ROUTER_MAX_TOKENS,
            )
        ),
        help="Maximum Router output tokens.",
    )
    parser.add_argument(
        "--response-max-tokens",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_RESPONSE_MAX_TOKENS",
                DEFAULT_RESPONSE_MAX_TOKENS,
            )
        ),
        help="Maximum response-model output tokens.",
    )
    parser.add_argument(
        "--max-task-tokens",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_MAX_TASK_TOKENS",
                DEFAULT_TASK_TOKEN_BUDGET,
            )
        ),
        help="Combined input/output token budget for one task, including clarifications.",
    )
    parser.add_argument(
        "--llm-timeout",
        type=float,
        default=float(
            os.environ.get(
                "NETZOO_LLM_TIMEOUT_SECONDS",
                DEFAULT_LLM_TIMEOUT_SECONDS,
            )
        ),
        help="Timeout in seconds for each Router or response-model call.",
    )
    parser.add_argument(
        "--tool-timeout",
        type=float,
        default=float(
            os.environ.get(
                "NETZOO_TOOL_TIMEOUT_SECONDS",
                DEFAULT_TOOL_TIMEOUT_SECONDS,
            )
        ),
        help=(
            "Timeout in seconds for one local NetZoo command; use 0 to disable "
            "the command timeout."
        ),
    )
    parser.add_argument(
        "--session",
        help="Session id used for a resumable checkpoint (generated when omitted).",
    )
    parser.add_argument(
        "--profile",
        default=os.environ.get("NETZOO_PROFILE", "default"),
        help="Long-term user profile id used for confirmed preferences and episodes.",
    )
    parser.add_argument(
        "--memory-status",
        action="store_true",
        help="Show the confirmed profile and compact episode count without calling an LLM.",
    )
    parser.add_argument(
        "--memory-cleanup",
        action="store_true",
        help="Migrate, secure and prune all episode memory without calling an LLM.",
    )
    parser.add_argument(
        "--forget-memory",
        action="store_true",
        help="Delete the selected profile and all of its compact episodes without calling an LLM.",
    )
    parser.add_argument(
        "--policy-status",
        action="store_true",
        help="Validate AGENTS.md and workflow YAML files, then show the effective policy without calling an LLM.",
    )
    parser.add_argument(
        "--resume",
        metavar="SESSION_ID",
        help="Resume a previous CLI session; use 'latest' for the newest pending session.",
    )
    parser.add_argument(
        "--keep-session",
        action="store_true",
        help="Keep an auto-generated checkpoint after a successful one-shot task.",
    )
    parser.add_argument(
        "--trace-status",
        metavar="RUN_ID",
        help="Verify and summarize one local trace without calling an LLM.",
    )
    parser.add_argument(
        "--trace-export",
        nargs=2,
        metavar=("RUN_ID", "ARCHIVE"),
        help="Export one verified local trace package without calling an LLM.",
    )
    parser.add_argument(
        "--trace-retention-days",
        type=int,
        default=int(os.environ.get("NETZOO_TRACE_RETENTION_DAYS", "90")),
        help="Retention period for sealed local traces.",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=int(os.environ.get("NETZOO_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)),
        help="Retention period for old auto-generated completed sessions and tool logs.",
    )
    parser.add_argument(
        "--session-hard-retention-days",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_SESSION_HARD_RETENTION_DAYS",
                DEFAULT_SESSION_HARD_RETENTION_DAYS,
            )
        ),
        help="Hard expiry for named and pending sessions.",
    )
    parser.add_argument(
        "--episode-retention-days",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_EPISODE_RETENTION_DAYS",
                DEFAULT_EPISODE_RETENTION_DAYS,
            )
        ),
        help="Retention period for successful episodes.",
    )
    parser.add_argument(
        "--episode-max-count",
        type=int,
        default=int(
            os.environ.get(
                "NETZOO_EPISODE_MAX_COUNT",
                DEFAULT_EPISODE_MAX_COUNT,
            )
        ),
        help="Maximum retained episodes per profile.",
    )
    parser.add_argument(
        "--episode-max-mb",
        type=float,
        default=float(
            os.environ.get(
                "NETZOO_EPISODE_MAX_MB",
                DEFAULT_EPISODE_MAX_BYTES / (1024 * 1024),
            )
        ),
        help="Approximate episode storage ceiling per profile in MiB.",
    )
    parser.add_argument(
        "--transient-trace",
        action="store_true",
        help=(
            "Show compact progress summaries on a temporary status line and clear "
            "them before the final answer. This is not raw model chain-of-thought."
        ),
    )
    display_group = parser.add_mutually_exclusive_group()
    display_group.add_argument(
        "--verbose",
        action="store_true",
        help="Show the full evidence ledger, graph events, evaluator details, and log paths.",
    )
    display_group.add_argument(
        "--quiet",
        action="store_true",
        help="Hide progress events and print only the compact final answer.",
    )
    return parser.parse_args()
