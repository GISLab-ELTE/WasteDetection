# syntax=docker/dockerfile:1

FROM continuumio/miniconda3

WORKDIR /workspace

COPY server_app/ .
RUN cp /workspace/docker/config.docker.json /workspace/resources/config.local.json
RUN mkdir -p /workspace/work_dir/satellite_images/automatic
RUN mkdir -p /workspace/work_dir/webapp_results/automatic

RUN conda update conda -q
RUN conda env create -f environment.yml -q

RUN cd src/

SHELL ["conda", "run", "-n", "WasteDetectionServerApp", "/bin/bash", "-c"]

CMD ["python", "__main__.py", "-st"]
