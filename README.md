# The Heat Tax — how much does temperature slow a marathon?

Pairing 14 Boston Marathons (2001–2014) with race-day weather: the field's median
finish time rises about **1 minute per °F** (correlation **r = 0.86**). A hot 80°F
day costs the median runner roughly **31 minutes** versus a cool 50°F day.

> 🌐 **Read the story:** https://lyhjeremy.github.io/marathon-heat-tax/

## Findings
- Temperature vs field median finish time: **r = 0.86** (2013 excluded).
- Slope ≈ **1 minute slower per °F**.
- 50°F → 80°F adds about **31 minutes** to the median finish.
- The hottest years (2012 at 81°F, 2004 at 74°F) were among the slowest.

## Reproduce
```bash
pip install -r requirements.txt
python fetch_data.py     # downloads 2001-2014 results + Open-Meteo race-day weather
python analyze.py        # writes figures/ and tables/heat_tax.csv
```

## Data
Official Boston Marathon results 2001–2014 via [llimllib/bostonmarathon](https://github.com/llimllib/bostonmarathon);
race-day temperatures from the free [Open-Meteo](https://open-meteo.com/) archive
(mean of the 10:00–16:00 window near the course). Median over finishers 2–8 h.
2013 is excluded from the fit (race halted by the bombing → truncated field).
Raw data is downloaded by `fetch_data.py` and git-ignored.

## Caveats
With 14 seasons this is a descriptive relationship, not a controlled experiment;
field size and qualifying standards also shifted over the years. The heat signal is
nonetheless large and consistent with sports-science literature.

## License
[MIT](LICENSE) © 2026 Jeremy Lee
