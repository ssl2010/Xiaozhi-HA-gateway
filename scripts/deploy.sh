#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
DEPLOY_DIR="${PROJECT_DIR}/deploy"

if [ ! -f "${DEPLOY_DIR}/.env" ]; then
    echo "Missing deploy/.env; configure HA_TOKEN on the server first" >&2
    exit 2
fi

if [ ! -f "${DEPLOY_DIR}/data/.config.yaml" ]; then
    cp "${DEPLOY_DIR}/data/.config.yaml.example" "${DEPLOY_DIR}/data/.config.yaml"
fi

"${SCRIPT_DIR}/download-model.sh"
cd "${DEPLOY_DIR}"
docker-compose build
docker-compose up -d
docker-compose ps
