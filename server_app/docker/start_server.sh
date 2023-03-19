#!/bin/bash

ARGS=$@
PYTHON_ARGS=()

if echo "${ARGS[@]}" | grep -qw "startup"; then
  PYTHON_ARGS+=("-st")
fi;
if echo "${ARGS[@]}" | grep -qw "sleep"; then
  PYTHON_ARGS+=("-s")
fi;

cd src
source /opt/conda/etc/profile.d/conda.sh
conda activate WasteDetectionServerApp

python __main__.py "${PYTHON_ARGS[@]}"
