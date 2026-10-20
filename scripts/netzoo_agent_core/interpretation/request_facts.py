"""ROUND-03 (collab/ROUND-03-PLAN.md): one record of the request's counts and settings, built once per check.

Every place the capability reading writes a count or a setting -- the request's own fields, each asked result's, a
count given as candidates, and an unknown count with its candidates -- is a read. Each read is verified exactly as
before (`method_conditions.verified_method`, `count_alternatives.verified_count_alternatives`) and kept as a fact:
the same words with the same value are one fact read again, never a second copy. A result's method and the count
candidates are then compiled from the record, so the data-size rules, the count questions and the run's controls all
take their values from it, and each result names the facts it was judged on (`CheckedRequirement.fact_ids`).

Nothing here decides anything new: the rules that choose between a result's own value and the request's are
`with_request_method`'s; where they set one aside, the record says so (`FactConflict`).
"""

from __future__ import annotations

from types import SimpleNamespace

from ..contracts.request_facts import FactConflict, FactEvidence, RequestFact
from ..workflow_conditions import UNREGISTERED, stated_numbers
from .count_alternatives import verified_count_alternatives
from .method_conditions import verified_method
from .request_spans import _span

__all__ = ["FactRecord", "fact_for_setting", "merge_facts", "run_fact_bindings"]

_PROPERTY = {"samples": "sample_count", "features": "feature_count"}
_OF = {value: key for key, value in _PROPERTY.items()}


def _number(value: str) -> int | float:
    number = float(value)
    return int(number) if number == int(number) else number


def _same(known: RequestFact, fact: RequestFact) -> bool:
    return (known.property, known.name, known.value, known.values, known.state) == (
        fact.property, fact.name, fact.value, fact.values, fact.state)


def _read_again(known: RequestFact, fact: RequestFact, evidence: FactEvidence) -> RequestFact:
    """A fact read once more: one more read, and the results either read applies it to (every result wins)."""
    scope = None if known.applies_to is None or fact.applies_to is None else list(
        dict.fromkeys([*known.applies_to, *fact.applies_to]))
    return known.model_copy(update={"evidence": [*known.evidence, evidence], "applies_to": scope,
                                    "scope_unverified": known.scope_unverified and fact.scope_unverified})


class FactRecord:
    """The turn's counts and settings, each kept once with every read of it."""

    def __init__(self, task: str):
        self.task = task
        self.facts: dict[str, RequestFact] = {}
        self.conflicts: list[FactConflict] = []
        self.scoped: list[str] = []
        self.scoped_features: list[str] = []
        """Reading shape 2: the request's scoped counts and settings, in the order read."""

    # -- reads -------------------------------------------------------------------------------------------------

    def _add(self, fact: RequestFact, evidence: FactEvidence) -> str:
        """The same words with the same value are one fact (one more read); with another value, a fact of its own.

        A count is also the same fact when its words overlap a stated count of the same kind and number: the request
        level quotes "40 samples", the result "our 40 liver samples" (on the recorded readings most repeats differ so).
        Words that do not overlap stay apart -- 300 RNA genes and 300 CpG probes are two counts (h4 M01)."""
        if fact.property != "setting" and fact.state == "stated":
            for known in self.facts.values():
                if (known.property, known.value, known.state, known.origin) == (
                        fact.property, fact.value, "stated", "user_stated") \
                        and known.span[0] < fact.span[1] and fact.span[0] < known.span[1]:
                    self.facts[known.id] = _read_again(known, fact, evidence)
                    return known.id
        base, number = fact.id, 1
        while (known := self.facts.get(fact.id)) is not None:
            if _same(known, fact):
                self.facts[fact.id] = _read_again(known, fact, evidence)
                return fact.id
            number += 1
            fact = fact.model_copy(update={"id": f"{base}#{number}"})
        self.facts[fact.id] = fact.model_copy(update={"evidence": [evidence]})
        return fact.id

    def read_method(self, item, reader: str, result: str = "") -> dict:
        """One reading's method: its counts and settings recorded, and the method compiled back from the record.

        `item`: an ask (reader "result", `result` its words) or the reading's request-level conditions (reader
        "request"). The named method is the reading's own and is not a fact of this round.
        """
        found = verified_method(self.task, item)
        method = {key: found[key] for key in ("named", "named_quote") if key in found}
        settings = [self._read_setting(setting, reader, result) for setting in found.get("settings", [])]
        if settings:
            method["settings"] = [self.setting(fact_id) for fact_id in settings]
        # A count's value is the fact's; its words are this read's own (they place it for the rules that look for
        # them, e.g. phase 5b's candidates inside a stated count's words).
        if "samples" in found:
            span = _span(self.task, getattr(item, "sample_count_quote", ""))
            fact_id = self._add(
                RequestFact(id=f"sample_count@{span[0]}-{span[1]}", property="sample_count",
                            value=str(found["samples"]), quote=found["samples_quote"], span=list(span)),
                FactEvidence(reader=reader, quote=found["samples_quote"], span=list(span), result=result))
            method.update(samples=_number(self.facts[fact_id].value), samples_quote=found["samples_quote"])
        features = [(start, end, self._add(
            RequestFact(id=f"feature_count@{start}-{end}", property="feature_count", value=str(count),
                        quote=self.task[start:end], span=[start, end]),
            FactEvidence(reader=reader, quote=self.task[start:end], span=[start, end], result=result)))
            for start, end, count in found.get("feature_items", [])]
        if features:
            items = [[start, end, _number(self.facts[fact_id].value)] for start, end, fact_id in features]
            method.update(features=sum(count for *_span_, count in items), feature_counts=len(items),
                          feature_items=items)
        return method

    def read_request(self, proposal) -> dict:
        """The request's own method, settings and data size (`method_conditions.request_method`), from the record.

        Reading shape 2 (ROUND-04): the request's counts and settings are the only ones, each scoped to the results it
        applies to (`scoped_method`); this is all of them, as the request states them (a sample count only when the
        request states one)."""
        conditions = getattr(proposal, "conditions", None)
        if not hasattr(conditions, "sample_counts"):
            return self.read_method(conditions, "request")
        method = {key: value for key, value in verified_method(self.task, SimpleNamespace(
            named_method=conditions.named_method, named_method_quote=conditions.named_method_quote)).items()}
        self.scoped = [fact_id for item in conditions.settings
                       if (fact_id := self._read_scoped("settings", item)) is not None]
        self.scoped += [fact_id for item in conditions.sample_counts
                        if (fact_id := self._read_scoped("samples", item)) is not None]
        self.scoped += [fact_id for item in conditions.feature_counts
                        if (fact_id := self._read_scoped("features", item)) is not None]
        self.scoped = list(dict.fromkeys(self.scoped))
        return {**method, **self._compiled(self.scoped)}

    def _read_scoped(self, kind: str, item) -> str | None:
        """One scoped count or setting, verified as an ask's would be (`verified_method`), with its scope."""
        if kind == "settings":
            found = verified_method(self.task, SimpleNamespace(settings=[item])).get("settings")
        elif kind == "samples":
            found = verified_method(self.task, SimpleNamespace(sample_count=item.count, sample_count_quote=item.quote))
        else:
            found = verified_method(self.task, SimpleNamespace(feature_counts=[item])).get("feature_items")
        if not found:
            return None
        raw = getattr(item, "applies_to", None)
        scope = None if raw is None else [
            self.task[span[0]:span[1]] for quote in raw
            if (quote or "").strip() and (span := _span(self.task, quote)) is not None]
        unverified = raw is not None and bool([quote for quote in raw if (quote or "").strip()]) and not scope
        scoped = {"applies_to": scope, "scope_unverified": unverified}
        if kind == "settings":
            return self._read_setting(found[0], "request", "", scoped)
        if kind == "samples":
            span = _span(self.task, item.quote)
            return self._add(
                RequestFact(id=f"sample_count@{span[0]}-{span[1]}", property="sample_count",
                            value=str(found["samples"]), quote=found["samples_quote"], span=list(span), **scoped),
                FactEvidence(reader="request", quote=found["samples_quote"], span=list(span)))
        start, end, count = found[0]
        owner = _span(self.task, item.belongs_to) if (item.belongs_to or "").strip() else None
        said = self.task[owner[0]:owner[1]] if owner else ""
        for fact_id in self.scoped_features:
            known = self.facts[fact_id]
            # The same number restated ("a 48-gene panel ... those 48 genes", p3 C57) is one count when the reading
            # names the same data type for both, or none for either; a named and an unnamed one, or two names, stay
            # two (300 RNA genes and 300 CpG probes, h4 M01).
            if known.value == str(count) and known.belongs_to.casefold() == said.casefold():
                self.facts[fact_id] = _read_again(
                    known, known.model_copy(update=scoped),
                    FactEvidence(reader="request", quote=self.task[start:end], span=[start, end]))
                return fact_id
        fact_id = self._add(
            RequestFact(id=f"feature_count@{start}-{end}", property="feature_count", value=str(count),
                        quote=self.task[start:end], span=[start, end],
                        belongs_to=said, **scoped),
            FactEvidence(reader="request", quote=self.task[start:end], span=[start, end]))
        self.scoped_features.append(fact_id)
        return fact_id

    def _applies(self, fact: RequestFact, span, single: bool) -> bool:
        if fact.applies_to is None:
            return True
        if fact.scope_unverified:
            return single
        return any((found := _span(self.task, words)) is not None and found[0] < span[1] and span[0] < found[1]
                   for words in fact.applies_to)

    def scoped_method(self, span, result: str, single: bool, workflows: set[str]) -> dict:
        """Shape 2: a result's counts and settings -- the request's facts that apply to it.

        A count applies to the results it is scoped to (every result when unscoped). Settings: see below. Two
        different sample counts for one result leave it with none (`several_values`)."""
        ids = []
        for fact_id in self.scoped:
            fact = self.facts[fact_id]
            if fact.property != "setting":
                if self._applies(fact, span, single):
                    ids.append(fact_id)
                continue
            scoped = fact.applies_to is not None
            if fact.name == UNREGISTERED:
                # Unscoped among several results, an unregistered setting holds none: it names no workflow, and the
                # misread ones are exactly these (h4 M23 "Let it estimate both shrinkage values" refused all three
                # results when applied to each in the offline conversion).
                if self._applies(fact, span, single) and (single or scoped):
                    ids.append(fact_id)
                continue
            own = fact.name.split(".", 1)[0] in workflows
            # A registered setting holds the results it is scoped to; and since one run of a workflow takes one set of
            # its settings, also every other result credited to that workflow (h2 J44 "set computing to gpu" read for
            # "Time to rerun OTTER ..." only, beside "Start it now."), unless scoped to no asked result. Unscoped among
            # several results, it holds only its workflow's results ("run PANDA ..., then CONDOR on it", M2).
            if (self._applies(fact, span, single) and (single or scoped or own)) or (own and fact.applies_to != []):
                ids.append(fact_id)
        samples = [fact_id for fact_id in ids if self.facts[fact_id].property == "sample_count"]
        if len({self.facts[fact_id].value for fact_id in samples}) > 1:
            self._conflict("sample_count", "", result, [], samples, "several_values")
            ids = [fact_id for fact_id in ids if fact_id not in samples]
        return self._compiled(ids)

    def _compiled(self, ids: list[str]) -> dict:
        """A method's counts and settings from facts (a sample count only when they give one value)."""
        method: dict = {}
        settings = [self.setting(fact_id) for fact_id in ids if self.facts[fact_id].property == "setting"]
        if settings:
            method["settings"] = settings
        samples = [self.facts[fact_id] for fact_id in ids if self.facts[fact_id].property == "sample_count"]
        if len({fact.value for fact in samples}) == 1:
            method.update(samples=_number(samples[0].value), samples_quote=samples[0].quote)
        items = sorted([*self.facts[fact_id].span, _number(self.facts[fact_id].value)]
                       for fact_id in ids if self.facts[fact_id].property == "feature_count")
        if items:
            method.update(features=sum(item[2] for item in items), feature_counts=len(items), feature_items=items)
        return method

    def _read_setting(self, setting: dict, reader: str, result: str, scoped: dict | None = None) -> str:
        value = setting.get("value", "")
        at = setting["at"]
        fact = RequestFact(
            id=f"setting:{setting['name']}@{setting['span'][0]}-{setting['span'][1]}", property="setting",
            name=setting["name"], value=value, quote=setting["quote"], span=list(setting["span"]),
            value_quote=value, value_span=[at, at + len(value)] if value else [], **(scoped or {}))
        return self._add(fact, FactEvidence(reader=reader, quote=setting["quote"], span=list(setting["span"]),
                                            result=result))

    def setting(self, fact_id: str) -> dict:
        """A setting as the method rules take it (`verified_method`'s shape)."""
        fact = self.facts[fact_id]
        return {"name": fact.name, "quote": fact.quote, "value": fact.value, "span": list(fact.span),
                "at": fact.value_span[0] if fact.value_span else fact.span[0]}

    def read_alternatives(self, proposal) -> list[dict]:
        """The counts the user gave as candidates, recorded -- with an unknown count stating the same candidates in
        the same words as one more read of it -- and compiled back as `count_update` takes them."""
        ids = []
        for found in verified_count_alternatives(self.task, proposal):
            start, end = found["span"]
            ids.append(self._add(
                RequestFact(id=f"{_PROPERTY[found['of']]}@{start}-{end}:candidates", property=_PROPERTY[found["of"]],
                            values=[str(value) for value in found["values"]], state="unsure", quote=found["quote"],
                            span=[start, end]),
                FactEvidence(reader="count_alternatives", quote=found["quote"], span=[start, end],
                             role="alternative")))
        for unknown in getattr(getattr(proposal, "conditions", None), "unknown_facts", None) or ():
            self._read_unknown_count(unknown)
        return [self.alternative(fact_id) for fact_id in dict.fromkeys(ids)]

    def _read_unknown_count(self, unknown) -> None:
        """An unknown sample count with its candidates (`count_kind` choices), kept when its words state each one.

        It is a second place the reading writes the same doubt (14 of the 26 recorded readings with candidates wrote
        both); `needed_facts` still acts on it as before, so here it is only recorded."""
        values = sorted(set(getattr(unknown, "count_values", None) or ()))
        if getattr(unknown, "about", "") != "sample_count" or getattr(unknown, "count_kind", "") != "choices" \
                or len(values) < 2:
            return
        span = _span(self.task, unknown.quote) if (unknown.quote or "").strip() else None
        if span is None:
            return
        words = self.task[span[0]:span[1]]
        if any(value <= 0 or value not in stated_numbers(words) for value in values):
            return
        evidence = FactEvidence(reader="unknown_facts", quote=words, span=list(span), role="alternative")
        for fact_id, fact in self.facts.items():
            if (fact.property == "sample_count" and fact.state == "unsure" and fact.values == [str(v) for v in values]
                    and fact.span[0] < span[1] and span[0] < fact.span[1]):
                self.facts[fact_id] = fact.model_copy(update={"evidence": [*fact.evidence, evidence]})
                return
        self._add(RequestFact(id=f"sample_count@{span[0]}-{span[1]}:candidates", property="sample_count",
                              values=[str(value) for value in values], state="unsure", quote=words, span=list(span)),
                  evidence)

    def alternative(self, fact_id: str) -> dict:
        fact = self.facts[fact_id]
        return {"of": _OF[fact.property], "quote": fact.quote, "values": [_number(v) for v in fact.values],
                "span": list(fact.span)}

    # -- what a result was judged on ---------------------------------------------------------------------------

    def _find(self, prop: str, name: str, span, value: str, quote: str | None = None) -> str | None:
        """The stated fact a method value was compiled from: same property and value, and one of its reads has
        these words (by place, or for a sample count, which the method keeps without its place, by its text)."""
        return next((fact_id for fact_id, fact in self.facts.items()
                     if fact.property == prop and fact.name == name and fact.value == value and fact.state == "stated"
                     and fact.origin == "user_stated"
                     and any(e.span == list(span) if quote is None else e.quote == quote for e in fact.evidence)),
                    None)

    def ids_for(self, method: dict, unknown_quote: str = "") -> list[str]:
        """The facts a result's method holds -- with the total code derived over several data types -- and the
        candidate count it waits on (`unknown_quote`)."""
        ids = [self._find("setting", item["name"], item.get("span") or [], item.get("value", ""))
               for item in method.get("settings", [])]
        if "samples" in method:
            ids.append(self._find("sample_count", "", [], str(method["samples"]), quote=method.get("samples_quote")))
        features = [self._find("feature_count", "", item[:2], str(item[2])) for item in method.get("feature_items", [])]
        ids += features
        if len(features) >= 2 and all(features):
            ids.append(self._derived_total(features))
        if unknown_quote:
            ids.append(next((fact_id for fact_id, fact in self.facts.items()
                             if fact.state == "unsure" and fact.quote == unknown_quote), None))
        return list(dict.fromkeys(fact_id for fact_id in ids if fact_id))

    def _derived_total(self, parts: list[str]) -> str:
        """Phase 4a's sum over data types, kept as code's own value with its operands -- never the user's words."""
        facts = [self.facts[fact_id] for fact_id in parts]
        fact_id = "feature_count=" + "+".join(parts)
        if fact_id not in self.facts:
            self.facts[fact_id] = RequestFact(
                id=fact_id, property="feature_count", value=str(sum(_number(fact.value) for fact in facts)),
                origin="derived", derived_from=list(parts),
                formula=" + ".join(f"{_number(fact.value):,}" for fact in facts),
                evidence=[FactEvidence(reader=fact.evidence[0].reader, quote=fact.quote, span=list(fact.span),
                                       result=fact.evidence[0].result, role="operand") for fact in facts])
        return fact_id

    def note_conflicts(self, result: str, own: dict, applied: dict, merged: dict) -> None:
        """Where a request-level value applied to a result disagrees with the result's own, the one the merge used."""
        if "samples" in own and "samples" in applied and own["samples"] != applied["samples"]:
            self._conflict("sample_count", "", result, self.ids_for({k: v for k, v in merged.items()
                                                                     if k in ("samples", "samples_quote")}),
                           self.ids_for({k: applied[k] for k in ("samples", "samples_quote")}), "result_own_value")
        if own.get("feature_items") and applied.get("feature_items") and \
                sorted(c for *_s, c in own["feature_items"]) != sorted(c for *_s, c in applied["feature_items"]):
            self._conflict("feature_count", "", result, self.ids_for({"feature_items": merged["feature_items"]}),
                           self.ids_for({"feature_items": applied["feature_items"]}), "result_own_value")
        mine = {item["name"]: item for item in own.get("settings", []) if item["name"] != UNREGISTERED}
        for item in applied.get("settings", []):
            other = mine.get(item["name"])
            if other is None or other.get("value", "").strip().casefold() == item.get("value", "").strip().casefold():
                continue
            kept = next((found for found in merged.get("settings", []) if found["name"] == item["name"]), other)
            dropped = item if kept is other else other
            self._conflict("setting", item["name"], result, self.ids_for({"settings": [kept]}),
                           self.ids_for({"settings": [dropped]}), "latest_stated")

    def _conflict(self, prop, name, result, used, set_aside, reason) -> None:
        found = FactConflict(property=prop, name=name, result=result, used=used, set_aside=set_aside, reason=reason)
        if set_aside and found not in self.conflicts:
            self.conflicts.append(found)

    def facts_list(self) -> list[RequestFact]:
        return list(self.facts.values())


def merge_facts(first: list[RequestFact], second: list[RequestFact], keep: set[str]) -> list[RequestFact]:
    """A re-read's facts beside the first reading's: the facts its kept results cite (`keep`), and for a fact both
    hold, the re-read's result reads added. The re-read carries the first reading's request-level conditions rather
    than reading them again, so its request reads are not counted twice."""
    merged = {fact.id: fact for fact in first}
    for fact in second:
        known = merged.get(fact.id)
        if known is None:
            if fact.id in keep:
                merged[fact.id] = fact
            continue
        if _same(known, fact):
            new = [e for e in fact.evidence if e.reader == "result" and e not in known.evidence]
            if new:
                merged[fact.id] = known.model_copy(update={"evidence": [*known.evidence, *new]})
    return list(merged.values())


def fact_for_setting(facts: list[RequestFact], setting: dict) -> str | None:
    """The fact a verified setting was compiled from."""
    return next((fact.id for fact in facts if fact.property == "setting" and fact.name == setting.get("name")
                 and fact.span == list(setting.get("span") or []) and fact.value == setting.get("value", "")), None)


def run_fact_bindings(check, action: str, set_by_request=lambda name: False, approved: bool = True) -> list[dict]:
    """Where each setting fact of a run's workflow went (the proposal's section 6.4: every stated requirement is
    applied, unsupported or waiting -- never read and then dropped).

    applied: its value is the run's control (`verified_controls` takes the same value); set_by_request: the request
    gave the control as name=value, which the run already carries; unbound: its value is not one the run can take,
    so the run waits (`unbound_settings`); held: the run was not approved, so nothing was bound.
    """
    from ..workflow_conditions import conditions_for
    from .method_conditions import _control_value, _run_settings
    from ..capability_sheet import entry

    conditions = conditions_for(action)
    if check is None or conditions is None:
        return []
    found = []
    for item in check.results():
        if action not in {entry(key).action for key in item.delivered_by}:
            continue
        for setting, limit in _run_settings(item, conditions):
            value = _control_value(limit, setting.get("value", ""), setting.get("quote", ""))
            if not approved:
                disposition = "held"
            elif set_by_request(limit.name):
                disposition = "set_by_request"
            elif value is not None:
                disposition = "applied"
            elif not setting.get("value", "").strip() and limit.control_type != "boolean":
                disposition = "no_value"
            else:
                disposition = "unbound"
            binding = {"fact": fact_for_setting(check.facts, setting), "control": limit.name,
                       "quote": setting.get("quote", ""), "value": value, "disposition": disposition}
            if binding not in found:
                found.append(binding)
    return found
