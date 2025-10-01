#!/usr/bin/env python3
"""Update visitor map data from a remote analytics endpoint.

Expected environment variables
-------------------------------
VISITOR_MAP_ENDPOINT
    URL returning JSON visitor data. The payload should be a list of objects
    containing at least coordinates and an optional visitor count. Supported
    keys include "name", "city", "country", "latitude", "longitude",
    "lat", "lon", "lng", "count", "visitors", and "value".

VISITOR_MAP_API_TOKEN (optional)
    If set, the token is attached as a Bearer authorization header.

The script normalises the response and writes `_data/visitor_map.yml` so the
homepage map stays in sync with your analytics provider.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List

import yaml

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "_data" / "visitor_map.yml"


def fetch_json(url: str, token: str | None = None) -> Any:
    request = urllib.request.Request(url)
    if token:
        request.add_header("Authorization", f"Bearer {token}")

    with urllib.request.urlopen(request) as response:  # nosec B310
        charset = response.headers.get_content_charset("utf-8")
        payload = response.read().decode(charset)
    return json.loads(payload)


def normalise(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalised: List[Dict[str, Any]] = []

    for entry in records:
        if not isinstance(entry, dict):
            continue

        name_parts: List[str] = []
        raw_name = entry.get("name")
        if isinstance(raw_name, str) and raw_name.strip():
            name_parts = [raw_name.strip()]
        else:
            city = entry.get("city")
            country = entry.get("country")
            if isinstance(city, str) and city.strip():
                name_parts.append(city.strip())
            if isinstance(country, str) and country.strip():
                name_parts.append(country.strip())

        name = ", ".join(name_parts) if name_parts else "Visitor"

        lat = entry.get("latitude")
        if lat is None:
            lat = entry.get("lat")

        lon = entry.get("longitude")
        if lon is None:
            lon = entry.get("lon")
        if lon is None:
            lon = entry.get("lng")

        try:
            lat_f = float(lat)
            lon_f = float(lon)
        except (TypeError, ValueError):
            continue

        raw_count = entry.get("count")
        if raw_count is None:
            raw_count = entry.get("visitors")
        if raw_count is None:
            raw_count = entry.get("value")

        try:
            count = int(float(raw_count)) if raw_count is not None else None
        except (TypeError, ValueError):
            count = None

        normalised.append(
            {
                "name": name,
                "latitude": round(lat_f, 4),
                "longitude": round(lon_f, 4),
                "count": count if count is not None else 1,
            }
        )

    normalised.sort(key=lambda item: item.get("count", 0), reverse=True)
    return normalised


def main() -> int:
    endpoint = os.environ.get("VISITOR_MAP_ENDPOINT")
    if not endpoint:
        print("VISITOR_MAP_ENDPOINT is not set. Skipping visitor map update.")
        return 0

    token = os.environ.get("VISITOR_MAP_API_TOKEN")

    try:
        payload = fetch_json(endpoint, token)
    except urllib.error.HTTPError as exc:  # pragma: no cover - network error handling
        print(f"Failed to fetch visitor map data: HTTP {exc.code} {exc.reason}")
        return 1
    except urllib.error.URLError as exc:  # pragma: no cover - network error handling
        print(f"Failed to fetch visitor map data: {exc.reason}")
        return 1
    except json.JSONDecodeError as exc:
        print(f"Visitor map endpoint did not return valid JSON: {exc}")
        return 1

    if isinstance(payload, dict) and "data" in payload:
        records = payload.get("data")
    else:
        records = payload

    if not isinstance(records, list):
        print("Visitor map endpoint must return a list of location records.")
        return 1

    normalised = normalise(records)

    if not normalised:
        print("No valid visitor records found; leaving existing data untouched.")
        return 0

    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(normalised, handle, allow_unicode=True, sort_keys=False)

    print(f"Updated {DATA_PATH.relative_to(ROOT)} with {len(normalised)} records.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
