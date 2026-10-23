"""Harness repair P1 (spec 2026-10-23, sections 5.2 and 7.1): a turn's open facts as obligations, asked or queued.

Before P1, a checked fact agent that kept any question lifted every legacy `needs_fact` wait: the row became available
with every outcome credited (the favourable answer assumed) or, delivering nothing, not available (a refusal). P0
fixtures F03 and F04 (research log harness-repair-2026-10-23). Now no wait is lifted. Each fact is an obligation that
is asked, covered by an asked question on the same fact, or queued past the two-question cap -- none is dropped.

Same fact, across sources only: overlapping user words in the request and a shared workflow (a counted candidate covers
on its words alone, as phase 5b already dropped an agent question on them). Of the 50 legacy waits beside an agent
question in the 1,340 recorded readings, 49 bind this way; h2 J19's scale wait ("I can't tell which my PI meant.") sits
in the next sentence and is asked beside the agent's question. Two agent questions never cover each other: the agent
proposes distinct facts on overlapping words (h5 Q17: "mean-centered per gene?" and "log-transformed before
centering?" on one sentence -- the second decides), and kept_facts already drops one on the same words (R6).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..contracts.core_decision import FactQuestion
from ..contracts.evidence import Obligation
from .count_alternatives import judged_count_words, splits_candidates
from .request_spans import _span, same_words
from .ruled_out import NETWORK_GIVEN

__all__ = ["MAX_ASKED", "AskPlan", "ask_plan", "fact_key", "key_of"]

MAX_ASKED = 2


def fact_key(source: str, what: str, task: str, quote: str) -> str:
    """`<source>:<what>@<start>-<end>` of the user's words in the request (their folded text when not placed)."""
    span = _span(task, quote) if task and quote.strip() else None
    where = f"{span[0]}-{span[1]}" if span else " ".join(quote.casefold().split())[:60]
    return f"{source}:{what or 'fact'}@{where}"


def key_of(fact: FactQuestion, task: str, source: str) -> str:
    """The fact's own key, or (a fact recorded before P1) the one `fact_key` gives it."""
    what = fact.depends_on if source != "agent" else "+".join(fact.workflows)
    return fact.fact_key or fact_key(source, what, task, fact.user_quote)


def _same_fact(task: str, cover: FactQuestion, fact: FactQuestion) -> bool:
    if not same_words(task, cover.user_quote, fact.user_quote):
        return False
    return cover.by_code or not cover.workflows or not fact.workflows or bool(set(cover.workflows) & set(fact.workflows))


@dataclass
class AskPlan:
    asked: list[FactQuestion] = field(default_factory=list)
    owned: list[FactQuestion] = field(default_factory=list)
    """The agent's questions on a count code judged that cannot tell its candidates apart (phase 5b, ROUND-09 R8)."""
    ledger: list[Obligation] = field(default_factory=list)

    def agent_asks(self) -> bool:
        """Whether a count or an agent question is asked (the turn is the agent's ASK, not the legacy one)."""
        return any(o.source != "dimension" and o.status == "asked" for o in self.ledger)


def ask_plan(counted: list[FactQuestion], legacy: list[FactQuestion], agent, check, task: str = "",
             limit: int = MAX_ASKED) -> AskPlan:
    """Every open fact of a checked fact agent's turn, in the order asked: candidate counts judged in code
    (`counted`), a named CONDOR's unstated network, the agent's kept questions, then the other legacy waits
    (`legacy`, the check's `needed_facts` dimensions). `limit` 0 queues them all (the goal is clarified first)."""
    kept = [*agent.accepted, *agent.queued]
    # ROUND-09 (R8): a question on candidates code weighed must be able to tell them apart, or it is not asked.
    # ROUND-21 (user decision): a fact the run's file check could settle is asked too (recorded R5 flags ignored).
    owned =[fact for fact in kept if any(same_words(task, fact.user_quote, words)
                                          and not splits_candidates(fact.question, values)
                                          for words, values in judged_count_words(check))]
    candidates = [*(("count", fact) for fact in counted),
                  *(("dimension", fact) for fact in legacy if fact.depends_on == NETWORK_GIVEN),
                  *(("agent", fact) for fact in kept if fact not in owned),
                  *(("dimension", fact) for fact in legacy if fact.depends_on != NETWORK_GIVEN)]
    plan, taken = AskPlan(owned=owned), []

    def record(source, fact, key, status, asked_as=""):
        plan.ledger.append(Obligation(fact_key=key, source=source, question=fact.question, user_quote=fact.user_quote,
                                      workflows=fact.workflows, status=status, asked_as=asked_as))

    for source, fact in candidates:
        key = key_of(fact, task, source)
        cover = next(((k, f, s) for k, f, s, by in taken if by != source and _same_fact(task, f, fact)), None)
        if cover is not None:
            record(source, fact, key, cover[2], cover[0])
            continue
        status = "asked" if len(plan.asked) < limit else "queued"
        if status == "asked":
            plan.asked.append(fact)
        taken.append((key, fact, status, source))
        record(source, fact, key, status)
    for fact in owned:
        cover = next(((k, f, s) for k, f, s, _ in taken if f.by_code and same_words(task, f.user_quote, fact.user_quote)),
                     None)
        record("agent", fact, key_of(fact, task, "agent"), cover[2] if cover else "settled_in_code",
               cover[0] if cover else "")
    return plan
