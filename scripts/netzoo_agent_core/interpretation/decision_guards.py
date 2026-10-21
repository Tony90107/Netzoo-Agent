"""Keep unread explicit settings and failed necessary fact checks out of approval."""
from __future__ import annotations

from ..capability_sheet import sheet_entries
from ..contracts.core_decision import FactQuestion
from ..method_names import registered_workflows, workflows_in
from .count_alternatives import judged_count_words
from .method_conditions import unresolved_settings
from .request_spans import _span, scope_applies


def unresolved_setting_questions(check, decision, task: str) -> list[FactQuestion]:
    if check is None or check.unconfirmed():
        return []
    methods = [(row.method, row.delivered_by or row.defaults) for row in check.results()
               if row.status in ("available", "with_step", "needs_fact")]
    # A methods-only question can have no result row, but the request-level facts still carry explicit settings.
    if not check.results():
        known = registered_workflows()
        names = [name for name in workflows_in(check.goal_quote) if name in known]
        offered = {decision.action, *decision.matched_actions, *decision.hypothesis_actions,
                   *decision.recommended_actions}
        if len(names) == 1:
            offered.add(known[names[0]])
        keys = [key for key, entry in sheet_entries().items() if entry.kind == "produces" and entry.action in offered]
        settings = [{"name": fact.name, "quote": fact.quote, "value": fact.value}
                    for fact in check.facts if fact.property == "setting" and fact.state == "stated"
                    and scope_applies(check.goal_quote, fact.applies_to)
                    and (not task or _span(task, fact.quote) is not None)]
        methods.append(({"settings": settings}, keys))
    found = {}
    for method, keys in methods:
        if not method.get("settings"):
            continue
        keys = [key for key in keys if key in sheet_entries()]
        for setting in unresolved_settings(method, keys):
            if task and _span(task, setting["quote"]) is None:
                continue
            key = (setting["name"], setting["quote"], setting["value"])
            found.setdefault(key, setting)
    return [FactQuestion(
        question=f'For {s["workflow"]}, what value should {s["control"]} have? '
                 f'I could not resolve "{s["value"] or s["quote"]}".',
        user_quote=s["quote"], workflows=[s["workflow"]], depends_on=s["name"],
        notes={"unresolved": s["reason"]}) for s in found.values()]


def unchecked_fact_quotes(check, agent, task: str) -> list[str]:
    """Only evidence-backed, still-unsettled doubts make a failed fact call necessary."""
    if check is None or agent is None or agent.status not in ("failed", "blocked") or not agent.candidates:
        return []
    settled = [quote for quote, _ in judged_count_words(check)]
    settled += [row.unknown_quote for row in check.needed_facts() if row.file_checked]
    quotes = []
    for quote in check.uncertain_quotes:
        if task and _span(task, quote) is None:
            continue
        if any(quote.casefold() in words.casefold() or words.casefold() in quote.casefold()
               for words in settled if words):
            continue
        quotes.append(quote)
    return list(dict.fromkeys(quotes))
