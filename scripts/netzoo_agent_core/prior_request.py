"""A request to build a TF motif prior and a TF PPI prior with SPONGE, read before workflow matching (2026-11-08).

SPONGE (kuijjerlab/sponge, Hovan et al.) scans JASPAR binding sites in the promoters of human genes and asks STRING
for the interactions between the selected TFs; its two files are the motif and PPI priors PANDA, PUMA, LIONESS-PANDA,
OTTER, GIRAFFE and SCORPION read. Like normalization, it is a preparation step, never a menu workflow: the semantic
interpreter reads results the registry's workflows produce, and a prior is an input. It is taken from the request's own
words -- SPONGE named, or building/generating a motif, PPI or prior network named -- and a command, not a question.

"Build the priors, then run PANDA on expression.tsv" names one workflow that reads a motif prior: the priors are
planned now, the workflow is recorded as `then_action` and planned on a later turn with the two prior files
(`cli.follow_up`). Every setting is read from explicit words only; none is guessed.

The router reads it before the semantic interpreter (`graph.router_invocation._route_request`): it needs no model
reading, and live 2026-11-09 a reading that failed twice sent "Build the priors with SPONGE ..., then run PANDA" to a
named PANDA run instead. A request read only as a command by the interpreter is still caught after it.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from workflow_registry import ACTION_DEFINITIONS

from .contracts import RequestedOutcome, TaskDecision
from .method_names import LIONESS_FAMILY, registered_workflows
from .routing.capability import has_explicit_advice_intent, is_workflow_information_request
from .routing.path_tokens import output_directory

if TYPE_CHECKING:
    from .contracts.outcomes import SemanticInterpretation

__all__ = [
    "PRIOR_CONSUMERS", "SPONGE_DEFAULTS", "SPONGE_MOTIFS_JASPAR2026", "prior_decision", "prior_requested",
    "requested_tf_names", "sponge_cost_note", "sponge_plan_lines",
]

#: Vertebrate JASPAR CORE motifs (latest versions) SPONGE selects without a TF list, counted with pyjaspar 4.0.0 on
#: 2026-11-08 (JASPAR2026). Each is one genome-wide binding-site track downloaded during the run.
SPONGE_MOTIFS_JASPAR2026 = 1019
SPONGE_DEFAULTS = {
    "genome_assembly": "hg38", "promoter_upstream": 750, "promoter_downstream": 250,
    "motif_score_threshold": 400, "ppi_score_threshold": 400, "n_cores": 1,
}
#: Workflows that read a motif prior (and a PPI network): the ones a "build priors, then run X" request can chain to.
PRIOR_CONSUMERS = frozenset(
    action for action in registered_workflows().values()
    if "motif_file" in {*ACTION_DEFINITIONS[action].required_inputs, *ACTION_DEFINITIONS[action].optional_inputs}
)

_SPONGE = re.compile(r"(?<![A-Za-z0-9-])SPONGE(?![A-Za-z0-9])|netzoopy-sponge", re.I)
_PRIOR = (r"(?:motif|binding[- ]site|TF[- ]gene|regulatory|PPI|protein[- ]protein\s+interaction)\s+priors?"
          r"|priors?\s+(?:network|GRN|files?)|prior\s+(?:gene\s+)?regulatory\s+network|motif\s+(?:and|&)\s+PPI\s+priors?"
          r"|(?:motif|PPI)\s*先驗|先驗(?:網路|网络|檔|文件)?")
_BUILD = r"\b(?:build|generate|create|make|construct|derive|produce|prepare)\w*\b|建立|產生|产生|生成|建構|构建|製作"
_BUILD_PRIOR = re.compile(rf"(?:{_BUILD}).{{0,60}}?(?:{_PRIOR})|(?:{_PRIOR}).{{0,30}}?(?:{_BUILD})", re.I | re.S)
_NEGATED = re.compile(
    r"\b(?:do\s*n[o']t|don't|never|without|no|skip|not)\s+(?:\w+\s+){0,2}(?:build|generat|creat|sponge)"
    r"|(?:不要|不用|不需要|別|勿).{0,6}(?:建立|產生|生成|sponge)",
    re.I,
)
_COMMAND = re.compile(
    r"(?:^|[.;!\n]\s*|\b(?:please|pls|can you|could you)\s+)"
    r"(?:build|generate|create|make|construct|derive|produce|prepare|run|use|get)\b|請|幫我|做",
    re.I,
)
_SEQUENCE = re.compile(r"\b(?:then|after(?:wards)?|followed by|and use (?:them|it))\b|之後|然後|再", re.I)
_NON_HUMAN = re.compile(
    r"\b(?:mouse|mice|murine|mus musculus|rat|rattus|zebrafish|danio|drosophila|fly|yeast|cerevisiae|arabidopsis|"
    r"c\.?\s*elegans|worm|chicken|pig|bovine|macaque)\b|小鼠|大鼠|斑馬魚|果蠅|酵母",
    re.I,
)


def _named_workflows(task: str) -> list[str]:
    """The workflows the request names to run; "PANDA priors" names the priors' consumer, not a run."""
    task = re.sub(r"[\w-]+(?:[- ]style|[- ]compatible|[- ]ready)?\s+(?:motif\s+|PPI\s+)?priors?\b", " ", task, flags=re.I)
    workflows = registered_workflows()
    spans: list[tuple[int, int, str]] = []
    for name in sorted([*workflows, LIONESS_FAMILY], key=len, reverse=True):
        for found in re.finditer(rf"(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", task, re.I):
            if not any(start <= found.start() and found.end() <= end for start, end, _ in spans):
                spans.append((found.start(), found.end(), name))
    return list(dict.fromkeys(workflows.get(name, name) for _, _, name in sorted(spans)))


def chained_action(task: str) -> str | None:
    """The one workflow a "build the priors, then run it" request names, when it reads a motif prior."""
    named = _named_workflows(task)
    if len(named) != 1 or named[0] not in PRIOR_CONSUMERS or not _SEQUENCE.search(task):
        return None
    return named[0]


def prior_requested(task: str, interpretation: SemanticInterpretation | None = None) -> bool:
    """The request asks, now, to build motif and PPI priors (and at most one workflow after them)."""
    if not (_SPONGE.search(task) or _BUILD_PRIOR.search(task)):
        return False
    if _NEGATED.search(task) or has_explicit_advice_intent(task):
        return False
    if is_workflow_information_request(task) and not _SPONGE.search(task):
        return False
    if _named_workflows(task) and chained_action(task) is None:
        return False  # another workflow named without "then": routing decides (e.g. "Run PANDA with my motif prior")
    commanded = interpretation is not None and interpretation.request_mode == "execute"
    return commanded or bool(_COMMAND.search(task.strip()))


_SYMBOL = r"[A-Z][A-Z0-9-]{1,14}"


def requested_tf_names(task: str) -> list[str]:
    """The TF symbols the request lists ("tf_names=SOX2,MYC"; "for the TFs SOX2, MYC and FOXF2"), in its order."""
    if explicit := re.search(r"\b(?:sponge_)?tf_names\s*[=:]\s*\[?([A-Za-z0-9 ,;-]+)", task, re.I):
        return list(dict.fromkeys(name.strip().upper() for name in re.split(r"[,;\s]+", explicit.group(1)) if name.strip()))
    found = re.search(
        rf"(?:\bTFs?\b|transcription\s+factors?|轉錄因子|转录因子)\s*(?:[:：]|such\s+as|like|namely|including)?\s*"
        rf"((?:{_SYMBOL})(?:\s*(?:,|、|/|\band\b|\bor\b|和|與|与)\s*(?:{_SYMBOL}))*)",
        task,
    )
    if not found:
        return []
    names = re.split(r"\s*(?:,|、|/|\band\b|\bor\b|和|與|与)\s*", found.group(1))
    return list(dict.fromkeys(name for name in names if re.fullmatch(_SYMBOL, name) and name not in {"TF", "TFS", "PPI"}))


def _jaspar_release(task: str) -> str | None:
    found = re.search(r"\bJASPAR\s*[-_ ]?(20\d\d)\b", task, re.I)
    return f"JASPAR{found.group(1)}" if found else None


def _assembly(task: str) -> str | None:
    named = {value for pattern, value in ((r"\bhg19\b|GRCh37", "hg19"), (r"\bhg38\b|GRCh38", "hg38"),
                                           (r"\bT2T\b|CHM13|\bhs1\b", "hs1")) if re.search(pattern, task, re.I)}
    return named.pop() if len(named) == 1 else None


def _window(task: str) -> tuple[int | None, int | None]:
    """A promoter window stated in bp or kb around the TSS: "-750/+250", "1000 bp upstream and 500 bp downstream",
    "+/-1 kb"."""
    def bp(number: str, unit: str | None) -> int:
        return int(float(number) * (1000 if unit and unit.lower().startswith("k") else 1))
    if found := re.search(r"[-−–]\s*(\d+(?:\.\d+)?)\s*(kb|bp)?\s*(?:/|to|,|and|\.\.)\s*\+\s*(\d+(?:\.\d+)?)\s*(kb|bp)?",
                          task, re.I):
        return bp(found.group(1), found.group(2) or found.group(4)), bp(found.group(3), found.group(4) or found.group(2))
    if found := re.search(r"(?:\+/-|±|plus\s+or\s+minus)\s*(\d+(?:\.\d+)?)\s*(kb|bp)", task, re.I):
        return bp(found.group(1), found.group(2)), bp(found.group(1), found.group(2))
    up = re.search(r"(\d+(?:\.\d+)?)\s*(kb|bp)\s+upstream", task, re.I)
    down = re.search(r"(\d+(?:\.\d+)?)\s*(kb|bp)\s+downstream", task, re.I)
    return (bp(*up.groups()) if up else None), (bp(*down.groups()) if down else None)


def _output_dir(task: str) -> str | None:
    found = re.search(r"\boutput_dir\s*=\s*(\S+)", task, re.I)
    return found.group(1).rstrip(".,;:)") if found else output_directory(task)  # any folder, not only /, data/ (2026-11-10)


def prior_decision(task: str, interpretation: SemanticInterpretation | None = None) -> TaskDecision | None:
    """build_priors for this request, or None when it is not one."""
    if not prior_requested(task, interpretation):
        return None
    upstream, downstream = _window(task)
    non_human = _NON_HUMAN.search(task)
    return TaskDecision(
        action="build_priors", in_scope=True, should_execute=True, intent_type="prepare_input", confidence=1.0,
        reason="Build a human TF motif prior and a TF PPI prior with SPONGE (JASPAR, Ensembl promoters, STRING).",
        requested_outcome=RequestedOutcome(operation="prepare", artifact_type="unknown", granularity="not_applicable"),
        capability_match_status="exact", match_basis="semantic", matched_actions=["build_priors"],
        then_action=chained_action(task),
        sponge_tf_names=requested_tf_names(task) or None,
        jaspar_release=_jaspar_release(task),
        genome_assembly=_assembly(task),
        promoter_upstream=upstream, promoter_downstream=downstream,
        output_dir=_output_dir(task),
        taxon=non_human.group(0) if non_human else None,
    )


def sponge_cost_note(tf_names: list[str] | None) -> str:
    """What the run will download, said before it is approved."""
    if tf_names:
        which = "the 1 TF" if len(tf_names) == 1 else f"each of the {len(tf_names)} TFs"
        return (f"SPONGE downloads one genome-wide JASPAR binding-site track for {which} "
                "(the FOXF2 track was 77 MB on 2026-11-08) and needs internet access to JASPAR, Ensembl, NCBI, "
                "UniProt and STRING.")
    return (f"No TF list: SPONGE selects every vertebrate JASPAR CORE motif ({SPONGE_MOTIFS_JASPAR2026:,} in "
            "JASPAR2026) and downloads one genome-wide binding-site track for each (the FOXF2 track was 77 MB), so "
            "the run can take hours. Name the TFs (tf_names=...) to keep it short. It needs internet access to "
            "JASPAR, Ensembl, NCBI, UniProt and STRING.")


def sponge_plan_lines(decision: dict) -> list[str]:
    """The plan's SPONGE settings, each marked as the request's or SPONGE's default, then the download note."""
    def said(name, label, shown=None):
        value = decision.get(name)
        if value in (None, "", []):
            return f"- {label}: {shown or SPONGE_DEFAULTS.get(name, 'newest')} [SPONGE default]"
        return f"- {label}: {', '.join(value) if isinstance(value, list) else value} [from your request]"
    upstream = decision.get("promoter_upstream")
    downstream = decision.get("promoter_downstream")
    window = (f"- Promoter window: {upstream if upstream is not None else 750} bp upstream to "
              f"{downstream if downstream is not None else 250} bp downstream of each TSS "
              + ("[from your request]" if upstream is not None or downstream is not None else "[SPONGE default]"))
    return [
        said("sponge_tf_names", "TFs", "every vertebrate JASPAR CORE motif"),
        said("jaspar_release", "JASPAR release", "the newest"),
        said("genome_assembly", "Genome assembly"),
        window,
        "- Organism: human (SPONGE builds human priors only)",
        f"- Download: {sponge_cost_note(decision.get('sponge_tf_names'))}",
    ]
