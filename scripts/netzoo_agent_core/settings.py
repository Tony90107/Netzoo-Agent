"""Process defaults, filesystem roots, and workflow role constants."""

from pathlib import Path

EXECUTE_TOOLS = False
# Synthetic test mode keeps schema and cross-file checks but permits labels that
# are not present in NCBI/Ensembl. It is session-scoped and never enabled by
# default.
TEST_DATA_MODE = False
TRACE_ENABLED = False
VERBOSE_OUTPUT = False
TRANSIENT_TRACE = False
PRESENTATION_MODE = "compact"
DEFAULT_TOOL_TIMEOUT_SECONDS = 86_400.0
TOOL_TIMEOUT_SECONDS = DEFAULT_TOOL_TIMEOUT_SECONDS
MAX_RECOVERY_ATTEMPTS = 1
TRANSIENT_TRACE_MIN_SECONDS = 0.6
USER_VISIBLE_OUTPUT_LANGUAGE = "English"
LIONESS_MODE_QUESTION = (
    "Which registered LIONESS-compatible workflow should run? Choose one of the "
    "options below. After selection, the agent will discover and validate remaining "
    "inputs and request authorization before actual execution."
)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SESSION_ROOT = PROJECT_ROOT / ".netzoo" / "sessions"
TOOL_LOG_ROOT = PROJECT_ROOT / ".netzoo" / "logs"
TRACE_ROOT = PROJECT_ROOT / ".netzoo" / "traces"
PLANNING_AUDIT_ROOT = PROJECT_ROOT / ".netzoo" / "planning_audits"
MEMORY_ROOT = PROJECT_ROOT / ".netzoo" / "memory"
PROFILE_ROOT = MEMORY_ROOT / "profiles"
EPISODE_ROOT = MEMORY_ROOT / "episodes"
TOOL_RAW_MAX_CHARS = 8_000
DEFAULT_RETENTION_DAYS = 30
DEFAULT_SESSION_HARD_RETENTION_DAYS = 180
DEFAULT_ROUTER_MODEL = "openai/gpt-4o-mini"
DEFAULT_ROUTER_MAX_TOKENS = 1_200
DEFAULT_RESPONSE_MAX_TOKENS = 800
# A valid interpreter + review + intent route can consume about 15_800 tokens
# when provider usage metadata is unavailable. Its final response can bring the
# conservative estimate above 25_000, so keep bounded headroom for all four calls.
DEFAULT_TASK_TOKEN_BUDGET = 30_000
DEFAULT_LLM_TIMEOUT_SECONDS = 30.0
DEFAULT_LLM_MAX_RETRIES = 0
ROUTER_CONTEXT_MAX_CHARS = 6_000
DEFAULT_EPISODE_RETENTION_DAYS = 180
DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS = 60
DEFAULT_EPISODE_FAILED_RETENTION_DAYS = 30
DEFAULT_EPISODE_MAX_COUNT = 200
DEFAULT_EPISODE_MAX_BYTES = 10 * 1024 * 1024
INPUT_ROLE_FIELDS = {
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
OUTPUT_ROLE_FIELDS = {"output_file", "lioness_output", "output_dir"}
PARAMETER_FIELDS = {
    "prefix", "with_header", "genes_axis", "norm_patient", "kmin", "kmax",
    "taxon",
    "gmt_msigdb", "subset_cancer_genes", "distance", "linkage", "cluster",
    "output_format", "bonobo_output_format", "sample_names", "sparsify",
    "bonobo_confidence", "save_pvals", "keep_in_memory", "delta", "log_transformed",
    "centered", "lambda1", "lambda2",
    "computing", "precision", "lam", "gamma", "iterations", "eta", "bexp",
}

__all__ = [
    "EXECUTE_TOOLS", "TEST_DATA_MODE", "TRACE_ENABLED", "VERBOSE_OUTPUT", "TRANSIENT_TRACE",
    "PRESENTATION_MODE",
    "TOOL_TIMEOUT_SECONDS", "TRANSIENT_TRACE_MIN_SECONDS",
    "USER_VISIBLE_OUTPUT_LANGUAGE", "LIONESS_MODE_QUESTION", "PROJECT_ROOT",
    "SESSION_ROOT", "TOOL_LOG_ROOT", "TRACE_ROOT", "MEMORY_ROOT",
    "PLANNING_AUDIT_ROOT",
    "PROFILE_ROOT", "EPISODE_ROOT", "TOOL_RAW_MAX_CHARS",
    "DEFAULT_RETENTION_DAYS", "DEFAULT_SESSION_HARD_RETENTION_DAYS",
    "DEFAULT_ROUTER_MODEL", "DEFAULT_ROUTER_MAX_TOKENS",
    "DEFAULT_RESPONSE_MAX_TOKENS", "DEFAULT_TASK_TOKEN_BUDGET",
    "DEFAULT_LLM_TIMEOUT_SECONDS", "DEFAULT_LLM_MAX_RETRIES",
    "DEFAULT_TOOL_TIMEOUT_SECONDS", "MAX_RECOVERY_ATTEMPTS",
    "ROUTER_CONTEXT_MAX_CHARS", "DEFAULT_EPISODE_RETENTION_DAYS",
    "DEFAULT_EPISODE_DRY_RUN_RETENTION_DAYS",
    "DEFAULT_EPISODE_FAILED_RETENTION_DAYS", "DEFAULT_EPISODE_MAX_COUNT",
    "DEFAULT_EPISODE_MAX_BYTES", "INPUT_ROLE_FIELDS", "OUTPUT_ROLE_FIELDS",
    "PARAMETER_FIELDS",
]
