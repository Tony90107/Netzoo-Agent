# Contextual Follow-up Resolution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve interactive follow-up replies from trusted prior-turn context, prevent underspecified acknowledgements from entering the scientific Router, and render CLI-owned status and navigation exactly once.

**Architecture:** Add a focused structured-output reply resolver at the CLI boundary. It receives a bounded context envelope built from `WorkflowPlan`, `TaskDecision`, and `NextTurnPrompt`; it classifies conversational intent but cannot authorize an action. The existing scientific Router receives only a deterministic self-contained task after resolution, while response and next-turn rendering retain separate ownership.

**Tech Stack:** Python 3.12, Pydantic v2, LangChain message/model interfaces, LangGraph, pytest, Ruff.

## Global Constraints

- Do not enumerate affirmative phrases such as `yes`, `ok`, or `好的` to resolve ordinary follow-up intent.
- Explicit CLI controls and literal file paths remain deterministic and preserve their original text.
- The reply resolver cannot add a workflow action that is absent from the trusted context envelope.
- A contextual acceptance cannot bypass missing-input validation, execution mode, the Plan Evaluator, or the workflow registry.
- Prior assistant prose is excluded from action authorization and scientific Router context.
- Invalid, unavailable, or low-confidence reply resolution returns `needs_detail`.
- All user-visible agent output remains English, as required by `AGENTS.md`.
- Existing user changes in the dirty worktree must not be staged or rewritten.

## File Structure

- Create `scripts/netzoo_agent_core/contracts/interaction.py`: typed context and reply-resolution contracts.
- Create `scripts/netzoo_agent_core/cli/reply_resolution.py`: prompt construction, structured model invocation, safe fallback, deterministic task construction, and LLM usage tracing.
- Modify `scripts/netzoo_agent_core/contracts/__init__.py`: export the new public contracts.
- Modify `scripts/netzoo_agent_core/cli/bootstrap.py`: build and inject the structured reply resolver into `CliRuntime`.
- Modify `scripts/netzoo_agent_core/cli/conversation.py`: place contextual resolution before scientific graph invocation and retain the prior trusted context.
- Modify `scripts/netzoo_agent_core/cli/follow_up.py`: build the trusted context envelope, remove affirmative phrase routing, and use imperative next-turn wording.
- Modify `scripts/netzoo_agent_core/graph/prompts.py`: assign scientific prose only to the response LLM.
- Modify `scripts/netzoo_agent_core/graph/response.py`: normalize the model tail and append one canonical operational footer.
- Modify `scripts/netzoo_agent_core/presentation.py`: remove CLI-owned status/navigation paragraphs from model prose.
- Create `tests/test_reply_resolution.py`: public reply-resolver behavior and telemetry tests.
- Modify `tests/test_cli_lifecycle.py`: interactive conversation-loop regressions.
- Modify `tests/test_progress_summaries.py`: next-turn context and continuation contract tests.
- Modify `tests/test_graph_package.py`: response ownership regression.

---

### Task 1: Typed contextual reply resolver

**Files:**
- Create: `scripts/netzoo_agent_core/contracts/interaction.py`
- Create: `scripts/netzoo_agent_core/cli/reply_resolution.py`
- Modify: `scripts/netzoo_agent_core/contracts/__init__.py`
- Test: `tests/test_reply_resolution.py`

**Interfaces:**
- Consumes: `NextTurnPrompt`, `LLMUsage`, `RecommendedAction`, LangChain-compatible structured model `.invoke(messages)`.
- Produces: `FollowUpContext`, `ReplyIntentDecision`, `ContextualReplyResolution`, and `ContextualReplyResolver.resolve(context, reply, current_usage, run_id)`.

- [ ] **Step 1: Write the failing context-envelope and semantic-resolution tests**

```python
from unittest.mock import Mock

from netzoo_agent_core.cli.reply_resolution import ContextualReplyResolver
from netzoo_agent_core.contracts import FollowUpContext, ReplyIntentDecision


def _context(*, continuation_action=None):
    return FollowUpContext(
        prior_user_goal="Which tools produce sample-specific miRNA networks?",
        prompt_kind="completed",
        prompt_question="Enter a follow-up question or describe another NetZoo goal.",
        candidate_actions=["run_puma", "run_lioness_puma"],
        continuation_action=continuation_action,
        expected_field=None,
        alternative_action=None,
    )


def test_acknowledgement_without_offered_continuation_needs_detail():
    model = Mock()
    model.invoke.return_value = ReplyIntentDecision(
        kind="needs_detail", confidence=0.98, reason="No concrete request was supplied."
    )
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(_context(), "certainly", None, "run-1")

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.resolved_task is None
    rendered_input = str(model.invoke.call_args.args[0])
    assert "Which tools produce sample-specific miRNA networks?" in rendered_input
    assert "Enter a follow-up question" in rendered_input
    assert "certainly" in rendered_input


def test_model_acceptance_is_downgraded_without_concrete_continuation():
    model = Mock()
    model.invoke.return_value = ReplyIntentDecision(
        kind="accept_workflow", confidence=0.99, reason="The reply accepts."
    )
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(_context(), "sounds good", None, "run-1")

    assert result.resolution.kind == "needs_detail"
    assert result.resolution.resolved_task is None


def test_substantive_follow_up_becomes_bounded_self_contained_task():
    model = Mock()
    model.invoke.return_value = ReplyIntentDecision(
        kind="follow_up", confidence=0.95, reason="It refers to the prior workflow."
    )
    resolver = ContextualReplyResolver.for_test(model)

    result = resolver.resolve(
        _context(), "What format should the motif prior use?", None, "run-1"
    )

    assert result.resolution.kind == "follow_up"
    assert result.resolution.resolved_task == (
        "Previous NetZoo goal: Which tools produce sample-specific miRNA networks?\n"
        "Current follow-up: What format should the motif prior use?"
    )
```

- [ ] **Step 2: Run the tests to verify the resolver seam is red**

Run: `python -m pytest tests/test_reply_resolution.py -q`

Expected: collection fails because `interaction.py` and `reply_resolution.py` do not exist.

- [ ] **Step 3: Add the typed interaction contracts**

```python
# scripts/netzoo_agent_core/contracts/interaction.py
from typing import Literal

from pydantic import BaseModel, Field
from workflow_registry import RecommendedAction


ReplyIntent = Literal[
    "follow_up", "new_goal", "accept_workflow", "needs_detail", "navigation"
]


class FollowUpContext(BaseModel):
    prior_user_goal: str = Field(min_length=1, max_length=4_000)
    prompt_kind: str = Field(min_length=1, max_length=40)
    prompt_question: str = Field(min_length=1, max_length=600)
    candidate_actions: list[RecommendedAction] = Field(default_factory=list)
    continuation_action: RecommendedAction | None = None
    expected_field: str | None = None
    alternative_action: RecommendedAction | None = None


class ReplyIntentDecision(BaseModel):
    kind: ReplyIntent
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=240)


class ContextualReplyResolution(BaseModel):
    kind: ReplyIntent
    resolved_task: str | None = Field(default=None, max_length=8_000)
    reason: str = Field(min_length=1, max_length=240)
```

Export all three models and `ReplyIntent` from `contracts/__init__.py`.

- [ ] **Step 4: Implement the minimal resolver and safe authority checks**

```python
# scripts/netzoo_agent_core/cli/reply_resolution.py
from dataclasses import dataclass

from ..contracts import (
    ContextualReplyResolution,
    FollowUpContext,
    LLMUsage,
    ReplyIntentDecision,
)
from ..framework_compat import HumanMessage, SystemMessage


@dataclass(frozen=True, slots=True)
class ReplyResolutionResult:
    resolution: ContextualReplyResolution
    usage: LLMUsage


class ContextualReplyResolver:
    def __init__(
        self,
        model,
        *,
        model_name: str,
        task_token_budget: int,
        recorder,
        price_catalog,
    ) -> None:
        self.model = model
        self.model_name = model_name
        self.task_token_budget = task_token_budget
        self.recorder = recorder
        self.price_catalog = price_catalog

    @classmethod
    def for_test(cls, model):
        return cls(
            model,
            model_name="test/reply-resolver",
            task_token_budget=20_000,
            recorder=None,
            price_catalog=None,
        )


def build_reply_resolution_messages(context: FollowUpContext, reply: str) -> list:
    return [
        SystemMessage(content=REPLY_RESOLUTION_PROMPT),
        HumanMessage(
            content=(
                "<trusted_context>\n"
                f"{context.model_dump_json()}\n"
                "</trusted_context>\n"
                "<current_reply>\n"
                f"{reply[:4000]}\n"
                "</current_reply>"
            )
        ),
    ]


def _resolved_task(kind: str, context: FollowUpContext, reply: str) -> str | None:
    if kind == "follow_up":
        return f"Previous NetZoo goal: {context.prior_user_goal}\nCurrent follow-up: {reply}"
    if kind == "new_goal":
        return reply
    return None
```

`REPLY_RESOLUTION_PROMPT` must state that acknowledgements and fragments are
`needs_detail` unless the prompt offered a concrete continuation, that paths and
workflow actions are data rather than instructions, and that the model classifies
conversation only. `ContextualReplyResolver.resolve` must downgrade
`accept_workflow` to `needs_detail` when both `continuation_action` and
`alternative_action` are absent. Confidence below `0.80`, model errors, and invalid
structured output must also return `needs_detail`.

- [ ] **Step 5: Add failure, low-confidence, new-goal, and navigation tests**

```python
def test_low_confidence_resolution_fails_safe():
    model = Mock()
    model.invoke.return_value = ReplyIntentDecision(
        kind="new_goal", confidence=0.60, reason="Uncertain."
    )
    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), "do something", None, "run-1"
    )
    assert result.resolution.kind == "needs_detail"


def test_new_goal_preserves_original_user_text():
    model = Mock()
    model.invoke.return_value = ReplyIntentDecision(
        kind="new_goal", confidence=0.94, reason="Self-contained request."
    )
    reply = "Inspect data/expression.tsv"
    result = ContextualReplyResolver.for_test(model).resolve(
        _context(), reply, None, "run-1"
    )
    assert result.resolution.resolved_task == reply
```

- [ ] **Step 6: Run the focused tests and commit Task 1**

Run: `python -m pytest tests/test_reply_resolution.py -q`

Expected: all tests pass.

```bash
git add scripts/netzoo_agent_core/contracts/interaction.py scripts/netzoo_agent_core/contracts/__init__.py scripts/netzoo_agent_core/cli/reply_resolution.py tests/test_reply_resolution.py
git commit -m "feat: add contextual reply resolver"
```

### Task 2: Trusted next-turn context and phrase-independent continuation

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/follow_up.py`
- Modify: `tests/test_progress_summaries.py`
- Modify: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: `build_next_turn_prompt(state) -> NextTurnPrompt`, `WorkflowPlan`, `TaskDecision`.
- Produces: `build_follow_up_context(state, prompt, prior_user_goal) -> FollowUpContext` and `resolve_next_turn_input(prompt, resolution, original_reply) -> str | None`.

- [ ] **Step 1: Replace phrase-driven tests with resolution-driven tests**

```python
def test_workflow_acceptance_uses_structured_resolution():
    prompt = build_next_turn_prompt(_sample_specific_puma_guidance_state())
    resolution = ContextualReplyResolution(
        kind="accept_workflow",
        reason="Accepted the concrete workflow offer.",
    )

    continuation = resolve_next_turn_input(prompt, resolution, "sounds good")

    assert continuation.startswith("PREVIOUS_ACTION=run_lioness_puma")


def test_follow_up_context_uses_code_owned_candidates():
    state = _sample_specific_puma_guidance_state()
    prompt = build_next_turn_prompt(state)

    context = build_follow_up_context(
        state,
        prompt,
        "Which tools produce sample-specific miRNA networks?",
    )

    assert context.candidate_actions == ["run_puma", "run_lioness_puma"]
    assert context.prior_user_goal.startswith("Which tools")
```

Delete assertions that require passing literal `"yes"` into
`resolve_next_turn_input`. Keep explicit preference-confirmation tests unchanged;
they protect a separate code-enforced confirmation gate.

- [ ] **Step 2: Run the focused tests and verify red behavior**

Run: `python -m pytest tests/test_progress_summaries.py tests/test_agent_gate.py -q`

Expected: failures show that `build_follow_up_context` is missing and
`resolve_next_turn_input` still expects raw phrase matching.

- [ ] **Step 3: Build the trusted context from graph state**

```python
def build_follow_up_context(
    state: dict,
    prompt: NextTurnPrompt,
    prior_user_goal: str,
) -> FollowUpContext:
    plan = WorkflowPlan.model_validate(state["plan"])
    decision = TaskDecision.model_validate(plan.decision)
    candidates = list(
        dict.fromkeys(
            decision.recommended_actions
            or decision.matched_actions
            or decision.hypothesis_actions
        )
    )
    return FollowUpContext(
        prior_user_goal=prior_user_goal[-4000:],
        prompt_kind=prompt.kind,
        prompt_question=prompt.question,
        candidate_actions=candidates,
        continuation_action=prompt.continuation_action,
        expected_field=prompt.expected_field,
        alternative_action=prompt.alternative_action,
    )
```

- [ ] **Step 4: Make continuation consume structured intent**

`resolve_next_turn_input` must branch on `ContextualReplyResolution.kind`, never on
an affirmative word set. For `follow_up` and `new_goal`, return
`resolution.resolved_task`. For `accept_workflow`, construct only the continuation
whose action is present on `NextTurnPrompt`. For `needs_detail` and `navigation`,
return `None`. Its third argument is the untouched original reply; preserve it as an
input value only when it is structurally path-like and both `expected_field` and a
validated continuation action are present.

- [ ] **Step 5: Use imperative next-turn wording**

Replace the generic completed question with:

```python
"Enter a follow-up question or describe another NetZoo goal."
```

For a concrete recommended workflow, use:

```python
f"Enter a follow-up question, provide the {field_label} path to start the "
f"recommended {workflow} workflow, or describe another NetZoo goal."
```

Do not instruct users to type a particular affirmative phrase.

- [ ] **Step 6: Run focused tests and commit Task 2**

Run: `python -m pytest tests/test_progress_summaries.py tests/test_agent_gate.py -q`

Expected: all next-turn and continuation tests pass.

```bash
git add scripts/netzoo_agent_core/cli/follow_up.py tests/test_progress_summaries.py tests/test_agent_gate.py
git commit -m "refactor: make follow-up continuation context driven"
```

### Task 3: Integrate contextual resolution into the interactive lifecycle

**Files:**
- Modify: `scripts/netzoo_agent_core/cli/bootstrap.py`
- Modify: `scripts/netzoo_agent_core/cli/conversation.py`
- Modify: `tests/test_cli_lifecycle.py`
- Test: `tests/test_reply_resolution.py`

**Interfaces:**
- Consumes: `ContextualReplyResolver.resolve`, `build_follow_up_context`, and `resolve_next_turn_input` from Tasks 1 and 2.
- Produces: `CliRuntime.reply_resolver` and an interactive loop that invokes the scientific graph only for resolved tasks.

- [ ] **Step 1: Add failing lifecycle tests at the injected CLI seam**

```python
def test_underspecified_follow_up_does_not_reinvoke_scientific_graph(capsys):
    runtime = _runtime_with_first_guidance_result(
        interactive_answers=["Which tools produce sample-specific miRNA networks?", "certainly", "exit"],
        reply_kind="needs_detail",
    )

    assert conversation.run_conversation(
        SimpleNamespace(task=None, keep_session=False), runtime
    ) == 0

    assert runtime.invoke_graph_turn_func.call_count == 1
    assert "Please enter a concrete follow-up question" in capsys.readouterr().out


def test_substantive_follow_up_reaches_graph_with_prior_goal_context():
    runtime = _runtime_with_two_results(
        interactive_answers=[
            "Which tools produce sample-specific miRNA networks?",
            "What format should the motif prior use?",
            "exit",
        ],
        reply_kind="follow_up",
    )

    conversation.run_conversation(SimpleNamespace(task=None, keep_session=False), runtime)

    second_invocation = runtime.invoke_graph_turn_func.call_args_list[1].args[1]
    submitted = second_invocation["messages"][-1].content
    assert "Previous NetZoo goal:" in submitted
    assert "Current follow-up: What format" in submitted
```

The fake runtime must inject a fake `reply_resolver`; tests must not call a network
model.

- [ ] **Step 2: Run the lifecycle tests and verify they fail**

Run: `python -m pytest tests/test_cli_lifecycle.py -q`

Expected: failures show `CliRuntime` has no `reply_resolver` and the second reply still
enters the graph unchanged.

- [ ] **Step 3: Build and inject the production structured resolver**

In `bootstrap_runtime`, construct a temperature-zero model using the configured Router
model and bind it to `ReplyIntentDecision`:

```python
reply_llm = build_llm(
    args.router_model,
    0.0,
    max_output_tokens=min(args.router_max_tokens, 256),
    timeout_seconds=args.llm_timeout,
)
reply_model = reply_llm.with_structured_output(
    ReplyIntentDecision,
    method="function_calling",
    include_raw=True,
)
reply_resolver = ContextualReplyResolver(
    model=reply_model,
    model_name=args.router_model,
    task_token_budget=args.max_task_tokens,
    recorder=recorder,
    price_catalog=PriceCatalog.from_environment(),
)
```

Add `reply_resolver: ContextualReplyResolver` to `CliRuntime`. Update every test runtime
factory to inject a deterministic fake resolver.

- [ ] **Step 4: Resolve non-initial replies before graph invocation**

Track `follow_up_context: FollowUpContext | None` beside `next_prompt`. After each
completed graph turn:

```python
next_prompt = build_next_turn_prompt(result)
follow_up_context = build_follow_up_context(result, next_prompt, task)
```

For each later reply, process slash commands, empty/back commands, and explicit exit
before model resolution. Then start a trace run, invoke `reply_resolver.resolve`, and:

- print `Please enter a concrete follow-up question, provide the requested input path, or describe another NetZoo goal.` and keep the same context for `needs_detail`;
- return to the initial prompt for `navigation`;
- pass only `resolve_next_turn_input(prompt, resolution, answer)` to the graph for
  `follow_up`, `new_goal`, or valid `accept_workflow`.

When resolution produces no graph task, finish its trace run and clear its per-turn
usage. When it produces a task, pass the returned usage into the graph invocation so
the existing token budget includes the reply-resolution call.

- [ ] **Step 5: Record resolver usage and safe failures**

Use `append_llm_usage` with role `follow_up`, record one `llm.completed` event, and
return `needs_detail` on provider, parsing, or budget failure. Add tests asserting:

```python
assert result.usage.calls[-1].role == "follow_up"
assert result.usage.calls[-1].status == "success"
```

and for a raising fake model:

```python
assert result.resolution.kind == "needs_detail"
assert result.usage.calls[-1].status == "failed"
```

- [ ] **Step 6: Run lifecycle and resolver tests and commit Task 3**

Run: `python -m pytest tests/test_reply_resolution.py tests/test_cli_lifecycle.py -q`

Expected: all tests pass and fake `needs_detail` replies do not call the graph.

```bash
git add scripts/netzoo_agent_core/cli/bootstrap.py scripts/netzoo_agent_core/cli/conversation.py scripts/netzoo_agent_core/cli/reply_resolution.py tests/test_reply_resolution.py tests/test_cli_lifecycle.py
git commit -m "feat: resolve interactive replies from trusted context"
```

### Task 4: Single ownership of response status and navigation

**Files:**
- Modify: `scripts/netzoo_agent_core/graph/prompts.py`
- Modify: `scripts/netzoo_agent_core/graph/response.py`
- Modify: `scripts/netzoo_agent_core/presentation.py`
- Modify: `tests/test_graph_package.py`
- Modify: `tests/test_progress_summaries.py`

**Interfaces:**
- Consumes: response-model prose and the structured `TaskDecision`.
- Produces: `strip_cli_owned_guidance_tail(text) -> str`, one canonical footer, and one CLI-owned next-turn prompt.

- [ ] **Step 1: Write the failing duplicate-status regression**

```python
def test_guidance_response_removes_model_owned_status_and_cta_before_footer():
    response_model = GuidanceResponseLLM(
        "Use PUMA followed by LIONESS-PUMA.\n\n"
        "No tools were executed, and no files were inspected. "
        "If you need to start, provide the required files."
    )

    result = response_node(_guidance_state(), response_model=response_model)
    answer = result["messages"][0].content

    assert answer == (
        "Use PUMA followed by LIONESS-PUMA.\n\n"
        "No files were inspected and no analysis ran."
    )
```

- [ ] **Step 2: Run the response test and verify the duplicate tail remains**

Run: `python -m pytest tests/test_graph_package.py -q`

Expected: the model-owned operational paragraph remains before the canonical footer.

- [ ] **Step 3: Make ownership explicit in the response prompt**

Replace the instruction that asks the response LLM to state no files were inspected
with:

```text
For no_tool guidance, write only the scientific explanation. Do not mention whether
tools ran, whether files were inspected, or what the user should type next. The CLI
appends operational status and owns the next-turn prompt.
```

Keep the rules that prevent invented capabilities and preserve ordered compositions.

- [ ] **Step 4: Normalize CLI-owned trailing paragraphs**

Add `strip_cli_owned_guidance_tail` in `presentation.py`. Split the response into
paragraphs and remove only trailing paragraphs that contain a no-execution/no-file-
inspection operational statement or a CLI-style invitation. Do not remove scientific
requirements or workflow descriptions. Preserve `strip_cli_owned_follow_up_question`
as a compatibility alias that delegates to the new function.

Call the new function in `graph/response.py`, then append the canonical footer once for
`decision.action == "no_tool"` with no structured results.

- [ ] **Step 5: Verify prompt wording and footer ownership**

Add assertions that:

```python
assert answer.count("No files were inspected and no analysis ran.") == 1
assert "If you need to start" not in answer
assert "Would you like" not in answer
```

Also assert that `render_next_turn_prompt(build_next_turn_prompt(state))` contains one
imperative next step and no instruction to reply with a specific affirmative word.

- [ ] **Step 6: Run focused response tests and commit Task 4**

Run: `python -m pytest tests/test_graph_package.py tests/test_progress_summaries.py tests/test_concept_answers.py -q`

Expected: all tests pass.

```bash
git add scripts/netzoo_agent_core/graph/prompts.py scripts/netzoo_agent_core/graph/response.py scripts/netzoo_agent_core/presentation.py tests/test_graph_package.py tests/test_progress_summaries.py
git commit -m "fix: separate guidance prose from CLI interaction"
```

### Task 5: End-to-end regression and release evidence

**Files:**
- Modify: `tests/test_cli_lifecycle.py`
- Modify: `tests/test_agent_gate.py`

**Interfaces:**
- Consumes: the complete interactive CLI, contextual resolver, scientific graph, and response renderer.
- Produces: regression evidence for the original sample-specific miRNA conversation.

- [ ] **Step 1: Add the original transcript as a behavioral regression**

Use injected fake reply and graph models so the test remains deterministic. The test
must model this sequence:

```text
Which tools produce sample-specific miRNA networks?
certainly
What format should the motif prior use?
exit
```

Assert that the first answer recommends `PUMA` then `LIONESS-PUMA`, the acknowledgement
does not invoke the scientific graph, the substantive question does invoke it with a
self-contained prior-goal context, and each guidance answer has one operational footer.

- [ ] **Step 2: Run the full focused interaction suite**

Run: `python -m pytest tests/test_reply_resolution.py tests/test_cli_lifecycle.py tests/test_progress_summaries.py tests/test_graph_package.py tests/test_agent_gate.py -q`

Expected: all tests pass.

- [ ] **Step 3: Run static validation**

Run:

```bash
ruff check scripts/netzoo_agent_core/contracts/interaction.py scripts/netzoo_agent_core/contracts/__init__.py scripts/netzoo_agent_core/cli/reply_resolution.py scripts/netzoo_agent_core/cli/bootstrap.py scripts/netzoo_agent_core/cli/conversation.py scripts/netzoo_agent_core/cli/follow_up.py scripts/netzoo_agent_core/graph/prompts.py scripts/netzoo_agent_core/graph/response.py scripts/netzoo_agent_core/presentation.py tests/test_reply_resolution.py tests/test_cli_lifecycle.py tests/test_progress_summaries.py tests/test_graph_package.py tests/test_agent_gate.py
python -m compileall -q scripts tests
git diff --check
```

Expected: Ruff reports `All checks passed!`; compileall and diff check exit zero.

- [ ] **Step 4: Run the complete test suite**

Run: `python -m pytest -q`

Expected: all tests pass; the existing `pytz` deprecation warning may remain.

- [ ] **Step 5: Manually verify the Docker CLI interaction**

Run: `./netzoo-chat` and enter:

```text
if i want to get sample specific mi-RNA network data,what tools do i need?
certainly
what format should the motif prior use?
exit
```

Verify:

- the first answer recommends the PUMA to LIONESS-PUMA composition;
- the first answer contains one canonical no-analysis footer;
- the CLI renders one imperative next-turn prompt;
- `certainly` asks for a concrete follow-up without scientific reclassification;
- the substantive motif question is answered in the sample-specific miRNA context;
- no tool executes in Planning mode.

- [ ] **Step 6: Commit the regression evidence**

```bash
git add tests/test_cli_lifecycle.py tests/test_agent_gate.py
git commit -m "test: cover contextual follow-up conversation"
```
