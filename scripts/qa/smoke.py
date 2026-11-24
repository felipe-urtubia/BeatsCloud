#!/usr/bin/env python3
"""Read-only local QA smoke checks for frontend, API, preview, and permissions."""

from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


backend = f"http://127.0.0.1:{os.environ.get('QA_BACKEND_PORT', '8010')}"
frontend = f"http://127.0.0.1:{os.environ.get('QA_FRONTEND_PORT', '3010')}"


def get(url: str):
    return urlopen(url, timeout=8)


def fail(message: str) -> None:
    print(f"QA smoke failed: {message}", file=sys.stderr)
    raise SystemExit(1)


try:
    with get(frontend + "/") as response:
        if response.status != 200:
            fail(f"Vite returned HTTP {response.status}")
    with get(frontend + "/api/session/") as response:
        if response.status != 200:
            fail(f"Vite proxy to Django session returned HTTP {response.status}")
    with get(frontend + "/api/catalogo/") as response:
        catalog = json.load(response)
    required = {"tracks", "total_resultados", "pagina_actual", "total_paginas"}
    if not required.issubset(catalog):
        fail("catalog response is missing expected pagination fields")
    if not catalog["tracks"] or catalog["total_resultados"] < len(catalog["tracks"]):
        fail("QA catalog is empty or has inconsistent totals")

    track = next((item for item in catalog["tracks"] if item.get("preview")), None)
    if track is None:
        fail("catalog tracks have no preview fixture")
    with get(frontend + track["preview"]) as response:
        if response.status != 200 or not response.headers.get("Content-Type", "").startswith("audio/"):
            fail(f"preview returned HTTP {response.status} or non-audio content")
        if not response.read(1):
            fail("preview response was empty")

    try:
        response = get(frontend + f"/api/track/{track['id_track']}/descargar/")
    except HTTPError as exc:
        if exc.code != 403:
            fail(f"anonymous download returned HTTP {exc.code}, expected 403")
    else:
        response.close()
        fail("anonymous download unexpectedly succeeded")
except (URLError, TimeoutError, OSError, ValueError, KeyError) as exc:
    fail(str(exc))

print(
    "QA smoke passed: Vite HTTP 200; Vite-to-Django session/catalog proxy HTTP 200; "
    f"catalog {len(catalog['tracks'])}/{catalog['total_resultados']} tracks; "
    f"preview HTTP 200 ({track['id_track']}); anonymous download HTTP 403."
)
