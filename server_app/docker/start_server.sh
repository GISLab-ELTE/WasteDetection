#!/bin/bash

ARGS=$@
PYTHON_ARGS=()

if [[ -f "/mnt/config.docker.json" ]]; then
  cp /mnt/config.docker.json /workspace/resources/config.local.json
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
if echo "${ARGS[@]}" | grep -qw "classify"; then
  PYTHON_ARGS+=("--classify")
fi;

cd src
source /opt/conda/etc/profile.d/conda.sh
conda activate WasteDetectionServerApp

python __main__.py "${PYTHON_ARGS[@]}"
