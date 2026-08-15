"""Shared HTTPS helpers with working SSL certs on macOS/Python."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request

try:
    import certifi
    _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover
    _SSL_CONTEXT = ssl.create_default_context()


def http_json(url: str, *, data: dict | None = None, headers: dict | None = None, timeout: int = 30) -> dict:
    body = None
    req_headers = {'User-Agent': 'BookmarkApp/1.0', **(headers or {})}
    method = 'GET'
    if data is not None:
        body = json.dumps(data).encode('utf-8')
        req_headers.setdefault('Content-Type', 'application/json')
        method = 'POST'
    req = urllib.request.Request(url, data=body, headers=req_headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout, context=_SSL_CONTEXT) as resp:
        return json.loads(resp.read().decode('utf-8'))
