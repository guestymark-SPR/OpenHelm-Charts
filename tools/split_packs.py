#!/usr/bin/env python3
"""Cut regional chart packs out of UK-wide layer files, merging layers per tile (memory-safe: one region at a time).
Coastline only: the first input is the land/base map; the others (seamarks, depth) mark where the sea is.
From zoom 10 up, a base-map tile is kept only if it is at sea or within a couple of km of it (or of a seamark/marina)."""
import sqlite3, gzip, json, math, sys, os
regions = json.load(open(sys.argv[1])); outdir = sys.argv[2]; ins = sys.argv[3:]
os.makedirs(outdir, exist_ok=True)
srcs = [sqlite3.connect(p) for p in ins]
layers = []
for db in srcs:
    md = dict(db.execute('select name, value from metadata').fetchall())
    try: layers += json.loads(md.get('json', '{}')).get('vector_layers', [])
    except Exception: pass
COAST_Z = 10
def tx(lon, z): return int((lon + 180) / 360 * 2 ** z)
def ty(lat, z):
    r = math.radians(lat); return int((1 - math.log(math.tan(r) + 1 / math.cos(r)) / math.pi) / 2 * 2 ** z)
for reg in regions:
    w, s, e, n = reg['bounds']; path = os.path.join(outdir, reg['id'] + '.mbtiles')
    if os.path.exists(path): os.remove(path)
    o = sqlite3.connect(path)
    o.executescript('CREATE TABLE metadata (name text, value text); CREATE UNIQUE INDEX name on metadata (name);'
                    'CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);')
    total = 0; skipped = 0
    for z in range(0, 15):
        x0, x1, y0, y1 = tx(w, z), tx(e, z), ty(n, z), ty(s, z)
        r0, r1 = (1 << z) - 1 - y1, (1 << z) - 1 - y0
        acc = {}
        sea = None
        if z >= COAST_Z:
            sea = set()
            for db in srcs[1:]:
                sea.update(db.execute('select tile_column, tile_row from tiles where zoom_level=? and tile_column between ? and ? and tile_row between ? and ?', (z, x0 - 2, x1 + 2, r0 - 2, r1 + 2)).fetchall())
            k = 1 if z < 13 else 2  # land band: ~1 tile at z10-12 (2-20 km), 2 tiles at z13-14 (~2-4 km)
            near = set()
            for x, r in sea:
                for dx in range(-k, k + 1):
                    for dr in range(-k, k + 1): near.add((x + dx, r + dr))
            sea = near
        for i, db in enumerate(srcs):
            for x, r, d in db.execute('select tile_column, tile_row, tile_data from tiles where zoom_level=? and tile_column between ? and ? and tile_row between ? and ?', (z, x0, x1, r0, r1)):
                if i == 0 and sea is not None and (x, r) not in sea: skipped += 1; continue
                if d[:2] == b'\x1f\x8b': d = gzip.decompress(d)
                acc[(x, r)] = acc[(x, r)] + d if (x, r) in acc else d
        o.executemany('insert into tiles values (?,?,?,?)', ((z, x, r, gzip.compress(d, 6)) for (x, r), d in acc.items()))
        total += len(acc)
    o.execute('create unique index tile_index on tiles (zoom_level, tile_column, tile_row)')
    from datetime import date
    o.executemany('insert into metadata values (?,?)', [('name', reg['title']), ('format', 'pbf'), ('type', 'baselayer'), ('minzoom', '0'), ('maxzoom', '14'),
        ('bounds', ','.join(str(v) for v in reg['bounds'])), ('openhelm_pack', reg['id']), ('version', date.today().isoformat()),
        ('attribution', '© OpenStreetMap contributors, © OpenMapTiles, EMODnet Bathymetry'), ('json', json.dumps({'vector_layers': layers}))])
    o.commit(); o.execute('VACUUM'); o.close()
    print(f"::notice::{reg['id']}: {total} tiles ({skipped} inland tiles left out), {os.path.getsize(path) // 1048576} MB", flush=True)
