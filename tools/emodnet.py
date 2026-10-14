#!/usr/bin/env python3
"""Download the EMODnet Bathymetry DTM (depths relative to LAT) for a box as one GeoTIFF, in chunks."""
import subprocess, sys, urllib.request, math, os, time
W, S, E, N, out = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
STEP = 1.5
parts = []
y = S
while y < N - 1e-9:
    x = W
    while x < E - 1e-9:
        x2, y2 = min(x + STEP, E), min(y + STEP, N)
        url = ('https://ows.emodnet-bathymetry.eu/wcs?service=WCS&version=2.0.1&request=GetCoverage&coverageId=emodnet__mean'
               f'&format=image/tiff&subset=Lat({y:.4f},{y2:.4f})&subset=Long({x:.4f},{x2:.4f})')
        fn = f'emod_{len(parts)}.tif'
        for attempt in range(4):
            try:
                urllib.request.urlretrieve(url, fn)
                if os.path.getsize(fn) > 1000:
                    break
            except Exception as e:
                print('retry', attempt, e)
            time.sleep(5)
        parts.append(fn)
        print('chunk', fn, os.path.getsize(fn))
        x = x2
    y = y2
subprocess.check_call(['gdalbuildvrt', 'depth.vrt'] + parts)
subprocess.check_call(['gdal_translate', '-q', '-co', 'COMPRESS=DEFLATE', 'depth.vrt', out])
