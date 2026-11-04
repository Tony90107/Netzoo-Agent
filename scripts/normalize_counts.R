# Between-sample normalization of a count-scale gene-by-sample matrix with the
# Bioconductor packages the method is published in (the comparison arms of the
# PySNAIL manuscript):
#   rle      DESeq2 median-of-ratios size factors (estimateSizeFactorsForMatrix);
#            output = counts / size factor
#   tmm      edgeR TMM normalization factors (normLibSizes); output = CPM on the
#            TMM-effective library sizes
#   quantile preprocessCore normalize.quantiles; every sample takes the same
#            distribution
# Usage: Rscript normalize_counts.R <method> <expression.tsv> <output.tsv> <record.json>
# Inputs are checked in Python first (netzoo_agent_core/data/normalization.py).

suppressPackageStartupMessages(library(jsonlite))

args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 4) {
  stop("usage: normalize_counts.R <rle|tmm|quantile> <expression.tsv> <output.tsv> <record.json>")
}
method <- args[1]
expression_file <- args[2]
output_file <- args[3]
record_file <- args[4]

counts <- as.matrix(read.delim(expression_file, row.names = 1, check.names = FALSE))
storage.mode(counts) <- "double"
samples <- colnames(counts)

if (method == "rle") {
  suppressPackageStartupMessages(library(DESeq2))
  factors <- tryCatch(
    estimateSizeFactorsForMatrix(counts),
    error = function(e) stop(paste(
      "DESeq2 could not estimate size factors:", conditionMessage(e),
      "(median-of-ratios needs genes with a non-zero count in every sample)"
    ))
  )
  normalized <- sweep(counts, 2, factors, "/")
  package <- "DESeq2"
  factor_name <- "size_factor"
  scale <- "normalized counts: counts divided by each sample's DESeq2 median-of-ratios size factor"
} else if (method == "tmm") {
  suppressPackageStartupMessages(library(edgeR))
  y <- normLibSizes(DGEList(counts = counts), method = "TMM")
  factors <- y$samples$norm.factors
  normalized <- cpm(y, log = FALSE)
  package <- "edgeR"
  factor_name <- "norm_factor"
  scale <- "counts per million on TMM-effective library sizes (library size x TMM factor)"
} else if (method == "quantile") {
  suppressPackageStartupMessages(library(preprocessCore))
  normalized <- normalize.quantiles(counts)
  factors <- NULL
  package <- "preprocessCore"
  factor_name <- NULL
  scale <- "quantile-normalized values: every sample takes the mean sorted distribution"
} else {
  stop(paste("unknown method:", method))
}

dimnames(normalized) <- dimnames(counts)
if (any(!is.finite(normalized))) {
  stop("normalization produced non-finite values")
}
out <- data.frame(gene = rownames(normalized), normalized, check.names = FALSE)
write.table(out, output_file, sep = "\t", quote = FALSE, row.names = FALSE)

record <- list(
  method = method,
  package = package,
  package_version = as.character(packageVersion(package)),
  r_version = R.version.string,
  scale = scale,
  genes = nrow(normalized),
  samples = ncol(normalized)
)
if (!is.null(factors)) {
  record[[paste0(factor_name, "s")]] <- as.list(setNames(as.numeric(factors), samples))
}
write_json(record, record_file, auto_unbox = TRUE, digits = NA, pretty = TRUE)
cat(sprintf("%s normalization complete: %d genes x %d samples (%s %s).\n",
            toupper(method), nrow(normalized), ncol(normalized), package, record$package_version))
