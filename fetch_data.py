"""
fetch_data.py - download Boston Marathon results 2001-2014 and race-day weather.
================================================================================
Results: llimllib/bostonmarathon (public mirror of official results). We only need
the `official` finish-time column, available for every year.

Weather: Open-Meteo's free historical archive API (no key). For each year's race
date (Patriots' Day, the 3rd Monday of April) we pull hourly 2 m temperature near
the course midpoint and keep the late-morning-to-afternoon window runners are out.

Everything is cached under ./data/ (git-ignored).
"""
import os
import csv
import json
import urllib.request

HERE = os.path.dirname(__file__)
DATA = os.path.join(HERE, "data")
RESULTS_URL = "https://raw.githubusercontent.com/llimllib/bostonmarathon/master/results/{y}/results.csv"

# Boston Marathon race dates (Patriots' Day, 3rd Monday of April)
RACE_DATES = {
    2001: "2001-04-16", 2002: "2002-04-15", 2003: "2003-04-21", 2004: "2004-04-19",
    2005: "2005-04-18", 2006: "2006-04-17", 2007: "2007-04-16", 2008: "2008-04-21",
    2009: "2009-04-20", 2010: "2010-04-19", 2011: "2011-04-18", 2012: "2012-04-16",
    2013: "2013-04-15", 2014: "2014-04-21",
}
# course midpoint (Hopkinton -> Boston), roughly Natick/Wellesley
LAT, LON = 42.30, -71.35


def fetch_results():
    os.makedirs(DATA, exist_ok=True)
    for y in RACE_DATES:
        out = os.path.join(DATA, f"boston_{y}.csv")
        if os.path.exists(out):
            continue
        urllib.request.urlretrieve(RESULTS_URL.format(y=y), out)
        print(f"  results {y} -> {os.path.getsize(out):,} bytes")


def fetch_weather():
    rows = []
    for y, d in RACE_DATES.items():
        url = ("https://archive-api.open-meteo.com/v1/archive"
               f"?latitude={LAT}&longitude={LON}&start_date={d}&end_date={d}"
               "&hourly=temperature_2m&temperature_unit=fahrenheit"
               "&timezone=America%2FNew_York")
        with urllib.request.urlopen(url, timeout=60) as r:
            j = json.loads(r.read())
        temps = j["hourly"]["temperature_2m"]
        times = j["hourly"]["time"]
        # average over the 10:00-16:00 window runners are on course
        window = [t for tm, t in zip(times, temps) if 10 <= int(tm[11:13]) <= 16 and t is not None]
        mid = sum(window) / len(window)
        mx = max(t for t in temps if t is not None)
        rows.append({"year": y, "date": d, "temp_midday_F": round(mid, 1), "temp_max_F": round(mx, 1)})
        print(f"  weather {y}: midday {mid:.1f}F, max {mx:.1f}F")
    with open(os.path.join(DATA, "weather.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["year", "date", "temp_midday_F", "temp_max_F"])
        w.writeheader(); w.writerows(rows)


if __name__ == "__main__":
    print("Downloading results...")
    fetch_results()
    print("Fetching race-day weather (Open-Meteo)...")
    fetch_weather()
    print("Done.")
