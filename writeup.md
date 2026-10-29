# The Heat Tax: race-day weather and Boston Marathon times, 1940 to 2019

Every Boston Marathon from 1940 to 2019, paired with the weather on the course that day, shows the same pattern. Below about 55°F the temperature makes no measurable difference to how fast the field runs. Above 55°F the median finisher loses 0.42% of their time for each °F (90% bootstrap interval 0.20 to 0.52), which is 0.95 minutes at a 3:47 finish. The share is similar at every position in the field, between 0.29% and 0.46% from the 10th man to the 90th percentile, so the slower runner loses more minutes: 0.43 per °F at 2:13, 1.34 at 5:01.

## October 2026 upgrade

The June 2026 version of this study used fourteen races (2001 to 2014), one temperature reading per race at a single point, and a straight line through thirteen medians. It found 1.03 minutes per °F (r = 0.86) and 31 minutes between a 50°F and an 80°F race. I rebuilt it in October 2026 for three reasons: thirteen points could not separate the weather from a field that kept changing, humidity and wind were left out, and there was no test on races the fit had not seen. That headline is superseded as of 28 October 2026; the new figure is 0.95 minutes per °F above 55°F and nothing below, or about 25 minutes from 50°F to 80°F.

What changed:

- Data. Results for 1940 to 2019 from adrian3/Boston-Marathon-Data-Project, cross-checked against the llimllib mirror the June version used. The two agree on 2001 to 2014 except in timing: llimllib's `official` column is gun time in 2001 to 2005 and 2012, and adrian3 has chip times there. Gun time made hot 2004 and 2012 look 10.2 and 4.8 minutes slower at the median. On the June races with chip times and the new weather window, the June method gives 0.76 minutes per °F, not 1.03.
- Weather. ERA5 reanalysis from the Open-Meteo archive at three points on the course, over each year's race hours from a dated race table: temperature, dew point, humidity, heat index, wind along the course, rain, sun and cloud.
- The field. Early result lists are short or stop at a time limit, so the study measures the field three ways, each where the list allows: the 10th and 25th man (1940 to 2019), the 100th and 1000th man (1975 to 2019), and the 10th to 90th percentile of all finishers (1998 to 2019). Each series has a smooth trend in the year to absorb qualifying times, prize money, growth and the rise in women and charity entrants.
- Model choice by cross-validation. Temperature with a bend at 55°F removed 37% of the trend-only model's leave-one-year-out error, a straight line 32%, the heat index at best 35%, dew point nothing. Every extra weather term made predictions worse.
- A holdout. 2015 to 2019 were left out of all fitting and choices.
- A tool. The model ships as `model/heat_model.json` with `heat_model.py`, and the write-up page prices a race day from a live Open-Meteo forecast, falling back to climatology beyond 16 days.

## What the trend does to the slope

The field changed far more than the weather. The 25th man ran 2:53:32 in 1940 and 2:18:01 in 2019. Fitted with no trend at all, the heat slope for the 25th man is 0.24% per °F; with a straight-line trend 0.34; with era steps 0.45; with field size and the share of women 0.35; with the spline 0.41. For the whole-field percentiles the choice hardly matters: the median stays between 0.42 and 0.45 under every version.

## Wind

The course runs east-northeast. For the 10th and 25th man each mph of tailwind took 0.08% and 0.11% off the time, with intervals that exclude zero. For the field percentiles the estimate had the wrong sign and an interval that included either answer. Wind did not improve the cross-validated fit, so the main model leaves it out, and the exported tool applies the front-of-race rate (0.095% per mph of headwind) to everyone when given a wind, and says so.

## The holdout

The level of the field drifted after 2014, so the fair test is whether the weather part of the model gets the ups and downs of 2015 to 2019 right. Across nine series it averaged 2.26% error against 2.15% for a flat guess. It did well on 2015 (cold, wet, headwind: 0.90% against 2.76%) and 2016, over-predicted the slowdown in 2017 (69°F with an 11 mph tailwind), and missed 2018 badly, a 44°F race in cold rain and a 15 mph headwind that the model scores as ideal. 33 of 45 actual values fell inside the 80% bands; for 2018 one of nine did. The model prices heat on a dry day; it says nothing about cold rain, and on unseen races it did not beat a flat guess overall.

## What it can't tell you

The field percentiles rest on 16 training races, two of them above 70°F, so their intervals are wide, and the bootstrap does not redo the choice of the 55°F bend. The weather is a gridded reanalysis. Who chooses to start on a hot morning changes the field, and the 2012 deferral offer is the clearest case. The numbers describe Boston fields in April and say nothing certain about any one runner.

Code: `fetch_data.py`, `build_dataset.py`, `model_fit.py`, `heat_model.py`, `figures.py`, `export_web.py`; the June analysis is `legacy_2001_2014.py`. Tables in `tables/`, figures in `figures/`.
