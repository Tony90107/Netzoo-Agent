"""The capability check: what the request asks for, and which sheet entry gives it (Log 387).

Log 385: routing quoted the wanted result correctly 42 times in 45, then had
to name it with the nearest artifact of a vocabulary that has no "none of
these", so pseudotime, splicing and spatial deconvolution became TF networks.
Here the model reads the request sentence by sentence, quotes each thing it
asks for, and lists the capability-sheet entries that give it -- an empty list
is a normal answer. Entry ids are enums of the sheet, so none can be invented;
quotes and sentence coverage are checked in code
(`interpretation.capability_check`).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, create_model, field_validator

from ..capability_sheet import not_produced_ids, produces_ids
from .request_facts import FactConflict, RequestFact
from .strict_schema import strict_json_schema

__all__ = ["APPROVING_RUN_VERDICTS", "CONDITIONS", "CapabilityCheck", "CheckedRequirement", "MAX_SENTENCES",
           "RequirementKind", "RunVerdict", "RunVerdictName",
           "SecondOpinionAnswer", "condition_check_model", "conditions_model", "proposal_model", "proposal_sentences",
           "reading_version", "reread_as_proposal", "reread_model", "schema_version", "second_opinion_model",
           "unstated_conditions"]

RequirementKind = Literal["result", "about_methods", "context"]
SentenceRole = Literal["background", "asks", "methods_question", "mixed"]


MAX_SENTENCES = 12
"""Sentences after the twelfth are not read; the coverage check lists them as not checked."""


@lru_cache(maxsize=4)
def _method_fields(compact: bool = False, described: bool = True) -> dict[str, Any]:
    """M1 (2026-10-14): the method, settings and data size an ask states, as typed values with their words.

    Final acceptance a24b: OTTER "with an L1 sparsity penalty of 0.1", GIRAFFE with "its regularisation lambda",
    "the TIGER Bayesian model", "one OTTER network per sample, LIONESS-style", "exactly two RNA-seq samples" and
    "20,000 genes and 800 proteins for our 300 patients" were all read, but only as context or as a requirement
    beside the ask, so the result was credited to the workflow that cannot run it that way. Names are enums of
    the registry (`workflow_conditions`); code keeps a value only when its words are in the request and judges it.
    The defaults read recordings from before M1, which state none of these.

    `described` False (ROUND-05, reading shape 3): a setting's name points to the description given once for the
    request's settings instead of repeating it. The provider's schema inlines every reference, so the ~3.8k-character
    list of what each setting does was sent once per sentence, once per open-choice option and once for the request
    (3 copies for a one-sentence request, 14 for twelve).
    """
    from ..method_names import UNREGISTERED, method_names, setting_meanings, setting_names

    # Compact (M2, live m2b P30): the backup model's provider takes at most 1,000 enum values per schema, counted
    # for every sentence; names are then strings, and code reads any name not registered as unregistered.
    method = str if compact else Literal[(*method_names(), UNREGISTERED, "none")]  # type: ignore[valid-type]
    setting = create_model(
        "StatedSetting", __config__=ConfigDict(extra="forbid"),
        name=(str if compact else Literal[(*setting_names(), UNREGISTERED)], Field(description=(  # type: ignore
            "The registered setting the words set, as WORKFLOW.setting; unregistered when none of these is it. "
            + ("What each registered setting does (the registry's own description): " + " | ".join(setting_meanings())
               if described else "What each registered setting does is described under conditions.settings.")))),
        quote=(str, Field(description="Exact words of the request naming the setting.")),
        value_quote=(str, Field(description="Exact words of the request giving its value; empty when none is given.")))
    count = create_model(
        "StatedCount", __config__=ConfigDict(extra="forbid"),
        count=(int, Field(description="The number the words state.")),
        quote=(str, Field(description="Exact words of the request stating it.")))
    addition = create_model(
        "Addition", __config__=ConfigDict(extra="forbid"),
        quote=(str, Field(description="Exact words of the request that add it.")),
        adds=(Literal["omics_layer", "regulator_class", "group_overlap", "other"], Field(description=(
            "What it adds: a further omics layer, a further class of regulators, letting items belong to several "
            "groups, or anything else."))))
    return {
        # M2 (a24b MX03, MX09): "a DRAGON network between the proteome and the transcriptome ..., and please fold the
        # metabolome ... into the same model as a third layer" was one ask of three layers, so the two-layer network
        # was refused with the third; the additions are typed with their words, and code reads the result without them.
        "adds": (list[addition], Field(default_factory=list, description=(
            "Words in this ask that add something to a result the same ask also names on its own -- one item per "
            "addition; empty when the ask names one result as a whole."))),
        "named_method": (method, Field(default="none", description=(
            "The method the request names for this result: a registered workflow, or LIONESS for any LIONESS "
            "version; unregistered when it names a method, model or variant not in this list (including a LIONESS "
            "version of a workflow that has none here); none when it names no method."
            + (f" Registered: {', '.join(method_names())}." if compact else "")))),
        "named_method_quote": (str, Field(default="", description=(
            "Exact words of the request naming the method; empty when none is named."))),
        "settings": (list[setting], Field(default_factory=list, description=(
            "Each setting of the method the request gives for this result -- a parameter, penalty, threshold, "
            "precision, output format or hardware -- one item per setting; empty when it gives none. Not the input "
            "data."))),
        "sample_count": (int | None, Field(default=None, description=(
            "How many samples, patients or profiles the request says the data for this result has; null when it "
            "does not say."))),
        "sample_count_quote": (str, Field(default="", description=(
            "Exact words of the request stating that number; empty when it is null."))),
        "feature_counts": (list[count], Field(default_factory=list, description=(
            "Each number of genes, proteins or other features the request says the data for this result has, one "
            "item per data type; empty when none is stated."))),
    }


def schema_version() -> int:
    """ROUND-04 (collab/ROUND-04-PLAN.md): the reading shape the check asks for. 1: counts and settings on every ask
    and again for the request. 2: once, for the request, each with the asked results it applies to. Set by
    NETZOO_CHECK_SCHEMA; 1 until the user accepts another. 3 (ROUND-05): shape 1, but an ask's settings point to the
    request's description of each setting rather than repeating it (ROUND-04: shape 2 was not adopted)."""
    return {"2": 2, "3": 3}.get(os.environ.get("NETZOO_CHECK_SCHEMA", "1").strip(), 1)


_ASK_METHOD_FIELDS_V2 = ("adds", "named_method", "named_method_quote")
"""ROUND-04: what an ask still says of its method in shape 2 -- the counts and settings are the request's."""


@lru_cache(maxsize=2)
def _scoped_fields(compact: bool = False) -> dict[str, Any]:
    """ROUND-04, shape 2: the request's counts and settings, each once, with the asked results it applies to.

    ROUND-03 (979 recorded readings): 94% of the counts and settings an ask wrote repeated the request's own; the
    rest were another cohort's or group's ("30 ALS and 30 control"), or a setting written into one result only
    (h3 L10: the lambdas held for the second result, not the DRAGON network). `applies_to` reads as the unknown
    facts' does.
    """
    from ..method_names import UNREGISTERED, setting_meanings, setting_names

    applies = (list[str] | None, Field(description=(
        "Exact quotes of the asked-for results this applies to, each as quoted in its ask; [] when it concerns no "
        "asked-for result (another dataset, a later step); null only when it applies to every asked-for result.")))
    setting = create_model(
        "ScopedSetting", __config__=ConfigDict(extra="forbid"),
        name=(str if compact else Literal[(*setting_names(), UNREGISTERED)], Field(description=(  # type: ignore
            "The registered setting the words set, as WORKFLOW.setting; unregistered when none of these is it. "
            "What each registered setting does (the registry's own description): "
            + " | ".join(setting_meanings())))),
        quote=(str, Field(description="Exact words of the request naming the setting.")),
        value_quote=(str, Field(description="Exact words of the request giving its value; empty when none is given.")),
        applies_to=applies)
    samples = create_model(
        "ScopedSamples", __config__=ConfigDict(extra="forbid"),
        count=(int, Field(description="The number of samples, patients or profiles the words state.")),
        quote=(str, Field(description="Exact words of the request stating it.")),
        applies_to=applies)
    features = create_model(
        "ScopedFeatures", __config__=ConfigDict(extra="forbid"),
        count=(int, Field(description="The number of genes, proteins or other features the words state.")),
        quote=(str, Field(description="Exact words of the request stating it.")),
        belongs_to=(str, Field(description=(
            "Exact words of the request naming the data type or file it counts (e.g. \"RNA-seq\", \"cpg_85.csv\"); "
            "empty when the request does not say."))),
        applies_to=applies)
    return {
        "settings": (list[setting], Field(default_factory=list, description=(
            "Each setting of a method the request gives anywhere -- a parameter, penalty, threshold, precision, "
            "output format or hardware -- one item per setting; empty when it gives none. Not the input data."))),
        "sample_counts": (list[samples], Field(default_factory=list, description=(
            "Each number of samples, patients or profiles the request states, one item per group or cohort it "
            "counts; empty when none is stated. Not candidates the user cannot choose between."))),
        "feature_counts": (list[features], Field(default_factory=list, description=(
            "Each number of genes, proteins or other features the request states, one item per data type; empty "
            "when none is stated. Not candidates the user cannot choose between."))),
    }


@lru_cache(maxsize=4)
def _ask_model(compact: bool = False, version: int = 1) -> type[BaseModel]:
    """One asked-for result and the sheet entries that give it (shared by the check and its re-read).

    `compact`: entry ids and names as strings, for the backup model's provider (see `_method_fields`); code drops
    ids not on the sheet."""
    produces = str if compact else Literal[produces_ids()]  # type: ignore[valid-type]
    not_produced = str if compact else Literal[not_produced_ids()]  # type: ignore[valid-type]
    return create_model(
        "Ask",
        __config__=ConfigDict(extra="forbid"),
        mutation_origin=(Literal["somatic", "germline", "not_stated"], Field(default="not_stated",
            description="Origin of the mutation data for THIS result; somatic, germline, or not stated.")),
        value_type=(Literal["continuous", "binary", "not_stated"], Field(default="not_stated",
            description="Measurements for THIS result: continuous, binary, or not stated.")),
        mirna_driver=(Literal["target_prior", "measured_expression", "not_stated"], Field(default="not_stated",
            description="Required source driving miRNA links for THIS result; not merely data the user has.")),
        quote=(str, Field(description="Exact contiguous words from the sentence, copied without translation.")),
        delivered_by=(list[produces], Field(description=(
            "The PRODUCES entries whose result gives what the quote asks for, as asked; empty when none does."))),
        not_by=(list[not_produced], Field(description=(
            "NOT PRODUCED entries that describe what the quote asks for; may be empty."))),
        # Log 388: code checks these against each entry's granularity and layers (Log 387 G5:
        # a per-patient network credited to OTTER, a three-layer network to DRAGON).
        scale=(Literal["per_sample", "whole_cohort", "unstated"], Field(description=(
            "per_sample: one result for each sample, patient or individual. whole_cohort: one result for all "
            "the samples together. unstated: the request does not say."))),
        omics_layers=(int, Field(description=(
            "How many different omics data types the asked-for result must model together; 0 when it is not a "
            "multi-omic result."))),
        # Log 389: typed attributes code compares with each entry (Log 388: per-cell networks
        # credited to LIONESS, lncRNA regulators to PUMA, the sign of regulation to PANDA).
        data_unit=(Literal["bulk_samples", "single_cells", "not_stated"], Field(description=(
            "What each unit of the asked-for result is computed from: bulk samples (tissues, patients, cell "
            "lines), or single cells."))),
        regulator_kinds=(list[Literal["tf", "mirna", "lncrna", "other"]], Field(description=(
            "The kinds of regulators the asked-for result must contain; empty when it is not about regulators."))),
        needs_sign=(bool, Field(description=(
            "Whether the asked-for result must say if a regulator activates or represses its targets."))),
        # Log 394 (Log 390 LN8: communities of a gene-gene co-expression network went to CONDOR).
        input_network=(Literal["regulator_gene", "gene_gene", "other", "none"], Field(description=(
            "The kind of existing network the asked-for result is computed from: regulator_gene (regulators "
            "linked to target genes), gene_gene (e.g. co-expression), other (e.g. protein interactions), "
            "or none when it is not computed from an existing network."))),
        # Log 402, re-applied in Log 403: result forms no registered workflow gives (heldout7 ON5,
        # heldout8 QN5/QN8/QN10, heldout10 SN1/SN5).
        group_membership=(Literal["one_group", "several_groups", "not_about_groups"], Field(description=(
            "When the asked-for result groups genes, regulators or samples: whether each may belong to only one "
            "group or to several groups at once; not_about_groups otherwise."))),
        time_model=(Literal["dynamic", "not_dynamic"], Field(description=(
            "dynamic: the asked-for result must model how the system changes from one time point to the next "
            "(time lags, transitions, trajectories). not_dynamic otherwise, including results compared between or "
            "related to time points, stages or follow-up."))),
        spatial=(Literal["uses_neighbors", "not_spatial"], Field(description=(
            "uses_neighbors: the asked-for result must use where samples sit in space or which are neighbours."))),
        # Log 403 (plan item 2): asking whether a method gives a result is still asking for that result;
        # how it was asked is kept apart from what is asked for.
        asked_as=(Literal["request", "question"], Field(description=(
            "request: the user wants the result produced. question: the user asks whether, or which, method "
            "produces it."))),
        **{name: field for name, field in _method_fields(compact, described=version != 3).items()
           if version != 2 or name in _ASK_METHOD_FIELDS_V2},
    )


CONDITIONS = {
    # field: (values, the value that rules results out, description)
    "mutation_origin": (("somatic", "germline", "not_stated"), "germline",
                        "Whether the mutations to be scored are acquired somatic mutations or inherited germline variants."),
    "value_type": (("continuous", "binary", "not_stated"), "binary",
                   "Whether the omics measurements to be modeled are continuous values or binary indicators."),
    "mirna_driver": (("target_prior", "measured_expression", "not_stated"), "measured_expression",
                     "What must drive miRNA-gene links: a target prior with a miRNA regulator list, or measured miRNA expression. Having miRNA expression without requiring its use does not set this."),
    "data_unit": (("bulk_samples", "single_cells", "not_stated"), "single_cells",
                  "What each sample or profile of the user's data is: bulk samples (tissues, patients, cell lines, or "
                  "cells summed into pseudo-bulk profiles), or single cells."),
    "samples_matched": (("same_samples", "different_samples", "not_stated"), "different_samples",
                        "Whether the user's different omics data types were measured on the same samples."),
    "spatial": (("uses_neighbors", "not_spatial"), "uses_neighbors",
                "uses_neighbors: the results must use where samples sit in space or which are neighbours."),
    "time_model": (("dynamic", "not_dynamic"), "dynamic",
                   "dynamic: the results must model how the system changes from one time point to the next."),
    "group_membership": (("several_groups", "one_group", "not_stated"), "several_groups",
                         "several_groups: a gene, regulator or sample must be allowed in more than one group."),
}
"""Log 412: the conditions a request states outside the sentence of an ask, as typed values.

heldout17 KN1 ("The 80 samples are cells from a single 10x run.") and KN3 ("The two layers were not
measured on the same samples."): the check filed each condition as something the user has, and judged
the ask from its own sentence (data_unit not_stated), so a per-sample co-expression network and a
DRAGON network were credited 4 times in 4. Each condition comes with the words that state it; code
keeps one only when those words are in the request, and applies it to the asks
(`interpretation.capability_check`).
"""


OtherAbout = Literal["how_computed", "what_it_contains", "file_format", "delivery", "which_data"]
def _recorded_about(value):
    """Recordings from before the split: "format_or_delivery" was never acted on, as "file_format" is not."""
    return "file_format" if value == "format_or_delivery" else value


UnknownAbout = Literal["data_unit", "input_network", "samples_matched", "sample_alignment", "regulator_kinds",
                       "omics_layers", "scale", "sample_count", "mutation_origin", "value_type", "mirna_driver",
                       "other"]
"""Core decision phase 2: `other` keeps any other uncertainty with its words -- the second reader that rule R1 asks
the fact agent's words to agree with (the fixed dimensions above still drive only the legacy asks)."""


@lru_cache(maxsize=4)
def conditions_model(compact: bool = False, version: int = 1) -> type[BaseModel]:
    fields = {}
    for name, (values, _rules_out, description) in CONDITIONS.items():
        fields[name] = (Literal[values], Field(default=values[-1], description=description))  # type: ignore[valid-type]
        fields[f"{name}_quote"] = (str, Field(default="", description=(
            f"The exact words of the request that state {name}; empty when it is not stated.")))
    fields["joint_layers"] = (int | None, Field(default=None, description=(
        "Number of omics types that the request explicitly requires together in ONE joint result (minimum if a range or alternatives), including a count "
        "stated in another sentence. Null for an inventory not all requested together or separate results.")))
    fields["joint_layers_quote"] = (str, Field(default="", description=(
        "Exact words stating that joint layer count; empty when null.")))
    # Log 414: a requirement on the results that none of the typed fields covers is kept with its words, so it
    # can be checked against each workflow the check credits (heldout16 NC7: "The miRNA links should be
    # estimated from negative correlation with the miRNA levels we measured." -- PUMA was offered as fitting).
    # Items 4-5 live check (2026-10-14): "format_or_delivery" held both a file format and a delivery; the check read
    # "uploaded automatically to a public database", "emailed to each patient's doctor automatically" and "a dashboard
    # that updates live" 4 times in 4, and code dropped them all with "save it as a tab-separated file". Live check c3:
    # with "automatic or scheduled re-runs" in it, "We will run the analysis on our own server overnight" was read as a
    # delivery once in 2; how the user runs the analysis is not one.
    other = create_model(
        "OtherRequirement", __config__=ConfigDict(extra="forbid"),
        __validators__={"_recorded": field_validator("about", mode="before")(_recorded_about)},
        quote=(str, Field(description="Exact words of the request that state it.")),
        about=(OtherAbout, Field(description=(
            "how_computed: how a result must be estimated or what it must be based on. what_it_contains: a "
            "property or content a result must have. file_format: the file type, file or column names, or the "
            "folder results are written to. delivery: results sent, uploaded, published or shown to anyone outside "
            "the analysis (e-mail, a database or repository, a website, a dashboard or app). which_data: which of "
            "the user's samples or files to use."))))
    fields["other_requirements"] = (list[other], Field(description=(
        "Every other requirement the request states about the asked-for results that none of the fields above "
        "covers; empty when there is none.")))
    # Verdict layer step 2: what the user says they do not know or have not decided, typed to the dimensions code
    # compares with the sheet (blind set heldout416b: "I never checked whether its nodes are regulators plus genes,
    # or genes only" -- 0/10 such requests were asked about; most were given a workflow, some refused).
    unknown = create_model(
        "UnknownFact", __config__=ConfigDict(extra="forbid"),
        count_kind=(Literal["choices", "range", "unspecified"], Field(default="unspecified", description=(
            "For an unknown sample/layer count: choices means only the listed discrete alternatives; range means "
            "every integer between two bounds; unspecified means no bounds or alternatives are stated."))),
        count_values=(list[int], Field(default_factory=list, description=(
            "Only numeric alternatives or two range bounds stated in the unknown's quote; exclude unrelated counts. Empty if unspecified."))),
        applies_to=(list[str] | None, Field(default=None, description=(
            "Exact quoted results this unknown affects. [] if it concerns unrelated data or no requested result. "
            "Null only when it applies to every requested result. Keep separate input datasets separate."))),
        quote=(str, Field(description="Exact words of the request saying the user does not know or has not decided it.")),
        about=(UnknownAbout, Field(description=(
            "data_unit: whether the data's units are single cells or bulk samples. input_network: whether an "
            "existing network links regulators to genes or genes to genes. samples_matched: whether different omics "
            "data types come from the same biological subjects/samples (not file order or ID alignment). sample_alignment: whether file IDs or their order align. regulator_kinds: whether the regulators or prior include "
            "miRNAs. omics_layers: how many omics data types there are. scale: one result for all samples together "
            "or one per sample. sample_count: how many independent samples there are. mutation_origin: somatic "
            "or germline mutations. value_type: continuous measurements or binary indicators. mirna_driver: whether "
            "miRNA links must use a target prior or measured miRNA expression. other: anything else about the "
            "user's data or the wanted result that the user says they do not know or have not decided."))))
    fields["unknown_facts"] = (list[unknown], Field(default_factory=list, description=(
        "Each property of the user's data or of the wanted result that the user says they do not know or have not "
        "decided; empty when there is none.")))
    # Verdict layer step 2b: a choice among results the user names but has not made (feasibility eval F43: "I cannot
    # tell if I mean their activity or their network wiring"). `differs_in` keeps it apart from a methods question
    # (Log 416 G0: "should we use LIONESS or BONOBO?" read as a result choice).
    choice = create_model(
        "OpenChoice", __config__=ConfigDict(extra="forbid"),
        quote=(str, Field(description="Exact words of the request saying the choice is not made.")),
        differs_in=(Literal["result", "method"], Field(description=(
            "result: the options give different results. method: the options are methods for the same result."))),
        options=(list[_ask_model(compact, version)], Field(description=(
            "Each option the user names, one ask per option, its quote the exact words naming it."))))
    fields["open_choices"] = (list[choice], Field(default_factory=list, description=(
        "Each choice among options the user names but says they have not made; empty when there is none.")))
    # M1 (live m1a F1): "Can you run PANDA with its alpha update rate set to 0.25 ...?" was read as a question about
    # the methods with no ask, so its setting had nothing to attach to and the run went ahead. The method the request
    # names and the settings it gives are read for the request too (`interpretation.method_conditions`).
    method = _method_fields(compact)
    fields["named_method"] = (method["named_method"][0], Field(default="none", description=(
        "The method the request names for what it asks, including a method it asks to run: a registered workflow, "
        "or LIONESS for any LIONESS version; unregistered when it names a method, model or variant not in this list; "
        "none when it names no method.")))
    fields["named_method_quote"] = (str, Field(default="", description=(
        "Exact words of the request naming that method; empty when none is named.")))
    if version == 2:
        fields.update(_scoped_fields(compact))  # ROUND-04: the only place counts and settings are read
    else:
        fields["settings"] = (method["settings"][0], Field(default_factory=list, description=(
            "Each setting of a method the request gives anywhere -- a parameter, penalty, threshold, precision, "
            "output format or hardware -- one item per setting; empty when it gives none. Not the input data.")))
    # Round m3 (2026-10-15): "Can LIONESS-PANDA run for exactly two expression samples ...?", "Can BONOBO run on
    # exactly two total samples ...?" and "Can SAMBAR run with kmin=2 and kmax=9 on exactly six mutation samples ...?"
    # were questions about a method with no ask, so the data size they state had no field: the sample minimums, the
    # clustering limit and the LIONESS-DRAGON cap were never applied and each was answered as if it could run. The
    # data size is read for the request too, as its method and settings are.
    if version != 2:
        fields["sample_count"] = (method["sample_count"][0], Field(default=None, description=(
            "How many samples, patients or profiles the request says the user's data has, anywhere in it; null when "
            "it does not say.")))
        fields["sample_count_quote"] = (str, Field(default="", description=(
            "Exact words of the request stating that number; empty when it is null.")))
        fields["feature_counts"] = (method["feature_counts"][0], Field(default_factory=list, description=(
            "Each number of genes, proteins or other features the request says the user's data has, one item per "
            "data type; empty when none is stated.")))
    # Core decision spec, phase 1 (2026-10-15): whether the request names the result it wants. Round p0: 9 of 14
    # requests that named none ("send me the results", "tell me what you find", "Should I go with BONOBO or
    # LIONESS ...?") were read as asks, matched nothing and were answered "no registered workflow produces this".
    fields["goal"] = (Literal["result_named", "method_named", "purpose_only"], Field(default="result_named", description=(
        "What the request says it wants produced. result_named: it names the kind of result it wants (for example "
        "one network for the whole cohort, a network per sample, communities, subtypes, TF activities, a co-expression "
        "matrix, or a comparison between groups), even when it also asks which method gives it. method_named: it asks "
        "to run, or asks about, a named method for that method's own output, or asks how methods work or differ. "
        "purpose_only: it gives only a topic or an aim, its data or files, or leaves the choice of analysis to the "
        "assistant, without naming the kind of result -- including asking which of several methods to use without "
        "saying what it wants from them.")))
    # Core decision phase 4b (spec 12.3): an input the user says they do not have (round p0-p3 C18: "I don't have any
    # motif or PPI files, just this expression table" -- CONDOR was offered through PANDA, which needs both).
    ruled_out = create_model(
        "RuledOutInput", __config__=ConfigDict(extra="forbid"),
        kind=(Literal["motif_prior", "ppi", "mirna_list", "covariates", "second_omics", "mutations", "network",
                      "expression"], Field(description=(
            "motif_prior: a TF motif or binding prior. ppi: a protein-interaction network. mirna_list: miRNA "
            "identifiers or miRNA-target predictions. covariates: a sample covariate or design table. second_omics: "
            "a second omics data type measured on the samples. mutations: somatic mutation calls. network: an "
            "existing regulator-gene or gene-gene network. expression: gene expression data."))),
        quote=(str, Field(description="Exact words of the request saying the user does not have it.")))
    # Phase 4b smoke S1 ("I only have expr_liver.tsv"; C18 "just this expression table"): saying these are the only
    # inputs rules out the rest, without naming each one.
    kinds = Literal["motif_prior", "ppi", "mirna_list", "covariates", "second_omics", "mutations", "network",
                    "expression"]
    fields["only_inputs"] = (list[kinds], Field(default_factory=list, description=(  # type: ignore[valid-type]
        "When the request says these are the only inputs the user has (they 'only have' them, it is 'just' this "
        "table), each of their kinds, as listed for ruled_out_inputs; empty otherwise.")))
    fields["only_inputs_quote"] = (str, Field(default="", description=(
        "Exact words of the request saying those are the only inputs; empty when only_inputs is empty.")))
    fields["ruled_out_inputs"] = (list[ruled_out], Field(default_factory=list, description=(
        "Each input the user says they do not have and cannot get. Not one they have not uploaded yet, will send "
        "later, or that someone else has; empty when there is none.")))
    fields["goal_quote"] = (str, Field(default="", description=(
        "Exact words of the request that name the result (result_named) or the method (method_named), or that state "
        "the aim (purpose_only).")))
    # Core decision phase 5b (spec 13.3): a count the user gives as candidates (p2-p4c C45: "I don't remember whether
    # the proteomics we got back is the 200-protein targeted panel or the 2,000-protein discovery panel" -- the
    # LIONESS-DRAGON size limit decides it, and code can judge each number).
    alternative = create_model(
        "CountAlternative", __config__=ConfigDict(extra="forbid"),
        of=(Literal["samples", "features"], Field(description=(
            "samples: the number of samples, patients or profiles. features: the number of genes, proteins or other "
            "features of one data type."))),
        quote=(str, Field(description="Exact words of the request giving the candidate numbers.")),
        values=(list[int], Field(description="Each candidate number, as the quote states it.")))
    fields["count_alternatives"] = (list[alternative], Field(default_factory=list, description=(
        "Each count the user gives as two or more candidate numbers and cannot say which is right (\"the 200-protein "
        "panel or the 2,000-protein panel\", \"either 100 or 1000 features\"). Not a range, and not a count the "
        "request states; empty when there is none.")))
    return create_model("RequestConditions", __config__=ConfigDict(extra="forbid"), **fields)


def unstated_conditions(version: int = 1) -> dict:
    """The conditions of a reading that states none (a re-read reads asks only)."""
    counts = ({"sample_count": None, "sample_count_quote": "", "feature_counts": []} if version != 2
              else {"sample_counts": [], "feature_counts": []})
    return {**{key: value for name, (values, _rules_out, _description) in CONDITIONS.items()
               for key, value in ((name, values[-1]), (f"{name}_quote", ""))},
            "other_requirements": [], "unknown_facts": [], "open_choices": [],
            "named_method": "none", "named_method_quote": "", "settings": [], **counts,
            "goal": "result_named", "goal_quote": "", "ruled_out_inputs": [], "only_inputs": [],
            "only_inputs_quote": "", "count_alternatives": []}


def reading_version(proposal) -> int:
    """The shape a reading (or its conditions) was given in: 2 when its counts are scoped (ROUND-04)."""
    conditions = getattr(proposal, "conditions", proposal)
    return 2 if hasattr(conditions, "sample_counts") else 1


ConditionAnswer = Literal["satisfies", "violates", "unrelated", "not_about_results"]
"""Items 4-5 live check c2 (2026-10-14): "Name the output after our project, ZEBRA." was filed as what a result must
contain, answered `violates` for DRAGON, and the supported network was refused. `not_about_results` -- the requirement
sets the result files' names, format or folder, or how the user runs the analysis -- removes nothing, as `unrelated`."""


@lru_cache(maxsize=32)
def condition_check_model(pairs: int) -> type[BaseModel]:
    """Log 414: per (asked result, stated requirement, one workflow's result), whether that result can meet it."""
    fields = {
        f"a{index}": (ConditionAnswer, Field(description=(
            f"Pair {index}: violates -- the workflow's result, as described, cannot meet the requirement; "
            "satisfies -- it meets it; unrelated -- the requirement does not concern this result; not_about_results -- "
            "the requirement only sets the result files' names, format or folder, or how the user runs the "
            "analysis.")))
        for index in range(1, pairs + 1)
    }
    model = create_model("ConditionCheck", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


@lru_cache(maxsize=4 * (MAX_SENTENCES + 1))
def proposal_model(sentences: int = 1, compact: bool = False, version: int = 1) -> type[BaseModel]:
    """The provider-facing schema: one required field per request sentence, sheet ids as enums.

    Log 387 smoke run: with one free-length list of sentences gpt-4o-mini returned
    only the first (the data sentence) 3 times in 4, so the goal was never read.
    Strict mode requires every property, so a field per sentence cannot be skipped.
    """
    ask = _ask_model(compact, version)
    # Log 387 dev round: with a kind beside the entry lists, a data sentence was given
    # 16 not-produced entries. Only an ask can name entries now.
    # Log 387 dev round 2: data sentences ("We have expression from 50 kidney samples ...")
    # were filed as asks. The sentence's role comes first; code drops asks the role rules out.
    sentence = create_model(
        "SentenceReading",
        __config__=ConfigDict(extra="forbid"),
        role=(SentenceRole, Field(description=(
            "background: it only says what the user has, did or must respect. asks: it asks for results, as a "
            "request or as a question about which method gives them. methods_question: it only asks how a method "
            "works or what it needs, naming no result. mixed: more than one of these."))),
        has=(list[str], Field(description=(
            "Exact quotes of what the user has, did or must respect (data, samples, constraints)."))),
        about_methods=(list[str], Field(description=(
            "Exact quotes of questions about how a method works or what it needs, naming no result."))),
        asks=(list[ask], Field(description=(
            "Each result the user wants produced, or asks whether or which method produces, about their data or "
            "biology; one item per result."))),
    )
    fields = {
        f"s{index}": (sentence, Field(description=f"Sentence {index} of the request."))
        for index in range(1, max(1, min(sentences, MAX_SENTENCES)) + 1)
    }
    # The provider's strict schema still requires it; the default reads recordings and fixtures from before Log 412.
    fields["conditions"] = (conditions_model(compact, version), Field(
        default_factory=lambda: conditions_model(compact, version)(**unstated_conditions(version)), description=(
        "Conditions the request states anywhere -- in another sentence, or a follow-up to an earlier request -- "
        "about the user's data or about what every asked-for result must satisfy.")))
    model = create_model("CapabilityCheckProposal", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


@lru_cache(maxsize=4 * (MAX_SENTENCES + 1))
def reread_model(sentences: int = 1, compact: bool = False, version: int = 1) -> type[BaseModel]:
    """Log 406: a second reading of words the check left unread, with only one thing to say about them.

    The check's sentence reading can file a sentence as background or as a question about methods
    (heldout11 VN5q: "Is there a method that models how each TF-gene edge at one time point depends
    on the edges at the previous time point?", 3 of 3), or quote one result of a sentence and
    nothing of the next one in it (heldout13 P1: "uploaded automatically to a public database").
    Asked again with the same choices it chooses the same; here the only field is what results
    the words ask for -- an empty list is a normal answer.
    """
    ask = _ask_model(compact, version)
    sentence = create_model(
        "SentenceAsks",
        __config__=ConfigDict(extra="forbid"),
        asks=(list[ask], Field(description=(
            "Each result these words ask to be produced, or ask whether or which method produces, about the "
            "user's data or biology; one item per result; empty when they ask for none."))),
    )
    fields = {
        f"s{index}": (sentence, Field(description=f"Passage {index}."))
        for index in range(1, max(1, min(sentences, MAX_SENTENCES)) + 1)
    }
    model = create_model("CapabilityReread", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


def reread_as_proposal(reread, conditions=None) -> BaseModel:
    """The re-read in the check's own proposal shape, every passage an `asks` sentence.

    Log 413: it carries the request's conditions as the check read them, so a result the re-read finds is
    held to them too (heldout18 CK6-2: "patient subtypes" re-read beside "A patient should be able to
    belong to two subtypes").
    """
    count = len(type(reread).model_fields)
    version = reading_version(conditions) if conditions is not None else 1
    return proposal_model(count, version=version).model_validate({
        **{f"s{index}": {"role": "asks", "has": [], "about_methods": [],
                         "asks": [item.model_dump() for item in getattr(reread, f"s{index}").asks]}
           for index in range(1, count + 1)},
        "conditions": conditions.model_dump() if conditions is not None else unstated_conditions(version)})


SecondOpinionAnswer = Literal["all", "part", "none", "named"]


@lru_cache(maxsize=32)
def second_opinion_model(pairs: int) -> type[BaseModel]:
    """Log 390: one required answer per (request words, registered result) pair.

    Log 403 (plan items 2 and 5): "part" -- the words ask for more than one result and the
    workflow gives some of them -- so a request that mixes a doable and an undoable result
    in one quote (heldout8 QP2-QP4: communities, then an interactive 3D view) is partly
    available, not a full gap that drops the doable half.
    """
    fields = {
        f"a{index}": (SecondOpinionAnswer, Field(description=(
            f"Pair {index}: all -- the workflow's results, together, give everything the request words ask for; "
            "part -- the words ask for more than one result and the workflow's results give some of them; "
            "none -- they give none of it; named -- the words only ask to run or use this workflow itself and name no "
            "result.")))
        for index in range(1, pairs + 1)
    }
    model = create_model("SecondOpinion", __config__=ConfigDict(extra="forbid"), **fields)
    model.model_json_schema = classmethod(  # type: ignore[method-assign]
        lambda cls, *args, **kwargs: strict_json_schema(BaseModel.model_json_schema.__func__(cls, *args, **kwargs)))
    return model


def proposal_sentences(proposal) -> list:
    """The sentence readings of a proposal, in order."""
    count = sum(1 for name in type(proposal).model_fields if name[1:].isdigit())
    return [getattr(proposal, f"s{index}") for index in range(1, count + 1)]


class CheckedRequirement(BaseModel):
    """One verified requirement and what the sheet says about it."""

    model_config = ConfigDict(extra="forbid")
    quote: str
    kind: RequirementKind
    status: Literal["available", "with_step", "partial", "not_available", "not_checked", "needs_fact"]
    """`not_checked` for about_methods and context; `not_available` when no produces entry gives it;
    `partial` when one reading of the passage names an entry and another names none."""
    delivered_by: list[str] = Field(default_factory=list)
    not_by: list[str] = Field(default_factory=list)
    attrs: dict[str, Any] = Field(default_factory=dict)
    """The ask's typed attributes (scale, layers, data unit, regulators, sign), for the second opinion."""
    blank: bool = False
    """Log 397: no reading named any sheet entry, delivering or not -- a verdict with no reason."""
    second_opinion: bool = False
    """Log 390: credited by the second opinion on a conflict with an exact routing match."""
    asked_as: Literal["request", "question"] = "request"
    """Log 403: whether the user wants it produced or asks whether/which method produces it."""
    violations: list[str] = Field(default_factory=list)
    """Log 414: why a credited workflow was removed -- it cannot meet a requirement the request states
    elsewhere (code-rendered from the condition check's answer)."""
    depends_on: str | None = None
    """Verdict layer step 2 (status needs_fact): the dimension the user said they do not know, on which the result's
    workflows differ."""
    outcomes: dict[str, list[str]] = Field(default_factory=dict)
    """Verdict layer step 2: for each value of `depends_on`, the produces entries that give the result."""
    unknown_quote: str = ""
    """Verdict layer step 2: the user's words saying they do not know it."""
    file_checked: str | None = None
    """Item 5 (2026-10-14): a dimension the user said they do not know that the workflow's own input check settles from
    the files before it runs (`needed_facts.FILE_CHECKED`); it is said with the result, never asked."""
    method: dict[str, Any] = Field(default_factory=dict)
    """M1 (2026-10-14): the ask's named method, settings and data size whose words are in the request
    (`interpretation.capability_check.verified_method`); every later step that credits a workflow holds it to them."""
    limits: list[str] = Field(default_factory=list)
    """M1: why a credited workflow cannot run as asked -- not the named method, a setting it lacks or a value it does
    not take, too few samples, too much data (code-rendered from `workflow_conditions`)."""
    instead: list[str] = Field(default_factory=list)
    """M1: produces entries of workflows that give the result by a method the request did not name; said as
    alternatives, never as the result asked for."""
    defaults: list[str] = Field(default_factory=list)
    """M1: produces entries of workflows that give the result with their own settings, only not with the stated ones;
    the workflow is offered as that (a run of it is held for the user), so the result is not a full gap."""
    by_code: bool = False
    """Phase 5b (spec 13.3): the wait is on a count the user gave as candidates, and code judged each candidate
    (`interpretation.count_alternatives`); a code-verified fact, never a legacy dimension's shadow."""
    outcome_notes: dict[str, str] = Field(default_factory=dict)
    """Phase 5b: for a candidate count whose workflows lose a credit, the contract limit that removes it."""
    fact_ids: list[str] = Field(default_factory=list)
    """ROUND-03: the facts of `CapabilityCheck.facts` its method was compiled from and judged on (a derived total
    with its parts), and the candidate count it waits on; empty in recordings from before ROUND-03."""
    blocks: list[str] = Field(default_factory=list)
    """ROUND-17: the workflows this not-available row shows cannot run as asked (a setting set apart, a stated
    requirement they violate); every other row resting on them alone is held with it (`same_run.same_run_holds`)."""


class CapabilityCheck(BaseModel):
    """The turn's capability check, as the reply and the card read it."""

    model_config = ConfigDict(extra="forbid")
    requirements: list[CheckedRequirement] = Field(default_factory=list)
    unchecked: list[str] = Field(default_factory=list)
    """Request sentences no verified requirement covers (the coverage check)."""
    full_gap: bool = False
    """Every result is not available and every sentence was read: no workflow is the answer."""
    unavailable: bool = False
    """Log 394: the check could not run this turn (its budget spent, or the model failed twice)."""
    provisional: bool = False
    """Log 401: only the backup model read the request (the check's own model failed), so what it
    found is reported but never acted on -- a gap it finds does not clear routing (Log 400: all three
    false gaps of heldout9 came from the backup model)."""
    cleared: list[str] = Field(default_factory=list)
    """Log 392: the routing candidates a full gap cleared, so an outside-step note tied to one
    of them (ALPACA beside CONDOR) is still said."""
    conditions: dict[str, str] = Field(default_factory=dict)
    unknown_domains: dict[str, dict[str, Any]] = Field(default_factory=dict)
    unknown_scopes: dict[str, list[str]] = Field(default_factory=dict)
    """Verified unknown-fact quote -> exact result quotes it affects; absent means shared (legacy compatible)."""
    """Log 412: the request-level conditions whose words were found in the request and that rule results out
    (e.g. data_unit single_cells), applied to every ask they concern."""
    unknowns: list[list[str]] = Field(default_factory=list)
    """Verdict layer step 2: (dimension, the user's words) for each fact the user said they do not know."""
    gap_unconfirmed: bool = False
    """Log 403: a full gap the second opinion was owed but could not give (its budget spent, or the
    model failed), so, as for the backup model, the gap is reported unconfirmed and clears nothing
    (traces: 11 second opinions blocked by the turn budget on h8-h9, o10, f10)."""
    goal: str = ""
    """Core decision spec, phase 1: result_named, method_named or purpose_only, kept only when its words are in the
    request (`interpretation.capability_check.verified_goal`); empty when unread or unverified."""
    goal_quote: str = ""
    ruled_out: dict[str, str] = Field(default_factory=dict)
    """Phase 4b: each input kind the user says they do not have, with their verified words."""
    only_inputs: list[str] = Field(default_factory=list)
    only_inputs_quote: str = ""
    """Phase 4b: the input kinds the user says are all they have, with their verified words (the rest are absent)."""
    count_alternatives: list[dict[str, Any]] = Field(default_factory=list)
    """Phase 5b: each count the user gave as candidates ({of, quote, values}), its words and numbers verified."""
    uncertain_quotes: list[str] = Field(default_factory=list)
    """Phase 2 R1: the request's words the check read as the user not knowing or not having decided something (any
    unknown fact, any open choice); the fact agent's words must agree with one of them."""
    stated_quotes: list[str] = Field(default_factory=list)
    """Phase 2 R4: the request's words for each condition, method and setting the reading typed with a definite
    value; a fact proposed from inside them is stated, not uncertain."""
    facts: list[RequestFact] = Field(default_factory=list)
    """ROUND-03: the request's counts and settings, each kept once with every read of it
    (`interpretation.request_facts`); the results cite them by id."""
    fact_conflicts: list[FactConflict] = Field(default_factory=list)
    """ROUND-03: where a result's own value and a request-level one disagreed, which was used and why."""

    def results(self) -> list[CheckedRequirement]:
        return [item for item in self.requirements if item.kind == "result"]

    def needed_facts(self) -> list[CheckedRequirement]:
        """Verdict layer step 2: results that wait on a fact the user said they do not know."""
        return [item for item in self.results() if item.status == "needs_fact"]

    def unconfirmed(self) -> bool:
        """Log 403: nothing this turn's check says was confirmed by the check's own model."""
        return self.unavailable or self.provisional or self.gap_unconfirmed


RunVerdictName = Literal["agrees", "no_result", "not_on_sheet", "no_check_model", "user_selected",
                         "other_workflow", "partial_gap", "outside_step", "needs_fact", "unread", "gap", "unconfirmed"]

APPROVING_RUN_VERDICTS = frozenset({"agrees", "no_result", "not_on_sheet", "no_check_model", "user_selected"})
"""agrees: the run's workflow gives every result asked for, directly; no_result: the check found nothing asked for
beyond running it; not_on_sheet: not an analysis workflow (STRING download, own rules); no_check_model: nothing is
configured to read the check (tests, the routing harness -- never production); user_selected: the user picked the
workflow from what an earlier turn offered, or continues a plan made under an approving verdict."""


class RunVerdict(BaseModel):
    """Verdict layer items 1-2 (2026-10-14): the capability verdict a run is planned under.

    Until now only a full gap changed a run (3578b00); `other_workflow` and `partial_gap` were recorded beside a
    run that went ahead. Routing, the reply, the Plan Evaluator and the executor gate read this one record, so a
    run the check did not approve is never an approved plan.
    """

    model_config = ConfigDict(extra="forbid")
    action: str
    verdict: RunVerdictName
    request_sha256: str = ""
    """The full request message the verdict was given for (stamped by `classify_task`); a plan for another fails."""
    held: bool = False
    """The run was not planned: the reply says why and offers it for the user to confirm."""
    named: bool = False
    """The user named the run's workflow, so another workflow is offered beside it, never put in its place."""
    credited: list[str] = Field(default_factory=list)
    """The workflows the check credits for every result some workflow gives."""
    results: list[dict[str, Any]] = Field(default_factory=list)
    """Each result's quote, status and credited workflows."""
    unchecked: list[str] = Field(default_factory=list)
    """Request sentences the check did not read."""

    def run_failures(self, action: str, request_sha256: str) -> list[str]:
        """Why this verdict does not approve a run of `action` for the request hashed `request_sha256`."""
        failures = []
        if self.action != action:
            failures.append(f"the capability verdict was given for {self.action}, not {action}")
        if not self.request_sha256 or self.request_sha256 != request_sha256:
            failures.append("the capability verdict was given for a different request")
        if self.held or self.verdict not in APPROVING_RUN_VERDICTS:
            failures.append(f"the capability check did not approve this run ({self.verdict})")
        return failures
