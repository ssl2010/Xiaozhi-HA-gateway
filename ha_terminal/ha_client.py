"""Small Home Assistant REST client with an explicit entity allow-list."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .intent_parser import Command


class UnsupportedCommand(ValueError):
    pass


def load_entities(path: str | Path | None = None) -> dict[str, dict[str, str]]:
    source = Path(path) if path else Path(__file__).with_name("entities.json")
    return json.loads(source.read_text(encoding="utf-8"))


def build_service_call(
    command: Command, entities: dict[str, dict[str, str]]
) -> tuple[str, str, dict[str, Any]]:
    room = entities.get(command.room)
    if not room or command.device not in room:
        raise UnsupportedCommand(f"{command.room}暂未配置{command.device}")

    entity_id = room[command.device]
    domain = entity_id.split(".", 1)[0]
    data: dict[str, Any] = {"entity_id": entity_id}

    if command.action in {"turn_on", "turn_off"}:
        return domain, command.action, data
    if command.device == "climate" and command.action == "set_temperature":
        data["temperature"] = command.value
        return "climate", "set_temperature", data
    if command.device == "climate" and command.action == "set_hvac_mode":
        hvac_mode = str(command.value)
        if hvac_mode not in {"off", "auto", "cool", "heat", "dry", "fan_only"}:
            raise UnsupportedCommand("空调模式不受支持")
        data["hvac_mode"] = hvac_mode
        return "climate", "set_hvac_mode", data
    if command.device == "climate" and command.action == "set_fan_mode":
        data["fan_mode"] = command.value
        return "climate", "set_fan_mode", data
    if command.device == "climate" and command.action == "set_swing":
        swing_mode = command.value
        if swing_mode is True:  # Compatibility with commands created before capability discovery.
            swing_mode = "vertical"
        elif swing_mode is False:
            swing_mode = "off"
        if swing_mode not in {"off", "vertical", "horizontal", "both"}:
            raise UnsupportedCommand("摆风只支持关闭、上下、左右或全向")
        data["swing_mode"] = swing_mode
        return "climate", "set_swing_mode", data
    if command.device == "light" and command.action == "set_brightness":
        value = int(command.value)
        if not 0 <= value <= 100:
            raise UnsupportedCommand("灯光亮度必须在0到100之间")
        data["brightness_pct"] = value
        return "light", "turn_on", data
    if command.device == "light" and command.action == "set_effect":
        data["effect"] = str(command.value)
        return "light", "turn_on", data
    if command.device == "air_purifier" and command.action == "set_preset_mode":
        preset_mode = str(command.value)
        if preset_mode not in {"自动", "睡眠", "最爱"}:
            raise UnsupportedCommand("空气净化器只支持自动、睡眠或最爱模式")
        data["preset_mode"] = preset_mode
        return "fan", "set_preset_mode", data
    if command.device == "air_purifier" and command.action == "set_percentage":
        value = int(command.value)
        if not 0 <= value <= 100:
            raise UnsupportedCommand("空气净化器风量必须在0到100之间")
        data["percentage"] = value
        return "fan", "set_percentage", data
    raise UnsupportedCommand(f"不支持的动作: {command.action}")


class HomeAssistantClient:
    def __init__(self, base_url: str, token: str, entities: dict[str, dict[str, str]] | None = None):
        self.base_url = base_url.rstrip("/")
        self.entities = entities or load_entities()
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def execute(self, command: Command) -> dict[str, Any]:
        import httpx

        domain, service, data = build_service_call(command, self.entities)
        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            response = await client.post(
                f"{self.base_url}/api/services/{domain}/{service}",
                headers=self._headers,
                json=data,
            )
        response.raise_for_status()
        return {"domain": domain, "service": service, "data": data, "result": response.json()}

    async def room_states(self) -> dict[str, dict[str, Any]]:
        import httpx

        async with httpx.AsyncClient(timeout=httpx.Timeout(8.0, connect=3.0)) as client:
            response = await client.get(f"{self.base_url}/api/states", headers=self._headers)
        response.raise_for_status()
        by_id = {item["entity_id"]: item for item in response.json()}
        result: dict[str, dict[str, Any]] = {}
        for room_name, room_entities in self.entities.items():
            room: dict[str, Any] = {}
            for role, entity_id in room_entities.items():
                state = by_id.get(entity_id)
                # Missing entities remain absent. A known but unavailable entity
                # is included so the display can render it as offline.
                if state is not None:
                    room[role] = {
                        "entity_id": entity_id,
                        "state": state.get("state"),
                        "attributes": state.get("attributes", {}),
                    }
            if room:
                result[room_name] = room
        return result
