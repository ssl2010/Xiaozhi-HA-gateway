"""Read-only room-state API consumed by the ESP32 dashboard."""

from __future__ import annotations

import os
import time

from aiohttp import web

from .ha_client import HomeAssistantClient


class DisplayStateServer:
    def __init__(self):
        self.client = HomeAssistantClient(
            os.environ.get("HA_URL", "http://192.168.3.185:8123"),
            os.environ.get("HA_TOKEN", ""),
        )
        self.cache = None
        self.cache_time = 0.0

    async def health(self, request):
        return web.json_response({"status": "ok"})

    async def display(self, request):
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
            {"updated_at": int(time.time()), "rooms": self.cache},
            headers={"Cache-Control": "no-store"},
        )


def main():
    server = DisplayStateServer()
    app = web.Application()
    app.add_routes([web.get("/health", server.health), web.get("/api/display", server.display)])
    web.run_app(app, host="0.0.0.0", port=8090, access_log=None)


if __name__ == "__main__":
    main()
