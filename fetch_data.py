"""
fetch_data.py: download Boston Marathon results and race-day weather.

Results
  adrian3/Boston-Marathon-Data-Project, results1897.csv to results2019.csv, pinned to
  commit ADRIAN3_SHA so a rerun reads the same files.
  llimllib/bostonmarathon, 2001 to 2014, used only to cross-check adrian3 where the two
  overlap (the October 2026 upgrade uses adrian3 for every year).

Weather
  Open-Meteo historical archive (ERA5 reanalysis, 1940 onward), hourly, at three points
  on the course: the Hopkinton start, Wellesley near halfway, and the Boylston Street
  finish. One call per race day; the race date for each year comes from race_days().

Everything goes to ~/data-cache/marathon-heat-tax/ (outside the repo). The small
derived race-day table is written to tables/race_days.csv.
"""
import csv
import datetime as dt
import json
import os
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.expanduser("~/data-cache/marathon-heat-tax")
TAB = os.path.join(HERE, "tables")

ADRIAN3_SHA = "cc4fdd8404a1fe54455bac66ad5727567cd917ed"
ADRIAN3_URL = "https://raw.githubusercontent.com/adrian3/Boston-Marathon-Data-Project/{sha}/results{y}.csv"
LLIM_URL = "https://raw.githubusercontent.com/llimllib/bostonmarathon/master/results/{y}/results.csv"

FIRST_YEAR, LAST_YEAR = 1940, 2019   # ERA5 starts in 1940; adrian3 ends in 2019

# Course points (lat, lon): Hopkinton start, Wellesley (about 13 mi), Boylston St finish.
COURSE = [(42.2297, -71.5196), (42.2968, -71.2924), (42.3500, -71.0780)]
COURSE_BEARING_DEG = 69.6   # initial great-circle bearing, start to finish (ENE)

HOURLY = ("temperature_2m,dew_point_2m,relative_humidity_2m,wind_speed_10m,"
          "wind_direction_10m,shortwave_radiation,cloud_cover,precipitation")

SOURCES = {
    "date_pre1969": "Wikipedia, Boston Marathon: 'Through 1968, the holiday was observed on April 19', moved to Monday when April 19 fell on a Sunday",
    "date_1969": "Wikipedia, Boston Marathon: 'Since 1969, the holiday has been observed on the third Monday in April'",
    "noon": "Wikipedia, Boston Marathon: 'Through 2005, the race began at noon'",
    "2006": "Wikipedia, Boston Marathon: 2006 wave start, first group at noon, second at 12:30",
    "2007": "B.A.A. announcement, August 2006 (worldmarathonmajors.com, '2007 Boston Marathon to begin at 10am'): wave one 10:00, wave two 10:30",
    "2011": "B.A.A. press release on the three-wave start from 2011 (marathonguide.com); last wave taken as 10:40",
    "2015": "Wikipedia, Boston Marathon, 2019 schedule: elite men 10:00, wave one 10:02, wave four 11:15; assumed the same for 2015 to 2018 (four waves)",
}


def race_date(y):
    if y >= 1969:
        d = dt.date(y, 4, 1)
        first_monday = d + dt.timedelta(days=(0 - d.weekday()) % 7)
        return first_monday + dt.timedelta(days=14), "date_1969"
    d = dt.date(y, 4, 19)
    if d.weekday() == 6:
        d = dt.date(y, 4, 20)
    return d, "date_pre1969"


def race_days():
    """One row per race: date, start time of the lead men, and the hourly windows used
    for weather. elite window: lead men's race (start hour to start + 2 h).
    field window: first start to the time the bulk of the field has finished."""
    rows = []
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        d, dsrc = race_date(y)
        if y <= 2005:
            start, last_wave, ssrc = "12:00", "12:00", "noon"
        elif y == 2006:
            start, last_wave, ssrc = "12:00", "12:30", "2006"
        elif y <= 2010:
            start, last_wave, ssrc = "10:00", "10:30", "2007"
        elif y <= 2014:
            start, last_wave, ssrc = "10:00", "10:40", "2011"
        else:
            start, last_wave, ssrc = "10:00", "11:15", "2015"
        h0 = int(start[:2])
        hl = int(last_wave[:2]) + (1 if last_wave[3:] != "00" else 0)
        rows.append({
            "year": y, "date": d.isoformat(), "weekday": d.strftime("%A"),
            "start_lead_men": start, "start_last_wave": last_wave,
            "elite_hours": f"{h0}-{h0 + 2}", "field_hours": f"{h0}-{hl + 4}",
            "date_source": SOURCES[dsrc], "start_source": SOURCES[ssrc],
        })
    return rows


def get(url, out, tries=4):
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return False
    for k in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                data = r.read()
            with open(out, "wb") as fh:
                fh.write(data)
            return True
        except Exception as e:  # network hiccup or rate limit
            if k == tries - 1:
                raise
            time.sleep(3 * (k + 1))


def fetch_results():
    a = os.path.join(CACHE, "adrian3"); os.makedirs(a, exist_ok=True)
    for y in range(1897, LAST_YEAR + 1):
        if get(ADRIAN3_URL.format(sha=ADRIAN3_SHA, y=y), os.path.join(a, f"results{y}.csv")):
            print("  adrian3", y)
    l = os.path.join(CACHE, "llimllib"); os.makedirs(l, exist_ok=True)
    for y in range(2001, 2015):
        if get(LLIM_URL.format(y=y), os.path.join(l, f"boston_{y}.csv")):
            print("  llimllib", y)


def fetch_weather(rows):
    w = os.path.join(CACHE, "weather"); os.makedirs(w, exist_ok=True)
    lat = ",".join(str(p[0]) for p in COURSE)
    lon = ",".join(str(p[1]) for p in COURSE)
    for r in rows:
        out = os.path.join(w, f"{r['year']}.json")
        url = ("https://archive-api.open-meteo.com/v1/archive"
               f"?latitude={lat}&longitude={lon}&start_date={r['date']}&end_date={r['date']}"
               f"&hourly={HOURLY}&temperature_unit=fahrenheit&wind_speed_unit=mph"
               "&timezone=America%2FNew_York")
        if get(url, out):
            print("  weather", r["year"], r["date"])
            time.sleep(0.4)


def main():
    os.makedirs(CACHE, exist_ok=True); os.makedirs(TAB, exist_ok=True)
    rows = race_days()
    with open(os.path.join(TAB, "race_days.csv"), "w", newline="", encoding="utf-8") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
    print("Results ->", CACHE); fetch_results()
    print("Weather (Open-Meteo archive, ERA5)"); fetch_weather(rows)
    with open(os.path.join(CACHE, "SOURCES.json"), "w") as fh:
        json.dump({"adrian3_sha": ADRIAN3_SHA, "fetched": dt.date.today().isoformat()}, fh)
    print("Done.")


if __name__ == "__main__":
    main()
