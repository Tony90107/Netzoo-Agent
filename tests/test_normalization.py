"""SNAIL normalization (PySNAIL) as an explicit preparation step."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPTS_DIR = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from netzoo_agent_core.contracts import TaskDecision  # noqa: E402
from netzoo_agent_core.data.normalization import (  # noqa: E402
    normalization_input_report,
    normalization_record_path,
)
from netzoo_agent_core.data.artifacts import validate_output_artifacts  # noqa: E402
from netzoo_agent_core.data.preflight import validate_workflow_inputs  # noqa: E402
from netzoo_agent_core.interpretation.request_parameters import (  # noqa: E402
    extract_explicit_request_parameters,
)
from netzoo_agent_core.cli.follow_up import build_workflow_continuation  # noqa: E402
from netzoo_agent_core.contracts.interaction import ContextualReplyResolution, FollowUpContext  # noqa: E402
from netzoo_agent_core.contracts.state import NextTurnPrompt  # noqa: E402
from netzoo_agent_core.cli.clarification import _normalization_continuation  # noqa: E402
from netzoo_agent_core.contracts import ClarificationInputError  # noqa: E402
from netzoo_agent_core.contracts.normalization import NeedReading  # noqa: E402
from netzoo_agent_core.normalization_request import (  # noqa: E402
    decision_from_needs,
    method_choice_evidence,
    methods_for_needs,
    needs_normalization_reading,
    normalization_decision,
    verified_needs,
)
from netzoo_agent_core.routing.authorization import action_operation_kind  # noqa: E402
from netzoo_agent_core.routing.capability import validate_task_text  # noqa: E402
from workflow_registry import (  # noqa: E402
    ACTION_DEFINITIONS,
    LOCAL_WORKFLOW_ACTIONS,
    RUN_ACTIONS,
    executor_arguments,
)

HAS_PYSNAIL = importlib.util.find_spec("pysnail") is not None
RSCRIPT = os.environ.get("NETZOO_RSCRIPT", "/opt/conda/envs/netzoo-r/bin/Rscript")
HAS_R_ENV = Path(RSCRIPT).is_file()


def _counts(genes: int = 60, samples: int = 8, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    mean = rng.lognormal(3, 1.5, size=genes)
    depth = rng.uniform(0.5, 2.0, size=samples)
    values = rng.poisson(mean[:, None] * depth[None, :])
    return pd.DataFrame(
        values,
        index=[f"G{i}" for i in range(genes)],
        columns=[f"S{j}" for j in range(samples)],
    )


class NormalizationInputTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.expression = self.dir / "counts.tsv"
        _counts().to_csv(self.expression, sep="\t")
        self.output = self.dir / "out" / "normalized.tsv"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _groups(self, mapping: dict[str, str], name: str = "groups.tsv") -> Path:
        path = self.dir / name
        path.write_text("".join(f"{sample}\t{group}\n" for sample, group in mapping.items()))
        return path

    def report(self, expression: Path | None = None, groups: Path | str = "", aggregation: str = "median"):
        return normalization_input_report(
            str(expression or self.expression), str(self.output), str(groups), aggregation
        )

    def test_counts_with_groups_pass(self):
        groups = self._groups({f"S{j}": "A" if j < 4 else "B" for j in range(8)})
        report, ok, inputs = self.report(groups=groups)
        self.assertTrue(ok, report)
        self.assertIn("groups: 2 (A 4, B 4)", report)
        self.assertEqual(list(inputs.groups.index), [f"S{j}" for j in range(8)])

    def test_no_groups_says_result_is_quantile_normalization(self):
        report, ok, _ = self.report()
        self.assertTrue(ok, report)
        self.assertIn("quantile normalization", report)

    def test_expected_counts_are_accepted(self):
        frame = _counts() + 0.37
        frame.to_csv(self.expression, sep="\t")
        report, ok, _ = self.report()
        self.assertTrue(ok, report)
        self.assertIn("non-integer", report)

    def test_negative_values_are_refused(self):
        frame = _counts().astype(float)
        frame.iloc[0, 0] = -1.2
        frame.to_csv(self.expression, sep="\t")
        report, ok, _ = self.report()
        self.assertFalse(ok)
        self.assertIn("negative values", report)

    def test_log_scale_values_are_refused(self):
        np.log2(_counts() + 1.5).to_csv(self.expression, sep="\t")
        report, ok, _ = self.report()
        self.assertFalse(ok)
        self.assertIn("log-scale", report)

    def test_groups_must_cover_every_sample(self):
        groups = self._groups({f"S{j}": "A" for j in range(7)})
        report, ok, _ = self.report(groups=groups)
        self.assertFalse(ok)
        self.assertIn("1 expression samples have no group", report)

    def test_groups_file_needs_two_columns(self):
        path = self.dir / "bad_groups.tsv"
        path.write_text("S0\tA\textra\n")
        report, ok, _ = self.report(groups=path)
        self.assertFalse(ok)
        self.assertIn("exactly two", report)

    def test_single_group_is_called_quantile_like(self):
        groups = self._groups({f"S{j}": "A" for j in range(8)})
        report, ok, _ = self.report(groups=groups)
        self.assertTrue(ok, report)
        self.assertIn("only one group", report)

    def test_output_may_not_overwrite_input(self):
        report, ok, _ = normalization_input_report(str(self.expression), str(self.expression))
        self.assertFalse(ok)
        self.assertIn("different from the inputs", report)

    def test_unknown_aggregation_is_refused(self):
        report, ok, _ = self.report(aggregation="max")
        self.assertFalse(ok)
        self.assertIn("aggregation must be one of", report)

    def test_preflight_dispatches_to_normalization_checks(self):
        decision = {"expression_file": str(self.expression), "output_file": str(self.expression)}
        errors = validate_workflow_inputs("normalize_expression", decision)
        self.assertTrue(errors)
        self.assertIn("different from the inputs", " ".join(errors))


class RMethodInputTests(unittest.TestCase):
    def test_r_methods_ignore_groups_and_skip_snail_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            expression = Path(tmp) / "counts.tsv"
            _counts().to_csv(expression, sep="\t")
            groups = Path(tmp) / "groups.tsv"
            groups.write_text("".join(f"S{j}\tA\n" for j in range(8)))
            report, ok, inputs = normalization_input_report(
                str(expression), str(Path(tmp) / "o.tsv"), str(groups), "median", "tmm"
            )
            self.assertTrue(ok, report)
            self.assertIn("TMM (edgeR) normalization inputs", report)
            self.assertIn("used only by SNAIL", report)
            self.assertIsNone(inputs.groups_path)
            self.assertNotIn("tied values", report)

    def test_fpkm_needs_a_length_for_every_gene(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            expression = tmp_path / "counts.tsv"
            counts = _counts()
            counts.to_csv(expression, sep="\t")
            output = str(tmp_path / "o.tsv")
            report, ok, _ = normalization_input_report(str(expression), output, "", "median", "fpkm")
            self.assertFalse(ok)
            self.assertIn("FPKM needs a gene-lengths file", report)
            short = tmp_path / "short.tsv"
            short.write_text("".join(f"{gene}\t1500\n" for gene in counts.index[:-1]))
            report, ok, _ = normalization_input_report(str(expression), output, "", "median", "fpkm", str(short))
            self.assertFalse(ok)
            self.assertIn("1 expression genes have no length", report)
            full = tmp_path / "lengths.tsv"
            full.write_text("gene\tlength\n" + "".join(f"{gene}\t{1000 + i}\n" for i, gene in enumerate(counts.index)))
            report, ok, inputs = normalization_input_report(str(expression), output, "", "median", "fpkm", str(full))
            self.assertTrue(ok, report)  # a header row is accepted
            self.assertEqual(list(inputs.lengths.index), list(counts.index))
            report, ok, inputs = normalization_input_report(str(expression), output, "", "median", "tmm", str(full))
            self.assertTrue(ok, report)
            self.assertIn("used only by FPKM", report)
            self.assertIsNone(inputs.lengths_path)

    def test_unknown_method_is_refused(self):
        report, ok, _ = normalization_input_report("counts.tsv", "o.tsv", "", "median", "upperquartile")
        self.assertFalse(ok)
        self.assertIn("method must be one of", report)

    def test_log_scale_refusal_names_the_method(self):
        with tempfile.TemporaryDirectory() as tmp:
            expression = Path(tmp) / "log.tsv"
            np.log2(_counts() + 1.5).to_csv(expression, sep="\t")
            report, ok, _ = normalization_input_report(str(expression), str(Path(tmp) / "o.tsv"), "", "median", "rle")
            self.assertFalse(ok)
            self.assertIn("RLE expects count-scale data", report)


class NormalizationRegistryTests(unittest.TestCase):
    def test_registered_as_local_transform_not_a_menu_workflow(self):
        self.assertIn("normalize_expression", ACTION_DEFINITIONS)
        self.assertIn("normalize_expression", LOCAL_WORKFLOW_ACTIONS)
        self.assertNotIn("normalize_expression", RUN_ACTIONS)
        self.assertEqual(action_operation_kind("normalize_expression"), "transform")

    def test_executor_defaults(self):
        decision = TaskDecision(
            action="normalize_expression", in_scope=True, should_execute=True, confidence=1.0,
            reason="test", expression_file="counts.tsv", output_file="norm.tsv",
        )
        self.assertEqual(
            executor_arguments("normalize_expression", decision),
            {"expression_file": "counts.tsv", "output_file": "norm.tsv", "groups_file": "", "snail_aggregation": "median",
             "normalization_method": "snail", "gene_lengths_file": ""},
        )

    def test_unset_fields_do_not_change_decision_dumps(self):
        decision = TaskDecision(action="no_tool", in_scope=True, should_execute=False, confidence=1.0, reason="t")
        dumped = decision.model_dump()
        self.assertNotIn("groups_file", dumped)
        self.assertNotIn("snail_aggregation", dumped)

    def test_output_check_needs_matrix_and_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "snail.tsv"
            output.write_text("gene\tS0\tS1\nG0\t1.5\t2.0\nG1\t0\t3.25\n")
            decision = TaskDecision(
                action="normalize_expression", in_scope=True, should_execute=True, confidence=1.0,
                reason="test", expression_file="counts.tsv", output_file=str(output),
            )
            missing = validate_output_artifacts("normalize_expression", decision)
            self.assertFalse(missing.ok)
            self.assertIn("record is missing", " ".join(missing.errors))
            normalization_record_path(output).write_text("{}\n")
            present = validate_output_artifacts("normalize_expression", decision)
            self.assertTrue(present.ok, present.errors)
            self.assertEqual(present.metrics["expression_rows"], 2)

    def test_request_must_name_normalization(self):
        self.assertIsNotNone(validate_task_text("Run it on counts.tsv", "normalize_expression"))
        self.assertIsNone(
            validate_task_text("Normalize counts.tsv with SNAIL, groups file groups.tsv", "normalize_expression")
        )

    def test_explicit_parameters_bind(self):
        parameters = extract_explicit_request_parameters(
            "Normalize expression_file=counts.tsv with groups_file=tissues.tsv, snail_aggregation=mean"
        )
        self.assertEqual(parameters.get("groups_file"), "tissues.tsv")
        self.assertEqual(parameters.get("snail_aggregation"), "mean")


class NormalizationRequestTests(unittest.TestCase):
    """The request reading the live check (2026-11-04) depends on: read before workflow matching."""

    RUNS = {
        "Normalize the counts in /data/counts.tsv with SNAIL, using the tissue groups in /data/groups.tsv, "
        "and write the result to /data/out/snail.tsv.": {
            "expression_file": "/data/counts.tsv", "groups_file": "/data/groups.tsv", "output_file": "/data/out/snail.tsv",
        },
        "Run PySNAIL smooth-quantile normalization on /data/counts.tsv and save it to /data/out/norm.tsv.": {
            "expression_file": "/data/counts.tsv", "output_file": "/data/out/norm.tsv",
        },
        "Please normalize my RNA-seq counts in /data/counts.tsv and write them to /data/out/n.tsv.": {
            "expression_file": "/data/counts.tsv", "output_file": "/data/out/n.tsv",
        },
    }
    NOT_RUNS = (
        "Should I normalize my RNA-seq counts before running PANDA?",
        "What is SNAIL normalization?",
        "Run PANDA on /data/expr.tsv without normalization.",
        "Run PANDA on my SNAIL-normalized counts /data/n.tsv.",
        "Do not normalize; just run LIONESS on my data.",
    )

    def test_commands_become_a_normalization_with_their_files(self):
        for task, files in self.RUNS.items():
            decision = normalization_decision(task)
            self.assertIsNotNone(decision, task)
            self.assertEqual(decision.action, "normalize_expression")
            self.assertEqual(decision.requested_outcome.operation, "prepare")
            bound = {field: getattr(decision, field) for field in ("expression_file", "groups_file", "output_file")}
            self.assertEqual({k: v for k, v in bound.items() if v}, files, task)

    def test_the_named_method_is_the_one_planned(self):
        cases = {
            "Normalize /data/counts.tsv with TMM (edgeR) and save it to /data/out/tmm.tsv.": "tmm",
            "Run DESeq2 RLE normalization on /data/counts.tsv and write it to /data/out/rle.tsv.": "rle",
            "Normalize /data/counts.tsv by median of ratios, output /data/out/r.tsv.": "rle",
            "Apply quantile normalization (preprocessCore) to /data/counts.tsv; save to /data/out/q.tsv.": "quantile",
            "Run PySNAIL smooth-quantile normalization on /data/counts.tsv and save it to /data/out/s.tsv.": "snail",
            "Please normalize my RNA-seq counts in /data/counts.tsv and write them to /data/out/n.tsv.": "snail",
            "Normalize expression_file=/data/counts.tsv output_file=/data/out/x.tsv normalization_method=quantile": "quantile",
            "Compute FPKM for /data/counts.tsv with gene lengths /data/len.tsv and save it to /data/out/f.tsv.": "fpkm",
        }
        for task, method in cases.items():
            decision = normalization_decision(task)
            self.assertIsNotNone(decision, task)
            self.assertEqual(decision.normalization_method, method, task)

    def test_fpkm_request_binds_its_lengths_file(self):
        decision = normalization_decision(
            "Compute FPKM for the counts in /data/counts.tsv using the gene lengths in /data/len.tsv, "
            "and save it to /data/out/f.tsv."
        )
        self.assertEqual(
            (decision.expression_file, decision.gene_lengths_file, decision.output_file),
            ("/data/counts.tsv", "/data/len.tsv", "/data/out/f.tsv"),
        )

    def test_two_methods_are_not_read_as_one(self):
        self.assertIsNone(normalization_decision("Normalize /data/counts.tsv with RLE and with TMM, output /data/out/x.tsv."))

    def test_questions_negations_and_chains_are_left_to_routing(self):
        for task in self.NOT_RUNS:
            self.assertIsNone(normalization_decision(task), task)

    def test_normalize_then_workflow_records_the_workflow(self):
        decision = normalization_decision(
            "Normalize the counts in /data/counts.tsv with SNAIL, save to /data/out/snail.tsv, then run PANDA "
            "with motif /data/motif.tsv and ppi /data/ppi.tsv."
        )
        self.assertEqual(decision.then_action, "run_panda")
        self.assertEqual(decision.expression_file, "/data/counts.tsv")  # motif and PPI are not the matrix
        self.assertEqual(decision.output_file, "/data/out/snail.tsv")
        self.assertEqual(
            normalization_decision("Normalize /data/counts.tsv with SNAIL and then run LIONESS-PANDA on it.").then_action,
            "run_lioness_panda",
        )
        self.assertIsNone(normalization_decision("Normalize /data/counts.tsv with SNAIL.").then_action)

    def test_unchainable_or_ambiguous_followers_are_left_to_routing(self):
        for task in (
            "Normalize /data/counts.tsv with SNAIL and then run BONOBO.",  # needs log-scale, centered values
            "Normalize /data/counts.tsv with SNAIL, then run PANDA and PUMA.",
        ):
            self.assertIsNone(normalization_decision(task), task)

    def test_accepted_follow_on_reads_the_normalized_matrix(self):
        prompt = NextTurnPrompt(
            kind="recommended_workflow", question="q", continuation_action="run_panda",
            expected_field="expression_file", carried_inputs={"expression_file": "/data/out/snail.tsv"},
        )
        context = FollowUpContext(
            prior_user_goal="Normalize the counts in /data/counts.tsv with SNAIL, using the tissue groups in "
            "/data/groups.tsv, save the result to /data/out/snail.tsv, and then run PANDA on it.",
            prompt_kind="recommended_workflow", prompt_question="q", continuation_action="run_panda",
        )
        resolution = ContextualReplyResolution(kind="accept_workflow", reason="continue", selected_action="run_panda")
        continuation = build_workflow_continuation(prompt, context, resolution, "continue")
        self.assertEqual(continuation.action, "run_panda")
        self.assertEqual(continuation.parameters.get("expression_file"), "/data/out/snail.tsv")
        for field in ("output_file", "groups_file", "snail_aggregation"):
            self.assertNotIn(field, continuation.parameters)


class NeedBasedChoiceTests(unittest.TestCase):
    """The method chosen from what the request says it needs corrected (no LLM: readings are given)."""

    TASK = ("My samples were sequenced at very different depths; make /data/counts.tsv comparable across "
            "samples and save it to /data/out/n.tsv.")

    def need(self, need: str, quote: str) -> NeedReading:
        return NeedReading(need=need, text_span=quote)

    def test_only_quoted_needs_are_kept(self):
        kept = verified_needs(self.TASK, [
            self.need("sequencing_depth", "sequenced at very different depths"),
            self.need("gene_length", "longer genes get more reads"),  # not in the request
        ])
        self.assertEqual([reading.need for reading in kept], ["sequencing_depth"])

    def test_needs_map_to_methods(self):
        depth, length = self.need("sequencing_depth", "d"), self.need("gene_length", "g")
        groups, same = self.need("group_differences", "t"), self.need("same_distribution", "s")
        self.assertEqual(methods_for_needs([depth]), ["rle", "tmm"])
        self.assertEqual(methods_for_needs([length]), ["fpkm"])
        self.assertEqual(methods_for_needs([depth, length]), ["fpkm"])  # FPKM also divides by library size
        self.assertEqual(methods_for_needs([groups]), ["snail"])
        self.assertEqual(methods_for_needs([same]), ["quantile"])
        self.assertEqual(methods_for_needs([groups, same]), ["snail", "quantile"])

    def test_one_fitting_method_is_used_with_its_reason(self):
        task = "I need values that account for gene length; lengths in /data/len.tsv for /data/counts.tsv. Save to /data/out/n.tsv."
        decision = decision_from_needs(task, [self.need("gene_length", "account for gene length")])
        self.assertEqual(decision.normalization_method, "fpkm")
        self.assertEqual(decision.normalization_choice.source, "need")
        self.assertEqual((decision.expression_file, decision.gene_lengths_file), ("/data/counts.tsv", "/data/len.tsv"))

    def test_several_fitting_methods_are_asked(self):
        decision = decision_from_needs(self.TASK, [self.need("sequencing_depth", "sequenced at very different depths")])
        self.assertIsNone(decision.normalization_method)
        self.assertEqual(decision.normalization_choice.candidates, ["rle", "tmm"])
        [item] = method_choice_evidence(decision)
        self.assertEqual((item.field, item.status, item.candidates), ("normalization_method", "missing", ["rle", "tmm"]))
        self.assertIn('"sequenced at very different depths"', item.reason)

    def test_no_stated_need_keeps_the_default_said_as_default(self):
        decision = decision_from_needs("Normalize /data/counts.tsv and save it to /data/out/n.tsv.", [])
        self.assertEqual((decision.normalization_method, decision.normalization_choice.source), ("snail", "default"))
        self.assertEqual(method_choice_evidence(decision), [])

    def test_named_method_needs_no_reading(self):
        decision = normalization_decision("Normalize /data/counts.tsv with TMM and save it to /data/out/t.tsv.")
        self.assertEqual((decision.normalization_method, decision.normalization_choice.source), ("tmm", "named"))

    def test_which_unnamed_requests_are_read_for_needs(self):
        self.assertTrue(needs_normalization_reading(self.TASK))
        for task in (
            "Should I correct /data/counts.tsv for sequencing depth?",
            "Run PANDA on /data/counts.tsv with motif /data/m.tsv and ppi /data/p.tsv.",
            "Make my data comparable across samples.",  # no matrix named
        ):
            self.assertFalse(needs_normalization_reading(task), task)

    def test_the_chosen_method_comes_back_with_every_file(self):
        task = ("Make /data/counts.tsv comparable across sequencing depths, save it to /data/out/n.tsv, "
                "and then run PANDA on it.")
        decision = decision_from_needs(task, [self.need("sequencing_depth", "comparable across sequencing depths")])
        follow = _normalization_continuation(decision, {"normalization_method": "tmm"})
        again = normalization_decision(follow)
        self.assertEqual(again.normalization_method, "tmm")
        self.assertEqual(again.normalization_choice.source, "answered")  # said as the user's choice, not as named
        self.assertEqual((again.expression_file, again.output_file), ("/data/counts.tsv", "/data/out/n.tsv"))
        self.assertEqual(again.then_action, "run_panda")
        with self.assertRaises(ClarificationInputError):
            _normalization_continuation(decision, {"normalization_method": "quantile"})  # not among the candidates


@unittest.skipUnless(HAS_R_ENV, "the R environment exists only in the Docker runtime")
class RNormalizationRunnerTests(unittest.TestCase):
    """The R arms against what each method is defined to give."""

    def run_method(self, method: str, counts: pd.DataFrame, tmp: Path, extra: tuple[str, ...] = ()) -> tuple[pd.DataFrame, dict]:
        expression = tmp / "counts.tsv"
        counts.to_csv(expression, sep="\t")
        output = tmp / f"{method}.tsv"
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(SCRIPTS_DIR), os.environ.get("PYTHONPATH", "")])}
        result = subprocess.run(
            [sys.executable, str(SCRIPTS_DIR / "run_r_normalization.py"), "-m", method, "-e", str(expression), "-o", str(output),
             *extra],
            capture_output=True, text=True, env=env, timeout=300,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        normalized = pd.read_csv(output, sep="\t", index_col=0)
        self.assertEqual(list(normalized.index), list(counts.index))
        self.assertEqual(list(normalized.columns), list(counts.columns))
        return normalized, json.loads(normalization_record_path(output).read_text())

    def test_rle_divides_by_median_of_ratios(self):
        counts = _counts(genes=80, samples=6) + 1  # no zeros: every gene enters the geometric mean
        with tempfile.TemporaryDirectory() as tmp:
            normalized, record = self.run_method("rle", counts, Path(tmp))
        log = np.log(counts.to_numpy(dtype=float))
        expected = np.exp(np.median(log - log.mean(axis=1, keepdims=True), axis=0))
        self.assertTrue(np.allclose(list(record["size_factors"].values()), expected))
        self.assertTrue(np.allclose(normalized.to_numpy(), counts.to_numpy() / expected, rtol=1e-8))
        self.assertEqual(record["package"], "DESeq2")

    def test_tmm_gives_cpm_on_effective_library_sizes(self):
        counts = _counts(genes=200, samples=6)
        with tempfile.TemporaryDirectory() as tmp:
            normalized, record = self.run_method("tmm", counts, Path(tmp))
        factors = np.array(list(record["norm_factors"].values()))
        self.assertAlmostEqual(float(np.exp(np.log(factors).mean())), 1.0, places=6)  # edgeR scales them to geomean 1
        expected = counts.to_numpy() / (counts.sum().to_numpy() * factors) * 1e6
        self.assertTrue(np.allclose(normalized.to_numpy(), expected, rtol=1e-8))
        self.assertEqual(record["package"], "edgeR")

    def test_fpkm_scales_by_gene_length_and_library_size(self):
        counts = _counts(genes=120, samples=5)
        lengths = np.random.default_rng(2).integers(300, 9000, size=len(counts))
        with tempfile.TemporaryDirectory() as tmp:
            table = Path(tmp) / "lengths.tsv"
            # Rows in another order than the matrix, with a header: the runner aligns them by gene.
            pd.Series(lengths, index=counts.index).iloc[::-1].rename("length").to_csv(table, sep="\t", index_label="gene")
            normalized, record = self.run_method("fpkm", counts, Path(tmp), ("-l", str(table)))
        expected = counts.to_numpy() / (lengths[:, None] / 1e3) / (counts.sum().to_numpy()[None, :] / 1e6)
        self.assertTrue(np.allclose(normalized.to_numpy(), expected, rtol=1e-8))
        self.assertEqual(record["package"], "edgeR")
        self.assertIn("gene_lengths_sha256", record)

    def test_quantile_gives_every_sample_one_distribution(self):
        counts = _counts(genes=100, samples=5).astype(float) + np.random.default_rng(1).random((100, 5))  # no ties
        with tempfile.TemporaryDirectory() as tmp:
            normalized, record = self.run_method("quantile", counts, Path(tmp))
        ordered = np.sort(normalized.to_numpy(), axis=0)
        self.assertTrue(np.allclose(ordered, ordered[:, :1]))
        self.assertTrue(np.allclose(ordered[:, 0], np.sort(counts.to_numpy(), axis=0).mean(axis=1)))
        self.assertEqual(record["package"], "preprocessCore")


@unittest.skipUnless(HAS_PYSNAIL, "PySNAIL is installed only in the Docker runtime")
class PySnailRunnerTests(unittest.TestCase):
    def test_runner_writes_matrix_and_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            counts = _counts(genes=200, samples=12)
            counts.iloc[:30, 0] = 0  # zeros in one sample: the tie case SNAIL targets
            expression = tmp_path / "counts.tsv"
            counts.to_csv(expression, sep="\t")
            groups = tmp_path / "groups.tsv"
            groups.write_text("".join(f"S{j}\t{'A' if j < 6 else 'B'}\n" for j in range(12)))
            output = tmp_path / "out" / "snail.tsv"
            env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(SCRIPTS_DIR), os.environ.get("PYTHONPATH", "")])}
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "run_pysnail.py"), "-e", str(expression), "-g", str(groups), "-o", str(output)],
                capture_output=True, text=True, env=env, timeout=300,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            normalized = pd.read_csv(output, sep="\t", index_col=0)
            self.assertEqual(list(normalized.index), list(counts.index))
            self.assertEqual(list(normalized.columns), list(counts.columns))
            self.assertFalse(normalized.isna().any().any())
            self.assertTrue((normalized.to_numpy() >= 0).all())
            record = json.loads(normalization_record_path(output).read_text())
            self.assertEqual(record["software"], "PySNAIL")
            self.assertEqual(record["groups"], {"A": 6, "B": 6})
            self.assertEqual(record["aggregation_used"], "median")
            self.assertEqual((record["genes"], record["samples"]), (200, 12))

    def test_runner_refuses_log_scale_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            expression = Path(tmp) / "log.tsv"
            np.log2(_counts() + 1.5).to_csv(expression, sep="\t")
            env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(SCRIPTS_DIR), os.environ.get("PYTHONPATH", "")])}
            result = subprocess.run(
                [sys.executable, str(SCRIPTS_DIR / "run_pysnail.py"), "-e", str(expression), "-o", str(Path(tmp) / "o.tsv")],
                capture_output=True, text=True, env=env, timeout=120,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("log-scale", result.stderr)


if __name__ == "__main__":
    unittest.main()
