#!/usr/bin/env python3
"""
Mirror the newest Trout Lake buoy reading into a small JSON file.

Why: the UW-Madison Center for Limnology's buoy feed only allows browsers
on https://uwcfl.github.io to read it (CORS). A server - like a GitHub
Actions runner - isn't subject to that rule, so this script fetches the
same two daily CSV files the official viewer uses
(https://uwcfl.github.io/buoy-viewer/trout.html) and writes the newest
reading to trout_latest.json, which the DVM drawing then reads from the
same GitHub Pages site (https://audreylolaarts.github.io/DVM_Zooplankton/).

Standard library only; run with:  python3 scripts/fetch_trout_buoy.py [out_path]
"""

import csv
import io
import json
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

EXPORT_URL = "https://buoy-export-proxy.uwcfl.workers.dev/Trout"
WTEMP_URL = "https://buoy-watertemp-proxy.uwcfl.workers.dev/Trout"
DEPTHS = [0, 0.25, 0.5, 0.75, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6, 7, 8, 9, 10,
          11, 12, 13, 14, 16, 20, 25, 30]
WEATHER_FIELDS = ["air_temp", "rel_hum", "wind_speed", "wind_dir", "par",
                  "do_raw", "do_sat", "spec_cond", "precip_mm"]
MAX_DAYS_BACK = 3
CT = ZoneInfo("America/Chicago")


def num(v):
    if v is None:
        return None
    s = str(v).strip()
    if s in ("", "NAN", "-99"):
        return None
    try:
        f = float(s)
    except ValueError:
        return None
    return None if f == -99 else f


def get_rows(base, day):
    url = f"{base}/{day:%Y}/{day:%Y%m%d}"
    req = urllib.request.Request(url, headers={"User-Agent": "dvm-lake-map mirror (GitHub Actions)"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
    except Exception as e:  # file not posted yet, network, etc.
        print(f"  {url}: {e}")
        return []
    rows = list(csv.DictReader(io.StringIO(text)))
    # drop a final row that was still being written
    return [r for r in rows if r.get("TIMESTAMP") and None not in r.values()]


def profile_of(row):
    out = []
    for i, depth in enumerate(DEPTHS):
        key = "RBRSurfTemp" if i == 0 else f"RBRTempProfile({i})"
        t = num(row.get(key))
        if t is not None and -2 < t < 40:
            out.append({"depth": depth, "temp": round(t, 3)})
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "trout_latest.json"
    today = datetime.now(CT).date()

    for back in range(MAX_DAYS_BACK + 1):
        day = today - timedelta(days=back)
        print(f"Checking {day}")
        wrows = get_rows(WTEMP_URL, day)
        for row in reversed(wrows):
            prof = profile_of(row)
            if len(prof) >= len(DEPTHS) / 2:
                break
        else:
            continue  # no usable profile this day, look further back

        ts = row["TIMESTAMP"].strip()
        erows = get_rows(EXPORT_URL, day)
        erow = next((r for r in erows if r["TIMESTAMP"].strip() == ts), erows[-1] if erows else {})
        data = {
            "source": "UW-Madison Center for Limnology, Trout Lake buoy (not quality controlled)",
            "viewer": "https://uwcfl.github.io/buoy-viewer/trout.html",
            "mirrored_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "timestamp_local": ts,  # America/Chicago, as logged by the buoy
            "profile": prof,
            "weather": {k: num(erow.get(k)) for k in WEATHER_FIELDS},
        }
        # leave the file untouched when the buoy hasn't posted anything new
        try:
            with open(out_path) as f:
                if json.load(f).get("timestamp_local") == ts:
                    print(f"Newest reading ({ts}) already mirrored; nothing to do.")
                    return
        except (OSError, ValueError):
            pass
        with open(out_path, "w") as f:
            json.dump(data, f, indent=1)
        print(f"Wrote reading from {ts} ({len(prof)} temperature sensors) to {out_path}")
        return

    print("No usable buoy reading found; leaving existing file alone.")


if __name__ == "__main__":
    main()
