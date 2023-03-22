# syntax=docker/dockerfile:1

FROM continuumio/miniconda3

WORKDIR /workspace

COPY . .

RUN conda env create -f environment.yml -q && conda clean --all -q

RUN chmod 755 docker/start_server.sh

ENTRYPOINT ["docker/start_server.sh"]
