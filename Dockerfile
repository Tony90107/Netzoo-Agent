# The browser build of the desktop window. The netzoo-web service serves it, so
# using NetZoo needs nothing on the host but Docker.
FROM node:20-bookworm-slim AS web-ui
WORKDIR /ui
COPY desktop/package.json desktop/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY desktop/index.html desktop/tsconfig.json desktop/vite.config.ts ./
COPY desktop/src ./src
RUN npm run build

FROM mambaorg/micromamba:1.5.10

COPY --chown=mambauser:mambauser environment.yml /tmp/environment.yml

RUN micromamba env create -y -f /tmp/environment.yml \
    && micromamba clean -a -y

# Fail the image build if the pinned MCP adapter/API pair cannot be imported;
# otherwise Websearch and Context7 only reveal this dependency drift at runtime.
RUN micromamba run -n netzoo python -c \
    'from langchain_mcp_adapters.client import MultiServerMCPClient; from mcp.shared.context import RequestContext; print("MCP adapter compatibility OK")'

# RLE (DESeq2), TMM (edgeR) and quantile (preprocessCore) normalization: the PySNAIL
# manuscript's comparison arms, in an R environment of its own so the Bioconductor
# solve never moves the Python environment's packages. Versions as tested 2026-11-04.
RUN micromamba create -y -n netzoo-r -c conda-forge -c bioconda \
      r-base=4.5.3 bioconductor-deseq2=1.50.2 bioconductor-edger=4.10.7 \
      bioconductor-preprocesscore=1.72.0 r-jsonlite=2.0.0 \
    && micromamba clean -a -y \
    && /opt/conda/envs/netzoo-r/bin/Rscript -e 'suppressPackageStartupMessages({library(DESeq2); library(edgeR); library(preprocessCore); library(jsonlite)}); cat("R normalization packages OK\n")'

# PORCUPINE (kuijjerlab/PORCUPINE, R): pathway-level PCA over sample-specific
# LIONESS networks. Not on CRAN/Bioconductor and has no releases, so pin the
# commit; dependencies come from conda in the same netzoo-r env. Tested 2026-11-05.
ARG PORCUPINE_REF=96d68c057803473b0a1ee76631c7c0c78872d04c
ENV PORCUPINE_REF=${PORCUPINE_REF}
RUN micromamba install -y -n netzoo-r -c conda-forge -c bioconda \
      bioconductor-fgsea=1.36.2 r-irlba=2.4.1 r-factoextra=2.2.0 r-lsr=1.0.0 \
      r-data.table=1.18.6.1 r-dplyr=1.2.1 r-plyr=1.8.9 r-purrr=1.2.2 r-gridextra=2.3.1 r-remotes=2.5.0 \
    && micromamba clean -a -y \
    && /opt/conda/envs/netzoo-r/bin/Rscript -e 'remotes::install_github(paste0("kuijjerlab/PORCUPINE@", Sys.getenv("PORCUPINE_REF")), dependencies = FALSE, upgrade = "never", build_vignettes = FALSE); suppressPackageStartupMessages({library(PORCUPINE); library(DESeq2)}); stopifnot(all(c("pca_pathway", "porcupine", "get_pathway_ind_scores", "get_pathway_features_scores") %in% getNamespaceExports("PORCUPINE")), exists("create_gene_set", envir = asNamespace("PORCUPINE"), inherits = FALSE)); cat("PORCUPINE OK\n")'

# SCORPION (kuijjerlab/SCORPION, R): single-cell PANDA networks per group of cells and testEdges. Pinned to the
# 1.3.5 commit that makes its PANDA match netZooPy (CRAN has 1.3.4); dependencies from conda in netzoo-r, added
# without changing any installed package. Tested 2026-11-08.
ARG SCORPION_REF=5c0fff00eb08c4b49b807150566e0a31ff592ab4
ENV SCORPION_REF=${SCORPION_REF}
RUN micromamba install -y -n netzoo-r -c conda-forge \
      r-igraph=2.3.4 r-rann=2.6.2 r-pbapply=1.7_4 r-furrr=0.4.0 r-future=1.82.0 \
    && micromamba clean -a -y \
    && /opt/conda/envs/netzoo-r/bin/Rscript -e 'remotes::install_github(paste0("kuijjerlab/SCORPION@", Sys.getenv("SCORPION_REF")), dependencies = FALSE, upgrade = "never", build_vignettes = FALSE); suppressPackageStartupMessages(library(SCORPION)); stopifnot(packageVersion("SCORPION") == "1.3.5", all(c("runSCORPION", "testEdges") %in% getNamespaceExports("SCORPION"))); cat("SCORPION OK\n")'

# SPONGE (netzoopy-sponge, kuijjerlab/sponge): human motif and PPI priors from JASPAR, Ensembl and STRING. Its
# pybbi/bioframe/pyjaspar stack lives in an environment of its own so the agent's packages never move. Tested
# 2026-11-08 (2.2.2; JASPAR2026 has 1,019 vertebrate CORE motifs).
ARG SPONGE_VERSION=2.2.2
RUN micromamba create -y -n netzoo-sponge -c conda-forge -c bioconda \
      python=3.12 pybbi=0.4.2 bioframe=0.8.0 pyjaspar=4.0.0 pandas=2.3.3 matplotlib-base=3.10 \
      scikit-learn=1.7.2 tqdm pyyaml requests \
    && micromamba clean -a -y \
    && /opt/conda/envs/netzoo-sponge/bin/python -m pip install --no-cache-dir --no-deps "netzoopy-sponge==${SPONGE_VERSION}" \
    && /opt/conda/envs/netzoo-sponge/bin/python -c 'from sponge.sponge import Sponge; from importlib.metadata import version; print("SPONGE", version("netzoopy-sponge"))'

USER root
ARG NETZOOPY_REF=60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822
ENV NETZOOPY_REF=${NETZOOPY_REF}
RUN micromamba run -n netzoo git clone https://github.com/netZoo/netZooPy.git /opt/netZooPy \
    && micromamba run -n netzoo git -C /opt/netZooPy checkout "$NETZOOPY_REF"
# Upstream master currently uses the imported os.path module instead of the
# save_lioness_results(file=...) argument in LionessPuma. Patch only that method.
RUN sed -i \
    -e 's/path\.endswith/file.endswith/g' \
    -e 's/np\.savetxt(path/np.savetxt(file/g' \
    -e 's/path, self\.export_lioness_results/file, self.export_lioness_results/g' \
    -e 's/np\.save(path/np.save(file/g' \
    /opt/netZooPy/netZooPy/lioness/lioness_for_puma.py
# Use Lioness' labeled export path directly instead of writing an extra
# lioness_output/lioness.npy and then a second unlabeled file.
RUN sed -i \
    -e 's/Lioness(panda_obj)/Lioness(panda_obj, export_filename=lioness_file)/' \
    -e '/lioness_obj\.save_lioness_results(lioness_file)/d' \
    /opt/netZooPy/netZooPy/panda/run_panda.py
# The pinned source checkout is the runtime of record. Install it into the
# micromamba environment so its documented `netzoopy` console entry point is
# available to the wrapper scripts.
RUN micromamba run -n netzoo python -m pip install --no-deps -e /opt/netZooPy \
    && micromamba run -n netzoo netzoopy --help >/dev/null \
    && micromamba run -n netzoo python -c 'import inspect, netZooPy; from netZooPy.giraffe import Giraffe; from netZooPy.bonobo import Bonobo; assert netZooPy.__version__ == "0.11.0"; print(inspect.signature(Giraffe)); print(inspect.signature(Bonobo)); print(inspect.signature(Bonobo.run_bonobo))'
# PySNAIL (Kuijjer lab) for SNAIL smooth-quantile normalization. PyPI's
# "pysnail" is an unrelated package, so install the pinned GitHub source.
# Upstream reads the groups file with read_csv(squeeze=True), removed in
# pandas 2; patch only that call, and fail the build if the patch no longer applies.
ARG PYSNAIL_REF=55bfe71002c36298a732752cb6ca8d99b16aa1d4
ENV PYSNAIL_REF=${PYSNAIL_REF}
RUN mkdir -p /opt/PySNAIL \
    && micromamba run -n netzoo curl -fsSL -o /tmp/pysnail.tar.gz "https://codeload.github.com/kuijjerlab/PySnail/tar.gz/${PYSNAIL_REF}" \
    && tar xzf /tmp/pysnail.tar.gz --strip-components=1 -C /opt/PySNAIL \
         "PySNAIL-${PYSNAIL_REF}/setup.py" "PySNAIL-${PYSNAIL_REF}/LICENSE" "PySNAIL-${PYSNAIL_REF}/pysnail" \
    && rm /tmp/pysnail.tar.gz \
    && grep -q "squeeze=True" /opt/PySNAIL/pysnail/utils.py \
    && sed -i -z 's/            header=None,\n            squeeze=True\n        )/            header=None,\n        ).squeeze("columns")/' /opt/PySNAIL/pysnail/utils.py \
    && ! grep -q "squeeze=True" /opt/PySNAIL/pysnail/utils.py \
    && micromamba run -n netzoo python -m pip install --no-deps /opt/PySNAIL \
    && micromamba run -n netzoo python -c 'from pysnail import Dataset, qsmooth; print("PySNAIL import OK")'
COPY docker/run-panda /usr/local/bin/run-panda
COPY docker/run-panda-precomputed /usr/local/bin/run-panda-precomputed
COPY docker/run-puma /usr/local/bin/run-puma
COPY docker/run-puma-precomputed /usr/local/bin/run-puma-precomputed
COPY docker/run-lioness /usr/local/bin/run-lioness
COPY docker/run-condor /usr/local/bin/run-condor
COPY docker/run-cobra /usr/local/bin/run-cobra
COPY docker/run-sambar /usr/local/bin/run-sambar
COPY docker/run-porcupine /usr/local/bin/run-porcupine
COPY docker/run-scorpion /usr/local/bin/run-scorpion
COPY docker/run-sponge /usr/local/bin/run-sponge
COPY docker/run-pysnail /usr/local/bin/run-pysnail
COPY docker/run-normalize-r /usr/local/bin/run-normalize-r
COPY scripts/netzoo_table_io.py /opt/netzoo-harness/netzoo_table_io.py
COPY scripts /opt/netzoo-app/scripts
COPY docker/add-puma-lioness-header /usr/local/bin/add-puma-lioness-header
COPY docker/web-url /usr/local/bin/web-url
COPY --from=web-ui /ui/dist /opt/netzoo-web
RUN chmod +x /usr/local/bin/run-panda /usr/local/bin/run-panda-precomputed /usr/local/bin/run-puma /usr/local/bin/run-puma-precomputed /usr/local/bin/run-lioness /usr/local/bin/run-condor /usr/local/bin/run-cobra /usr/local/bin/run-sambar /usr/local/bin/run-porcupine /usr/local/bin/run-scorpion /usr/local/bin/run-sponge /usr/local/bin/run-pysnail /usr/local/bin/run-normalize-r /usr/local/bin/add-puma-lioness-header /usr/local/bin/web-url \
    && mkdir -p /work /data /outputs \
    && chown -R $MAMBA_USER:$MAMBA_USER /work /data /outputs /opt/netZooPy /opt/netzoo-harness

USER $MAMBA_USER
WORKDIR /work

ENV NETZOOPY_SRC=/opt/netZooPy
ENV PYTHONPATH=/opt/netZooPy:/opt/netzoo-harness:/opt/netzoo-app/scripts

ENTRYPOINT ["micromamba", "run", "-n", "netzoo"]
CMD ["bash"]
