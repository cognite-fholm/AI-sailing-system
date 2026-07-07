"""HTTP client for polar-manager target speeds."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


def fetch_target_bsp(base_url: str, vessel_id: str, tws: float, twa: float) -> float | None:
    if tws <= 0:
        return None
    query = urllib.parse.urlencode({"tws": tws, "twa": abs(twa)})
    url = f"{base_url.rstrip('/')}/polars/{urllib.parse.quote(vessel_id)}/target?{query}"
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return float(data.get("target_bsp", 0)) or None
    except (urllib.error.URLError, json.JSONDecodeError, ValueError, KeyError) as exc:
        logger.debug("polar-manager target lookup failed: %s", exc)
        return None
