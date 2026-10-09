# Zooplankton Diel Vertical Migration

Animated drawings of *Daphnia* diel vertical migration in Trout Lake, Wisconsin, made during the 2026 Drawing Water residency at Trout Lake Station.

Live site: https://audreylolaarts.github.io/DVM_Zooplankton/

- `index.html` is the landing page.
- `dvm_lake_map_slider.html` (Data Sliders) lets you set the light and temperature yourself.
- `dvm_lake_live_data.html` (Live Buoy Data) is driven by the Trout Lake buoy.

## How the live data works

The UW-Madison Center for Limnology buoy feed only allows browser pages on `uwcfl.github.io` to read it. To get around that, `.github/workflows/trout-buoy.yml` runs about every 10 minutes:

1. It runs `scripts/fetch_trout_buoy.py`, which saves the newest buoy reading as `trout_latest.json`.
2. It publishes the site to GitHub Pages.

The live page reads `trout_latest.json`. The Pages source must be set to **GitHub Actions** (Settings → Pages).

## Sources

- Model: DaphniaDVM by Bennett McAfee, ported to JavaScript with permission. Predator profile (both drawings) and baseline temperatures (Data Sliders): Trout Lake, May 1992.
- Live data: [Trout Lake Buoy Live Data](https://uwcfl.github.io/buoy-viewer/trout.html), UW-Madison Center for Limnology. These data are not quality controlled.
- Chlorophyll: Magnuson, J.J., S.R. Carpenter, and E.H. Stanley. 2025. North Temperate Lakes LTER: Chlorophyll - Trout Lake Area 1981 - current ver 33. Environmental Data Initiative. https://doi.org/10.6073/pasta/659e43f4796f71e3a37673a0f2d7a77a (Accessed 2026-10-09). Median chlorophyll by depth: the current month for Live Buoy Data, all dates for Data Sliders.
- Zooplankton: NTL LTER, E.H. Stanley, S.R. Carpenter, and J.J. Magnuson. 2026. North Temperate Lakes LTER: Zooplankton - Trout Lake Area 1982 - current ver 42. Environmental Data Initiative. Monthly Daphnia density sets the dot count, and measured lengths set the size mix.
- Lake volume: Trout Lake, 0.240 km³ (Wisconsin DNR).
