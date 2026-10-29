"""
build_dataset.py: turn the cached downloads into three small tables.

tables/field_by_year.csv   one row per race, 1940 to 2019: finisher count, field
                           percentiles (10th to 90th), men's 1st, 10th and 25th place
                           times, and whether the list is complete enough for percentiles.
tables/weather_by_year.csv race-day weather on the course for two windows (lead men,
                           whole field): temperature, dew point, humidity, heat index,
                           wind along the course, sun, cloud, rain.
tables/source_reconcile.csv adrian3 against llimllib, 2001 to 2014.

Exclusions: wheelchair and handcycle entrants. adrian3 has none outside 1993 and 1995,
where its own README says some may be mixed in (it removed every time faster than the
winner); a 120-minute floor drops any that remain. In llimllib they carry a W bib.
"""
import csv
import glob
import json
import math
import os

import numpy as np
import pandas as pd

from fetch_data import CACHE, COURSE_BEARING_DEG, FIRST_YEAR, LAST_YEAR

HERE = os.path.dirname(os.path.abspath(__file__))
TAB = os.path.join(HERE, "tables")
PCTS = [10, 25, 50, 75, 90]


def read_adrian3(y):
    """adrian3 files are MySQL exports: quoted text, \\" escapes, bare NULL."""
    p = os.path.join(CACHE, "adrian3", f"results{y}.csv")
    df = pd.read_csv(p, escapechar="\\", na_values=["NULL"], keep_default_na=True,
                     low_memory=False, dtype=str)
    sec = pd.to_numeric(df["seconds"], errors="coerce")
    g = df["gender"].fillna("U").str.upper().str.strip()
    out = pd.DataFrame({"min": sec / 60.0, "gender": g})
    out = out[(out["min"] >= 120) & (out["min"] <= 600)]
    return out


def read_llim(y):
    df = pd.read_csv(os.path.join(CACHE, "llimllib", f"boston_{y}.csv"), low_memory=False, dtype=str)
    bib = df["bib"].fillna("").str.strip()
    off = pd.to_numeric(df["official"], errors="coerce")
    keep = ~bib.str.upper().str.startswith(("W", "H")) & off.between(120, 600)
    return pd.DataFrame({"min": off[keep], "gender": df.loc[keep, "gender"].str.upper()})


def place(times, k):
    t = np.sort(times.values)
    return float(t[k - 1]) if len(t) >= k else np.nan


def field_table():
    rows = []
    for y in range(FIRST_YEAR, LAST_YEAR + 1):
        d = read_adrian3(y)
        men = d.loc[d["gender"] == "M", "min"]
        r = {"year": y, "n_listed": len(d), "n_men": len(men), "n_women": int((d["gender"] == "F").sum()),
             "max_min": round(d["min"].max(), 2),
             "men_1st": place(men, 1), "men_10th": place(men, 10), "men_25th": place(men, 25),
             "men_100th": place(men, 100), "men_1000th": place(men, 1000),
             "share_over_5h": round(float((d["min"] > 300).mean()), 4)}
        # a list that runs well past 5:00 (at least 2% of it slower) is taken as the whole field
        r["complete_list"] = bool(r["share_over_5h"] >= 0.02 and len(d) > 5000)
        for q in PCTS:
            r[f"p{q}"] = round(float(np.percentile(d["min"], q)), 2) if len(d) >= 1000 else np.nan
        r["men_p50"] = round(float(np.percentile(men, 50)), 2) if len(men) >= 1000 else np.nan
        r["share_women"] = round(r["n_women"] / max(len(d), 1), 4)
        rows.append(r)
    t = pd.DataFrame(rows)
    t["note"] = ""
    t.loc[t.year == 2013, "note"] = "halted after the bombing; field percentiles not comparable"
    t.loc[t.year == 1996, "note"] = "centennial race, field of about 36,000"
    return t


def reconcile():
    rows = []
    for y in range(2001, 2015):
        a, l = read_adrian3(y), read_llim(y)
        rows.append({"year": y, "n_adrian3": len(a), "n_llimllib": len(l),
                     "p50_adrian3": round(a["min"].median(), 2), "p50_llimllib": round(l["min"].median(), 2),
                     "p90_adrian3": round(a["min"].quantile(.9), 2), "p90_llimllib": round(l["min"].quantile(.9), 2)})
    return pd.DataFrame(rows)


def heat_index_f(t, rh):
    """NWS heat index (Rothfusz with the NWS adjustments; the simple Steadman form below 80 F)."""
    simple = 0.5 * (t + 61.0 + (t - 68.0) * 1.2 + rh * 0.094)
    hi = simple if (simple + t) / 2 < 80 else (
        -42.379 + 2.04901523 * t + 10.14333127 * rh - .22475541 * t * rh - .00683783 * t * t
        - .05481717 * rh * rh + .00122874 * t * t * rh + .00085282 * t * rh * rh - .00000199 * t * t * rh * rh)
    if (simple + t) / 2 >= 80:
        if rh < 13 and 80 <= t <= 112:
            hi -= ((13 - rh) / 4) * math.sqrt((17 - abs(t - 95)) / 17)
        elif rh > 85 and 80 <= t <= 87:
            hi += ((rh - 85) / 10) * ((87 - t) / 5)
    return hi


def window_stats(js, h0, h1):
    """Average over the three course points and the hours h0..h1 inclusive. Wind is
    averaged as a vector, then projected on the course bearing (positive = tailwind)."""
    T, D, RH, HI, SW, CC, PR, TW, CW, SP = ([] for _ in range(10))
    b = math.radians(COURSE_BEARING_DEG)
    for loc in js:
        H = loc["hourly"]
        for i, tm in enumerate(H["time"]):
            hr = int(tm[11:13])
            if not (h0 <= hr <= h1):
                continue
            t, dp, rh = H["temperature_2m"][i], H["dew_point_2m"][i], H["relative_humidity_2m"][i]
            ws, wd = H["wind_speed_10m"][i], H["wind_direction_10m"][i]
            T.append(t); D.append(dp); RH.append(rh); HI.append(heat_index_f(t, rh))
            SW.append(H["shortwave_radiation"][i]); CC.append(H["cloud_cover"][i]); PR.append(H["precipitation"][i])
            # direction is where the wind blows FROM; it blows toward wd + 180
            to = math.radians(wd + 180.0)
            tail = ws * math.cos(to - b)
            cross = ws * math.sin(to - b)
            TW.append(tail); CW.append(cross); SP.append(ws)
    m = lambda v: round(float(np.mean(v)), 2)
    return {"temp_f": m(T), "temp_max_f": round(float(np.max(T)), 1), "dewpoint_f": m(D), "rh_pct": m(RH),
            "heat_index_f": m(HI), "temp_plus_dew": round(m(T) + m(D), 1), "sw_rad_wm2": m(SW),
            "cloud_pct": m(CC), "precip_mm": round(float(np.sum(PR)) / len(js), 2),
            "tailwind_mph": m(TW), "crosswind_mph": m(CW), "wind_mph": m(SP)}


def weather_table():
    rd = pd.read_csv(os.path.join(TAB, "race_days.csv"))
    rows = []
    for _, r in rd.iterrows():
        with open(os.path.join(CACHE, "weather", f"{r.year}.json")) as fh:
            js = json.load(fh)
        e0, e1 = map(int, r.elite_hours.split("-"))
        f0, f1 = map(int, r.field_hours.split("-"))
        row = {"year": r.year, "date": r.date}
        for k, v in window_stats(js, e0, e1).items():
            row[f"e_{k}"] = v
        for k, v in window_stats(js, f0, f1).items():
            row[f"f_{k}"] = v
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    f = field_table(); f.to_csv(os.path.join(TAB, "field_by_year.csv"), index=False)
    w = weather_table(); w.to_csv(os.path.join(TAB, "weather_by_year.csv"), index=False)
    rc = reconcile(); rc.to_csv(os.path.join(TAB, "source_reconcile.csv"), index=False)
    pd.set_option("display.width", 200)
    print(f[["year", "n_listed", "max_min", "complete_list", "men_10th", "men_25th", "p10", "p50", "p90"]].to_string(index=False))
    print(rc.to_string(index=False))
    print(w[["year", "f_temp_f", "f_dewpoint_f", "f_heat_index_f", "f_tailwind_mph", "e_temp_f", "e_tailwind_mph"]].to_string(index=False))


if __name__ == "__main__":
    main()
