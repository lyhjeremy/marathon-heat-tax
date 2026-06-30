# The Heat Tax: temperature vs Boston Marathon field times, 2001-2014

**Question.** How many minutes does heat add to a marathon field's time?

**Data.** Official Boston Marathon results 2001-2014 (`llimllib/bostonmarathon`);
`official` finish times in decimal minutes, filtered to 120-480 min. Race-day
temperature from Open-Meteo's historical archive (mean of hourly 2 m temperature,
10:00-16:00 local, near the course midpoint).

**Method.** Per year, median finish time vs race-day midday temperature; ordinary
least squares. 2013 excluded (race halted by the bombing -> truncated finisher field).

**Results.** Pearson r = 0.86 (p < 0.001); slope approximately 1.0 minute per degF.
Across 50F -> 80F that is about +31 minutes on the median finish. The two hottest
years (2012, 81F; 2004, 74F) had the slowest median times (~4:16, ~4:20); the
coolest years (2009-2011, ~49-54F) the fastest (~3:44).

**Caveats.** Descriptive, not causal: field size and qualifying standards changed
over the period, and humidity/wind/sun also matter. The effect size aligns with
published marathon-and-temperature research.

See `analyze.py` and `figures/`.
