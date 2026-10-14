#!/usr/bin/env python3
"""Spot soundings like a paper chart: thinned depth points (metres below LAT), denser at higher zooms."""
import json, subprocess, sys
src, out = sys.argv[1], sys.argv[2]
subprocess.check_call(['gdal_translate', '-q', '-of', 'XYZ', '-r', 'max', '-outsize', '25%', '25%', src, 'snd.xyz'])
n = 0
with open(out, 'w') as o:
    for i, line in enumerate(open('snd.xyz')):
        p = line.split()
        if len(p) < 3:
            continue
        x, y, z = float(p[0]), float(p[1]), float(p[2])
        if z != z or z < -12000 or z > 30:
            continue
        d = -z
        # shallowest value in each block (safe side); every 4th point appears from zoom 11, the rest from 13
        mz = 11 if i % 4 == 0 else 13
        o.write(json.dumps({'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [round(x, 5), round(y, 5)]},
                            'properties': {'d': round(d, 1)}, 'tippecanoe': {'minzoom': mz}}, separators=(',', ':')) + '\n')
        n += 1
print('soundings:', n)
