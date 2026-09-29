"""HTTP front for bed_alarm on Cloud Run.

  POST /wake    GET /status    POST /sleep

Every request needs `Authorization: Bearer $BED_TOKEN`.
"""
from __future__ import annotations

import hmac
import logging
import os

from aiohttp import web

from bed_alarm import run

logging.basicConfig(level=logging.INFO)


@web.middleware
async def require_token(request: web.Request, handler):
    expected = os.environ["BED_TOKEN"]
    given = request.headers.get("Authorization", "").removeprefix("Bearer ").strip()
    if not hmac.compare_digest(given, expected):
        raise web.HTTPUnauthorized(text="unauthorized\n")
    return await handler(request)


def handler(command: str):
    async def handle(_: web.Request) -> web.Response:
        try:
            result = await run(command)
        except LookupError as e:
            return web.Response(status=400, text=f"{e}\n")
        except Exception:
            logging.exception("bed %s failed", command)
            return web.Response(status=502, text=f"{command} failed, see logs\n")
        logging.info("bed %s: %s", command, result)
        return web.Response(text=result + "\n")
    return handle


app = web.Application(middlewares=[require_token])
app.add_routes([
    web.post("/wake", handler("wake")),
    web.post("/sleep", handler("sleep")),
    web.get("/status", handler("status")),
])

if __name__ == "__main__":
    web.run_app(app, port=int(os.environ.get("PORT", "8080")))
