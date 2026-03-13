# syntax=docker/dockerfile:1

FROM continuumio/miniconda3:latest AS base

# Create Conda environment
COPY environment.yml .
RUN conda env create -f environment.yml -q && \
    conda clean --all -q && \
    rm environment.yml

# Install execstack and fix PyTorch shared libraries
RUN apt-get update \
    && apt-get install -y patchelf \
    && find $(conda info --base)/envs/WasteDetection/lib/python*/site-packages/torch -name "*.so" -exec sh -c 'patchelf --clear-execstack "$1" || true' _ {} \; \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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
COPY model/ model/
ENV FLASK_APP=app.py
ENV FLASK_APP_HOST=0.0.0.0
ENV FLASK_APP_PORT=5000
ENV FLASK_DEBUG=False
ENV FLASK_CORS_ORIGIN=http://localhost:5500
ENV SESSION_COOKIE_SECURE=True
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
