"""Read-only room-state API consumed by the ESP32 dashboard."""

from __future__ import annotations

import os
import time

from .ha_client import HomeAssistantClient
from .intent_parser import Command


DEVICE_META = {
    "climate": {"name": "空调", "type": "climate"},
    "light": {"name": "吸顶灯", "type": "light"},
    "floor_lamp": {"name": "落地灯", "type": "switch"},
    "air_purifier": {"name": "空气净化器", "type": "purifier"},
}


def compact_room_states(states):
    result = {}
    for room_name, roles in states.items():
        room = {}
        devices = []
        for role, item in roles.items():
            state = item.get("state")
            attributes = item.get("attributes", {})
            compact = {"state": state}
            if role == "climate":
                for key in ("temperature", "current_temperature", "fan_mode", "swing_mode"):
                    if attributes.get(key) is not None:
                        compact[key] = attributes[key]
            elif role == "light" and attributes.get("brightness") is not None:
                compact["brightness_pct"] = round(attributes["brightness"] * 100 / 255)
                if attributes.get("effect_list"):
                    compact["effect_list"] = attributes["effect_list"]
            elif role == "air_purifier":
                for key in ("percentage", "preset_mode", "preset_modes"):
                    if attributes.get(key) is not None:
                        compact[key] = attributes[key]
            room[role] = compact
            if role in DEVICE_META:
                devices.append({"id": role, **DEVICE_META[role], **compact})
        if devices:
            room["devices"] = devices
        if room:
            result[room_name] = room
    return result


class DisplayStateServer:
    def __init__(self):
        self.client = HomeAssistantClient(
            os.environ.get("HA_URL", "http://192.168.3.185:8123"),
            os.environ.get("HA_TOKEN", ""),
        )
        self.cache = None
        self.cache_time = 0.0

    async def health(self, request):
        from aiohttp import web

        return web.json_response({"status": "ok"})

    async def display(self, request):
        from aiohttp import web

        if not os.environ.get("HA_TOKEN"):
            raise web.HTTPServiceUnavailable(text="HA token is not configured")
        now = time.monotonic()
        if self.cache is None or now - self.cache_time >= 3:
            try:
                self.cache = await self.client.room_states()
                self.cache_time = now
            except Exception:
                raise web.HTTPBadGateway(text="Home Assistant is unavailable")
        return web.json_response(
            {"updated_at": int(time.time()), "rooms": compact_room_states(self.cache)},
            headers={"Cache-Control": "no-store"},
        )

    async def control(self, request):
        from aiohttp import web

        if not os.environ.get("HA_TOKEN"):
            raise web.HTTPServiceUnavailable(text="HA token is not configured")
        try:
            payload = await request.json()
            command = Command(
                room=str(payload.get("room", "")),
                device=str(payload.get("device", "")),
                action=str(payload.get("action", "")),
                value=payload.get("value"),
            )
            result = await self.client.execute(command)
        except (ValueError, TypeError) as exc:
            raise web.HTTPBadRequest(text=str(exc))
        except Exception:
            raise web.HTTPBadGateway(text="Home Assistant control failed")
        self.cache = None
        return web.json_response({"status": "ok", "service": result["service"]})


def main():
    from aiohttp import web

    server = DisplayStateServer()
    app = web.Application()
    app.add_routes([
        web.get("/health", server.health),
        web.get("/api/display", server.display),
        web.post("/api/control", server.control),
    ])
    web.run_app(app, host="0.0.0.0", port=8090, access_log=None)


if __name__ == "__main__":
    main()
