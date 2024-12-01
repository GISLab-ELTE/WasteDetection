# syntax=docker/dockerfile:1

FROM continuumio/miniconda3 AS base

WORKDIR /workspace
COPY environment.yml .
RUN conda env create -f environment.yml -q && conda clean --all -q


FROM base AS server_app

ADD server_app server_app
ADD model model
COPY run_server_app.py .
RUN chmod 755 server_app/docker/start_server.sh
ENTRYPOINT ["server_app/docker/start_server.sh"]


FROM base AS web_app_backend

ADD web_app/backend flask_app
ENV FLASK_APP=app.py
EXPOSE 5000
CMD ["bash", \ 
     "-c", \
     "source /opt/conda/etc/profile.d/conda.sh && \
     conda activate WasteDetection && \
     cd flask_app && \
     flask db upgrade && \
     flask run"]
