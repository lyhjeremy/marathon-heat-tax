"""
figures.py: static PNGs of the October 2026 charts, for the README and for readers
without JavaScript. Reads tables/*.csv only.
"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
TAB, FIG = os.path.join(HERE, "tables"), os.path.join(HERE, "figures")
PAPER, PANEL, INK, INK2, RULE = "#ECEBE6", "#F4F3EF", "#1A1C1E", "#4E535A", "#C5C6C4"
RUST, BLUE = "#94462A", "#1F4A72"
KNOT = 55.0
plt.rcParams.update({"figure.dpi": 160, "savefig.dpi": 160, "font.size": 11, "font.family": "DejaVu Sans",
                     "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
                     "axes.grid": True, "grid.color": RULE, "axes.axisbelow": True,
                     "figure.facecolor": PAPER, "axes.facecolor": PANEL, "axes.spines.top": False,
                     "axes.spines.right": False})


def hm(m):
    return f"{int(m // 60)}:{int(round(m % 60)):02d}"


def main():
    w = pd.read_csv(os.path.join(TAB, "weather_by_year.csv")).set_index("year")
    sl = pd.read_csv(os.path.join(TAB, "slopes_by_series.csv")).set_index("series")

    # 03: eighty years, men's 25th place against trend
    s = pd.read_csv(os.path.join(TAB, "series_men_25th.csv"))
    s["t"] = s.year.map(w.e_temp_f)
    fig, ax = plt.subplots(figsize=(8.6, 5.2))
    for (a, b), mk, kw, lab in [((1940, 1969), "o", dict(facecolors="none", edgecolors=INK2), "1940-1969, no qualifying time"),
                                ((1970, 1985), "s", dict(color=BLUE), "1970-1985, qualifying times"),
                                ((1986, 2019), "o", dict(color=RUST), "1986-2019, prize money")]:
        g = s[s.year.between(a, b)]
        ax.scatter(g.t, g.detrended_pct, marker=mk, s=42, linewidths=1.5, label=lab, zorder=3, **kw)
    xs = np.array([36, KNOT, 90])
    ax.plot(xs, sl.loc["men_25th", "beta_pct"] * np.clip(xs - KNOT, 0, None), ls="--", color=INK, lw=2,
            label=f"fit: +{sl.loc['men_25th', 'beta_pct']:.2f}% per °F above {KNOT:.0f}°F")
    for y in (1976, 2012, 2004, 2018, 2011, 1994):
        r = s[s.year == y].iloc[0]
        ax.annotate(str(y), (r.t, r.detrended_pct), xytext=(6, 3), textcoords="offset points", fontsize=9, color=INK)
    ax.axhline(0, color=INK2, lw=1)
    ax.set_xlabel("Race-day temperature on the course (°F, first two hours)")
    ax.set_ylabel("Men's 25th place, % against long-run trend")
    ax.set_title("80 Boston Marathons: hot races are slow ones", color=INK, loc="left", weight="bold")
    ax.legend(fontsize=9, frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "03_eighty_years.png")); plt.close(fig)

    # 04: slope by position in the field
    r = sl.sort_values("typical_min")
    fig, ax = plt.subplots(figsize=(8.6, 4.6))
    for _, x in r.iterrows():
        c, m = (RUST, "o") if x.tier == "field" else (BLUE, "s")
        ax.plot([x.typical_min] * 2, [x.beta_lo90, x.beta_hi90], color=INK2, lw=2)
        ax.scatter([x.typical_min], [x.beta_pct], color=c, marker=m, s=60, zorder=3)
    ax.set_xticks([120, 150, 180, 210, 240, 270, 300]); ax.set_xticklabels([hm(v) for v in [120, 150, 180, 210, 240, 270, 300]])
    ax.set_ylim(0, 0.7)
    ax.set_xlabel("Typical finish time of that position (2014 trend, cool day)")
    ax.set_ylabel("% of finish time per °F above 55°F")
    ax.set_title("A similar share at every position in the field (90% bootstrap intervals)", color=INK, loc="left", weight="bold")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "04_slopes.png")); plt.close(fig)

    # 05: wind along the course
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    v = w.f_tailwind_mph
    ax.bar(v.index, v.values, color=[BLUE if t >= 0 else RUST for t in v.values], width=0.8)
    for y in (1994, 2011, 2018, 2015, 1943):
        ax.annotate(str(y), (y, v[y]), xytext=(0, 4 if v[y] >= 0 else -12), textcoords="offset points", ha="center", fontsize=9)
    ax.axhline(0, color=INK2, lw=1)
    ax.set_ylabel("mph along the course (+ tailwind, - headwind)")
    ax.set_title("Wind along the Hopkinton-to-Boston course on race day", color=INK, loc="left", weight="bold")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "05_wind.png")); plt.close(fig)

    # 06: holdout, median
    h = pd.read_csv(os.path.join(TAB, "holdout_2015_2019.csv")).query("series == 'p50'")
    fig, ax = plt.subplots(figsize=(8.6, 4.2))
    x = np.arange(len(h))
    ax.bar(x, 2 * 1.2816 * h.pred_sd_pct, bottom=h.dev_pred_pct - 1.2816 * h.pred_sd_pct, color=RULE, width=0.45, label="80% band")
    ax.scatter(x, h.dev_pred_pct, marker="_", s=600, color=INK, linewidths=2.5, label="predicted", zorder=3)
    ax.scatter(x, h.dev_actual_pct, color=RUST, s=60, zorder=4, label="actual")
    ax.set_xticks(x); ax.set_xticklabels([f"{y}\n{w.f_temp_f[y]:.0f}°F" for y in h.year])
    ax.axhline(0, color=INK2, lw=1)
    ax.set_ylabel("Median time, % against 2015-2019 average")
    ax.set_title("Holdout: the median runner in five races the model never saw", color=INK, loc="left", weight="bold")
    ax.legend(fontsize=9, frameon=False, loc="upper left")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "06_holdout.png")); plt.close(fig)
    print("figures written")


if __name__ == "__main__":
    main()
