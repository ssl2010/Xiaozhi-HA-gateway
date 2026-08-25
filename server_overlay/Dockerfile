# Pin the tested upstream image so future `server_latest` changes cannot alter
# this deployment unexpectedly. Override the build arg deliberately to upgrade.
ARG XIAOZHI_SERVER_IMAGE=ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest@sha256:f77d000713fde8c4bcb6a62e83a507b4fc8f92e9e5ad523eb0cbf41a37e3913c
FROM ${XIAOZHI_SERVER_IMAGE}

COPY ha_terminal /opt/xiaozhi-esp32-server/ha_terminal
COPY server_overlay/core/providers/intent/ha_rules /opt/xiaozhi-esp32-server/core/providers/intent/ha_rules
COPY server_overlay/core/providers/llm/local_control /opt/xiaozhi-esp32-server/core/providers/llm/local_control
COPY server_overlay/plugins_func/functions/ha_control.py /opt/xiaozhi-esp32-server/plugins_func/functions/ha_control.py
