"""Deterministic answers for basic registered-workflow concept questions."""

from __future__ import annotations

import re

from workflow_registry import ACTION_DEFINITIONS, DOWNSTREAM_ANALYSES, OTHER_READING_NOTES

from ..contracts import ProjectPolicySnapshot, TaskDecision
from ..routing.clarification_planner import algorithmic_assumptions_for
from ..presentation import _NON_ENGLISH, _ui_text
from .inspected_answers import with_inspection_footer
from .advisory_answers import render_advisory_recommendation, render_method_capability_gap
from .method_philosophy import method_philosophies_for
from .reply_notes import with_reply_notes
from .single_candidate import single_candidate_question
from .tie_guidance import concern_section_for_workflow, render_tie_guidance
from ..routing.outcome_matching import (
    guidance_actions_for,
    has_granularity_only_ambiguity,
)
from ..routing.method_rejections import unsupported_algorithm_request
from ..routing.named_labels import solely_named_run_action
from ..routing.path_tokens import without_path_tokens
from .registry_guidance import (
    handoff_input_fields,
    preferred_registry_composition_actions,
)
from ..handoff import sample_specific_coexpression_handoff_requested
from ..settings import INPUT_ROLE_FIELDS
from .extraction import INPUT_LABELS

_PURPOSE_PATTERN = re.compile(
    r"\b(?:function|purpose|what\s+is|what\s+does)\b|(?:功能|用途|是什麼)",
    flags=re.IGNORECASE,
)
_SCRIPT_REQUEST_PATTERN = re.compile(
    r"\b(?:write|generate|create|give|show)\b.{0,40}\b(?:script|code|template)\b"
    r"|\b(?:script|code|template)\b.{0,40}\b(?:write|generate|create)\b"
    r"|(?:幫我|請).{0,20}(?:寫|產生|生成).{0,20}(?:腳本|程式|script|code)",
    flags=re.IGNORECASE,
)
_WORKFLOW_CONTRACT_PATTERN = re.compile(
    r"(?:input|inputs|file|files|data|parameter|parameters|輸入|檔案|資料|先驗)"
    r".{0,100}(?:output|outputs|result|產生|輸出|結果|網路|network|matrix|矩陣)"
    r"|(?:output|outputs|result|產生|輸出|結果|網路|network|matrix|矩陣)"
    r".{0,100}(?:input|inputs|file|files|data|parameter|parameters|輸入|檔案|資料|先驗)",
    flags=re.IGNORECASE | re.DOTALL,
)
_TWO_GROUP_COMPARISON_PATTERN = re.compile(
    r"\b(?:between|compare|comparison)\b.{0,100}\b(?:groups?|conditions?)\b"
    r"|\b(?:groups?|conditions?)\b.{0,100}\b(?:differences?|differential|compare)\b"
    r"|兩組|兩群|組間|組別.{0,12}(?:差異|比較)|癌症.{0,12}正常|正常.{0,12}癌症",
    flags=re.IGNORECASE | re.DOTALL,
)
_OPERATION_VERBS = {
    "acquire": "acquire",
    "prepare": "prepare",
    "validate": "validate",
    "infer": "infer",
    "analyze": "analyze",
    "explain": "explain",
    "unknown": "produce",
}
_ARTIFACT_LABELS = {
    "measurement_dataset": "measurement data",
    "expression_matrix": "expression matrices",
    "regulatory_network": "regulatory networks",
    "signed_regulatory_effect_network": "signed regulatory-effect networks",
    "tf_activity_matrix": "TF activity matrices",
    "coexpression_network": "co-expression networks",
    "pvalue_matrix": "matching p-value matrices",
    "community_assignment": "community assignments",
    "validation_report": "validation reports",
    "unknown": "the requested result",
}
_GRANULARITY_LABELS = {
    "aggregate": "aggregate",
    "sample_specific": "sample-specific",
    "not_applicable": "",
    "unknown": "",
}
_ENTITY_LABELS = {"tf": "TF", "mirna": "miRNA", "gene": "gene"}


def _artifact_label(artifact: str) -> str:
    return _ARTIFACT_LABELS.get(artifact, artifact.replace("_", " "))


def _outcome_phrase(outcome, *, include_granularity: bool = True) -> str:
    if outcome is None:
        return "the requested result"
    pieces = []
    granularity = (
        _GRANULARITY_LABELS[outcome.granularity] if include_granularity else ""
    )
    if granularity:
        pieces.append(granularity)
    entities = [item for item in outcome.display_entities if not _NON_ENGLISH.search(item)] or [
        _ENTITY_LABELS.get(item, item)
        for item in outcome.entity_types
        if item != "unknown"
    ]
    if entities:
        pieces.append("/".join(entities))
    pieces.append(_artifact_label(outcome.artifact_type))
    return " ".join(pieces)


def _requested_outcome_phrase(decision: TaskDecision) -> str:
    return _outcome_phrase(decision.requested_outcome)


def _capability_phrase(spec, decision: TaskDecision) -> str:
    capability = spec.output_capability
    requested_granularity = (
        decision.requested_outcome.granularity if decision.requested_outcome else None
    )
    granularity = (
        requested_granularity
        if requested_granularity in capability.granularities
        else capability.granularities[-1]
    )
    prefix = _GRANULARITY_LABELS[granularity]
    if capability.artifact_type == "regulatory_network":
        regulators = "/".join(
            _ENTITY_LABELS[item] for item in capability.regulator_types
        )
        targets = "/".join(_ENTITY_LABELS[item] for item in capability.target_types)
        relationship = f"{regulators}-to-{targets} " if regulators and targets else ""
        return f"{prefix} {relationship}regulatory networks".strip()
    return f"{prefix} {_artifact_label(capability.artifact_type)}".strip()


def _workflow_sequence(
    action: str,
    policy: ProjectPolicySnapshot,
) -> str:
    names = []
    for item in guidance_actions_for(action):
        spec = policy.workflows.get(item)
        if spec is not None:
            names.append(spec.workflow)
    return " → ".join(names)


def _network_family_label(spec) -> str:
    capability = spec.output_capability
    if capability.artifact_type == "coexpression_network":
        return "Gene co-expression network"
    if capability.artifact_type in {
        "regulatory_network",
        "signed_regulatory_effect_network",
    }:
        regulators = set(capability.regulator_types)
        signed = capability.artifact_type == "signed_regulatory_effect_network"
        if regulators == {"tf"}:
            if signed:
                return "TF-only signed regulatory-effect network"
            return "TF-only regulatory network"
        labels = "/".join(_ENTITY_LABELS[item] for item in capability.regulator_types)
        if signed:
            return f"{labels} signed regulatory-effect network"
        return f"{labels} regulatory network"
    return _artifact_label(capability.artifact_type).capitalize()


def _decision_assumptions(decision: TaskDecision) -> list[str]:
    assumptions = []
    seen = set()
    for hypothesis in decision.outcome_hypotheses:
        for assumption in hypothesis.assumptions:
            normalized = " ".join(assumption.split())
            # Model-written text in another language is not shown: agent output is English (Log 207).
            if normalized and normalized.casefold() not in seen and not _NON_ENGLISH.search(normalized):
                assumptions.append(normalized)
                seen.add(normalized.casefold())
    return assumptions[:6]


def _assumptions_block(decision: TaskDecision, heading: str) -> str:
    assumptions = _decision_assumptions(decision)
    if not assumptions:
        return ""
    return heading + "\n" + "\n".join(f"- {item}" for item in assumptions)


def _input_summary(spec) -> str:
    required_fields = [field for field in spec.required_inputs if field in INPUT_ROLE_FIELDS]
    parts = []
    if required_fields:
        labels = [
            INPUT_LABELS.get(field, field.replace("_", " "))
            for field in required_fields
        ]
        parts.append("all of: " + ", ".join(labels))
    for group in spec.required_input_groups:
        labels = [
            INPUT_LABELS.get(field, field.replace("_", " "))
            for field in group
            if field in INPUT_ROLE_FIELDS
        ]
        if labels:
            parts.append("one of: " + " or ".join(labels))
    return (
        "; and ".join(parts)
        if parts
        else "no required biological input fields are registered"
    )


def _candidate_details(action: str, spec, policy: ProjectPolicySnapshot, *, recommended=False) -> list[str]:
    capability = spec.output_capability
    sequence = _workflow_sequence(action, policy) or spec.workflow
    marker = " (recommend)" if recommended else ""
    lines = [f"- **{_network_family_label(spec)} — {sequence}**{marker}"]
    lines.append("  - Registered purpose: " + spec.description)
    method_notes = list(algorithmic_assumptions_for(capability.selection_tags))
    if capability.guidance_notes:
        detail = capability.guidance_notes[0]
        if detail not in method_notes:
            method_notes.append(detail)
    if method_notes:
        lines.append("  - Method premise: " + "; ".join(method_notes[:2]))
    for philosophy in method_philosophies_for(capability.selection_tags):
        lines.append("  - Mathematical interpretation: " + philosophy)
    lines.append("  - Required inputs: " + _input_summary(spec) + ".")
    artifacts = sorted(capability.produced_artifacts or {capability.artifact_type})
    output_labels = [_artifact_label(artifact) for artifact in artifacts]
    granularities = [
        label
        for value, label in (
            ("aggregate", "cohort-level aggregate"),
            ("sample_specific", "sample-specific, one network per sample"),
        )
        if value in capability.granularities
    ]
    output = ", ".join(output_labels)
    if granularities:
        output += " (" + "; ".join(granularities) + ")"
    lines.append("  - Declared output: " + output + ".")
    return lines


def render_outcome_clarification(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    *,
    task: str = "",
    semantic_goal: dict | None = None,
) -> str | None:
    """Explain compatible hypotheses before asking one validated clarification."""
    return with_inspection_footer(
        with_reply_notes(
            _render_outcome_clarification(decision, policy, task=task, semantic_goal=semantic_goal),
            decision, task,
        ),
        decision.inspected_directories,
    )


def _render_outcome_clarification(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    *,
    task: str = "",
    semantic_goal: dict | None = None,
) -> str | None:
    if decision.requested_outcome and decision.requested_outcome.artifact_type == "unknown":
        # An unknown result has not qualified every registry workflow. Use the
        # catalog conditionally instead of asserting that unrelated modalities fit.
        return None
    if decision.advisory_capability_gap:
        return render_method_capability_gap(decision, policy, artifact_label=_artifact_label)
    beginner_guidance = _render_beginner_group_network_guidance(
        task, decision, semantic_goal,
    )
    if beginner_guidance is not None:
        return beginner_guidance
    # A one-candidate tie with no question still gets one (Log 194).
    question = decision.clarification_question or single_candidate_question(decision)
    if decision.capability_match_status != "ambiguous" or not question:
        return None
    if len(decision.hypothesis_actions) == 1:
        action = decision.hypothesis_actions[0]
        spec = policy.workflows.get(action)
        if spec is not None:
            granularity_ambiguous = has_granularity_only_ambiguity(
                decision.outcome_hypotheses
            )
            interpretation = (
                _outcome_phrase(
                    decision.outcome_hypotheses[0].outcome,
                    include_granularity=False,
                )
                if granularity_ambiguous
                else (
                    _requested_outcome_phrase(decision)
                    if decision.requested_outcome is not None
                    else _capability_phrase(spec, decision)
                )
            )
            details = "\n".join(_candidate_details(action, spec, policy))
            assumptions = _assumptions_block(
                decision,
                "Unconfirmed assumptions in my current interpretation (please correct me if needed):",
            )
            if granularity_ambiguous:
                sections = [
                    f"It sounds like you want {interpretation}.",
                    question,
                    "Compatible workflow method and input/output details:\n"
                    f"{details}",
                ]
                if assumptions:
                    sections.append(assumptions)
                sections.append("No files were inspected and no analysis ran.")
                return _ui_text("\n\n".join(sections))
            sections = [
                f"It sounds like you want {interpretation}.\n\n"
                "Registered method and input/output fit:\n"
                f"{details}"
            ]
            if assumptions:
                sections.append(assumptions)
            sections.extend(
                [
                    question,
                    "No files were inspected and no analysis ran.",
                ]
            )
            return _ui_text("\n\n".join(sections))
    if len(decision.hypothesis_actions) > 1 and decision.advisory_recommendation:
        recommended = render_advisory_recommendation(
            decision, policy, candidate_details=_candidate_details,
            downstream_section=downstream_section, family_label=_network_family_label,
        )
        if recommended is not None:
            return recommended
    if len(decision.hypothesis_actions) > 1:
        # Organized by what separates the candidates, not a spec sheet (Log 261).
        tie = render_tie_guidance(decision, policy, family_label=_network_family_label, assumptions=_assumptions_block(
            decision,
            "Unconfirmed assumptions in these interpretations (please correct me if needed):",
        ))
        if tie is not None:
            return _ui_text(tie)
    return _ui_text(
        "I cannot select a workflow until the requested result is clear. "
        f"{question}\n\n"
        "No files were inspected and no analysis ran."
    )


def downstream_section(action: str) -> str:
    """The registered downstream-use notes for a workflow, or '' (Log 160/162/166)."""
    if action not in DOWNSTREAM_ANALYSES:
        return ""
    heading, notes = DOWNSTREAM_ANALYSES[action]
    return heading + "\n" + "".join(f"   - {note}\n" for note in notes)


def _render_beginner_group_network_guidance(
    task: str,
    decision: TaskDecision,
    semantic_goal: dict | None,
) -> str | None:
    """Explain group-vs-sample network comparison before asking about methods."""
    outcome = decision.requested_outcome
    if not (
        (semantic_goal or {}).get("request_mode") == "guidance"
        and decision.action == "no_tool"
        and decision.intent_type == "answer_question"
        and not decision.advisory_recommendation
        and decision.capability_match_status == "ambiguous"
        and decision.clarification_question
        and decision.clarification_question.casefold().startswith(
            "which modeling assumption"
        )
        and outcome is not None
        and outcome.artifact_type == "regulatory_network"
        and "tf" in outcome.regulator_types
        and "gene" in outcome.target_types
        and "run_panda" in decision.hypothesis_actions
        and _TWO_GROUP_COMPARISON_PATTERN.search(task)
    ):
        return None

    return _ui_text(
        "Your goal is to compare TF-to-gene regulation between cancer and normal groups. "
        "You do not need to choose among matrix factorization, message passing, or graph "
        "matching assumptions before getting started.\n\n"
        "A straightforward first step is to prepare a normalized or appropriately "
        "transformed gene-by-sample expression matrix and sample group labels. Infer one "
        "aggregate network for each group, then compare TF-to-gene edges. PANDA is a "
        "common starting method; "
        "it requires expression data, a TF-motif prior, and a PPI prior.\n\n"
        "If you want to retain patient-level differences, LIONESS-PANDA can infer one "
        "network per sample, followed by a group comparison of edge weights. That "
        "statistical comparison is a later analysis step; network inference alone does "
        "not prove causal regulation.\n\n"
        "About how many patients are in each group? Are the cancer and normal samples "
        "paired, and do you already have TF-motif and PPI priors?\n\n"
        "No files were inspected and no analysis ran."
    )


def render_capability_gap(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Explain an unsupported deliverable without promoting a related workflow."""
    if decision.capability_match_status != "unsupported":
        return None
    if "input_artifacts" in decision.mismatch_dimensions:
        question = decision.clarification_question or (
            "Which compatible input bundle can you provide?"
        )
        return _ui_text(
            "The requested result is supported, but no compatible registered "
            "workflow matches the input availability you stated.\n\n"
            f"{question}\n\n"
            "No files were inspected and no analysis ran."
        )
    operation = (
        _OPERATION_VERBS[decision.requested_outcome.operation]
        if decision.requested_outcome
        else "produce"
    )
    lines = [
        f"The registered NetZoo workflows do not {operation} "
        f"{_requested_outcome_phrase(decision)}."
    ]
    alternative = (
        decision.alternative_actions[0] if decision.alternative_actions else None
    )
    spec = policy.workflows.get(alternative) if alternative else None
    if spec is not None:
        lines.append(
            f"{spec.workflow} can instead {spec.output_capability.operation} "
            f"{_capability_phrase(spec, decision)}. Did you mean that supported result?"
        )
    else:
        supported = sorted(
            {
                _artifact_label(item.output_capability.artifact_type)
                for item in policy.workflows.values()
            }
        )
        lines.append("Registered outputs are: " + ", ".join(supported) + ".")
    lines.append("No files were inspected and no analysis ran.")
    return _ui_text("\n\n".join(lines))


def render_sample_specific_coexpression_handoff_boundary(
    task: str,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Explain an unnamed sample-specific co-expression handoff boundary.

    A request may describe the producer output and name an aggregate consumer
    without naming the producer method.  That is still enough to reject the
    direct handoff, but not enough to select one of several producers.  Keep
    this boundary independent of producer selection and derive the consumer
    input contract from the registry.
    """
    if not sample_specific_coexpression_handoff_requested(task):
        return None

    normalized = without_path_tokens(task).casefold()
    consumers = [
        spec
        for spec in policy.workflows.values()
        if spec.output_capability is not None
        and spec.workflow.casefold() in normalized
        and "coexpression_network" in spec.output_capability.input_artifacts
    ]
    if not consumers:
        consumer_phrase = "the requested downstream workflow"
        consumer_spec = None
    else:
        consumer_phrase = ", ".join(spec.workflow for spec in consumers)
        consumer_spec = consumers[0]

    input_field = "coexpression_file"
    accepted_granularities = (
        set(consumer_spec.output_capability.accepted_input_granularities)
        if consumer_spec is not None
        else set()
    )
    if consumer_spec is not None and input_field not in (
        set(consumer_spec.required_inputs) | set(consumer_spec.optional_inputs)
    ):
        input_field = "the registered co-expression input"

    prior_inputs = []
    if consumer_spec is not None:
        prior_inputs = [
            field
            for field in consumer_spec.required_inputs
            if field not in {"expression_file", "coexpression_file", "output_file", "output_dir"}
        ]

    if consumer_spec is None:
        lines = [
            "The first stage requests sample-specific gene-gene co-expression "
            "matrices, but no registered downstream consumer contract was found "
            "for the requested handoff.",
        ]
    else:
        lines = [
            "The first stage requests sample-specific gene-gene co-expression "
            f"matrices, but {consumer_phrase} cannot receive them directly through "
            f"`{input_field}`.",
        ]
    if "aggregate" in accepted_granularities and "sample_specific" not in accepted_granularities:
        lines.append(
            f"The registered {consumer_phrase} input contract accepts an aggregate "
            "gene-by-gene co-expression matrix, not one matrix per sample."
        )
    if prior_inputs:
        lines.append(
            "The downstream workflow also requires these registered prior inputs: "
            + ", ".join(f"`{field}`" for field in prior_inputs)
            + "."
        )
    if re.search(
        r"(?:不要|不做|禁止|without|no).{0,32}"
        r"(?:aggregation|aggregate|sample\s+selection|averag|平均|選樣本|選取樣本)",
        task,
        re.IGNORECASE,
    ):
        lines.append(
            "The request explicitly forbids aggregation or sample selection, "
            "so no valid conversion path remains."
        )
    else:
        lines.append(
            "A separate, explicitly validated aggregation or sample-selection "
            "conversion would be required; it is not inserted automatically."
        )
    lines.extend([
        "No execution is permitted for this direct handoff.",
        "No files were inspected and no analysis ran.",
    ])
    return _ui_text("\n\n".join(lines))


def render_cobra_expression_boundary(task: str) -> str | None:
    """Prevent a scientifically invalid COBRA-output-to-PANDA handoff."""
    normalized = task.casefold()
    if not (
        "cobra" in normalized
        and "panda" in normalized
        and re.search(r"(?:result|output|結果|輸出).{0,80}(?:expression|表現)", normalized)
    ):
        return None
    return _ui_text(
        "COBRA output cannot be used directly as PANDA expression input. "
        "COBRA produces a covariate-associated covariance decomposition plus an "
        "adjusted_coexpression.tsv/.npz "
        "artifact. Pass that labeled gene-by-gene matrix through coexpression_file; "
        "keep the original gene-by-sample expression matrix as PANDA's expression_file "
        "for gene/prior compatibility, together with motif and PPI inputs. The raw "
        "psi/Q/d/g decomposition is not itself a PANDA matrix input.\n\n"
        "No files were inspected and no analysis ran."
    )


def render_unsupported_algorithm_boundary(task: str) -> str | None:
    """Correct method premises that no registered workflow actually satisfies."""
    boundary = unsupported_algorithm_request(task)
    if boundary is None:
        return None
    if boundary == "glasso_bayesian_optimization":
        return _ui_text(
            "No registered netZooPy workflow implements the requested combination "
            "of Graphical Lasso precision-matrix inference and Bayesian Optimization. "
            "DRAGON is the nearest registered precision/partial-correlation workflow, "
            "but it uses covariance shrinkage for one or two omics layers; it is not "
            "Graphical Lasso and does not use Bayesian Optimization or motif/PPI priors. "
            "BONOBO is a conjugate Bayesian sample-specific covariance/co-expression "
            "model; its data-calibrated delta is not Bayesian Optimization, and it "
            "does not estimate an inverse-covariance precision matrix.\n\n"
            "No files were inspected and no analysis ran."
        )
    if boundary == "active_learning_gaussian_process":
        return _ui_text(
            "No registered netZooPy workflow implements active learning with "
            "Gaussian-process sampling over parameter bounds for a sparse, "
            "conditionally independent regulatory network. GIRAFFE and OTTER are the "
            "nearest registered expression/motif/PPI regulatory workflows, but their "
            "iterative optimization is not Gaussian-process Bayesian Optimization. "
            "BONOBO is expression-only sample-specific gene-gene co-expression; it "
            "does not accept motif/PPI priors or produce a TF-gene precision network.\n\n"
            "No files were inspected and no analysis ran."
        )
    return None


def render_registered_handoff_script_guidance(
    task: str,
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Render a script only for a registry-selected direct handoff.

    The request interpretation selects the workflow path. This renderer only
    reads the declared producer/consumer contract and never chooses a method
    from keywords or a hard-coded source/target pair.
    """
    if not _SCRIPT_REQUEST_PATTERN.search(task):
        return None
    actions = preferred_registry_composition_actions(
        task,
        decision,
        policy.workflows,
    )
    if len(actions) != 2:
        return None
    producer, consumer = (policy.workflows.get(action) for action in actions)
    if producer is None or consumer is None:
        return None
    if consumer.action not in producer.output_capability.handoff_targets:
        return None
    workflow_path = f"{producer.workflow} → {consumer.workflow}"
    handoff_fields = handoff_input_fields(
        producer.output_capability.handoff_contract,
        consumer,
    )
    if handoff_fields != ["coexpression_file"]:
        return _ui_text(
            f"The registry declares the **{workflow_path}** artifact handoff, but "
            "it does not declare a script template for the target input contract. "
            "No executable script was generated. Add a typed consumer adapter and "
            "its validation contract before enabling this handoff.\n\n"
            "No files were inspected and no analysis ran."
        )
    artifact_name = next(
        (
            name
            for name in producer.output_files
            if "coexpression" in name and name.endswith(".tsv")
        ),
        None,
    )
    if artifact_name is None or "output_dir" not in producer.required_inputs:
        return _ui_text(
            f"The registry declares the **{workflow_path}** artifact handoff, but "
            "the producer output contract is incomplete for script generation. "
            "No executable script was generated.\n\n"
            "No files were inspected and no analysis ran."
        )
    producer_definition = ACTION_DEFINITIONS[producer.action]
    consumer_definition = ACTION_DEFINITIONS[consumer.action]
    producer_cli = producer_definition.cli_command
    consumer_cli = consumer_definition.handoff_cli_commands.get(handoff_fields[0])
    if producer_cli is None or consumer_cli is None:
        return _ui_text(
            f"The registry declares the **{workflow_path}** artifact handoff, but "
            "no typed executable adapter is registered for that consumer input. "
            "No executable script was generated.\n\n"
            "No files were inspected and no analysis ran."
        )
    return _ui_text(
        f"Use the registry-selected **{workflow_path}** handoff. The producer "
        "creates an adjusted gene-by-gene co-expression artifact; it is not a "
        "corrected expression matrix. The consumer therefore receives the original "
        "expression matrix as `expression_file` and the producer TSV as "
        "`coexpression_file`.\n\n"
        "```bash\n"
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n\n"
        "expression_file=\"path/to/expression.tsv\"   # genes × samples\n"
        "design_file=\"path/to/design.tsv\"           # samples × numeric covariates\n"
        "# One-hot encode categorical batches before writing design_file.\n"
        "motif_file=\"path/to/motif.tsv\"\n"
        "ppi_file=\"path/to/ppi.tsv\"\n"
        "producer_output_dir=\"outputs/producer\"\n"
        "consumer_output_file=\"outputs/regulatory-network.tsv\"\n\n"
        f"# Runs {producer.workflow} and writes its declared handoff artifacts.\n"
        f"docker compose run --rm netzoo {producer_cli} \\\n"
        "  -e \"$expression_file\" -d \"$design_file\" -o \"$producer_output_dir\"\n\n"
        f"coexpression_file=\"$producer_output_dir/{artifact_name}\"\n"
        "# These are existence guards only; they do not validate artifact schema.\n"
        "test -s \"$producer_output_dir/manifest.json\"\n"
        "test -s \"$coexpression_file\"\n\n"
        "# Keeps the original expression input; -c supplies the declared handoff\n"
        "# artifact to the consumer's precomputed-coexpression entry point.\n"
        f"docker compose run --rm netzoo {consumer_cli} \\\n"
        "  -e \"$expression_file\" -m \"$motif_file\" -p \"$ppi_file\" \\\n"
        "  -c \"$coexpression_file\" -o \"$consumer_output_file\"\n"
        "```\n\n"
        "Before execution: expression must be labeled genes × samples; design row "
        "IDs must exactly match expression sample IDs (any row order is aligned), "
        "and all design covariates must be numeric; one-hot encode categorical "
        "batch labels before writing the design file. The producer runner adds an "
        "all-ones intercept when absent, or rejects an invalid intercept when it is "
        "present. The two `test -s` commands "
        "only prove those files are non-empty; confirming a square/symmetric numeric matrix, "
        "identifier compatibility, and downstream gene-axis checks remains the responsibility of the registered "
        "workflow runners and the agent's input-inspection/confirmation lifecycle.\n\n"
        "No files were inspected and no analysis ran."
    )


def render_spec_backed_concept_answer(
    task: str,
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Return registered workflow facts for a basic no-tool purpose question."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and _PURPOSE_PATTERN.search(task)
    ):
        return None
    normalized = without_path_tokens(task).casefold()
    for spec in policy.workflows.values():
        if spec.workflow.casefold() not in normalized:
            continue
        inputs = ", ".join(spec.required_inputs) or "no registered required inputs"
        return _ui_text(
            f"{spec.workflow} {spec.description}\n\n"
            f"Registered required inputs: {inputs}.\n"
            "No files were inspected and no analysis ran."
        )
    return None


def render_registered_workflow_contract_answer(
    task: str,
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Answer a named workflow's contract without re-routing alternatives."""
    if not (decision.in_scope and decision.action == "no_tool"):
        return None
    if not _WORKFLOW_CONTRACT_PATTERN.search(task):
        return None
    action = solely_named_run_action(task)
    if action is None:
        return None
    spec = policy.workflows.get(action)
    if spec is None or spec.output_capability is None:
        return None
    capability = spec.output_capability
    inputs = ", ".join(spec.required_inputs) or "no registered required inputs"
    if capability.artifact_type == "coexpression_network":
        output = (
            "one gene-gene co-expression network per selected sample"
            if "sample_specific" in capability.granularities
            else "a gene-gene co-expression network"
        )
    else:
        output = _capability_phrase(spec, decision)
    lines = [
        f"{spec.workflow}: {spec.description}",
        f"Registered required inputs: {inputs}.",
    ]
    if spec.controls:
        controls = ", ".join(
            f"{control.name} (type={control.control_type}, default={control.default!r})"
            for control in spec.controls
        )
        lines.append(f"Registered workflow controls: {controls}.")
    lines.append(f"Output: {output}.")
    if capability.artifact_type == "coexpression_network":
        lines.append(
            "This is a co-expression result, not a regulatory network (TF/miRNA) "
            "or a covariance-decomposition artifact."
        )
    for conditional in capability.conditional_outputs:
        if not conditional.valid:
            continue
        conditions = " and ".join(
            f"`{name}={value}`" for name, value in conditional.when.items()
        )
        lines.append(f"When {conditions}: {conditional.semantics}.")
    concerns = concern_section_for_workflow(decision, policy, action)
    return _ui_text("\n".join(lines) + (f"\n\n{concerns}" if concerns else "")
                    + "\n\nNo files were inspected and no analysis ran.")


def render_ambiguous_workflow_guidance(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    semantic_goal: dict | None = None,
) -> str | None:
    """Explain multiple registered candidates without inventing a selection."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and len(decision.recommended_actions) > 1
        and (semantic_goal or {}).get("relationship") == "alternatives"
    ):
        return None
    specs = [policy.workflows.get(action) for action in decision.recommended_actions]
    registered = [spec for spec in specs if spec is not None]
    if len(registered) < 2:
        return None
    options = "\n".join(
        line
        for spec in sorted(registered, key=lambda item: item.workflow)
        for line in _candidate_details(spec.action, spec, policy)
    )
    assumptions = _assumptions_block(
        decision,
        "Unconfirmed assumptions in these interpretations (please correct me if needed):",
    )
    sections = [
        "I can match your goal to more than one registered workflow:",
        options,
    ]
    if assumptions:
        sections.append(assumptions)
    sections.append(
        "Which result and modeling premise best matches your experiment? "
        "This answer will narrow the recommendation; no analysis will run yet."
    )
    return _ui_text(
        "\n\n".join(sections)
        + "\n\nNo files were inspected and no analysis ran."
    )


def render_workflow_composition_guidance(
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
    semantic_goal: dict | None = None,
) -> str | None:
    """Explain an ordered, registry-defined workflow composition."""
    if not (
        decision.in_scope
        and decision.action == "no_tool"
        and decision.recommended_actions
    ):
        return None
    specs = [policy.workflows.get(action) for action in decision.recommended_actions]
    registered = [spec for spec in specs if spec is not None]
    if len(registered) < 2:
        return None
    expected_actions = [
        *registered[-1].output_capability.guidance_predecessors,
        registered[-1].action,
    ]
    if list(decision.recommended_actions) != expected_actions:
        return None
    biological_inputs = [
        field_name
        for field_name in registered[-1].required_inputs
        if field_name not in {"output_file", "lioness_output", "output_dir"}
    ]
    input_labels = {
        "expression_file": "Expression matrix",
        "motif_file": "Motif/prior",
        "ppi_file": "PPI network",
        "mirna_file": "miRNA list",
        "coexpression_file": "Adjusted co-expression matrix",
    }
    inputs = "\n".join(
        f"   - `{field_name}`: {input_labels.get(field_name, field_name)}"
        for field_name in biological_inputs
    )
    aggregate, final = registered[0], registered[-1]
    # Only a stated downstream concern brings its notes; the other per-sample
    # reading (Log 219) is always named (Log 283).
    downstream = "\n\n".join(part for part in (
        OTHER_READING_NOTES.get(final.action, ""),
        concern_section_for_workflow(decision, policy, final.action),
    ) if part)
    downstream = f"{downstream}\n\n" if downstream else ""
    requested = decision.requested_outcome
    final_granularities = final.output_capability.granularities
    if (
        requested is not None
        and requested.granularity == "sample_specific"
        and requested.artifact_type == final.output_capability.artifact_type
        and {"aggregate", "sample_specific"}.issubset(final_granularities)
        and "output_file" in final.required_inputs
        and "lioness_output" in final.required_inputs
    ):
        return _ui_text(
            f"For the sample-specific output you described, use **{final.workflow}**.\n\n"
            f"Required inputs:\n{inputs}\n\n"
            "Outputs:\n"
            "   - Aggregate network (`output_file`).\n"
            "   - Sample-specific network for each patient/sample (`lioness_output`).\n\n"
            f"You do not need to run **{aggregate.workflow}** separately; "
            f"**{final.workflow}** also produces the aggregate output. Use "
            f"**{aggregate.workflow}** alone only when a cohort-level aggregate "
            "result is sufficient.\n\n"
            f"{downstream}"
            "No files were inspected and no analysis ran."
        )
    return _ui_text(
        "I matched your goal to an aggregate and a sample-specific workflow. "
        "They use the same biological inputs:\n\n"
        f"1. **{aggregate.workflow}**\n"
        "   - **Inputs**:\n"
        f"{inputs}\n"
        "   - **Output**: Aggregate workflow output (`output_file`).\n\n"
        f"2. **{final.workflow}**\n"
        "   - **Inputs**:\n"
        f"{inputs}\n"
        "   - **Outputs**:\n"
        "     - Aggregate workflow output (`output_file`).\n"
        "     - Sample-specific LIONESS output (`lioness_output`).\n\n"
        f"Use {aggregate.workflow} when you only need the aggregate result. "
        f"Use {final.workflow} directly when you need the sample-specific result; "
        "it also produces its aggregate output, so running the aggregate workflow "
        "first is unnecessary.\n\n"
        f"{downstream}"
        "No files were inspected and no analysis ran."
    )


def render_recovered_workflow_guidance(
    task: str,
    decision: TaskDecision,
    policy: ProjectPolicySnapshot,
) -> str | None:
    """Compatibility entry point; provenance is typed, never parsed from prose."""
    from .verified_guidance import guidance_contract, render_verified_guidance

    if decision.capability_match_status != "fallback":
        return None
    return render_verified_guidance(decision, guidance_contract(decision, policy, task))


__all__ = [
    "render_ambiguous_workflow_guidance",
    "render_capability_gap",
    "render_sample_specific_coexpression_handoff_boundary",
    "render_cobra_expression_boundary",
    "render_unsupported_algorithm_boundary",
    "render_registered_handoff_script_guidance",
    "render_outcome_clarification",
    "render_recovered_workflow_guidance",
    "render_spec_backed_concept_answer",
    "render_registered_workflow_contract_answer",
    "render_workflow_composition_guidance",
]
