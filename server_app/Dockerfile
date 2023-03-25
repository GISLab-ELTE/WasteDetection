# syntax=docker/dockerfile:1

FROM continuumio/miniconda3 AS base
WORKDIR /workspace
COPY environment.yml .
RUN conda env create -f environment.yml -q && conda clean --all -q


FROM base as server_app
COPY . .
RUN chmod 755 docker/start_server.sh
ENTRYPOINT ["docker/start_server.sh"]
