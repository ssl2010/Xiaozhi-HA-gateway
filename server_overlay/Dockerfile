ARG XIAOZHI_SERVER_IMAGE=ghcr.nju.edu.cn/xinnan-tech/xiaozhi-esp32-server:server_latest
FROM ${XIAOZHI_SERVER_IMAGE}

COPY ha_terminal /opt/xiaozhi-esp32-server/ha_terminal
COPY server_overlay/core/providers/intent/ha_rules /opt/xiaozhi-esp32-server/core/providers/intent/ha_rules
COPY server_overlay/core/providers/llm/local_control /opt/xiaozhi-esp32-server/core/providers/llm/local_control
COPY server_overlay/plugins_func/functions/ha_control.py /opt/xiaozhi-esp32-server/plugins_func/functions/ha_control.py
