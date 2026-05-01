"""
Fetch lat/lon for each station via the Rejseplan location.details endpoint.
Reads RPL_ACCESS_ID from .env in the project root.

Usage:
    uv run scripts/get_station_coords.py
"""

import os
import requests
from pathlib import Path

# Load .env manually (no extra dependency needed)
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

STATIONS = [
    {"id": "8600675", "name": "Lyngby"},
    {"id": "8600626", "name": "Kbh H"},
    {"id": "8600646", "name": "Nørreport"},
    {"id": "8600642", "name": "Nørrebro"},
    {"id": "8600655", "name": "Hellerup"},
    {"id": "8600645", "name": "Vesterport"},
    {"id": "8600650", "name": "Østerport"},
]

BASE_URL = "https://www.rejseplanen.dk/api/location.details"
ACCESS_ID = os.environ.get("RPL_ACCESS_ID")

if not ACCESS_ID:
    raise SystemExit("RPL_ACCESS_ID not set — add it to .env")

session = requests.Session()
session.headers.update({"Accept": "application/json"})

for station in STATIONS:
    resp = session.get(BASE_URL, params={
        "accessId": ACCESS_ID,
        "id": station["id"],
    }, timeout=15)
    resp.raise_for_status()

    stops = resp.json().get("stopLocationOrCoordLocation", [])
    stop = stops[0]["StopLocation"] if stops else None

    if stop:
        lat = stop.get("lat")
        lon = stop.get("lon")
        print(f'{{"id": "{station["id"]}", "name": "{station["name"]}", "lat": {lat}, "lon": {lon}}},')
    else:
        print(f'# {station["name"]} ({station["id"]}): no result')
