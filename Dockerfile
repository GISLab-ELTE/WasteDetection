# syntax=docker/dockerfile:1

FROM continuumio/miniconda3:latest AS base

COPY environment.yml .
RUN conda env create -f environment.yml -q && \
    conda clean --all -q && \
    rm environment.yml
WORKDIR /workspace


FROM base AS server_app

COPY server_app/ server_app/
COPY model/ model/
COPY run_server_app.py .
RUN chmod 755 server_app/docker/start_server.sh
ENTRYPOINT ["server_app/docker/start_server.sh"]


FROM base AS web_app_backend

WORKDIR /workspace/flask_app
COPY web_app/backend/ ./
ENV FLASK_APP=app.py
ENV FLASK_APP_HOST=0.0.0.0
ENV FLASK_APP_PORT=5000
ENV FLASK_DEBUG=False
ENV FLASK_CORS_ORIGIN=http://localhost:5173
ENV GUNICORN_WORKERS=5
EXPOSE 5000
RUN useradd -m flaskuser
USER flaskuser
ENTRYPOINT ["bash", \
            "-c", \
            "source /opt/conda/etc/profile.d/conda.sh && \
            conda activate WasteDetection && \
            flask db upgrade && \
            exec gunicorn --workers $GUNICORN_WORKERS --bind $FLASK_APP_HOST:$FLASK_APP_PORT --access-logfile '-' --log-level info app:app"]
