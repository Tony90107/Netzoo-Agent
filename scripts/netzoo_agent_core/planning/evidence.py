"""Ordered workflow-input evidence construction."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .context import _PlanningContext
from ..data.bonobo import bonobo_artifact_paths, load_bonobo_inputs
from ..data.bundles import MULTI_FILE_ACTIONS, discover_bundle_candidates
from ..data.content_mapping import detect_role_mismatches, infer_input_roles
from ..data.gene_repair_hints import suggest_gene_corrections
from ..data.gene_validation import UNRECOGNIZED_PHRASE
from ..data.preflight import validate_workflow_inputs
from ..contracts import InputEvidence, OUTPUT_ROLE_FIELDS, PROJECT_ROOT, _is_demo_request
from ..interpretation import (
    _candidate_keywords,
    _choose_unambiguous_candidate,
    _mentions_unspecified_data_directory,
    _task_path,
    _unlabeled_input_bindings,
    discover_demo_bundle,
    reusable_episode_inputs,
)
from ..routing import (
    _default_lioness_outputs,
    _default_network_output,
    _find_candidate_files,
)
from ..data.paths import _resolve_user_path

__all__: list[str] = []

_FILE_INPUT_FIELDS = frozenset(
    {
        "expression_file",
        "design_file",
        "motif_file",
        "ppi_file",
        "mirna_file",
        "coexpression_file",
        "network_file",
        "mutation_file",
        "exon_size_file",
        "cancer_gene_file",
        "pathway_file",
        "omics_layer_1",
        "omics_layer_2",
    }
)


def _apply_bonobo_parameter_bindings(context: _PlanningContext) -> None:
    """Parse only explicit BONOBO parameter assignments from the user text.

    In particular, numeric-looking sample names remain strings and are checked
    against the expression header; they are never reinterpreted as positions.
    """
    if context.action != "run_bonobo":
        return
    task = context.task
    decision = context.decision
    match = re.search(
        r"(?:sample_names?|samples?)\s*=\s*([^;\n]+)", task, flags=re.IGNORECASE
    )
    if match:
        raw = match.group(1).strip().split()[0].rstrip(",")
        names = [item.strip() for item in raw.split(",") if item.strip()]
        if names:
            decision.sample_names = names
    else:
        # Natural-language sample selection is a parameter binding too. Keep
        # this deliberately narrow: only identifiers containing a letter and
        # a digit are collected, so a cohort size such as "20 samples" cannot
        # become a sample name. Validation against the expression header still
        # happens in the Bonobo preflight/executor path.
        selection = re.search(
            r"(?:只|僅)?(?:分析|處理|查看|選擇|選用)"
            r"(?P<zh>[^,.;。！？!?；\n]{1,100})|"
            r"(?:analy[sz]e|process|inspect|use)\s+(?:only\s+)?"
            r"(?P<en>[^,.;。！？!?；\n]{1,100})",
            task,
            flags=re.IGNORECASE,
        )
        if selection:
            candidate_text = selection.group("zh") or selection.group("en") or ""
            names = re.findall(
                r"(?<![A-Za-z0-9_-])[A-Za-z][A-Za-z0-9_-]*\d[A-Za-z0-9_-]*(?![A-Za-z0-9_-])",
                candidate_text,
            )
            if names:
                decision.sample_names = list(dict.fromkeys(names))
    format_match = re.search(
        r"(?:bonobo[_ -]?output[_ -]?format|output[_ -]?format)\s*=\s*(\.?h5|\.?hdf|\.?txt|\.?csv)",
        task,
        flags=re.IGNORECASE,
    )
    if format_match:
        value = format_match.group(1).casefold()
        decision.bonobo_output_format = value if value.startswith(".") else "." + value
    for field_name in ("sparsify", "save_pvals", "keep_in_memory", "log_transformed", "centered"):
        match = re.search(
            rf"{field_name}\s*=\s*(true|false)", task, flags=re.IGNORECASE
        )
        if match:
            setattr(decision, field_name, match.group(1).casefold() == "true")
    for field_name, decision_field in (("confidence", "bonobo_confidence"), ("delta", "delta")):
        match = re.search(rf"{field_name}\s*=\s*([0-9]*\.?[0-9]+)", task, flags=re.IGNORECASE)
        if match:
            setattr(decision, decision_field, float(match.group(1)))
    match = re.search(r"precision\s*=\s*(single|double)", task, flags=re.IGNORECASE)
    if match:
        decision.precision = match.group(1).casefold()


def _cobra_unlabeled_input_paths(task: str) -> tuple[str | None, str | None]:
    """Bind COBRA's two ordered table paths in natural-language requests."""
    if "cobra" not in task.casefold():
        return None, None
    paths = re.findall(
        r"(?<![A-Za-z0-9_.-])([A-Za-z0-9_./-]+\.(?:tsv|tab|csv|txt))(?![A-Za-z0-9_.-])",
        task,
        flags=re.IGNORECASE,
    )
    return (paths[0], paths[1]) if len(paths) >= 2 else (None, None)


_TABLE_SUFFIXES = (
    ".tsv", ".tab", ".txt", ".csv", ".gmt", ".npy", ".npz", ".bed", ".mtx",
    ".h5", ".hdf5", ".gz",
)
# A path-like token with at least one separator and no file suffix. Used only to
# recognize a directory the user typed; nothing here proposes a path.
_TASK_DIRECTORY_RE = re.compile(
    r"(?<![A-Za-z0-9_.~/-])(?P<path>[A-Za-z0-9_.~-]+(?:/[A-Za-z0-9_.~-]+)+/?)"
)


def _task_directory(task: str) -> Path | None:
    """Return the one existing directory the request names, if it names one.

    A request that says which folder holds its data ("用 data/case-1 裡的三個
    檔案") previously anchored discovery at the project data root instead,
    which scanned every dataset directory and could settle on an unrelated one.
    Two named directories are ambiguous, so neither is used.
    """
    found: list[Path] = []
    for match in _TASK_DIRECTORY_RE.finditer(task):
        token = match.group("path").rstrip("/")
        if "/" not in token or token.casefold().endswith(_TABLE_SUFFIXES):
            continue
        try:
            candidate = _resolve_user_path(token).resolve()
        except (OSError, RuntimeError, ValueError):
            continue
        if candidate.is_dir() and not candidate.is_symlink() and candidate not in found:
            found.append(candidate)
    return found[0] if len(found) == 1 else None


def _build_evidence_ledger(context: _PlanningContext) -> list[InputEvidence]:
    decision = context.decision
    task = context.task
    profile_model = context.profile
    episode_models = context.episodes
    action = context.action
    required = context.required
    _apply_bonobo_parameter_bindings(context)
    if action == "run_dragon" and re.search(
        r"(?:omics[_ -]?layer[_ -]?3|layer\s*3|three\s+omics|3\s+omics|三種|三層|三個.*omics)",
        task,
        flags=re.IGNORECASE,
    ):
        context.preflight_errors.append(
            "DRAGON accepts exactly two omics layers; choose the two layers for this run. "
            "A pairwise/chained workflow is not enabled without an explicit conversion contract."
        )
    input_fields = [
        field_name
        for field_name in required
        if field_name not in {"output_file", "lioness_output", "output_dir"}
    ]
    optional_file_fields = [
        field_name
        for field_name in (context.workflow_spec.optional_inputs if context.workflow_spec else ())
        if field_name in _FILE_INPUT_FIELDS
        and (getattr(decision, field_name, None) or _task_path(task, field_name))
    ]
    input_fields.extend(
        field_name for field_name in optional_file_fields if field_name not in input_fields
    )
    if action == "run_otter":
        otter_sources = {
            field_name
            for field_name in ("expression_file", "coexpression_file")
            if getattr(decision, field_name, None) or _task_path(task, field_name)
        }
        if not otter_sources:
            # OTTER has a conditional source contract: expression_file is required
            # when C is computed, otherwise coexpression_file is required.
            input_fields.append("expression_file")
        else:
            input_fields.extend(
                field_name
                for field_name in otter_sources
                if field_name not in input_fields
            )
    evidence_fields = [
        *required,
        *[field_name for field_name in input_fields if field_name not in required],
    ]
    natural_bindings = _unlabeled_input_bindings(task, input_fields)
    confirmed_bindings = {
        field_name: value
        for field_name, value in re.findall(
            r"CONFIRMED_INPUT_([a-z_]+)=([^\s;]+)", task, flags=re.IGNORECASE
        )
        if field_name in input_fields
    }
    corrected_bindings = {
        field_name: value
        for field_name, value in re.findall(
            r"CORRECTED_INPUT_([a-z_]+)=([^\s;]+)", task, flags=re.IGNORECASE
        )
        if field_name in input_fields
    }
    labeled_bindings = {
        field_name
        for field_name in input_fields
        if _task_path(task, field_name)
    }
    protected_bindings = (
        set(natural_bindings)
        | labeled_bindings
        | set(confirmed_bindings)
        | set(corrected_bindings)
    )
    # Only inspect a directory explicitly named by the user. Router-proposed paths
    # are untrusted and must not steer content discovery into an unrelated folder.
    expression_hint = _task_path(task, "expression_file") or _task_path(task, "omics_layer_1")
    content_nearby = (
        _resolve_user_path(expression_hint).parent
        if expression_hint
        else _task_directory(task) or PROJECT_ROOT / "data"
    )
    content_bindings = infer_input_roles(
        action,
        task,
        [field_name for field_name in input_fields if field_name not in protected_bindings],
        content_nearby,
        context.content_mapper,
    )
    inferred_input_values: set[str] = set()
    explicit_input_values: dict[str, str] = {}
    selected_fields = set(
        re.findall(r"SELECTED_FIELD=([a-z_]+)", task, flags=re.IGNORECASE)
    )
    carried_discovered_fields = set(
        re.findall(
            r"CARRIED_DISCOVERED_FIELD=([a-z_]+)",
            task,
            flags=re.IGNORECASE,
        )
    )
    cobra_expression, cobra_design = _cobra_unlabeled_input_paths(task)
    for field_name in input_fields:
        labeled = _task_path(task, field_name)
        parsed = (
            confirmed_bindings.get(field_name)
            or corrected_bindings.get(field_name)
            or labeled
            or natural_bindings.get(field_name)
            or (
                content_bindings[field_name].path
                if field_name in content_bindings
                else None
            )
            or (
                cobra_expression
                if action == "run_cobra" and field_name == "expression_file"
                else cobra_design
                if action == "run_cobra" and field_name == "design_file"
                else None
            )
        )
        routed = getattr(decision, field_name, None)
        if parsed:
            setattr(decision, field_name, parsed)
            if (
                field_name not in carried_discovered_fields
                and field_name not in natural_bindings
                and field_name not in content_bindings
            ):
                explicit_input_values[field_name] = parsed
            if (
                field_name in (set(natural_bindings) | set(content_bindings))
                and not labeled
                and field_name not in confirmed_bindings
                and field_name not in corrected_bindings
            ):
                inferred_input_values.add(field_name)
        elif routed and str(routed) in task:
            explicit_input_values[field_name] = str(routed)
        elif routed:
            # Router-produced paths are untrusted unless the literal path appears
            # in the user's request. Otherwise the Planner would present a guessed
            # workspace file as "provided".
            setattr(decision, field_name, None)

    for field_name in evidence_fields:
        if field_name not in OUTPUT_ROLE_FIELDS:
            continue
        routed = getattr(decision, field_name, None)
        parsed = _task_path(task, field_name)
        if parsed:
            setattr(decision, field_name, parsed)
        elif routed and str(routed) not in task:
            setattr(decision, field_name, None)

    autonomous_values: dict[str, str] = {}
    autonomous_reasons: dict[str, str] = {}
    autonomous_sources: dict[str, str] = {}
    autonomous_bundle_ids: dict[str, str] = {}
    bundle_choices_by_field: dict[str, list[str]] = {}
    bundle_choice_ids: list[str] = []
    partial_bundle_selected = False
    for field_name in carried_discovered_fields:
        value = _task_path(task, field_name)
        if not value:
            continue
        setattr(decision, field_name, value)
        autonomous_values[field_name] = value
        autonomous_reasons[field_name] = (
            "Carried forward from the coherent bundle shown in the prior clarification."
        )
        autonomous_sources[field_name] = "discovered"
        autonomous_bundle_ids[field_name] = (
            f"directory:{_resolve_user_path(value).parent.resolve()}"
        )
    if profile_model.preferences.get("reuse_last_inputs") is True:
        reused = reusable_episode_inputs(action, episode_models)
        if reused:
            reused_values, reason = reused
            for field_name, value in reused_values.items():
                if field_name not in explicit_input_values:
                    setattr(decision, field_name, value)
                    autonomous_values[field_name] = value
                    autonomous_reasons[field_name] = reason
                    autonomous_sources[field_name] = "discovered"
                    autonomous_bundle_ids[field_name] = f"reused:{reason}"
    if (
        _is_demo_request(task)
        and not _mentions_unspecified_data_directory(task)
        and profile_model.preferences.get("allow_demo_autofill", True) is not False
        and not explicit_input_values
        and not autonomous_values
        and not inferred_input_values
        and not protected_bindings
    ):
        bundle = discover_demo_bundle(action)
        if bundle:
            bundle_values, reason = bundle
            for field_name, value in bundle_values.items():
                # A validated coherent bundle outranks ungrounded paths proposed by
                # the language-model router. Literal user paths were handled above.
                setattr(decision, field_name, value)
                autonomous_values[field_name] = value
                autonomous_reasons[field_name] = reason
                autonomous_sources[field_name] = "demo_bundle"
            if action == "run_bonobo":
                # The checked-in BONOBO toy fixture is intentionally already
                # log-transformed and centered; keep those declarations explicit
                # in the demo plan so preflight does not infer them for user data.
                decision.log_transformed = True
                decision.centered = True
    # Outputs are safe and reversible defaults; input datasets require evidence.
    expression_hint = decision.expression_file or _task_path(task, "expression_file")
    if expression_hint:
        nearby = _resolve_user_path(expression_hint).parent
    else:
        nearby = _task_directory(task) or PROJECT_ROOT / "data"

    if action in MULTI_FILE_ACTIONS and not autonomous_values:
        discovery_anchors = {
            **explicit_input_values,
            **natural_bindings,
            **{
                field_name: assignment.path
                for field_name, assignment in content_bindings.items()
            },
        }
        candidates = discover_bundle_candidates(action, nearby, discovery_anchors)
        bundles = [item for item in candidates if not item.missing_fields]
        bundle = bundles[0] if len(bundles) == 1 else None
        if bundle is not None:
            for field_name, value in bundle.values.items():
                if (
                    field_name in explicit_input_values
                    or field_name in natural_bindings
                    or field_name in content_bindings
                ):
                    continue
                setattr(decision, field_name, value)
                autonomous_values[field_name] = value
                autonomous_reasons[field_name] = bundle.reason
                autonomous_sources[field_name] = "discovered"
                autonomous_bundle_ids[field_name] = bundle.bundle_id
        elif len(bundles) > 1:
            bundle_choice_ids = [item.bundle_id for item in bundles]
            bundle_choices_by_field = {
                field_name: [
                    item.values[field_name]
                    for item in bundles
                    if item.values.get(field_name)
                ]
                for field_name in input_fields
            }
        elif candidates:
            most_complete = max(len(item.values) for item in candidates)
            best_partials = [
                item for item in candidates if len(item.values) == most_complete
            ]
            if len(best_partials) == 1:
                partial = best_partials[0]
                partial_bundle_selected = True
                for field_name, value in partial.values.items():
                    if (
                        field_name in explicit_input_values
                        or field_name in natural_bindings
                        or field_name in content_bindings
                    ):
                        continue
                    setattr(decision, field_name, value)
                    autonomous_values[field_name] = value
                    autonomous_reasons[field_name] = partial.reason
                    autonomous_sources[field_name] = "discovered"
                    autonomous_bundle_ids[field_name] = partial.bundle_id

    default_output_dir = str(
        profile_model.preferences.get("default_output_dir", "outputs/demo")
    )
    evidence: list[InputEvidence] = []
    evidence_input_fields = [
        *input_fields,
        *[
            field_name
            for field_name in required
            if field_name in OUTPUT_ROLE_FIELDS
        ],
    ]
    for field_name in evidence_input_fields:
        value = getattr(decision, field_name) or _task_path(task, field_name)
        if value:
            setattr(decision, field_name, value)
            status = (
                autonomous_sources[field_name]
                if field_name in autonomous_values
                else "selected"
                if field_name in selected_fields
                else "discovered"
                if field_name in inferred_input_values
                else "provided"
            )
            content_assignment = content_bindings.get(field_name)
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status=status,
                    value=value,
                    reason=(
                        autonomous_reasons[field_name]
                        if field_name in autonomous_values
                        else (
                            (
                                "Role inferred from file contents by the LLM "
                                f"(confidence {content_assignment.confidence:.2f}). "
                                f"{content_assignment.rationale} Awaiting user confirmation."
                            )
                            if content_assignment is not None
                            else (
                                "Role inferred from the filename and awaiting content "
                                "compatibility confirmation."
                                if field_name in inferred_input_values
                                else "Explicitly provided by the user or the intent parser."
                            )
                        )
                    ),
                    bundle_id=autonomous_bundle_ids.get(field_name),
                )
            )
            continue

        if field_name in {"output_file", "lioness_output"}:
            seed = decision.expression_file or "expression.tsv"
            if "lioness" in action:
                aggregate, sample_specific = _default_lioness_outputs(
                    (
                        "puma"
                        if "puma" in action
                        else "panda"
                        if "panda" in action
                        else "coexpression"
                    ),
                    seed,
                    default_output_dir,
                )
                value = aggregate if field_name == "output_file" else sample_specific
            else:
                value = _default_network_output(
                    "puma"
                    if "puma" in action
                    else "otter"
                    if action == "run_otter"
                    else "panda",
                    seed,
                    default_output_dir,
                )
            setattr(decision, field_name, value)
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="defaulted",
                    value=value,
                    reason="The output location is reversible and does not overwrite an input, so the Planner used the project default.",
                )
            )
            continue
        if field_name == "output_dir" and action in {"run_condor", "run_cobra", "run_sambar", "run_bonobo"}:
            value = default_output_dir
            decision.output_dir = value
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="defaulted",
                    value=value,
                    reason=f"The Planner used the default {action.removeprefix('run_').upper()} output directory.",
                )
            )
            continue

        keywords = _candidate_keywords(action, field_name)
        candidates = _find_candidate_files(keywords, nearby) if keywords else []
        if partial_bundle_selected:
            candidates = []
        if bundle_choices_by_field.get(field_name):
            candidates = bundle_choices_by_field[field_name]
        if action in MULTI_FILE_ACTIONS:
            selected = None
            reason = (
                "Multiple complete validated input bundles are available; "
                "choose one before execution."
                if bundle_choices_by_field
                else "No single complete validated dataset bundle contains every "
                "remaining required input."
            )
        else:
            selected, reason = _choose_unambiguous_candidate(
                candidates,
                keywords,
                nearby,
            )
        if selected:
            setattr(decision, field_name, selected)
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="discovered",
                    value=selected,
                    reason=reason,
                    candidates=candidates[:5],
                )
            )
        else:
            evidence.append(
                InputEvidence(
                    field=field_name,
                    status="missing",
                    reason=reason,
                    candidates=candidates[:5],
                    candidate_bundle_ids=(
                        bundle_choice_ids[:5]
                        if bundle_choices_by_field.get(field_name)
                        else []
                    ),
                )
            )

    if action == "run_dragon":
        layer_items = [
            item for item in evidence
            if item.field in {"omics_layer_1", "omics_layer_2"}
        ]
        if any(item.status == "missing" for item in layer_items):
            # A single auto-discovered layer is not a usable DRAGON input pair.
            # Keep explicitly supplied paths visible, but ask for both when the
            # other half was only an ungrounded workspace discovery.
            for item in layer_items:
                if item.status in {"discovered", "demo_bundle"}:
                    item.status = "missing"
                    item.value = None
                    item.reason = (
                        "DRAGON requires both omics layers; this candidate was not "
                        "selected without a complete two-layer pair."
                    )
                    setattr(decision, item.field, None)

    if all(getattr(decision, field_name, None) for field_name in input_fields):
        context.preflight_errors[:] = list(dict.fromkeys(
            [*context.preflight_errors, *validate_workflow_inputs(action, decision)]
        ))
        if context.preflight_errors:
            corrections = _role_corrections(
                action, decision, input_fields, context.content_mapper
            )
            if corrections and _apply_role_corrections(
                action, decision, corrections
            ):
                # The files were right and only their roles were crossed. The
                # corrected assignment now passes, so offer it for confirmation
                # instead of handing back an error the user has to translate.
                context.preflight_errors.clear()
                context.role_corrections.update(corrections)
                for field_name, value in corrections.items():
                    explicit_input_values.pop(field_name, None)
                    natural_bindings[field_name] = value
                    for item in evidence:
                        if item.field != field_name:
                            continue
                        item.value = value
                        item.status = "discovered"
                        item.reason = (
                            "Role read from the file contents after the filename "
                            "reading failed input validation. Awaiting user "
                            "confirmation."
                        )
            else:
                context.role_mismatch_hints[:] = _render_role_hints(
                    decision, corrections
                )
                context.gene_repair_hints[:] = _gene_repair_hints(
                    context.preflight_errors,
                    getattr(decision, "taxon", "") or "",
                    context.content_mapper,
                )
    handoff = context.workflow_handoff
    if (
        action == "run_bonobo"
        and handoff is not None
        and handoff.status == "validated"
        and not context.preflight_errors
        and decision.expression_file
        and decision.output_dir
    ):
        try:
            bundle = load_bonobo_inputs(
                decision.expression_file,
                decision.sample_names,
                genes_axis=decision.genes_axis,
                log_transformed=decision.log_transformed,
                centered=decision.centered,
            )
            paths = bonobo_artifact_paths(
                decision.output_dir,
                bundle.selected_sample_ids,
                decision.bonobo_output_format,
                save_pvals=decision.save_pvals,
            )
            artifact_paths = {
                "coexpression_network": [str(path) for path in paths["networks"]],
            }
            if decision.save_pvals:
                artifact_paths["pvalue_matrix"] = [
                    str(path) for path in paths["pvalues"]
                ]
            context.workflow_handoff = handoff.model_copy(
                update={
                    "sample_ids": list(bundle.selected_sample_ids),
                    "gene_ids": list(bundle.gene_ids),
                    "source_artifact_paths": artifact_paths["coexpression_network"],
                    "artifact_paths": artifact_paths,
                }
            )
        except (OSError, TypeError, ValueError) as error:
            context.preflight_errors.append(
                f"BONOBO handoff identity could not be validated: {error}"
            )
    return evidence


def _role_corrections(
    action: str,
    decision: Any,
    input_fields: list[str],
    mapper: Any | None,
) -> dict[str, str]:
    """Read the supplied files by content when validation has already failed.

    Only reached once validation failed, so the extra content read is never on
    the path of a run that is going to succeed.
    """
    bindings = {
        field_name: str(getattr(decision, field_name, None) or "")
        for field_name in input_fields
        if getattr(decision, field_name, None)
    }
    return detect_role_mismatches(action, bindings, mapper)


def _apply_role_corrections(
    action: str,
    decision: Any,
    corrections: dict[str, str],
) -> bool:
    """Try the corrected assignment, and keep it only if it actually validates.

    Reporting a crossed pair without acting on it leaves the user to retype
    paths the agent already worked out. Acting on it without revalidating would
    trade one wrong assignment for another, so the correction has to earn its
    place: it is kept only when the workflow's own validator accepts it, and it
    still reaches the user as a confirmation rather than as a decision.
    """
    previous = {
        field_name: getattr(decision, field_name, None) for field_name in corrections
    }
    for field_name, value in corrections.items():
        setattr(decision, field_name, value)
    if not validate_workflow_inputs(action, decision):
        return True
    for field_name, value in previous.items():
        setattr(decision, field_name, value)
    return False


def _render_role_hints(decision: Any, corrections: dict[str, str]) -> list[str]:
    """Report a crossed pair the corrected assignment could not resolve."""
    return [
        f"{field_name}: {_resolve_user_path(str(getattr(decision, field_name, '')))}"
        f" does not match this role; {path} does"
        for field_name, path in sorted(corrections.items())
    ]


def _unrecognized_labels(errors: list[str]) -> list[str]:
    """Read back the labels the authority rejected, from the shared phrase."""
    labels: list[str] = []
    for error in errors:
        _, separator, listed = error.partition(UNRECOGNIZED_PHRASE)
        if not separator:
            continue
        labels.extend(
            value.strip() for value in listed.split(",") if value.strip()
        )
    return list(dict.fromkeys(labels))


def _gene_repair_hints(
    preflight_errors: list[str],
    taxon: str,
    mapper: Any | None,
) -> list[str]:
    """Explain what a rejected label was probably meant to be.

    Advisory only, and only on a path that has already failed. A proposed
    symbol appears solely when the gene authority confirms it exists.
    """
    labels = _unrecognized_labels(preflight_errors)
    if not labels:
        return []
    return [
        (
            f"{label}: probably {symbol}. {reason}".strip()
            if symbol
            else f"{label}: {reason}"
        )
        for label, symbol, reason in suggest_gene_corrections(labels, taxon, mapper)
    ]
