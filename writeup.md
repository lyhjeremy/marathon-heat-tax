# The Heat Tax: temperature and Boston Marathon field times, 2001 to 2014

Every degree Fahrenheit on race day added about a minute to the median Boston Marathon finish between 2001 and 2014. The fitted slope is 1.03 minutes per °F (standard error 0.19), and the correlation between temperature and the field median is r = 0.86 (p = 0.0002) over 13 races, or 0.82 if the halted 2013 race is put back in. At that rate a 50°F race and an 80°F race are about 31 minutes apart for the runner in the middle of the field.

The two hottest days make the point on their own. 2004 (73.6°F) had the slowest median of the fourteen, 4:20, and 2012 (81.3°F) was next at 4:16. The cool run from 2009 to 2011, at 48.7 to 54.0°F, finished with medians of 3:44 to 3:45.

## How the numbers were made

The results are the official Boston Marathon times for 2001 to 2014 from the public `llimllib/bostonmarathon` mirror, where the `official` column is the finish in decimal minutes. I kept times between 120 and 480 minutes, which leaves 13,422 to 31,939 finishers a year. Race-day temperature comes from the Open-Meteo historical archive: the mean of hourly 2 m temperature from 10:00 to 16:00 local time near the course midpoint.

Each year is one point, the field's median finish against that day's temperature, and the fit is a Pearson correlation plus an ordinary least squares line (`scipy.stats.linregress`). 2013 is left out of the fit because the race was stopped after the bombing, which cuts off the finisher field.

## What it can't tell you

The analysis is descriptive. Field size and qualifying standards both changed over the fourteen years, and I did not model humidity, sun or wind, which tend to arrive with the heat. The size of the effect is in line with published research on marathon times and temperature, but this analysis doesn't test that comparison.

Code: `fetch_data.py`, `analyze.py`. Figures: `figures/01_temp_vs_time.png`, `figures/02_median_by_year.png`. Per-year numbers: `tables/heat_tax.csv`.
