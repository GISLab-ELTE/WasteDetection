# syntax=docker/dockerfile:1

FROM continuumio/miniconda3

WORKDIR /workspace

COPY . .

RUN conda env create -f environment.yml -q

# TODO: mount config file
RUN cp /workspace/docker/config.docker.json /workspace/resources/config.local.json
RUN mkdir -p /workspace/work_dir/satellite_images/automatic
RUN mkdir -p /workspace/work_dir/webapp_results/automatic

RUN chmod 755 docker/start_server.sh

ENTRYPOINT ["docker/start_server.sh"]
