# Zooplankton Diel Vertical Migration

Animated drawings of *Daphnia* diel vertical migration in Trout Lake, Wisconsin, made during the 2026 Drawing Water residency at Trout Lake Station.

Live site: https://audreylolaarts.github.io/DVM_Zooplankton/

- `index.html` is the landing page.
- `dvm_lake_map_slider.html` (Data Sliders) lets you set the light and temperature yourself.
- `dvm_lake_live_data.html` (Live Buoy Data) is driven by the Trout Lake buoy.
- `dvm_lake_timeline.html` (Lake Through Time) plays the Trout Lake record from 1981 to 2025, one week per day-night cycle, with ice cover on the real dates. Its data are in `timeline_data.js`.

## How the live data works

The UW-Madison Center for Limnology buoy feed only allows browser pages on `uwcfl.github.io` to read it. To get around that, `.github/workflows/trout-buoy.yml` runs about every 10 minutes:

1. It runs `scripts/fetch_trout_buoy.py`, which saves the newest buoy reading as `trout_latest.json`.
2. It publishes the site to GitHub Pages.

The live page reads `trout_latest.json`. The Pages source must be set to **GitHub Actions** (Settings → Pages).

## Rebuilding the timeline data

`timeline_data.js` is built from six NTL-LTER CSV files by `scripts/build_timeline_data.py`. To refresh it with newer data, download the latest versions and run:

```
python3 scripts/build_timeline_data.py physical_limnology.csv chlorophyll.csv zooplankton.csv ice_duration.csv woodruff_hourly.csv sonar_interval_density.csv timeline_data.js
```

The script fills gaps between field samples. Gaps of up to 60 days are interpolated in a straight line; longer gaps use the typical value for that week of the year. The drawing shows which applies.

## Sources

- Model: DaphniaDVM by Bennett McAfee, ported to JavaScript with permission. McAfee, B. J. 2021. Programming Simulations of Diel Vertical Migration Behavior of Zooplankton. Lawrence University Honors Projects 157. https://lux.lawrence.edu/luhp/157. As in the original model, each size class is spread around its optimal depth as a normal distribution with a standard deviation of 3.84 m. Baseline temperatures (Data Sliders): Trout Lake, May 1992, from the model's example data.
- Live data: [Trout Lake Buoy Live Data](https://uwcfl.github.io/buoy-viewer/trout.html), UW-Madison Center for Limnology. These data are not quality controlled.
- Chlorophyll: Magnuson, J.J., S.R. Carpenter, and E.H. Stanley. 2025. North Temperate Lakes LTER: Chlorophyll - Trout Lake Area 1981 - current ver 33. Environmental Data Initiative. https://doi.org/10.6073/pasta/659e43f4796f71e3a37673a0f2d7a77a (Accessed 2026-10-09). Median chlorophyll by depth: the current month for Live Buoy Data, all dates for Data Sliders.
- Water temperature: Magnuson, J.J., S.R. Carpenter, and E.H. Stanley. 2026. North Temperate Lakes LTER: Physical Limnology of Primary Study Lakes 1981 - current ver 38. Environmental Data Initiative. https://doi.org/10.6073/pasta/eeaa2a029eda1683f004d06da5d8d808 (Accessed 2026-10-09).
- Ice: Magnuson, J.J., S.R. Carpenter, and E.H. Stanley. 2026. North Temperate Lakes LTER: Ice Duration - Trout Lake Area 1981 - current ver 32. Environmental Data Initiative. https://doi.org/10.6073/pasta/d2c65ae81f95dd29cc6568344621680c (Accessed 2026-10-09).
- Wind and sunlight: Magnuson, J.J., S.R. Carpenter, and E.H. Stanley. 2026. North Temperate Lakes LTER: Meteorological Data - Woodruff Airport 1989 - current ver 41. Environmental Data Initiative. https://doi.org/10.6073/pasta/ef5fbb5faa65e57449de0faeff8b497f (Accessed 2026-10-09). Hourly data.
- Fish: Magnuson, J., S. Carpenter, and E. Stanley. 2025. North Temperate Lakes LTER: Pelagic Prey - Sonar Data 2001 - current ver 36. Environmental Data Initiative. https://doi.org/10.6073/pasta/7ba35a0a5f23fd0fcc7039187a0fbd91 (Accessed 2026-10-09). The Interval Density table gives zooplankton-eating fish per 1,000 m³ by depth, which are the model's predator units.
- Zooplankton: NTL LTER, E.H. Stanley, S.R. Carpenter, and J.J. Magnuson. 2026. North Temperate Lakes LTER: Zooplankton - Trout Lake Area 1982 - current ver 42. Environmental Data Initiative. Monthly Daphnia density sets the dot count, and measured lengths set the size mix.
- Lake volume: Trout Lake, 0.240 km³ (Wisconsin DNR).
