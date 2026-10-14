#!/usr/bin/env python3
"""Merge several MBTiles vector packs into one. Vector tiles are protobuf messages whose 'layers'
field is repeated, so joining the decompressed bytes of tiles with different layers gives a valid tile."""
import sqlite3, gzip, sys, json
out, ins = sys.argv[1], sys.argv[2:]
o = sqlite3.connect(out)
o.executescript('''DROP TABLE IF EXISTS tiles; DROP TABLE IF EXISTS metadata;
CREATE TABLE metadata (name text, value text); CREATE UNIQUE INDEX name on metadata (name);
CREATE TABLE tiles (zoom_level integer, tile_column integer, tile_row integer, tile_data blob);''')
acc = {}
layers = []
minz, maxz = 99, 0
for path in ins:
    db = sqlite3.connect(path)
    md = dict(db.execute('select name, value from metadata').fetchall())
    try:
        layers += json.loads(md.get('json', '{}')).get('vector_layers', [])
    except Exception:
        pass
    n = 0
    for z, x, y, d in db.execute('select zoom_level, tile_column, tile_row, tile_data from tiles'):
        if d[:2] == b'\x1f\x8b':
            d = gzip.decompress(d)
        k = (z, x, y)
        acc[k] = acc[k] + d if k in acc else d
        minz, maxz = min(minz, z), max(maxz, z)
        n += 1
    print(path, 'tiles', n, flush=True)
    db.close()
o.executemany('insert into tiles values (?,?,?,?)', ((z, x, y, gzip.compress(d, 6)) for (z, x, y), d in acc.items()))
o.execute('create unique index tile_index on tiles (zoom_level, tile_column, tile_row)')
o.executemany('insert into metadata values (?,?)', [('format', 'pbf'), ('type', 'baselayer'), ('minzoom', str(minz)), ('maxzoom', str(maxz)),
               ('json', json.dumps({'vector_layers': layers}))])
o.commit()
print('merged tiles', len(acc))
