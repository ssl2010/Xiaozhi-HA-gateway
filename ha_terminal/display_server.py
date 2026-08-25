"""Read-only room-state API consumed by the ESP32 dashboard."""

from __future__ import annotations

import os
import time

from .ha_client import HomeAssistantClient


def compact_room_states(states):
    result = {}
    for room_name, roles in states.items():
        room = {}
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
            room[role] = compact
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


def main():
    from aiohttp import web

    server = DisplayStateServer()
    app = web.Application()
    app.add_routes([web.get("/health", server.health), web.get("/api/display", server.display)])
    web.run_app(app, host="0.0.0.0", port=8090, access_log=None)


if __name__ == "__main__":
    main()
