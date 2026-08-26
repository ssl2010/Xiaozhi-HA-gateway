#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "${SCRIPT_DIR}/.." && pwd)
DEPLOY_DIR="${PROJECT_DIR}/deploy"

cd "${DEPLOY_DIR}"
test -s .env || { echo "FAIL: deploy/.env is missing" >&2; exit 1; }
test "$(stat -c %a .env)" = "600" || { echo "FAIL: deploy/.env must be mode 600" >&2; exit 1; }

HA_TOKEN=$(sed -n 's/^HA_TOKEN=//p' .env)
test -n "${HA_TOKEN}" || { echo "FAIL: HA_TOKEN is empty" >&2; exit 1; }
trap 'unset HA_TOKEN' EXIT INT TERM

for service in xiaozhi-ha-gateway ha-display-api; do
    container_id=$(docker-compose ps -q "${service}")
    test -n "${container_id}" || { echo "FAIL: ${service} has no container" >&2; exit 1; }
    running=$(docker inspect -f '{{.State.Running}}' "${container_id}")
    test "${running}" = "true" || { echo "FAIL: ${service} is not running" >&2; exit 1; }
done

curl -fsS http://127.0.0.1:8090/health \
    | python3 -c 'import json,sys; assert json.load(sys.stdin) == {"status": "ok"}'

curl -fsS http://127.0.0.1:8003/xiaozhi/ota/ \
    | grep -Fq 'ws://192.168.3.188:8000/xiaozhi/v1/'

curl -fsS http://127.0.0.1:8090/api/display \
    | python3 -c '
import json, sys
data = json.load(sys.stdin)
rooms = data.get("rooms")
assert isinstance(rooms, dict)
assert set(rooms).issubset({"主卧", "次卧", "客厅", "书房"})
assert "climate" not in rooms.get("次卧", {})
allowed_roles = {"light", "climate", "floor_lamp", "air_purifier", "temperature", "humidity", "devices"}
allowed_devices = {"light", "climate", "floor_lamp", "air_purifier"}
for roles in rooms.values():
    assert set(roles).issubset(allowed_roles)
    devices = roles.get("devices", [])
    assert all(item.get("id") in allowed_devices for item in devices)
'

if docker-compose logs 2>&1 | grep -Fq "${HA_TOKEN}"; then
    echo "FAIL: HA token was found in container logs" >&2
    exit 1
fi

echo "PASS: containers, health, OTA, display contract, and token-log checks"
