"""Planning rules for explicit BONOBO downstream handoffs."""

from __future__ import annotations

import re
from collections.abc import Mapping

from workflow_registry import ACTION_DEFINITIONS, registered_handoff_consumers

from .contracts import TaskDecision
from .contracts.handoffs import WorkflowHandoff


_BONOBO_PATTERN = re.compile(r"\bbonobo\b", re.IGNORECASE)
_CHAIN_PATTERN = re.compile(
    r"(?:then|after|next|downstream|handoff|pass|feed|chain|follow[- ]?on|"
    r"再|接著|然後|後續|交給|串接|轉交|下游|"
    r"(?:output|result)\s+(?:to|into)|"
    r"(?:as\s+(?:the\s+)?input\s+to|to|into)\s+"
    r"(?:the\s+)?(?:regulatory|regulation|grn|tf[- ]?gene|panda|puma|giraffe|otter)|"
    r"(?:輸出|結果).{0,10}(?:交給|轉交))",
    re.IGNORECASE,
)
_CONSUMER_PATTERN = re.compile(
    r"(?:regulatory|regulation|grn|tf[- ]gene|panda|puma|giraffe|otter)",
    re.IGNORECASE,
)
_GENERIC_HANDOFF_PATTERN = re.compile(
    r"(?:pass|feed|handoff|hand\s+off|send|transfer|"
    r"交給|串接|轉交|下游|輸出.{0,10}(?:交給|轉交))",
    re.IGNORECASE,
)
_SAMPLE_SPECIFIC_PATTERN = re.compile(
    r"(?:sample[- ]specific|per[- ]sample|each\s+sample|"
    r"每個樣本|各自|樣本各自|每一個樣本)",
    re.IGNORECASE,
)
_GENE_COEXPRESSION_PATTERN = re.compile(
    r"(?:"
    r"(?:gene[- ](?:gene|by[- ]gene)|gene.?gene).{0,80}?"
    r"(?:co[- ]?expression|coexpression|共同表現|共表現)"
    r"|"
    r"(?:co[- ]?expression|coexpression|共同表現|共表現).{0,80}?"
    r"(?:gene[- ](?:gene|by[- ]gene)|gene.?gene)"
    r")",
    re.IGNORECASE,
)


def explicit_bonobo_handoff_requested(task: str) -> bool:
    """Recognize a requested BONOBO stage followed by another workflow."""
    bonobo = _BONOBO_PATTERN.search(task)
    if bonobo is None:
        return False
    chain = _CHAIN_PATTERN.search(task, bonobo.end())
    consumer = _CONSUMER_PATTERN.search(task, bonobo.end())
    known_consumer_handoff = chain is not None and consumer is not None
    generic_handoff = _GENERIC_HANDOFF_PATTERN.search(task)
    return bool(
        known_consumer_handoff
        or (
            generic_handoff is not None
            and generic_handoff.start() > bonobo.end()
        )
    )


def sample_specific_coexpression_handoff_requested(task: str) -> bool:
    """Recognize an unnamed sample-specific co-expression handoff request.

    This deliberately does not select a producer.  It only identifies the
    multi-stage shape so the response layer can explain a downstream schema
    boundary instead of claiming that the first-stage result is unsupported.
    Explicit BONOBO requests continue through the typed BONOBO handoff path.
    """
    if _BONOBO_PATTERN.search(task) is not None:
        return False
    sample_specific = _SAMPLE_SPECIFIC_PATTERN.search(task)
    coexpression = _GENE_COEXPRESSION_PATTERN.search(task)
    if sample_specific is None or coexpression is None:
        return False
    source_end = max(sample_specific.end(), coexpression.end())
    chain = _CHAIN_PATTERN.search(task, source_end)
    if chain is None:
        return False
    consumer = _CONSUMER_PATTERN.search(task, chain.start())
    return consumer is not None


def _named_consumer_action(task: str, registry: Mapping[str, object]) -> str | None:
    normalized = task.casefold()
    for action, definition in registry.items():
        if not action.startswith("run_") or action == "run_bonobo":
            continue
        workflow = str(getattr(definition, "workflow", ""))
        if workflow and workflow.casefold() in normalized:
            return action
    return None


def build_bonobo_handoff(
    task: str,
    decision: TaskDecision,
    registry: Mapping[str, object] | None = None,
) -> WorkflowHandoff | None:
    """Build a fail-closed BONOBO producer/consumer contract from the registry."""
    if not explicit_bonobo_handoff_requested(task):
        return None
    source = ACTION_DEFINITIONS if registry is None else registry
    if hasattr(source, "workflows"):
        source = source.workflows
    producer = source.get("run_bonobo")
    capability = getattr(producer, "output_capability", None)
    if producer is None or capability is None:
        return WorkflowHandoff(
            producer_action="run_bonobo",
            producer_workflow="BONOBO",
            source_artifact_type="coexpression_network",
            source_granularity="sample_specific",
            status="blocked_no_consumer",
            reason=(
                "BONOBO is not registered with a usable output capability, so the "
                "requested downstream handoff cannot be verified or executed."
            ),
        )

    producer_workflow = str(getattr(producer, "workflow", "BONOBO"))
    source_artifact = getattr(capability, "artifact_type", "coexpression_network")
    source_granularity = (
        "sample_specific"
        if "sample_specific" in getattr(capability, "granularities", ())
        else "unknown"
    )
    produced_artifacts = list(
        getattr(capability, "produced_artifacts", ()) or (source_artifact,)
    )
    consumers = registered_handoff_consumers("run_bonobo", source)
    named_action = _named_consumer_action(task, source)
    compatible = next(
        (item for item in consumers if named_action is None or item.action == named_action),
        None,
    )
    sample_ids = list(decision.sample_names)
    if compatible is None:
        if named_action is not None:
            named = source.get(named_action)
            named_workflow = getattr(named, "workflow", named_action)
            status = "blocked_incompatible"
            reason = (
                f"The requested {producer_workflow} → {named_workflow} handoff is "
                "blocked: the registered consumer schema does not explicitly accept "
                "BONOBO's sample-specific gene-gene co-expression artifact with the "
                "same granularity. No execution is permitted."
            )
        else:
            status = "blocked_no_consumer"
            reason = (
                f"No verifiable downstream workflow is registered for {producer_workflow}'s "
                "sample-specific gene-gene co-expression output. The registered "
                "regulatory consumers accept aggregate co-expression inputs, not this "
                "BONOBO artifact; no consumer is invented and no execution is permitted."
            )
        return WorkflowHandoff(
            producer_action="run_bonobo",
            producer_workflow=producer_workflow,
            source_artifact_type=source_artifact,
            source_granularity=source_granularity,
            produced_artifacts=produced_artifacts,
            sample_ids=sample_ids,
            status=status,
            reason=reason,
        )

    return WorkflowHandoff(
        producer_action="run_bonobo",
        producer_workflow=producer_workflow,
        source_artifact_type=source_artifact,
        source_granularity=source_granularity,
        produced_artifacts=produced_artifacts,
        sample_ids=sample_ids,
        consumer_action=compatible.action,
        consumer_workflow=compatible.workflow,
        consumer_input_field=compatible.input_field,
        required_prior_inputs=list(compatible.required_prior_inputs),
        status="validated",
        reason=(
            f"Validated registry handoff {producer_workflow} → {compatible.workflow}. "
            "The downstream stage must consume the same sample IDs and gene order, "
            "and must provide the registered prior inputs."
        ),
    )


__all__ = [
    "build_bonobo_handoff",
    "explicit_bonobo_handoff_requested",
    "sample_specific_coexpression_handoff_requested",
]
