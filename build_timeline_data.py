#!/usr/bin/env python3
"""
Build timeline_data.js for the "Lake Through Time" drawing
(dvm_lake_timeline.html) from five NTL-LTER datasets (Trout Lake rows only).

Usage:
  python3 scripts/build_timeline_data.py PHYS.csv CHL.csv ZOOP.csv ICE.csv MET_HOURLY.csv SONAR_INTERVAL.csv [out.js]

  PHYS  North Temperate Lakes LTER: Physical Limnology of Primary Study Lakes 1981 - current (ntl29)
  CHL   North Temperate Lakes LTER: Chlorophyll - Trout Lake Area 1981 - current (ntl35)
  ZOOP  North Temperate Lakes LTER: Zooplankton - Trout Lake Area 1982 - current (ntl37)
  ICE   North Temperate Lakes LTER: Ice Duration - Trout Lake Area 1981 - current (ntl32)
  MET   North Temperate Lakes LTER: Meteorological Data - Woodruff Airport 1989 - current, hourly (ntl17)
  SONAR North Temperate Lakes LTER: Pelagic Prey - Sonar Data 2001 - current, Interval Density table (ntl115)

The timeline runs in 7-day steps from the first Trout Lake temperature profile
to the last one. For each step it stores:
  - water temperature and chlorophyll on the model's 2 m patches (0-32 m)
  - total Daphnia density (individuals / L)
  - 24 hourly wind speeds and 24 hourly surface PAR values for that day
  - a quality code for each of temperature, chlorophyll, Daphnia, weather:
      m = measured on that day (a sample within 3 days)
      i = interpolated between two samples no more than GAP_DAYS apart
      e = estimated from the long-term average for that time of year
Ice-on / ice-off dates are passed through as a list of periods.
It also stores one fish (predator) profile per sonar survey year; see
predator_profiles() below.
"""

import json
import sys
from datetime import date, timedelta

import numpy as np
import pandas as pd

GRID = np.arange(0, 33, 2)          # model patches, m
STEP_DAYS = 7
GAP_DAYS = 60                        # longest gap bridged by straight interpolation
NEAR_DAYS = 3                        # sample this close counts as "measured"
PAR_MAX = 2500                       # drop impossible PAR readings (sensor spikes)


def profile_on_grid(depths, values):
    """Interpolate one depth profile onto GRID; hold the end values flat."""
    order = np.argsort(depths)
    d, v = np.asarray(depths)[order], np.asarray(values)[order]
    return np.interp(GRID, d, v)


def per_date_profiles(df, value_col, min_depths=4):
    """{date: array on GRID} for sample dates with enough depths."""
    out = {}
    for sd, g in df.groupby("sampledate"):
        g = g.dropna(subset=[value_col]).groupby("depth")[value_col].median()
        if len(g) >= min_depths:
            out[pd.Timestamp(sd).date()] = profile_on_grid(g.index.values, g.values)
    return out


def woy(d):
    return min(d.timetuple().tm_yday // 7, 51)


def climatology(series_by_date, stat=np.median):
    """typical value per week-of-year (arrays or scalars), with circular smoothing.
    Profiles use the median; Daphnia density uses the mean, because many
    samples are 0 and a median would make the lake look empty."""
    buckets = {}
    for d, v in series_by_date.items():
        buckets.setdefault(woy(d), []).append(v)
    clim = {}
    for w in range(52):
        # 5-week window smooths sparse weeks; widen it until it finds data
        # (e.g. Daphnia were never sampled in late December)
        near, span = [], 2
        while not near:
            near = [v for dw in range(-span, span + 1) for v in buckets.get((w + dw) % 52, [])]
            span += 1
        clim[w] = stat(np.array(near), axis=0)
    return clim


def series_at(day, by_date, sorted_dates, clim):
    """value for `day`: measured, interpolated, or climatology."""
    i = np.searchsorted(sorted_dates, day)
    prev = sorted_dates[i - 1] if i > 0 else None
    nxt = sorted_dates[i] if i < len(sorted_dates) else None
    for s in (prev, nxt):
        if s is not None and abs((s - day).days) <= NEAR_DAYS:
            return by_date[s], "m"
    if prev is not None and nxt is not None and (nxt - prev).days <= GAP_DAYS:
        f = (day - prev).days / (nxt - prev).days
        return by_date[prev] * (1 - f) + by_date[nxt] * f, "i"
    return clim[woy(day)], "e"


NMI2 = 1852.0 ** 2      # m^2 in a square nautical mile
PISCIVORES = {"WALLEYE", "LAKETROUT"}


def predator_profiles(sonar_p):
    """Fish per 1000 m^3 on the model's 2 m patches, one profile per survey
    year (Trout Lake, midsummer night surveys, south basin).

    Units: the Interval Density table's `density` is fish per square
    nautical mile in each 1 m layer (Echoview convention: dividing it by
    10^((Sv - TS)/10), the fish per m^3 implied by the layer's backscatter
    and the species' target strength, gives 1852^2 m^2 whenever a single
    species fills the layer). So fish per m^3 = density / 1852^2 for a 1 m
    layer, and x1000 gives fish per 1000 m^3 - the unit of the model's
    `predators` input (McAfee 2021 reports Trout Lake at ~15 fish per
    1000 m^3; the May 1992 column peaks at 25.7).

    Fish eaters (walleye, lake trout) are left out: the model's predators
    are visual zooplankton feeders. 2014's density column is corrupted (it
    holds the target strength, -41.1, with species_ts = 100), so 2014 is
    recomputed from sv_mean with cisco target strength -41.1 dB.
    The top patch (0 m) is not sampled by the sonar; it takes the 2 m value.
    """
    d = pd.read_csv(sonar_p, low_memory=False)
    d = d[d.lakeid == "TR"].copy()
    d["species"] = d.species.str.strip().str.upper()
    d = d[~d.species.isin(PISCIVORES)]
    d["per1000"] = d.density.clip(lower=0) / NMI2 * 1000
    bad = d.year4 == 2014
    sv = d.loc[bad, "sv_mean"]
    d.loc[bad, "per1000"] = np.where(sv > -900, 10 ** ((sv - (-41.1)) / 10), 0) * 1000
    lay = (d.groupby(["year4", "sampledate", "spatial_interval", "layer_depth_mean"]).per1000.sum()
           .reset_index())
    lay["patch"] = (2 * np.round(lay.layer_depth_mean / 2)).clip(0, 32)
    prof = lay.groupby(["year4", "patch"]).per1000.mean().unstack().reindex(columns=GRID.astype(float))
    prof[0.0] = prof[0.0].fillna(prof[2.0])
    prof = prof.fillna(0)
    return {int(y): [round(float(v), 2) for v in row] for y, row in prof.iterrows()}


def fix_clock_offsets(met):
    """Detect and undo whole-year clock offsets in the hourly weather.

    In the ver 41 file every 2025 hour is shifted by 12 h (sunlight peaks at
    "1 AM"; air temperature agrees), apparently an AM/PM mix-up. For each
    year, the average daily light curve is compared with the all-years curve
    at every possible hour shift; if a shift other than 0 matches clearly
    better, that year's hours are rolled back by it (within each day).
    """
    good = met[met.avg_par.between(0, PAR_MAX)]
    ref = good.groupby("h").avg_par.mean().reindex(range(24)).values
    years = pd.to_datetime(met.sampledate).dt.year
    for y in sorted(years.unique()):
        cur = good[pd.to_datetime(good.sampledate).dt.year == y].groupby("h").avg_par.mean().reindex(range(24))
        if cur.isna().sum() > 2:
            continue
        cur = cur.interpolate(limit_direction="both").values
        scores = [np.corrcoef(ref, np.roll(cur, -k))[0, 1] for k in range(24)]
        best = int(np.argmax(scores))
        if best != 0 and scores[best] - scores[0] > 0.3:
            print(f"weather {y}: hours shifted by {best} h, corrected")
            sel = years == y
            met.loc[sel, "h"] = (met.loc[sel, "h"] - best) % 24
    return met


def main():
    phys_p, chl_p, zoop_p, ice_p, met_p, sonar_p = sys.argv[1:7]
    out_p = sys.argv[7] if len(sys.argv) > 7 else "timeline_data.js"
    predators = predator_profiles(sonar_p)

    # temperature
    phys = pd.read_csv(phys_p, low_memory=False)
    phys = phys[(phys.lakeid == "TR") & phys.wtemp.between(-1, 35)]
    temp = per_date_profiles(phys, "wtemp", min_depths=8)

    # chlorophyll (negative readings dropped)
    chl = pd.read_csv(chl_p)
    chl = chl[(chl.lakeid == "TR") & (chl.chlor >= 0)]
    chlp = per_date_profiles(chl, "chlor", min_depths=4)

    # Daphnia: all species named DAPHNIA*, summed per date; dates with no
    # Daphnia recorded count as 0
    z = pd.read_csv(zoop_p)
    z = z[z.lakeid == "TR"].rename(columns={"sample_date": "sampledate"})
    dates = z.sampledate.unique()
    daph = (z[z.species_name.str.match(r"^DAPHNIA", na=False)]
            .groupby("sampledate").density.sum().reindex(dates, fill_value=0))
    dens = {pd.Timestamp(k).date(): float(v) for k, v in daph.items()}

    # ice
    ice = pd.read_csv(ice_p)
    ice = ice[ice.lakeid == "TR"].dropna(subset=["ice_on", "ice_off"])
    ice_periods = [[r.ice_on, r.ice_off] for r in ice.itertuples()]

    # hourly weather (hour 100 = hour ending 01:00, local standard time)
    met = pd.read_csv(met_p, usecols=["sampledate", "hour", "avg_wind_speed", "avg_par"], low_memory=False)
    met["h"] = (met.hour // 100).clip(0, 23)
    met["d"] = pd.to_datetime(met.sampledate).dt.date
    met = fix_clock_offsets(met)
    met.loc[(met.avg_par < 0), "avg_par"] = 0
    met.loc[(met.avg_par > PAR_MAX), "avg_par"] = np.nan
    wind_day = met.pivot_table(index="d", columns="h", values="avg_wind_speed")
    par_day = met.pivot_table(index="d", columns="h", values="avg_par")
    met["m"] = pd.to_datetime(met.sampledate).dt.month
    wind_clim = met.pivot_table(index="m", columns="h", values="avg_wind_speed", aggfunc="median")

    t_dates, c_dates, z_dates = (np.array(sorted(x)) for x in (temp, chlp, dens))
    t_clim, c_clim, z_clim = climatology(temp), climatology(chlp), climatology(dens, np.mean)

    start, end = t_dates[0], t_dates[-1]
    steps = []
    day = start
    while day <= end:
        t, tq = series_at(day, temp, t_dates, t_clim)
        c, cq = series_at(day, chlp, c_dates, c_clim)
        dn, zq = series_at(day, dens, z_dates, z_clim)

        if day in wind_day.index and wind_day.loc[day].notna().sum() >= 18:
            w = wind_day.loc[day].reindex(range(24)).interpolate(limit_direction="both").values
            wq = "m"
        else:
            w = wind_clim.loc[day.month].reindex(range(24)).values
            wq = "e"
        if day in par_day.index and par_day.loc[day].notna().sum() >= 18:
            p = par_day.loc[day].reindex(range(24)).interpolate(limit_direction="both").values
            p = [int(round(x)) for x in p]
        else:
            p = None   # the page estimates light from the sun's position

        steps.append([
            day.isoformat(),
            [round(float(x), 1) for x in t],
            [round(float(x), 2) for x in c],
            round(float(dn), 2),
            [round(float(x), 1) for x in w],
            p,
            tq + cq + zq + wq,
        ])
        day += timedelta(days=STEP_DAYS)

    data = {
        "grid": GRID.tolist(),
        "stepDays": STEP_DAYS,
        "fields": ["date", "temp", "chl", "daphniaPerL", "windHourly", "parHourly", "quality(temp,chl,daphnia,weather)"],
        "ice": ice_periods,
        "predatorsByYear": predators,
        "steps": steps,
    }
    with open(out_p, "w") as f:
        f.write("// Generated by scripts/build_timeline_data.py - see that file for sources and methods.\n")
        f.write("window.TIMELINE_DATA = ")
        json.dump(data, f, separators=(",", ":"))
        f.write(";\n")
    q = pd.Series([s[6] for s in steps])
    print(f"{len(steps)} steps, {steps[0][0]} to {steps[-1][0]}")
    for i, name in enumerate(["temp", "chl", "daphnia", "weather"]):
        print(name, q.str[i].value_counts().to_dict())
    print("days with measured PAR:", sum(s[5] is not None for s in steps))
    print("predator survey years:", sorted(predators))


if __name__ == "__main__":
    main()
