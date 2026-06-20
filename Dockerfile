FROM mambaorg/micromamba:1.5.10

COPY --chown=mambauser:mambauser environment.yml /tmp/environment.yml

RUN micromamba env create -y -f /tmp/environment.yml \
    && micromamba clean -a -y

USER root
ARG NETZOOPY_REF=master
RUN micromamba run -n netzoo git clone --depth=1 --branch "$NETZOOPY_REF" https://github.com/netZoo/netZooPy.git /opt/netZooPy
COPY docker/run-panda /usr/local/bin/run-panda
COPY docker/run-puma /usr/local/bin/run-puma
RUN chmod +x /usr/local/bin/run-panda /usr/local/bin/run-puma \
    && mkdir -p /work /data /outputs \
    && chown -R $MAMBA_USER:$MAMBA_USER /work /data /outputs /opt/netZooPy

USER $MAMBA_USER
WORKDIR /work

ENV NETZOOPY_SRC=/opt/netZooPy

ENTRYPOINT ["micromamba", "run", "-n", "netzoo"]
CMD ["bash"]
