"""
analyze.py - The Heat Tax: how much does temperature slow a marathon field?
===========================================================================
For each Boston Marathon 2001-2014 we compute the field's median finish time and
pair it with the race-day temperature, then measure the relationship.

`official` is the finish time in decimal minutes. We keep runners (120-480 min,
excluding wheelchair athletes and bad records).

Outputs: figures/*.png and tables/heat_tax.csv
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

HERE = os.path.dirname(__file__)
FIG = os.path.join(HERE, "figures"); TAB = os.path.join(HERE, "tables"); DATA = os.path.join(HERE, "data")
INK, GOLD, TEAL, CORAL = "#1a1a2e", "#D4A537", "#15868C", "#E0567A"
plt.rcParams.update({"figure.dpi": 200, "savefig.dpi": 200, "font.size": 12,
    "axes.edgecolor": "#888", "axes.grid": True, "grid.color": "#e8e2d4",
    "axes.axisbelow": True, "figure.facecolor": "white", "axes.facecolor": "white"})


def field_summary():
    wx = pd.read_csv(os.path.join(DATA, "weather.csv"))
    rows = []
    for _, w in wx.iterrows():
        y = int(w["year"])
        df = pd.read_csv(os.path.join(DATA, f"boston_{y}.csv"))
        off = pd.to_numeric(df["official"], errors="coerce")
        off = off[(off >= 120) & (off <= 480)]
        rows.append({"year": y, "temp_F": w["temp_midday_F"], "temp_max_F": w["temp_max_F"],
                     "median_min": off.median(), "mean_min": off.mean(),
                     "p25": off.quantile(.25), "p75": off.quantile(.75), "n": len(off)})
    return pd.DataFrame(rows).sort_values("year")


def hhmm(m):
    return f"{int(m//60)}:{int(round(m%60)):02d}"


def main():
    os.makedirs(FIG, exist_ok=True); os.makedirs(TAB, exist_ok=True)
    t = field_summary()
    t.to_csv(os.path.join(TAB, "heat_tax.csv"), index=False)
    print(t[["year", "temp_F", "median_min", "n"]].round(1).to_string(index=False))

    # 2013 was halted mid-race (Boston Marathon bombing): the finisher field is
    # truncated, so it is excluded from the fitted relationship and flagged.
    fit = t[t["year"] != 2013]
    x, y = fit["temp_F"].values, fit["median_min"].values
    sl, ic, r, p, se = stats.linregress(x, y)
    r_all = stats.linregress(t["temp_F"], t["median_min"]).rvalue
    print(f"\nPearson r = {r:.2f}  (p = {p:.4f})   [r with 2013 included = {r_all:.2f}]")
    print(f"Slope = {sl:.2f} min per degF  ->  {sl:.1f} min slower per +1F")
    print(f"From a cool 50F to a hot 80F: +{sl*30:.0f} min on the median finish")
    timefmt = FuncFormatter(lambda v, _: hhmm(v))

    # ---- Fig 1: scatter temp vs median time ----
    fig, ax = plt.subplots(figsize=(8.6, 5.4))
    ax.scatter(fit["temp_F"], fit["median_min"], c=fit["temp_F"], cmap="YlOrRd",
               s=140, edgecolor=INK, zorder=3)
    # 2013 shown separately (interrupted race)
    row13 = t[t["year"] == 2013].iloc[0]
    ax.scatter(row13["temp_F"], row13["median_min"], s=150, facecolor="white",
               edgecolor=TEAL, linewidth=2.5, zorder=3, marker="o")
    xs = np.linspace(x.min()-2, x.max()+2, 50)
    ax.plot(xs, ic + sl*xs, color=INK, lw=2, ls="--",
            label=f"+{sl:.1f} min per +1°F  (r = {r:.2f})")
    for _, row in t.iterrows():
        lab = "2013*" if row["year"] == 2013 else int(row["year"])
        ax.annotate(lab, (row["temp_F"], row["median_min"]),
                    textcoords="offset points", xytext=(7, 4), fontsize=9, color="#444")
    ax.set_xlabel("Race-day temperature (°F, late morning to afternoon)")
    ax.set_ylabel("Field median finish time")
    ax.yaxis.set_major_formatter(timefmt)
    ax.set_title("The Heat Tax: hotter Boston Marathons are slower", color=INK, weight="bold")
    ax.legend(title="* 2013 race halted (bombing); excluded from fit", title_fontsize=8)
    fig.tight_layout(); fig.savefig(f"{FIG}/01_temp_vs_time.png"); plt.close(fig)

    # ---- Fig 2: median time by year, colored by temperature ----
    fig, ax = plt.subplots(figsize=(9, 4.8))
    norm = (t["temp_F"]-t["temp_F"].min())/(t["temp_F"].max()-t["temp_F"].min())
    colors = matplotlib.colormaps["YlOrRd"](0.2+0.8*norm)
    bars = ax.bar(t["year"].astype(int).astype(str), t["median_min"], color=colors, edgecolor="#caa")
    for b, row in zip(bars, t.itertuples()):
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+1, f"{row.temp_F:.0f}°", ha="center", fontsize=9, color="#555")
    ax.set_ylabel("Field median finish time"); ax.set_ylim(t["median_min"].min()-15, t["median_min"].max()+15)
    ax.yaxis.set_major_formatter(timefmt)
    ax.set_title("Median finish time by year (label = race-day temp)", color=INK, weight="bold")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    fig.tight_layout(); fig.savefig(f"{FIG}/02_median_by_year.png"); plt.close(fig)

    print("\nSaved figures + tables/heat_tax.csv")


if __name__ == "__main__":
    main()
