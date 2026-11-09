#!/usr/bin/env Rscript
# Run the pinned SCORPION R package (kuijjerlab/SCORPION) from a params.json written by run_scorpion.py.
#
# Every network comes from runSCORPION(): without group_by, every cell gets one group ("all_cells"), so one network
# and many go through the same log normalization, cell minimum and super-cell step. With a comparison, testEdges()
# compares the networks on each side.
#
# Writes into params$output_dir:
#   scorpion_networks.tsv            tf, target, one column per network (edges x networks)
#   scorpion_network_cells.tsv       network_id, n_cells, built
#   scorpion_differential_edges.tsv  testEdges() output sorted by pAdj (only with a comparison)
#   summary.json                     counts read back into the manifest

suppressPackageStartupMessages({
  library(Matrix)
  library(SCORPION)
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1) stop("usage: scorpion_run.R params.json")
p <- fromJSON(args[[1]], simplifyVector = TRUE)
set.seed(p$seed)

read_text_matrix <- function(path, sep) {
  frame <- utils::read.table(path, sep = sep, header = TRUE, row.names = NULL, check.names = FALSE,
                             quote = "\"", comment.char = "", stringsAsFactors = FALSE)
  genes <- trimws(as.character(frame[[1]]))
  values <- as.matrix(frame[, -1, drop = FALSE])
  storage.mode(values) <- "double"
  list(matrix = Matrix(values, sparse = TRUE), genes = genes, cells = colnames(frame)[-1])
}

read_lines_tsv <- function(path) {
  utils::read.table(path, sep = "\t", header = FALSE, quote = "", comment.char = "",
                    stringsAsFactors = FALSE, colClasses = "character", fill = TRUE)
}

read_mtx <- function(mtx, features, barcodes, gene_column) {
  connection <- if (grepl("\\.gz$", mtx)) gzfile(mtx) else mtx
  m <- as(readMM(connection), "CsparseMatrix")
  feature_rows <- read_lines_tsv(features)
  column <- min(gene_column, ncol(feature_rows))
  list(matrix = m, genes = trimws(feature_rows[[column]]), cells = trimws(read_lines_tsv(barcodes)[[1]]))
}

loaded <- if (p$layout == "mtx") {
  read_mtx(p$mtx_file, p$features_file, p$barcodes_file, p$gene_column)
} else {
  read_text_matrix(p$cell_expression_file, p$separator)
}
x <- loaded$matrix
colnames(x) <- loaded$cells
genes <- loaded$genes
duplicated_genes <- sum(duplicated(genes))
if (duplicated_genes > 0) {
  # Several features with one symbol (10x features.tsv) are summed into one gene row.
  groups <- factor(genes, levels = unique(genes))
  x <- fac2sparse(groups) %*% x
  rownames(x) <- levels(groups)
} else {
  rownames(x) <- genes
}

# Cells: the ones the metadata names (all of them without group_by), with a group value, and with any counts.
cells_in_matrix <- ncol(x)
if (length(p$group_by) > 0) {
  meta <- utils::read.table(p$cell_metadata_file, sep = p$metadata_separator, header = TRUE, check.names = FALSE,
                            quote = "\"", comment.char = "", stringsAsFactors = FALSE, colClasses = "character")
  meta[[p$cell_id_column]] <- trimws(meta[[p$cell_id_column]])
  meta <- meta[match(colnames(x), meta[[p$cell_id_column]]), , drop = FALSE]
  has_row <- !is.na(meta[[p$cell_id_column]])
  has_group <- has_row & Reduce(`&`, lapply(p$group_by, function(column) {
    value <- meta[[column]]
    !is.na(value) & trimws(value) != ""
  }))
} else {
  meta <- data.frame(cell_id = colnames(x), network = p$all_cells, stringsAsFactors = FALSE)
  has_row <- rep(TRUE, ncol(x))
  has_group <- has_row
}
cell_totals <- Matrix::colSums(x)
has_counts <- cell_totals > 0
keep <- has_group & has_counts
x <- x[, keep, drop = FALSE]
meta <- meta[keep, , drop = FALSE]
group_by <- if (length(p$group_by) > 0) p$group_by else "network"
for (column in group_by) meta[[column]] <- trimws(as.character(meta[[column]]))

network_ids <- do.call(paste, c(meta[, group_by, drop = FALSE], sep = "--"))
cell_counts <- table(network_ids)
min_cells <- max(p$min_cells, 30)

nets <- runSCORPION(
  gexMatrix = x,
  tfMotifs = utils::read.table(p$motif_file, sep = p$motif_separator, header = p$motif_header, quote = "",
                               comment.char = "", stringsAsFactors = FALSE)[, 1:3],
  ppiNet = utils::read.table(p$ppi_file, sep = p$ppi_separator, header = p$ppi_header, quote = "",
                             comment.char = "", stringsAsFactors = FALSE)[, 1:3],
  cellsMetadata = meta,
  groupBy = group_by,
  normalizeData = isTRUE(p$normalize_data),
  minCells = p$min_cells,
  nCores = p$n_cores,
  gammaValue = p$gamma_value,
  nPC = p$n_pc,
  assocMethod = p$assoc_method,
  alphaValue = p$alpha_value,
  zScaling = isTRUE(p$z_scaling),
  outNet = "regNet",
  showProgress = TRUE
)
built <- setdiff(colnames(nets), c("tf", "target"))
utils::write.table(nets, file.path(p$output_dir, "scorpion_networks.tsv"), sep = "\t", quote = FALSE,
                   row.names = FALSE)
utils::write.table(
  data.frame(network_id = names(cell_counts), n_cells = as.integer(cell_counts),
             built = ifelse(names(cell_counts) %in% built, "yes", paste0("no (fewer than ", min_cells, " cells)"))),
  file.path(p$output_dir, "scorpion_network_cells.tsv"), sep = "\t", quote = FALSE, row.names = FALSE
)

summary <- list(
  cells_in_matrix = cells_in_matrix,
  cells_without_metadata = sum(!has_row),
  cells_without_group = sum(has_row & !has_group),
  cells_without_counts = sum(has_group & !has_counts),
  cells_used = ncol(x),
  genes_in_matrix = length(genes),
  duplicated_gene_rows_summed = duplicated_genes,
  networks_requested = length(cell_counts),
  networks_built = built,
  edges = nrow(nets),
  regulators = length(unique(nets$tf)),
  targets = length(unique(nets$target))
)

if (!is.null(p$comparison)) {
  position <- match(p$comparison$compare_by, group_by)
  parts <- strsplit(built, "--", fixed = TRUE)
  side <- function(value) {
    chosen <- built[vapply(parts, function(x) length(x) == length(group_by) && x[[position]] == value, logical(1))]
    keys <- vapply(strsplit(chosen, "--", fixed = TRUE), function(x) paste(x[-position], collapse = "--"),
                   character(1))
    stats::setNames(chosen, keys)
  }
  one <- side(p$comparison$group1)
  two <- side(p$comparison$group2)
  if (isTRUE(p$comparison$paired)) {
    shared <- sort(intersect(names(one), names(two)))
    one <- one[shared]
    two <- two[shared]
  } else {
    one <- sort(unname(one))
    two <- sort(unname(two))
  }
  if (length(one) < 2 || length(two) < 2) {
    stop(sprintf("testEdges needs at least 2 built networks per side; got %d (%s) and %d (%s)",
                 length(one), p$comparison$group1, length(two), p$comparison$group2))
  }
  result <- testEdges(nets, testType = "two.sample", group1 = unname(one), group2 = unname(two),
                      paired = isTRUE(p$comparison$paired))
  result <- result[order(result$pAdj, result$pValue), , drop = FALSE]
  utils::write.table(result, file.path(p$output_dir, "scorpion_differential_edges.tsv"), sep = "\t",
                     quote = FALSE, row.names = FALSE)
  summary$comparison <- list(
    compare_by = p$comparison$compare_by,
    group1 = p$comparison$group1, group1_networks = unname(one),
    group2 = p$comparison$group2, group2_networks = unname(two),
    paired = isTRUE(p$comparison$paired),
    edges_tested = nrow(result),
    edges_padj_below_0_05 = sum(result$pAdj < 0.05, na.rm = TRUE)
  )
}
writeLines(toJSON(summary, auto_unbox = TRUE, pretty = TRUE), file.path(p$output_dir, "summary.json"))
