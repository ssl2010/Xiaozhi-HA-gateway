#!/bin/sh
set -eu

MODEL_NAME=sherpa-onnx-paraformer-zh-small-2024-03-09
MODEL_URL="https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/${MODEL_NAME}.tar.bz2"
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DEPLOY_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/../deploy" && pwd)

mkdir -p "${DEPLOY_DIR}/models"
if [ -f "${DEPLOY_DIR}/models/${MODEL_NAME}/model.int8.onnx" ]; then
    echo "Model already present"
    exit 0
fi

ARCHIVE="${DEPLOY_DIR}/models/${MODEL_NAME}.tar.bz2"
curl -fL --retry 3 -o "${ARCHIVE}" "${MODEL_URL}"
tar -xjf "${ARCHIVE}" -C "${DEPLOY_DIR}/models"
echo "Downloaded ${MODEL_NAME}"
