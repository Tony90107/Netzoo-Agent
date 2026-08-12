# Rename to netzoo_agent and Single-Field Clarification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the active project identity to `netzoo_agent` and limit the missing-input wizard to one field per answer without changing supported NetZoo behavior.

**Architecture:** Clarification stays the boundary that converts a terminal answer into a workflow continuation, but accepts only the current field. Docker Compose receives an explicit new project name; packages, services, commands, workflow actions, and `.netzoo` storage remain unchanged.

**Tech Stack:** Python, pytest, Bash, Docker Compose, Markdown/YAML.

## Global Constraints

- Final root directory: `/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`.
- Replace active `network-zoo-panda-puma` and `netzoo-panda-puma` identity references with `netzoo_agent`.
- Preserve `netzoo_agent_core`, `netzoo-chat`, `NETZOO_*`, workflow actions, Compose service names, and `.netzoo` semantics.
- Do not delete Docker resources or touch unrelated user worktree changes.
- Remove advanced/batch `field=value` clarification. Only the current missing field may be answered.

---

## Task 1: Simplify the clarification wizard

**Files:** `scripts/netzoo_agent_core/cli/clarification.py`, `scripts/netzoo_agent_core/planning/assembly.py`, `tests/test_agent_gate.py`, `tests/test_cli_package.py`.

- [ ] Replace the test that accepts multiple `field=value` assignments with a test that a batch-looking reply resolves only `target_field`; assert prompts contain neither `Advanced:` nor `field=value`.
- [ ] Run `pytest tests/test_agent_gate.py -k clarification -q` and verify it fails on the old behavior.
- [ ] Delete aliases and regex batch parsing. Require a valid `target_field`; numeric input selects its candidate, all other non-empty input is stored only for that field. Preserve previous selections and LIONESS mode handling.
- [ ] Remove the `batch` parameter and all-missing rendering from `clarification_prompt`; show only the current field and candidate list. Replace `field_name=<full path>` with `Enter the full path.`
- [ ] Change Planner wording to: `Please provide the next missing input. The CLI wizard will ask for each unresolved field one at a time.`
- [ ] Update interaction facade exports/signature tests and run `pytest tests/test_agent_gate.py -k clarification -q` plus `pytest tests/test_cli_package.py tests/test_cli_lifecycle.py -q`.
- [ ] Commit only these files with `git commit -m "feat: simplify clarification input"`.

## Task 2: Rename active project identity

**Files:** `AGENTS.md`, `docker-compose.yml`, active README/usage/guides, `NETZOO_HARNESS_ARCHITECTURE.md`, `tests/test_netzoo_chat_launcher.py`.

- [ ] Add tests asserting `project: netzoo_agent`, `name: netzoo_agent`, `image: netzoo_agent:latest`, and absence of old Compose identifiers. Run `pytest tests/test_netzoo_chat_launcher.py -q` to prove initial failure.
- [ ] Add `name: netzoo_agent` to Compose and rename both built images to `netzoo_agent:latest`. Set policy front matter to `project: netzoo_agent`.
- [ ] Replace active documentation paths with `/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent`, update prose identity, and remove batch clarification documentation. Preserve archive/spec/plan history.
- [ ] Run launcher tests, `docker compose config --quiet`, and an active-file search for old identifiers or batch wording.
- [ ] Commit only changed identity files with `git commit -m "chore: rename project identity"`.

## Task 3: Move root and verify

- [ ] Confirm old root exists and `/Users/chenzhonghan/Documents/LLM AGENT/netzoo_agent` is absent.
- [ ] Move the root using `mv` without deleting any Docker or `.netzoo` data.
- [ ] From the new root run `pytest -q` and `docker compose config --quiet`.
- [ ] Smoke test `printf 'exit\n' | ./netzoo-chat`; verify normal TEST-mode startup and Compose resources under the `netzoo_agent-` prefix. Do not remove old resources.

## Review

Task 1 covers sequential-only clarification; Task 2 covers active identity and docs; Task 3 covers the physical move and runtime verification. No planned change expands tool permissions or deletes user data.
