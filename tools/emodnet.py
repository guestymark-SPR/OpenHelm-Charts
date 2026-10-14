#!/usr/bin/env python3
"""Download the EMODnet Bathymetry DTM (depths relative to LAT) for a box as one GeoTIFF, in chunks.
Robust against a busy server: long timeouts, retries with back-off, stubborn chunks are split into
quarters, and as a last resort a chunk is skipped with a warning rather than failing the whole build."""
import subprocess, sys, urllib.request, os, time

W, S, E, N, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
STEP = 1.5
BASE = 'https://ows.emodnet-bathymetry.eu/wcs?service=WCS&version=2.0.1&request=GetCoverage&coverageId=emodnet__mean&format=image/tiff'
parts, skipped = [], []


def get(x, y, x2, y2, fn):
    url = BASE + f'&subset=Lat({y:.4f},{y2:.4f})&subset=Long({x:.4f},{x2:.4f})'
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=240) as r, open(fn, 'wb') as f:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    f.write(b)
            with open(fn, 'rb') as f:
                head = f.read(4)
            if os.path.getsize(fn) > 1000 and head[:2] in (b'II', b'MM'):
                return True
            print(f'  {fn}: not a GeoTIFF ({os.path.getsize(fn)} bytes), retrying', flush=True)
        except Exception as e:
            print(f'  {fn}: attempt {attempt + 1} failed: {e}', flush=True)
        time.sleep(10 * (attempt + 1))
    return False


def chunk(x, y, x2, y2, level=0):
    fn = f'emod_{len(parts) + len(skipped)}_{level}.tif'
    if get(x, y, x2, y2, fn):
        parts.append(fn)
        print('chunk', fn, os.path.getsize(fn), flush=True)
        return
    if level < 2:
        mx, my = (x + x2) / 2, (y + y2) / 2
        print(f'splitting {x:.2f},{y:.2f},{x2:.2f},{y2:.2f}', flush=True)
        for a, b, c, d in ((x, y, mx, my), (mx, y, x2, my), (x, my, mx, y2), (mx, my, x2, y2)):
            chunk(a, b, c, d, level + 1)
        return
    skipped.append((x, y, x2, y2))
    print(f'::warning::EMODnet depth missing for {x:.2f},{y:.2f} to {x2:.2f},{y2:.2f} (server kept failing)', flush=True)


y = S
while y < N - 1e-9:
    x = W
    while x < E - 1e-9:
        x2, y2 = min(x + STEP, E), min(y + STEP, N)
        chunk(x, y, x2, y2)
        x = x2
    y = y2

if not parts:
    sys.exit('no depth data could be downloaded')
if len(skipped) > 6:
    sys.exit(f'too many depth chunks missing ({len(skipped)})')
subprocess.check_call(['gdalbuildvrt', '-q', 'depth.vrt'] + parts)
subprocess.check_call(['gdal_translate', '-q', '-co', 'COMPRESS=DEFLATE', '-co', 'BIGTIFF=IF_SAFER', 'depth.vrt', out])
print(f'depth chunks: {len(parts)} downloaded, {len(skipped)} skipped', flush=True)
