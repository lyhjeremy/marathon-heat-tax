# The Heat Tax: temperature and Boston Marathon field times, 2001 to 2014

**Question.** How many minutes does race-day heat add to a marathon field's finish time?

**Data.** Official Boston Marathon results for 2001 to 2014 from the public `llimllib/bostonmarathon` mirror. The `official` column is the finish time in decimal minutes; I kept times between 120 and 480 minutes, which leaves 13,422 to 31,939 finishers per year. Race-day temperature comes from the Open-Meteo historical archive: the mean of hourly 2 m temperature from 10:00 to 16:00 local time near the course midpoint.

**Method.** One point per year: the field's median finish time against that day's temperature. Pearson correlation and an ordinary least squares fit (`scipy.stats.linregress`). 2013 is excluded from the fit because the race was halted after the bombing, which truncates the finisher field.

**Results.** r = 0.86 (p = 0.0002) over 13 races; with 2013 included it is 0.82. The slope is 1.03 minutes per °F (standard error 0.19), so a 50°F race and an 80°F race differ by about 31 minutes on the median finish. The two races above 70°F had the slowest medians: 2004 at 73.6°F (4:20) and 2012 at 81.3°F (4:16). The cool years 2009 to 2011 (48.7 to 54.0°F) had medians of 3:44 to 3:45.

**Limitations.** This is descriptive. Field size and qualifying standards changed over the period, and humidity, sun and wind were not modeled. The size of the effect is in line with published research on marathon times and temperature, but this analysis doesn't test that comparison.

Code: `fetch_data.py`, `analyze.py`. Figures: `figures/01_temp_vs_time.png`, `figures/02_median_by_year.png`. Per-year numbers: `tables/heat_tax.csv`.
