#!/usr/bin/env Rscript
# Run the pinned PORCUPINE R package on a validated sample-specific network.
#
# Usage: Rscript porcupine_run.R <params.json>
#
# The JSON carries the paths prepared by scripts/run_porcupine.py:
#   network_matrix  TSV, header: regulator, target, <sample_1> ... <sample_n>
#                   one row per unique regulator->target edge (edges x samples)
#   pathway_file    GMT: pathway name, description, gene identifiers (tab separated)
#   output_dir      private staging directory; outputs are written here
# plus the declared parameters (min/max pathway size, permutations, cores,
# scaling, centering, FDR / effect-size thresholds and the random seed).
#
# Pathway gene filtering is done here in base R and is equivalent to
# PORCUPINE::filter_pathways (keep pathway genes present as network targets,
# drop empty pathways). The upstream helper depends on plyr's internal column
# name ("X..i..") and is therefore not called. pca_random is replaced by
# drawing the random gene sets up front with the internal create_gene_set
# (see below); PCA and the statistics are the package's exported functions.

suppressPackageStartupMessages({
  library(jsonlite)
  library(data.table)
  library(PORCUPINE)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("usage: porcupine_run.R <params.json>")
p <- jsonlite::fromJSON(args[[1]])

# L'Ecuyer-CMRG gives each parallel worker its own reproducible stream (parallel::mclapply).
RNGkind("L'Ecuyer-CMRG")
set.seed(as.integer(p$seed))

table <- data.table::fread(p$network_matrix, sep = "\t", header = TRUE,
                           check.names = FALSE, data.table = FALSE)
if (!identical(colnames(table)[1:2], c("regulator", "target"))) {
  stop("network matrix must start with regulator and target columns")
}
edges <- data.frame(reg = as.character(table$regulator),
                    tar = as.character(table$target),
                    stringsAsFactors = FALSE)
net <- as.matrix(table[, -(1:2), drop = FALSE])
storage.mode(net) <- "double"
rm(table)

pathways <- PORCUPINE::load_gmt(p$pathway_file)
targets <- unique(edges$tar)
# trimws: the Python input check strips padded GMT tokens, so R must match them the same way.
pathways <- lapply(pathways, function(genes) { genes <- trimws(genes); unique(genes[genes %in% targets]) })
pathways <- pathways[lengths(pathways) > 0]
pathways <- pathways[order(names(pathways))]
pathways_to_use <- PORCUPINE::filter_pathways_size(
  pathways, minSize = as.integer(p$min_pathway_size),
  maxSize = as.integer(p$max_pathway_size))
if (length(pathways_to_use) == 0) {
  stop("no pathway has between min_pathway_size and max_pathway_size genes among the network targets")
}
cat("Pathways overlapping network targets:", length(pathways), "\n")
cat("Pathways tested after size filter:", length(pathways_to_use), "\n")

ncores <- as.integer(p$n_cores)
scale_data <- isTRUE(p$scale_data)
center_data <- isTRUE(p$center_data)

# The random gene sets are drawn here, all of them, before any PCA runs. PORCUPINE::pca_random draws them
# between PCA calls, and with ncores = 1 each irlba PCA consumes random numbers from the same stream, so the
# null gene sets depended on n_cores. This is pca_random's own procedure (same universe: every gene of the
# pathways overlapping the network, as in the README; same sizes; same create_gene_set) in a fixed order.
universe <- unique(unlist(pathways))
null_sizes <- unique(lengths(pathways_to_use))
null_sets <- lapply(null_sizes, function(size)
  PORCUPINE:::create_gene_set(universe, size, n_perm = as.integer(p$n_permutations)))

pca_res <- PORCUPINE::pca_pathway(pathways_to_use, net, edges, ncores = ncores,
                                  scale_data = scale_data, center_data = center_data)
pca_rnd <- as.data.frame(do.call("rbind", lapply(null_sets, function(sets)
  PORCUPINE::pca_pathway(sets, net, edges, ncores = ncores,
                         scale_data = scale_data, center_data = center_data))))
stats <- PORCUPINE::porcupine(pca_res, pca_rnd)

stats$pc1 <- as.numeric(stats$pc1)
stats$pathway_size <- as.integer(stats$pathway_size)
n_edges <- setNames(as.integer(unlist(pca_res$n_edges)), pca_res$pathway)
null_mean <- tapply(as.numeric(unlist(pca_rnd$pc1)), as.integer(unlist(pca_rnd$pathway_size)), mean)
result <- data.frame(
  pathway = as.character(stats$pathway),
  pathway_size = stats$pathway_size,
  n_edges = unname(n_edges[as.character(stats$pathway)]),
  pc1_variance_pct = stats$pc1,
  null_mean_pc1_variance_pct = as.numeric(null_mean[as.character(stats$pathway_size)]),
  pvalue = as.numeric(stats$pval),
  padj = p.adjust(as.numeric(stats$pval), method = "BH"),
  effect_size = as.numeric(stats$es),
  stringsAsFactors = FALSE
)
result$significant <- result$padj < as.numeric(p$fdr_threshold) &
  result$effect_size > as.numeric(p$min_effect_size)
result <- result[order(result$padj, -result$effect_size, result$pathway), ]

out <- p$output_dir
write_tsv <- function(frame, name) {
  data.table::fwrite(frame, file.path(out, name), sep = "\t", quote = FALSE, na = "NA")
}
write_tsv(result, "porcupine_pathways.tsv")

null_table <- data.frame(
  pathway_size = as.integer(unlist(pca_rnd$pathway_size)),
  n_edges = as.integer(unlist(pca_rnd$n_edges)),
  pc1_variance_pct = as.numeric(unlist(pca_rnd$pc1))
)
write_tsv(null_table, "porcupine_random_null.tsv")

# Sample scores on PC1 for every tested pathway: pathways in rows, samples in
# columns (the same orientation as a feature-by-sample omics matrix). PC signs
# are arbitrary, as in any PCA.
tested <- pathways_to_use[result$pathway]
ind <- PORCUPINE::get_pathway_ind_scores(tested, net, edges,
                                         scale_data = scale_data, center_data = center_data)
scores <- do.call(rbind, lapply(ind, function(m) m[colnames(net), 1]))
scores <- data.frame(pathway = names(ind), scores, check.names = FALSE, stringsAsFactors = FALSE)
write_tsv(scores, "porcupine_pc1_sample_scores.tsv")

# Edge loadings (PC1, PC2) for significant pathways only: one row per
# pathway x regulator->target edge.
sig <- result$pathway[result$significant]
if (length(sig) > 0) {
  feat <- PORCUPINE::get_pathway_features_scores(pathways_to_use[sig], net, edges,
                                                  scale_data = scale_data, center_data = center_data)
  loadings <- do.call(rbind, lapply(names(feat), function(name) {
    f <- feat[[name]]
    data.frame(pathway = name, regulator = f$reg, target = f$tar,
               pc1_loading = f[[1]], pc2_loading = f[[2]], stringsAsFactors = FALSE)
  }))
} else {
  loadings <- data.frame(pathway = character(), regulator = character(), target = character(),
                         pc1_loading = numeric(), pc2_loading = numeric())
}
write_tsv(loadings, "porcupine_edge_loadings.tsv")
cat("PORCUPINE significant pathways:", length(sig), "\n")
