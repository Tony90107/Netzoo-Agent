FROM mambaorg/micromamba:1.5.10

COPY --chown=mambauser:mambauser environment.yml /tmp/environment.yml

RUN micromamba env create -y -f /tmp/environment.yml \
    && micromamba clean -a -y

USER root
ARG NETZOOPY_REF=60bcaf5ac69ac8f002db5fc6b1b10cbc101ee822
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
COPY docker/run-panda /usr/local/bin/run-panda
COPY docker/run-panda-precomputed /usr/local/bin/run-panda-precomputed
COPY docker/run-puma /usr/local/bin/run-puma
COPY docker/run-puma-precomputed /usr/local/bin/run-puma-precomputed
COPY docker/run-lioness /usr/local/bin/run-lioness
COPY docker/run-condor /usr/local/bin/run-condor
COPY docker/run-cobra /usr/local/bin/run-cobra
COPY docker/run-sambar /usr/local/bin/run-sambar
COPY scripts/netzoo_table_io.py /opt/netzoo-harness/netzoo_table_io.py
COPY scripts /opt/netzoo-app/scripts
COPY docker/add-puma-lioness-header /usr/local/bin/add-puma-lioness-header
COPY docker/web-url /usr/local/bin/web-url
RUN chmod +x /usr/local/bin/run-panda /usr/local/bin/run-panda-precomputed /usr/local/bin/run-puma /usr/local/bin/run-puma-precomputed /usr/local/bin/run-lioness /usr/local/bin/run-condor /usr/local/bin/run-cobra /usr/local/bin/run-sambar /usr/local/bin/add-puma-lioness-header /usr/local/bin/web-url \
    && mkdir -p /work /data /outputs \
    && chown -R $MAMBA_USER:$MAMBA_USER /work /data /outputs /opt/netZooPy /opt/netzoo-harness

USER $MAMBA_USER
WORKDIR /work

ENV NETZOOPY_SRC=/opt/netZooPy
ENV PYTHONPATH=/opt/netZooPy:/opt/netzoo-harness:/opt/netzoo-app/scripts

ENTRYPOINT ["micromamba", "run", "-n", "netzoo"]
CMD ["bash"]
