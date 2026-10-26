"""Tiny stdlib HTTP helpers (no third-party deps so CI stays trivial)."""

import json
import time
import urllib.error
import urllib.request

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) sleeper-autopilot/1.0"


class HttpError(RuntimeError):
    def __init__(self, url, status, body):
        super().__init__(f"HTTP {status} for {url}: {body[:300]}")
        self.status = status
        self.body = body


def request(url, *, data=None, headers=None, timeout=30, retries=3):
    hdrs = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    hdrs.update(headers or {})
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")
    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, headers=hdrs)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", "replace")
            # 4xx won't get better by retrying (bad token, bad request).
            if e.code < 500 or attempt == retries - 1:
                raise HttpError(url, e.code, text) from None
        except (urllib.error.URLError, TimeoutError):
            if attempt == retries - 1:
                raise
        time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def get_json(url, **kw):
    return json.loads(request(url, **kw))


def post_json(url, data, **kw):
    return json.loads(request(url, data=data, **kw))
