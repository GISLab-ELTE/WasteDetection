# syntax=docker/dockerfile:1

FROM continuumio/miniconda3

ARG startup=false
ARG sleep=false

WORKDIR /workspace

COPY server_app/ .

# RUN conda update conda -q
# Setting up conda environment
RUN conda env create -f environment.yml -q
SHELL ["conda", "run", "-n", "WasteDetectionServerApp", "/bin/bash", "-c"]

RUN cp /workspace/docker/config.docker.json /workspace/resources/config.local.json
RUN mkdir -p /workspace/work_dir/satellite_images/automatic
RUN mkdir -p /workspace/work_dir/webapp_results/automatic

WORKDIR /workspace/src

ENTRYPOINT ["conda", "run", "--no-capture-output", "-n", "WasteDetectionServerApp", "python", "__main__.py", "-st"]
