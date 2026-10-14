#!/usr/bin/env python3
"""Daily tidal-stream files for OpenHelm from the Copernicus Marine NW European Shelf model (1.5 km, hourly, tides included).

Writes one compact file per region (tools/regions.json) plus index.json:
  first line: JSON header; then int8 u (east) and int8 v (north) arrays, [time][row][col], row 0 = south.
  value * scale = metres/second; -128 = no data (land).
Needs COPERNICUSMARINE_SERVICE_USERNAME / COPERNICUSMARINE_SERVICE_PASSWORD in the environment.
"""
import json, os, sys, datetime as dt
import numpy as np
import copernicusmarine as cm
import xarray as xr

PRODUCT = 'NWSHELF_ANALYSISFORECAST_PHY_004_013'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'currents'
HOURS = int(os.environ.get('HOURS', '96'))
SCALE = 0.04  # m/s per step -> range +/-5.1 m/s
os.makedirs(OUT, exist_ok=True)


def pick_dataset():
    """Find the hourly (or 15-minute) surface current dataset; names change between product versions."""
    cat = cm.describe(product_id=PRODUCT)
    ids = []
    for p in getattr(cat, 'products', []) or []:
        for d in getattr(p, 'datasets', []) or []:
            ids.append(d.dataset_id)
    print('datasets:', ids, flush=True)
    def score(i):
        s = 0
        if 'PT1H' in i: s += 4
        if 'PT15M' in i: s += 2
        if '2D' in i: s += 3
        if 'uv' in i or 'cur' in i: s += 2
        if 'phy' in i: s += 1
        if 'detided' in i.lower() or 'P1D' in i or 'P1M' in i: s -= 20
        return s
    ids = [i for i in ids if score(i) > 0]
    if not ids:
        sys.exit('no suitable dataset found')
    return sorted(ids, key=score, reverse=True)


now = dt.datetime.now(dt.timezone.utc).replace(minute=0, second=0, microsecond=0)
t0, t1 = now - dt.timedelta(hours=2), now + dt.timedelta(hours=HOURS)
ds = None
for did in pick_dataset():
    try:
        print('trying', did, flush=True)
        ds = cm.open_dataset(dataset_id=did, variables=['uo', 'vo'], minimum_longitude=-11.2, maximum_longitude=2.6,
                             minimum_latitude=49.4, maximum_latitude=61.3, start_datetime=t0.isoformat(), end_datetime=t1.isoformat(),
                             minimum_depth=0, maximum_depth=1.5)
        if 'uo' in ds and 'vo' in ds:
            print('using', did, flush=True)
            break
    except Exception as e:
        print('  failed:', e, flush=True)
        ds = None
if ds is None:
    sys.exit('could not open any current dataset')

if 'depth' in ds.dims:
    ds = ds.isel(depth=0)
lon_name = 'longitude' if 'longitude' in ds.coords else 'lon'
lat_name = 'latitude' if 'latitude' in ds.coords else 'lat'
ds = ds.sortby(lat_name)
# hourly steps
ds = ds.resample(time='1h').mean() if ds.time.size > 1 and (ds.time[1] - ds.time[0]).values < np.timedelta64(59, 'm') else ds
times = ds.time.values.astype('datetime64[s]').astype(np.int64)
lon = ds[lon_name].values.astype(float)
lat = ds[lat_name].values.astype(float)
print('grid', lon.size, 'x', lat.size, 'times', times.size, flush=True)

regions = json.load(open(os.path.join(os.path.dirname(__file__), 'regions.json')))
index = {'updated': now.isoformat(), 'source': 'Copernicus Marine Service, ' + PRODUCT, 'scale': SCALE, 'files': []}
for r in regions:
    w, s, e, n = r['bounds']
    xi = np.where((lon >= w - .05) & (lon <= e + .05))[0]
    yi = np.where((lat >= s - .05) & (lat <= n + .05))[0]
    if xi.size < 2 or yi.size < 2:
        continue
    step = 2 if (e - w) * (n - s) > 6 else 1          # 3 km on the big offshore areas, 1.5 km elsewhere
    xi, yi = xi[::step], yi[::step]
    sub = ds.isel({lon_name: xi, lat_name: yi})
    u = sub['uo'].values.astype(np.float32)
    v = sub['vo'].values.astype(np.float32)
    def q(a):
        o = np.round(a / SCALE)
        o = np.clip(o, -127, 127)
        o[~np.isfinite(a)] = -128
        return o.astype(np.int8)
    hdr = {'id': r['id'], 'nx': int(xi.size), 'ny': int(yi.size), 'nt': int(times.size), 'lon0': float(lon[xi[0]]), 'lat0': float(lat[yi[0]]),
           'dlon': float(lon[xi[1]] - lon[xi[0]]), 'dlat': float(lat[yi[1]] - lat[yi[0]]), 't0': int(times[0]) * 1000, 'dt': 3600000, 'scale': SCALE,
           'bounds': r['bounds']}
    fn = f"cur-{r['id']}.bin"
    with open(os.path.join(OUT, fn), 'wb') as f:
        f.write((json.dumps(hdr) + '\n').encode())
        f.write(q(u).tobytes())
        f.write(q(v).tobytes())
    size = os.path.getsize(os.path.join(OUT, fn))
    index['files'].append({**hdr, 'file': fn, 'size': size})
    print(f"::notice::{r['id']}: {xi.size}x{yi.size}x{times.size} -> {size // 1024} KB", flush=True)
json.dump(index, open(os.path.join(OUT, 'index.json'), 'w'))
