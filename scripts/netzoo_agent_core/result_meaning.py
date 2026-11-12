"""What a workflow's result means, file by file: the curated reading the Description view shows.

Every sentence here restates the workflow contracts (``workflows/*.yaml``), the method notes in
``interpretation/method_philosophy.py`` or the runner scripts, so nothing is generated per run. A run adds only what
it can read from its own files: which recorded output is which, and each file's header row. A file this table does
not know is still listed, as the workflow's result, without a reading that might be wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


__all__ = ["COLUMN_GLOSSARY", "MEANINGS", "auto_tags", "describe_files", "meaning_for", "next_analyses"]

_NETZOOPY = "https://github.com/netZoo/netZooPy/tree/60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822/netZooPy/"


@dataclass(frozen=True)
class FileRule:
    """A recorded output: matched by its plan role (``role:output_file``) or a basename pattern."""

    match: str
    title: str
    read: str = ""
    #: The `result:` and `scale:` auto tags; "" leaves the tag out rather than guess.
    kind: str = ""
    scale: str = ""


@dataclass(frozen=True)
class Meaning:
    name: str
    about: str
    read: str
    limits: str
    sources: tuple[tuple[str, str], ...] = ()
    files: tuple[FileRule, ...] = ()


_LIONESS_ABOUT = (
    "LIONESS estimates one network per sample. For each sample it compares the {base} network built from all "
    "samples with the one rebuilt without that sample: N_k = n * N_all - (n - 1) * N_without_k."
)
_LIONESS_READ = (
    "Each sample column holds that sample's edge scores. Compare samples or groups across these columns with a "
    "statistical test, or give the table to PORCUPINE to find pathways whose regulation varies between samples."
)
_LIONESS_LIMITS = (
    "A sample's network is its estimated contribution to the cohort network, not a network measured from that "
    "sample alone, so it depends on the other samples in the cohort. Cross-sectional networks do not show "
    "changes over time."
)
_SAMPLE_TABLE = "Sample-specific networks: one row per {edge} edge and one column per sample."

MEANINGS: dict[str, Meaning] = {
    "run_panda": Meaning(
        "PANDA",
        "PANDA starts from a TF-to-gene motif prior and uses message passing to reconcile it with TF-TF protein "
        "interactions and gene co-expression from your expression data. It gives one network for all samples.",
        "Each edge score is the combined support for a TF regulating a gene. Higher means more support from the "
        "prior, the interactions and the co-expression together. Compare scores within this network, for example "
        "to rank a TF's targets or a gene's regulators.",
        "Edge scores are integrated network scores: not probabilities, not measured binding and not proof that the "
        "TF regulates the gene. One network for the whole cohort shows no differences between samples or groups.",
        (("PANDA (netZoo)", "https://netzoo.github.io/zooanimals/panda/panda/"), ("netZooPy source", _NETZOOPY + "panda")),
        (FileRule("role:output_file", "Cohort TF-to-gene network", "One row per TF-gene edge with its PANDA score.", kind="network", scale="cohort"),),
    ),
    "run_puma": Meaning(
        "PUMA",
        "PUMA extends PANDA's message passing to miRNA regulators, whose prior edges usually come from "
        "sequence-based target prediction. It gives one TF/miRNA-to-gene network for all samples.",
        "Each edge score is the combined support for a regulator (TF or miRNA) acting on a gene. For a miRNA, the "
        "support comes from agreement between its predicted targets and the co-expression of those targets.",
        "The miRNA's own expression is not used, and anti-correlation gets no special weight for repression. "
        "Scores are not probabilities or proof of regulation, and one cohort network shows no sample differences.",
        (("PUMA (netZoo)", "https://netzoo.github.io/zooanimals/panda/puma/"), ("netZooPy source", _NETZOOPY + "puma")),
        (FileRule("role:output_file", "Cohort TF/miRNA-to-gene network", "One row per regulator-gene edge.", kind="network", scale="cohort"),),
    ),
    "run_lioness_panda": Meaning(
        "LIONESS-PANDA",
        _LIONESS_ABOUT.format(base="PANDA"),
        _LIONESS_READ,
        _LIONESS_LIMITS + " Edge scores are inferred regulatory support, not measured binding.",
        (("LIONESS (netZoo)", "https://netzoo.github.io/zooanimals/lioness/"),
         ("Sample-specific networks (netZoo)", "https://netzoo.github.io/zooanimals/ss/"),
         ("netZooPy source", _NETZOOPY + "lioness")),
        (FileRule("role:output_file", "Cohort PANDA network (all samples)", "The network LIONESS starts from.", kind="network", scale="cohort"),
         FileRule("role:lioness_output", _SAMPLE_TABLE.format(edge="TF-gene"), kind="network", scale="per-sample")),
    ),
    "run_lioness_puma": Meaning(
        "LIONESS-PUMA",
        _LIONESS_ABOUT.format(base="PUMA"),
        _LIONESS_READ,
        _LIONESS_LIMITS + " Edge scores are inferred regulatory support, not measured binding.",
        (("LIONESS (netZoo)", "https://netzoo.github.io/zooanimals/lioness/"),
         ("Sample-specific networks (netZoo)", "https://netzoo.github.io/zooanimals/ss/"),
         ("netZooPy source", _NETZOOPY + "lioness")),
        (FileRule("role:output_file", "Cohort PUMA network (all samples)", "The network LIONESS starts from.", kind="network", scale="cohort"),
         FileRule("role:lioness_output", _SAMPLE_TABLE.format(edge="regulator-gene"), kind="network", scale="per-sample")),
    ),
    "run_lioness_coexpression": Meaning(
        "LIONESS co-expression",
        _LIONESS_ABOUT.format(base="co-expression"),
        "Each sample's network holds its gene-gene co-expression contribution; compare samples or groups with a "
        "statistical test.",
        _LIONESS_LIMITS + " Co-expression is association, not regulation or causality.",
        (("LIONESS (netZoo)", "https://netzoo.github.io/zooanimals/lioness/"), ("netZooPy source", _NETZOOPY + "lioness")),
        (FileRule("role:output_file", "Cohort co-expression network (all samples)", kind="network", scale="cohort"),
         FileRule("role:lioness_output", "Sample-specific co-expression networks", kind="network", scale="per-sample")),
    ),
    "run_dragon": Meaning(
        "DRAGON",
        "DRAGON fits a two-layer Gaussian graphical model with layer-aware shrinkage, estimating conditional "
        "associations within and between two omics layers measured on the same samples.",
        "A non-zero partial correlation means two features stay associated after accounting for every other "
        "measured feature in both layers; its sign gives the direction of the association.",
        "Partial correlations are associations, not causal or directed effects. One network for all samples.",
        (("DRAGON (netZoo)", "https://netzoo.github.io/zooanimals/dragon/"), ("netZooPy source", _NETZOOPY + "dragon")),
        (FileRule(r"\.adj_pvalues\.[^.]+$", "Adjusted p-values for each edge (Benjamini-Hochberg)", kind="p-values", scale="cohort"),
         FileRule(r"\.pvalues\.[^.]+$", "P-values for each edge", kind="p-values", scale="cohort"),
         FileRule("role:output_file", "Cohort multi-omic partial-correlation network",
                  "A symmetric partial-correlation matrix, or an edge list with source, target, partial_correlation "
                  "and precision, depending on output_format.", kind="network", scale="cohort")),
    ),
    "run_lioness_dragon": Meaning(
        "LIONESS-DRAGON",
        "LIONESS-DRAGON estimates DRAGON's shrinkage once on all samples, then derives each sample's network from the "
        "all-sample network and the network refitted without that sample.",
        "Each sample column holds that sample's partial correlations; compare samples or groups with a test.",
        _LIONESS_LIMITS + " Partial correlations are associations, not causal effects.",
        (("DRAGON (netZoo)", "https://netzoo.github.io/zooanimals/dragon/"),
         ("LIONESS (netZoo)", "https://netzoo.github.io/zooanimals/lioness/")),
        (FileRule("role:output_file", "All-sample DRAGON partial-correlation matrix (labeled, symmetric)", kind="network", scale="cohort"),
         FileRule("role:lioness_output", "Sample-specific networks",
                  "Edge-by-sample table: source, target and one column per sample, the upper triangle of each "
                  "sample's matrix in DRAGON edge-list order.", kind="network", scale="per-sample")),
    ),
    "run_otter": Meaning(
        "OTTER",
        "OTTER optimizes a TF-to-gene matrix so that it reproduces both the TF-TF interaction network and gene "
        "co-expression; lambda balances the two fits and gamma regularizes the matrix.",
        "Each weight is the optimized OTTER score for a TF-gene edge; higher means a stronger edge in the fitted "
        "network.",
        "Weights are optimized scores, not probabilities, and they depend on lambda and gamma. One network for all "
        "samples (this agent does not run the per-sample LIONESS-OTTER).",
        (("OTTER (netZoo)", "https://netzoo.github.io/zooanimals/otter/"),
         ("OTTER tutorial (netZooR)", "https://netzoo.github.io/netZooR/articles/TutorialOTTER.html")),
        (FileRule("role:output_file", "Cohort TF-to-gene network (OTTER)",
                  "A labeled TF-by-gene matrix, or a source, target, weight edge list, depending on output_format.", kind="network", scale="cohort"),),
    ),
    "run_giraffe": Meaning(
        "GIRAFFE",
        "GIRAFFE uses the motif and PPI priors to constrain a matrix factorization that jointly fits gene expression "
        "as regulatory effects (R) times TF activities (TFA).",
        "In R, a positive entry is a fitted activation and a negative one a fitted repression, read like linear-model "
        "coefficients. TFA is each TF's inferred activity per sample, which differs from the TF's own expression.",
        "Fitted coefficients do not on their own establish causality. R is one matrix for all samples.",
        (("netZooPy source", _NETZOOPY + "giraffe"),),
        (FileRule(r"\.tfa\.[^.]+$", "TF activity (TFA): one row per TF, one column per sample", kind="TF activity"),
         FileRule("role:output_file", "Regulatory-effect matrix R (signed TF-by-gene effects)", kind="network", scale="cohort")),
    ),
    "run_cobra": Meaning(
        "COBRA",
        "COBRA models gene co-expression as a function of sample covariates, splitting it into components associated "
        "with each covariate.",
        "Components with a large covariate impact carry co-expression structure associated with that covariate. The "
        "adjusted co-expression removes it and can be given to PANDA, PUMA or OTTER as coexpression_file after its "
        "gene order is checked again.",
        "Covariate-associated components are not TF-to-gene edges, and an association with a covariate does not show "
        "that the covariate causes the pattern.",
        (("COBRA (netZoo)", "https://netzoo.github.io/zooanimals/cobra/"), ("netZooPy source", _NETZOOPY + "cobra")),
        (FileRule(r"^adjusted_coexpression\.(tsv|npz)$", "Covariate-adjusted gene-by-gene co-expression",
                  "The intercept component, with gene IDs on both axes.", kind="network", scale="cohort"),
         FileRule(r"^components\.npz$", "COBRA decomposition (psi, Q, d, g)",
                  "Raw components; not a network input on their own.", kind="model components"),
         FileRule(r"^summary\.tsv$", "One row per component: eigenvalue and largest absolute covariate impact", kind="statistics")),
    ),
    "run_condor": Meaning(
        "CONDOR",
        "CONDOR finds communities in a bipartite regulator-gene network with bipartite modularity, keeping regulators "
        "and targets as separate node types.",
        "Regulators and genes in the same community are connected to each other more than the bipartite null model "
        "expects. A node's Qscore is its contribution to its community's modularity; high-Qscore nodes form the core.",
        "A giant community can reflect the null model, resolution or weight handling, and modularity does not "
        "guarantee biologically meaningful modules. For sample-specific networks, run it per sample.",
        (("CONDOR (netZoo)", "https://netzoo.github.io/zooanimals/condor/"),
         ("CONDOR tutorial (netZooR)", "https://netzoo.github.io/netZooR/articles/CONDOR.html")),
        (FileRule(r"edges\.tsv$", "The edge list CONDOR used", kind="network"),
         FileRule(r"reg_memb\.tsv$", "Community of each regulator", kind="communities"),
         FileRule(r"tar_memb\.tsv$", "Community of each target gene", kind="communities"),
         FileRule(r"reg_qscores\.tsv$", "Each regulator's Qscore (contribution to its community's modularity)", kind="statistics"),
         FileRule(r"tar_qscores\.tsv$", "Each target gene's Qscore (contribution to its community's modularity)", kind="statistics"),
         FileRule(r"summary\.txt$", "Run summary", kind="summary")),
    ),
    "run_sambar": Meaning(
        "SAMBAR",
        "SAMBAR reduces sparse somatic mutations to pathway-level scores, correcting for gene length (and, when set, "
        "each patient's mutation burden), then can cluster samples on those scores.",
        "Samples with similar pathway mutation scores cluster together as candidate subtypes.",
        "Distances and cluster labels depend on the clustering settings. A mutation score does not establish "
        "functional loss, and this is not a regulatory network.",
        (("SAMBAR (netZoo)", "https://netzoo.github.io/zooanimals/sambar/"), ("netZooPy source", _NETZOOPY + "sambar")),
        (FileRule(r"^mt_out\.csv$", "Gene-level mutation scores per sample", kind="mutation scores", scale="per-sample"),
         FileRule(r"^pt_out\.csv$", "Pathway mutation scores per sample", kind="mutation scores", scale="per-sample"),
         FileRule(r"^clustergroups\.csv$", "Cluster assignment of each sample", kind="clusters"),
         FileRule(r"^dist_matrix\.csv$", "Distances between samples", kind="distances")),
    ),
    "run_porcupine": Meaning(
        "PORCUPINE",
        "PORCUPINE takes the edges that target each pathway's genes in every sample-specific network, runs a PCA and "
        "tests whether PC1 explains more variance than size-matched random gene sets.",
        "A significant pathway's regulation varies coherently between samples. PC1 sample scores show which samples "
        "sit at either end of that variation; edge loadings show which regulator-target edges drive it.",
        "It finds heterogeneity without predefined groups: it is not a group comparison, and a heterogeneous pathway "
        "is not proof of a causal driver.",
        (("PORCUPINE (GitHub)", "https://github.com/kuijjerlab/PORCUPINE"),),
        (FileRule(r"porcupine_pathways\.tsv$", "Per-pathway statistics: PC1 variance, p-value, FDR, effect size", kind="statistics"),
         FileRule(r"porcupine_pc1_sample_scores\.tsv$", "PC1 score of each sample for each pathway", kind="sample scores", scale="per-sample"),
         FileRule(r"porcupine_edge_loadings\.tsv$", "Loading of each regulator-target edge on its pathway's PC1", kind="edge loadings"),
         FileRule(r"porcupine_random_null\.tsv$", "Null distribution from size-matched random gene sets", kind="null distribution")),
    ),
    "run_scorpion": Meaning(
        "SCORPION",
        "SCORPION merges similar cells into super-cells to overcome single-cell sparsity, then runs PANDA's message "
        "passing with the motif and PPI priors, one network per group of cells.",
        "Networks built with the same priors are comparable column by column; the edge test compares two groups "
        "with a moderated t-test.",
        "It does not give one network per individual cell, and edge scores are inferred support, not measured "
        "binding.",
        (("SCORPION (GitHub)", "https://github.com/kuijjerlab/SCORPION"),),
        (FileRule(r"scorpion_networks\.tsv$", "One TF-to-target network per group of cells",
                  "Columns: tf, target, then one column per network (group values joined by '--').", kind="network", scale="per-group"),
         FileRule(r"scorpion_network_cells\.tsv$", "Number of cells behind each network", kind="summary"),
         FileRule(r"scorpion_differential_edges\.tsv$", "Edge test between the two compared groups, sorted by pAdj", kind="statistics")),
    ),
    "run_bonobo": Meaning(
        "BONOBO",
        "BONOBO combines a prior built from the other samples with one sample's expression profile, using Bayesian "
        "shrinkage, to estimate that sample's gene-gene co-expression matrix.",
        "Each file is one sample's co-expression matrix; compare matrices across samples to see between-individual "
        "differences.",
        "There is no cohort network and no TF-to-gene regulation. The matrices are not direct coexpression_file "
        "inputs for PANDA or PUMA.",
        (("netZooPy source", _NETZOOPY + "bonobo"),),
        (FileRule(r"^pvals_", "P-values for one sample's co-expression matrix (for thresholding)", kind="p-values", scale="per-sample"),
         FileRule(r"^bonobo_", "Co-expression matrix for one sample (the file name carries the sample ID)", kind="network", scale="per-sample")),
    ),
    "normalize_expression": Meaning(
        "Normalization",
        "Normalization rescales the expression matrix so samples are comparable before network inference; the "
        "method is named in the file name and in its record.",
        "Use the normalized matrix as the expression input of the next workflow.",
        "Normalization does not remove batch effects or biological confounding.",
        (),
        (FileRule(r"\.normalization\.json$", "Normalization record: method, settings and checks", kind="run record"),
         FileRule("role:output_file", "Normalized expression matrix (genes by samples)", kind="expression matrix")),
    ),
    "build_priors": Meaning(
        "SPONGE priors",
        "SPONGE builds the motif and PPI priors that PANDA, OTTER and SCORPION read, from JASPAR binding sites in "
        "gene promoters and STRING protein interactions.",
        "Give motif_prior.tsv as motif_file and ppi_prior.tsv as ppi_file to the next workflow.",
        "A motif hit near a promoter is a predicted binding site, not observed binding.",
        (("SPONGE (GitHub)", "https://github.com/kuijjerlab/sponge"),),
        (FileRule(r"^motif_prior\.tsv$", "Motif prior: TF, target gene, 1 (no header)", kind="prior"),
         FileRule(r"^ppi_prior\.tsv$", "PPI prior: TF, TF, STRING combined score / 1000 (no header)", kind="prior")),
    ),
}

_COMMON = (
    FileRule(r"^manifest\.json$", "Run record: the inputs, settings and checks this run used", kind="run record"),
    FileRule(r"\.log$", "Run log", kind="run log"),
)

#: Column names a header row may carry, and what they hold (exact names, case-insensitive).
COLUMN_GLOSSARY = {
    "tf": "transcription factor", "tf_id": "transcription factor", "regulator": "regulator (TF or miRNA)",
    "gene": "target gene", "target": "target", "source": "edge source",
    "motif": "1 if the edge was in the motif prior, 0 if not", "prior": "edge weight in the prior",
    "prior_weight": "edge weight in the prior", "force": "PANDA edge score", "weight": "edge weight",
    "partial_correlation": "partial correlation", "precision": "precision (inverse covariance) entry",
    "padj": "adjusted p-value", "pvalue": "p-value", "component": "component number",
    "eigenvalue": "eigenvalue of the component", "max_absolute_covariate_impact": "largest absolute covariate effect",
}
_NAME_TO_ACTION = {meaning.name.casefold(): action for action, meaning in MEANINGS.items()}
_NAME_TO_ACTION["lioness-coexpression"] = "run_lioness_coexpression"
_TEXT_SUFFIXES = {".tsv", ".csv", ".txt"}
_MAX_COLUMNS = 8


def meaning_for(action_or_name: str) -> tuple[str, Meaning] | None:
    key = action_or_name if action_or_name in MEANINGS else _NAME_TO_ACTION.get(action_or_name.casefold(), "")
    return (key, MEANINGS[key]) if key else None


def _local(path: str) -> Path | None:
    for candidate in (Path(path), Path(path.removeprefix("/work/"))):
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            return None
    return None


def _number(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def _header(path: str) -> dict:
    """The file's header row (or, when it has none, its first row) and size, read from the file itself."""
    local = _local(path)
    if local is None:
        return {}
    facts: dict = {"bytes": local.stat().st_size}
    if local.suffix.casefold() not in _TEXT_SUFFIXES:
        return facts
    try:
        with local.open(encoding="utf-8", errors="replace") as handle:
            lines = [handle.readline(65_536).rstrip("\r\n") for _ in range(2)]
    except OSError:
        return facts
    separator = "\t" if "\t" in lines[0] else "," if "," in lines[0] else None
    if not lines[0] or separator is None:
        return facts
    first, second = (line.split(separator) for line in lines)
    # A header names a column that holds numbers in the next row; a data row is numeric where the next one is.
    has_header = any(not _number(a) and _number(b) for a, b in zip(first, second)) or not lines[1]
    shown = [cell.strip() for cell in first[:_MAX_COLUMNS]]
    more = max(0, len(first) - _MAX_COLUMNS)
    if has_header:
        facts["columns"] = [
            {"name": name, "meaning": COLUMN_GLOSSARY.get(name.casefold(), "")} for name in shown
        ]
    else:
        facts["first_row"] = shown
    facts["more_columns"] = more
    return facts


def _roles(evidence: list[dict]) -> dict[str, str]:
    """Output path -> plan role (output_file, lioness_output, output_dir)."""
    roles = {}
    for item in evidence:
        field, value = str(item.get("field") or ""), str(item.get("value") or "")
        if field in {"output_file", "lioness_output", "output_dir"} and value:
            roles[value.removeprefix("/work/").rstrip("/")] = field
    return roles


def _rule(action: str, path: str, role: str) -> FileRule | None:
    meaning = MEANINGS.get(action)
    rules = (meaning.files if meaning else ()) + _COMMON
    name = path.rstrip("/").rsplit("/", 1)[-1]
    by_pattern = [rule for rule in rules if not rule.match.startswith("role:") and re.search(rule.match, name)]
    by_role = [rule for rule in rules if role and rule.match == f"role:{role}"]
    return (by_pattern or by_role or [None])[0]


def describe_files(action: str, written: list[str], evidence: list[dict], *, planned: bool) -> list[dict]:
    """Each output with what it is: recorded files when the run wrote them, the planned paths when it only previewed."""
    roles = _roles(evidence)
    paths = written if not planned else [path for path, role in roles.items()]
    meaning = MEANINGS.get(action)
    files = []
    for path in paths:
        relative = path.removeprefix("/work/")
        role = roles.get(relative, "")
        rule = _rule(action, relative, role)
        if role == "output_dir" and planned:
            title, read = "Output folder", "The run writes its result files into this folder."
        elif rule:
            title, read = rule.title, rule.read
        else:
            title, read = (f"{meaning.name} result file" if meaning else "Result file"), ""
        entry = {"path": relative, "title": title, "read": read, "written": not planned, "workflow": meaning.name
                 if meaning else None, "tags": auto_tags(meaning.name if meaning else "", rule)}
        if not planned:
            entry.update(_header(path))
        files.append(entry)
    return files


def auto_tags(workflow: str, rule: FileRule | None) -> list[str]:
    """The tags NetZoo sets on an output from the run's own record: method, result kind and scale, when known."""
    tags = [f"method:{workflow}"] if workflow else []
    if rule and rule.kind:
        tags.append(f"result:{rule.kind}")
    if rule and rule.scale:
        tags.append(f"scale:{rule.scale}")
    return tags


def next_analyses(action: str, policy) -> list[dict]:
    """What this result can feed, from the workflow contracts: handoff targets, then per-sample extensions."""
    workflows = getattr(policy, "workflows", None) or {}
    spec = workflows.get(action)
    if spec is None:
        return []
    found = []
    for target in spec.output_capability.handoff_targets:
        if target in workflows:
            found.append({"workflow": workflows[target].workflow, "relation": "can take this result as input",
                          "description": workflows[target].description})
    for other, candidate in workflows.items():
        if action in candidate.output_capability.guidance_predecessors and other != action:
            found.append({"workflow": candidate.workflow, "relation": "per-sample version of this analysis",
                          "description": candidate.description})
    return found[:6]
