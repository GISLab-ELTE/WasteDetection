#!/bin/bash

ARGS=$@
PYTHON_ARGS=()

if [[ -f "/mnt/config.docker.json" ]]; then
  cp /mnt/config.docker.json /workspace/server_app/resources/config.local.json
else
  echo "No mounted config file!"
  exit 1
fi;

if [[ -d "/mnt/output" ]]; then
  mkdir -p /mnt/output/satellite_images/automatic
  mkdir -p /mnt/output/webapp_results/automatic
else
  echo "No mounted output directory!"
  exit 1
fi;

if echo "${ARGS[@]}" | grep -qw "download-init"; then
  PYTHON_ARGS+=("--download-init")
fi;
if echo "${ARGS[@]}" | grep -qw "download-update"; then
  PYTHON_ARGS+=("--download-update")
fi;
if echo "${ARGS[@]}" | grep -qw "classify-unet"; then
  PYTHON_ARGS+=("--classify-unet")
elif echo "${ARGS[@]}" | grep -qw "classify"; then
  PYTHON_ARGS+=("--classify")
fi;

source /opt/conda/etc/profile.d/conda.sh
conda activate WasteDetection

python run_server_app.py "${PYTHON_ARGS[@]}"
