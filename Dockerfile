# syntax=docker/dockerfile:1

FROM continuumio/miniconda3 AS base
WORKDIR /workspace
COPY environment.yml .
RUN conda env create -f environment.yml -q && conda clean --all -q


FROM base as server_app
ADD server_app server_app
ADD model model
COPY run_server_app.py .
RUN chmod 755 server_app/docker/start_server.sh
ENTRYPOINT ["server_app/docker/start_server.sh"]
