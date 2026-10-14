#!/usr/bin/env python3
"""Turn OpenStreetMap seamark/marina features into chart-ready features with a symbol id and a light label."""
import json, sys

COLS = {'white': 'W', 'red': 'R', 'green': 'G', 'yellow': 'Y', 'blue': 'Bu', 'orange': 'Or', 'violet': 'Vi', 'amber': 'Am'}
LINES = {'cable_submarine', 'pipeline_submarine', 'cable_overhead', 'separation_line', 'separation_boundary',
         'recommended_track', 'navigation_line', 'fairway', 'restricted_area', 'separation_zone', 'traffic_separation_scheme_lane_part'}

def light(t, p='seamark:light:'):
    ch = t.get(p + 'character')
    if not ch:
        return ''
    g = t.get(p + 'group')
    col = ''.join(COLS.get(c, '') for c in t.get(p + 'colour', '').split(';'))
    per = t.get(p + 'period')
    rng = t.get(p + 'range')
    s = ch + (f'({g})' if g else '') + col + (f'.{per}s' if per else '') + (f'{rng}M' if rng else '')
    return s

def sym(t):
    st = t.get('seamark:type', '')
    cat = t.get(f'seamark:{st}:category', '')
    if t.get('leisure') == 'marina' or (st == 'harbour' and 'marina' in t.get('seamark:harbour:category', '')):
        return 'marina'
    if st == 'harbour':
        return 'harbour'
    if t.get('waterway') == 'fuel' or 'fuel' in t.get('seamark:small_craft_facility:category', ''):
        return 'fuel'
    if t.get('leisure') == 'slipway':
        return 'slipway'
    if st in ('buoy_lateral', 'beacon_lateral'):
        b = 'bcn_' if st.startswith('beacon') else ''
        if 'preferred_channel_port' in cat: return b + 'pref_port'
        if 'preferred_channel_starboard' in cat: return b + 'pref_stbd'
        if 'port' in cat: return b + 'lat_port'
        if 'starboard' in cat: return b + 'lat_stbd'
        col = t.get(f'seamark:{st}:colour', '')
        return b + ('lat_port' if col.startswith('red') else 'lat_stbd' if col.startswith('green') else 'special')
    if st in ('buoy_cardinal', 'beacon_cardinal'):
        return 'card_' + (cat[:1] if cat[:1] in 'nesw' else 'n')
    if st in ('buoy_isolated_danger', 'beacon_isolated_danger'):
        return 'isolated'
    if st in ('buoy_safe_water', 'beacon_safe_water'):
        return 'safewater'
    if st.startswith('buoy_') or st.startswith('beacon_'):
        return 'special'
    if st in ('light_major', 'light_vessel', 'light_float'):
        return 'light_major'
    if st == 'light_minor' or (st in ('landmark', 'pile') and t.get('seamark:light:character')):
        return 'light_minor'
    if st == 'wreck':
        return 'wreck' if 'non' not in cat else 'wreck_safe'
    if st in ('rock', 'obstruction'):
        return st
    if st in ('anchorage', 'anchor_berth'):
        return 'anchorage'
    if st in ('mooring',):
        return 'mooring'
    if st == 'landmark':
        return 'landmark'
    if st == 'small_craft_facility':
        return 'facility'
    if st in ('rescue_station',):
        return 'rescue'
    return 'other'

def centroid(geom):
    pts = []
    def walk(c):
        if c and isinstance(c[0], (int, float)):
            pts.append(c)
        else:
            for x in c:
                walk(x)
    walk(geom['coordinates'])
    if not pts:
        return None
    return [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]

out = open(sys.argv[2], 'w')
n = 0
for line in open(sys.argv[1], encoding='utf-8'):
    line = line.strip().lstrip('\x1e')
    if not line:
        continue
    f = json.loads(line)
    t = f.get('properties') or {}
    st = t.get('seamark:type', '')
    g = f.get('geometry')
    if not g:
        continue
    props = {k: v for k, v in t.items() if k.startswith('seamark:') or k in (
        'name', 'leisure', 'waterway', 'phone', 'contact:phone', 'website', 'contact:website', 'email', 'contact:email', 'vhf',
        'opening_hours', 'capacity', 'operator', 'fuel', 'power_supply', 'drinking_water', 'shower', 'toilets', 'sanitary_dump_station',
        'depth', 'description', 'addr:street', 'addr:city', 'addr:postcode')}
    props['sym'] = sym(t)
    props['nm'] = t.get('seamark:name') or t.get('name') or ''
    lt = light(t)
    if not lt:
        for i in range(1, 10):
            lt = light(t, f'seamark:light:{i}:')
            if lt:
                break
    if lt:
        props['lt'] = lt
    props['osm'] = f"{t.get('@type', '')[:1]}{t.get('@id', '')}"
    if st in LINES and g['type'] in ('LineString', 'MultiLineString'):
        props['kind'] = 'line'
        feat = {'type': 'Feature', 'geometry': g, 'properties': props}
    else:
        c = g['coordinates'] if g['type'] == 'Point' else centroid(g)
        if not c:
            continue
        props['kind'] = 'point'
        mz = 9 if props['sym'] in ('light_major', 'marina', 'harbour') else 11 if props['sym'] in ('light_minor', 'card_n', 'card_e', 'card_s', 'card_w', 'isolated', 'safewater', 'wreck') else 12
        feat = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': c}, 'properties': props, 'tippecanoe': {'minzoom': mz}}
    out.write(json.dumps(feat, separators=(',', ':')) + '\n')
    n += 1
print('seamark features:', n)
