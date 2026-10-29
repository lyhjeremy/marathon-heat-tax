"""
model_fit.py: the October 2026 heat model.

Three tiers of the field, each a separate time series of one number per race:
  front     men's 10th and 25th place, 1940 to 2019 (ranks exist in every year's list)
  subelite  men's 100th and 1000th place, 1975 to 2019
  field     percentiles 10, 25, 50, 75, 90 of all finishers, in years whose list is the
            whole field (1998 to 2019; 1996 is left out as the centennial field)

For each series: log(time) = trend(year) + beta * heat + gamma * tailwind + error.
The trend absorbs the changing field (qualifying standards from 1970, prize money from
1986, field growth, charity entries). Several trend choices are fitted to show how
much the heat slope depends on that choice.

Holdout: 2015 to 2019 are never used for fitting, choosing variables or tuning.
Everything chosen here uses leave-one-year-out cross-validation inside 1940 to 2014.

Writes tables/*.csv, model/heat_model.json and figures/0[3-6]_*.png.
"""
import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TAB = os.path.join(HERE, "tables")
MODEL = os.path.join(HERE, "model")
HOLDOUT = [2015, 2016, 2017, 2018, 2019]
RNG = np.random.default_rng(20261028)
N_BOOT = 1000
VERSION = "heat-2026.10.1"

SERIES = [
    # key, label, column, first year, weather window prefix, tier
    ("men_10th", "Men's 10th place", "men_10th", 1940, "e_", "front"),
    ("men_25th", "Men's 25th place", "men_25th", 1940, "e_", "front"),
    ("men_100th", "Men's 100th place", "men_100th", 1975, "f_", "subelite"),
    ("men_1000th", "Men's 1000th place", "men_1000th", 1975, "f_", "subelite"),
    ("p10", "10th percentile", "p10", 1998, "f_", "field"),
    ("p25", "25th percentile", "p25", 1998, "f_", "field"),
    ("p50", "Median", "p50", 1998, "f_", "field"),
    ("p75", "75th percentile", "p75", 1998, "f_", "field"),
    ("p90", "90th percentile", "p90", 1998, "f_", "field"),
]
ERAS = [(1940, 1969, "1940-1969: no qualifying time"), (1970, 1985, "1970-1985: qualifying times, no prize money"),
        (1986, 2019, "1986-2019: prize money (from 1986)")]


# ---------------------------------------------------------------- data

def load():
    f = pd.read_csv(os.path.join(TAB, "field_by_year.csv"))
    w = pd.read_csv(os.path.join(TAB, "weather_by_year.csv"))
    d = f.merge(w, on="year")
    return d


def series_frame(d, s):
    key, label, col, y0, wp, tier = s
    x = d[(d.year >= y0)].copy()
    if tier == "field":
        x = x[x.complete_list]
        x = x[x.year != 1996]          # centennial: a one-off field of about 36,000
        x = x[x.year != 2013]          # halted race: the slower part of the field never finished
    x = x[x[col].notna()]
    x["y"] = np.log(x[col])
    for k in ["temp_f", "dewpoint_f", "heat_index_f", "temp_plus_dew", "tailwind_mph", "rh_pct",
              "sw_rad_wm2", "precip_mm", "crosswind_mph", "cloud_pct"]:
        x[k] = x[wp + k]
    return x


# ---------------------------------------------------------------- design

def rcs(x, knots):
    """Restricted (natural) cubic spline basis, Harrell's parameterization, scaled."""
    k = np.asarray(knots, float); t = len(k)
    cols = [x]
    norm = (k[-1] - k[0]) ** 2
    p = lambda u: np.clip(u, 0, None) ** 3
    for j in range(t - 2):
        cols.append((p(x - k[j]) - p(x - k[-2]) * (k[-1] - k[j]) / (k[-1] - k[-2])
                     + p(x - k[-1]) * (k[-2] - k[j]) / (k[-1] - k[-2])) / norm)
    return np.column_stack(cols)


def heat_term(x, var, knot=None):
    v = x[var].values.astype(float)
    return np.clip(v - knot, 0, None) if knot is not None else v


def trend_design(x, spec, train_years):
    yr = x.year.values.astype(float)
    if spec == "none":
        return np.ones((len(x), 1))
    if spec == "linear":
        return np.column_stack([np.ones(len(x)), (yr - 2000) / 10])
    if spec == "spline":
        ty = np.asarray(train_years, float)
        nk = 5 if ty.min() < 1960 else (4 if ty.min() < 1990 else 3)
        knots = np.quantile(ty, np.linspace(0.05, 0.95, nk))
        return np.column_stack([np.ones(len(x)), rcs((yr - 2000) / 10, (knots - 2000) / 10)])
    if spec == "era":
        cols = [np.ones(len(x))]
        present = [e for e in ERAS if any(e[0] <= y <= e[1] for y in train_years)]
        for a, b, _ in present[1:]:
            cols.append(((yr >= a) & (yr <= b)).astype(float))
        cols.append((yr - 2000) / 10)   # eras plus a common linear drift
        return np.column_stack(cols)
    if spec == "composition":
        return np.column_stack([np.ones(len(x)), (yr - 2000) / 10, np.log(x.n_listed.values),
                                x.share_women.values])
    raise ValueError(spec)


def design(x, spec, heat, knot, extras, train_years):
    """Columns: trend block, then the heat term (if any), then each extra weather term."""
    T = trend_design(x, spec, train_years)
    cols = [T]
    if heat:
        cols.append(heat_term(x, heat, knot)[:, None])
    for e in extras:
        cols.append(x[e].values.astype(float)[:, None])
    return np.column_stack(cols), T.shape[1]


def ols(X, y):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    return b


def fit(x, spec, heat, knot, extras=()):
    ty = x.year.values
    X, p = design(x, spec, heat, knot, extras, ty)
    b = ols(X, x.y.values)
    res = x.y.values - X @ b
    out = {"b": b, "p": p, "n": len(x),
           "resid_sd": float(np.sqrt(res @ res / max(len(res) - X.shape[1], 1)))}
    out["beta"] = float(b[p]) if heat else 0.0
    out["extra"] = {e: float(b[p + (1 if heat else 0) + j]) for j, e in enumerate(extras)}
    return out


def loyo_rmse(x, spec, heat, knot, extras=()):
    errs = []
    for i in range(len(x)):
        tr = x.drop(x.index[i])
        ty = tr.year.values
        X, _ = design(tr, spec, heat, knot, extras, ty)
        b = ols(X, tr.y.values)
        Xi, _ = design(x.iloc[[i]], spec, heat, knot, extras, ty)
        errs.append(x.y.values[i] - float((Xi @ b)[0]))
    return float(np.sqrt(np.mean(np.square(errs))))


def boot(x, heat, knot, extras):
    """Resample race years with replacement and refit; returns rows of (beta, extras...)."""
    out = []
    for _ in range(N_BOOT):
        xb = x.iloc[RNG.choice(len(x), len(x), replace=True)]
        if xb.year.nunique() < 8:
            continue
        fb = fit(xb, "spline", heat, knot, extras)
        out.append([fb["beta"]] + [fb["extra"][e] for e in extras])
    return np.array(out)


def score(train, base, heat, knot, extras):
    rel = {k: loyo_rmse(v, "spline", heat, knot, extras) / base[k] for k, v in train.items()}
    return rel


# ---------------------------------------------------------------- main

def main():
    os.makedirs(MODEL, exist_ok=True)
    d = load()
    frames = {s[0]: series_frame(d, s) for s in SERIES}
    train = {k: v[~v.year.isin(HOLDOUT)] for k, v in frames.items()}
    base = {k: loyo_rmse(v, "spline", None, None) for k, v in train.items()}

    # 1. heat variable and knot: leave-one-year-out CV inside the training years, scored as
    #    the mean over the nine series of CV RMSE relative to a trend-only model.
    cands = [("temp_f", None), ("dewpoint_f", None), ("heat_index_f", None), ("temp_plus_dew", None)]
    cands += [("temp_f", k) for k in (40, 45, 50, 55, 60)]
    cands += [("dewpoint_f", k) for k in (35, 40, 45)]
    cands += [("heat_index_f", k) for k in (45, 50, 55)]
    cands += [("temp_plus_dew", k) for k in (80, 90, 100)]
    rows = []
    for var, knot in cands:
        rel = score(train, base, var, knot, ())
        rows.append({"stage": 1, "heat_var": var, "knot": "" if knot is None else knot, "extra": "",
                     "cv_rel_mean": round(float(np.mean(list(rel.values()))), 4),
                     **{f"cv_rel_{k}": round(r, 4) for k, r in rel.items()}})
    s1 = pd.DataFrame(rows).sort_values("cv_rel_mean")
    HEAT, KNOT = s1.iloc[0].heat_var, (None if s1.iloc[0].knot == "" else float(s1.iloc[0].knot))
    best1 = float(s1.iloc[0].cv_rel_mean)
    # 2. extra weather terms added one at a time on top of the chosen heat term
    rows2 = []
    for e in ("tailwind_mph", "dewpoint_f", "rh_pct", "precip_mm", "sw_rad_wm2", "cloud_pct"):
        rel = score(train, base, HEAT, KNOT, (e,))
        rows2.append({"stage": 2, "heat_var": HEAT, "knot": KNOT, "extra": e,
                      "cv_rel_mean": round(float(np.mean(list(rel.values()))), 4),
                      **{f"cv_rel_{k}": round(r, 4) for k, r in rel.items()}})
    s2 = pd.DataFrame(rows2).sort_values("cv_rel_mean")
    sel = pd.concat([s1, s2])
    sel.to_csv(os.path.join(TAB, "model_selection.csv"), index=False)
    EXTRAS = (s2.iloc[0].extra,) if s2.iloc[0].cv_rel_mean < best1 - 0.005 else ()
    print(s1.head(8).to_string(index=False)); print(s2.to_string(index=False))
    print(f"\nchosen: heat={HEAT} knot={KNOT} extras={EXTRAS}")

    # 3. heat slope under each trend choice
    rob = []
    for s in SERIES:
        x = train[s[0]]
        for spec in ("none", "linear", "spline", "era", "composition"):
            if spec == "era" and s[5] == "field":
                continue      # within 1998-2014 there is one era change (2013) and one year after it
            ft = fit(x, spec, HEAT, KNOT, EXTRAS)
            rob.append({"series": s[0], "trend": spec, "n": ft["n"], "beta_pct": round(100 * ft["beta"], 4),
                        "cv_rmse_pct": round(100 * loyo_rmse(x, spec, HEAT, KNOT, EXTRAS), 3)})
    rob = pd.DataFrame(rob)
    rob.to_csv(os.path.join(TAB, "trend_robustness.csv"), index=False)
    print(rob.pivot(index="series", columns="trend", values="beta_pct").to_string())

    # 4. final fits (spline trend), bootstrap over years, holdout
    from build_dataset import read_adrian3
    recent_times = np.concatenate([read_adrian3(y)["min"].values for y in (2010, 2011, 2012, 2014)])
    hold_rows, slope_rows, anchors = [], [], []
    wind_pts, wind_draws = [], []
    for s in SERIES:
        key, label, col, y0, wp, tier = s
        x, full = train[key], frames[key]
        yrs = x.year.values
        ft = fit(x, "spline", HEAT, KNOT, EXTRAS)
        fw = fit(x, "spline", HEAT, KNOT, ("tailwind_mph",))
        dr = boot(x, HEAT, KNOT, EXTRAS)
        dw = boot(x, HEAT, KNOT, ("tailwind_mph",))
        p = ft["p"]
        # trend at 2014, the last training year; holdout predictions hold it flat there
        T14, _ = design(full[full.year == 2014], "spline", HEAT, KNOT, EXTRAS, yrs)
        trend14 = float(T14[0, :p] @ ft["b"][:p])
        typical = float(np.exp(trend14))          # time at baseline weather (heat term zero)
        h = full[full.year.isin(HOLDOUT)]
        Xh, _ = design(h, "spline", HEAT, KNOT, EXTRAS, yrs)
        wx = Xh[:, p:] @ ft["b"][p:]
        act = h.y.values
        pred_flat = trend14 + wx
        dev_pred, dev_act = wx - wx.mean(), act - act.mean()
        Xw = Xh[:, p:]
        cov = np.atleast_2d(np.cov(dr.T))
        psd = np.sqrt(ft["resid_sd"] ** 2 + np.einsum("ij,jk,ik->i", Xw, cov, Xw))
        for i, yy in enumerate(h.year.values):
            hold_rows.append({"series": key, "year": int(yy), "actual_min": round(float(np.exp(act[i])), 2),
                              "pred_flat_min": round(float(np.exp(pred_flat[i])), 2),
                              "err_flat_pct": round(100 * (act[i] - pred_flat[i]), 2),
                              "dev_actual_pct": round(100 * dev_act[i], 2), "dev_pred_pct": round(100 * dev_pred[i], 2),
                              "dev_err_pct": round(100 * (dev_act[i] - dev_pred[i]), 2),
                              "pred_sd_pct": round(100 * float(psd[i]), 2),
                              "in_80pct_band": bool(abs(dev_act[i] - dev_pred[i]) <= 1.2816 * psd[i])})
        pct = float(col[1:]) if col.startswith("p") else round(float((recent_times < typical).mean() * 100), 2)
        lo, hi = np.percentile(dr[:, 0], [5, 95])
        glo, ghi = np.percentile(dw[:, 1], [5, 95])
        slope_rows.append({"series": key, "label": label, "tier": tier, "n_races": ft["n"],
                           "years": f"{int(x.year.min())}-{int(x.year.max())}",
                           "typical_min": round(typical, 2), "field_pct": pct,
                           "beta_pct": round(100 * ft["beta"], 4), "beta_lo90": round(100 * lo, 4),
                           "beta_hi90": round(100 * hi, 4), "beta_min_at_typical": round(typical * ft["beta"], 3),
                           "tail_pct_per_mph": round(100 * fw["extra"]["tailwind_mph"], 4),
                           "tail_lo90": round(100 * glo, 4), "tail_hi90": round(100 * ghi, 4),
                           "beta_with_wind_pct": round(100 * fw["beta"], 4),
                           "resid_sd_pct": round(100 * ft["resid_sd"], 3)})
        anchors.append({"series": key, "label": label, "typical_min": round(typical, 2), "field_pct": pct,
                        "n_train": ft["n"], "years": f"{int(x.year.min())}-{int(x.year.max())}",
                        "beta": round(ft["beta"], 7), "resid_sd": round(ft["resid_sd"], 5),
                        "draws": [round(float(v), 6) for v in dr[:400, 0]]})
        if tier == "front":
            wind_pts.append(fw["extra"]["tailwind_mph"]); wind_draws.extend(dw[:200, 1].tolist())
        Xa, _ = design(full, "spline", HEAT, KNOT, EXTRAS, yrs)
        tr = Xa[:, :p] @ ft["b"][:p]
        full.assign(trend_min=np.exp(tr), detrended_pct=100 * (full.y.values - tr),
                    weather_pct=100 * (Xa[:, p:] @ ft["b"][p:]), holdout=full.year.isin(HOLDOUT))[
            ["year", col, "trend_min", "detrended_pct", "weather_pct", "holdout", "temp_f", "dewpoint_f",
             "heat_index_f", "tailwind_mph", "precip_mm"]].round(4).to_csv(
            os.path.join(TAB, f"series_{key}.csv"), index=False)

    slopes = pd.DataFrame(slope_rows); slopes.to_csv(os.path.join(TAB, "slopes_by_series.csv"), index=False)
    hold = pd.DataFrame(hold_rows); hold.to_csv(os.path.join(TAB, "holdout_2015_2019.csv"), index=False)
    pd.set_option("display.width", 250)
    print(slopes.to_string(index=False))

    # holdout summary, with a no-weather benchmark (predict every holdout year at the holdout mean)
    summ = []
    for tier, g in [("all", hold)] + list(hold.assign(t=hold.series.map({s[0]: s[5] for s in SERIES})).groupby("t")):
        summ.append({"group": tier, "n": len(g), "mae_flat_pct": round(g.err_flat_pct.abs().mean(), 2),
                     "mae_levelfree_pct": round(g.dev_err_pct.abs().mean(), 2),
                     "mae_levelfree_noweather_pct": round(g.dev_actual_pct.abs().mean(), 2),
                     "coverage_80": f"{int(g.in_80pct_band.sum())}/{len(g)}"})
    for yy, g in hold.groupby("year"):
        summ.append({"group": str(yy), "n": len(g), "mae_flat_pct": round(g.err_flat_pct.abs().mean(), 2),
                     "mae_levelfree_pct": round(g.dev_err_pct.abs().mean(), 2),
                     "mae_levelfree_noweather_pct": round(g.dev_actual_pct.abs().mean(), 2),
                     "coverage_80": f"{int(g.in_80pct_band.sum())}/{len(g)}"})
    summ = pd.DataFrame(summ); summ.to_csv(os.path.join(TAB, "holdout_summary.csv"), index=False)
    print(summ.to_string(index=False))

    # 5. the old 14-race result next to the new one
    old = pd.read_csv(os.path.join(TAB, "heat_tax.csv"))
    o = old[old.year != 2013]
    sl, ic = np.polyfit(o.temp_F, o.median_min, 1)
    new13 = frames["p50"][frames["p50"].year.between(2001, 2014) & (frames["p50"].year != 2013)]
    sl2, _ = np.polyfit(new13.temp_f, np.exp(new13.y), 1)
    h50 = frames["p50"][frames["p50"].year.isin(HOLDOUT)]
    oldpred = ic + sl * h50.temp_f.values
    comp = pd.DataFrame([
        {"what": "2026-06 result: llimllib official times, 10-16h temperature at one point, OLS, 13 races",
         "slope_min_per_F": round(sl, 3)},
        {"what": "same 13 races, adrian3 net times and the new course-average weather window, OLS",
         "slope_min_per_F": round(sl2, 3)},
        {"what": "new model at the median, spline trend, per F above the knot, 16 races 1998-2014",
         "slope_min_per_F": round(float(slopes.set_index("series").loc["p50", "beta_min_at_typical"]), 3)},
        {"what": "old line applied to 2015-2019 medians: mean abs error, min",
         "slope_min_per_F": round(float(np.mean(np.abs(np.exp(h50.y.values) - oldpred))), 2)},
        {"what": "new model on 2015-2019 medians, trend held at 2014: mean abs error, min",
         "slope_min_per_F": round(float(np.mean(np.abs(hold[hold.series == 'p50'].actual_min - hold[hold.series == 'p50'].pred_flat_min))), 2)},
    ])
    comp.to_csv(os.path.join(TAB, "old_vs_new.csv"), index=False)
    print(comp.to_string(index=False))

    # 6. export the model
    tr_all = d[~d.year.isin(HOLDOUT)]
    a1 = np.polyfit(tr_all.f_temp_f, tr_all.f_dewpoint_f, 1)
    anchors.sort(key=lambda a: a["typical_min"])
    model = {
        "model_version": VERSION,
        "created": "2026-10-28",
        "description": ("Boston Marathon heat model. Slowdown is relative to baseline conditions: "
                        f"{HEAT} at or below {KNOT} and no wind along the course. log(time) = trend(year) + "
                        "beta * max(temp_f - knot, 0) [+ tail * tailwind_mph], fitted separately for each "
                        "anchor series; a runner's finish time is matched to anchors by typical time and "
                        "the coefficients are interpolated."),
        "heat_var": HEAT, "knot_f": KNOT, "baseline_temp_f": KNOT, "baseline_headwind_mph": 0.0,
        "extras_in_main_model": list(EXTRAS),
        "dewpoint_used": HEAT != "temp_f" or "dewpoint_f" in EXTRAS,
        "dewpoint_from_temp": {"slope": round(float(a1[0]), 4), "intercept": round(float(a1[1]), 4)},
        "interval": "90% bootstrap over race years (1000 resamples, 400 kept per anchor); parameter uncertainty only",
        "course_bearing_deg": 69.6,
        "holdout_years": HOLDOUT,
        "holdout_summary": summ.to_dict(orient="records"),
        "training": {"front": "1940-2014", "subelite": "1975-2014", "field": "1998-2012, 2014"},
        "data": {"results": "adrian3/Boston-Marathon-Data-Project@cc4fdd8", "weather": "Open-Meteo historical archive (ERA5)"},
        "anchors": anchors,
        "wind": {
            "note": ("Along-course wind. Only the front-of-field series (men's 10th and 25th place, 1940-2014) "
                     "gave a clear estimate; the field-percentile series gave the wrong sign with wide intervals, "
                     "so this front estimate is applied to every finish time. Not part of the CV-selected model."),
            "pct_per_mph_headwind": round(-100 * float(np.mean(wind_pts)), 4),
            "draws_pct_per_mph_headwind": [round(-100 * float(v), 4) for v in wind_draws],
        },
    }
    with open(os.path.join(MODEL, "heat_model.json"), "w") as fh:
        json.dump(model, fh, separators=(",", ":"))
    print("model ->", os.path.getsize(os.path.join(MODEL, "heat_model.json")), "bytes")


if __name__ == "__main__":
    main()
