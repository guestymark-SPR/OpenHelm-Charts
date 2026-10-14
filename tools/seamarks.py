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


import math
def scf(t): return t.get('seamark:small_craft_facility:category', '')
FAC = [('fuel', lambda t: t.get('waterway') == 'fuel' or 'fuel' in scf(t)),
       ('water', lambda t: t.get('amenity') in ('drinking_water', 'water_point') or 'water_tap' in scf(t)),
       ('toilets', lambda t: t.get('amenity') == 'toilets' or 'toilets' in scf(t)),
       ('showers', lambda t: t.get('amenity') == 'shower' or 'showers' in scf(t)),
       ('pumpout', lambda t: t.get('amenity') == 'sanitary_dump_station' or t.get('waterway') == 'sanitary_dump_station' or 'pump_out' in scf(t)),
       ('waste', lambda t: t.get('amenity') in ('waste_disposal', 'recycling') or 'refuse_bin' in scf(t)),
       ('chandlery', lambda t: t.get('shop') in ('boat', 'chandler', 'ship_chandler', 'marine') or 'chandler' in scf(t)),
       ('boatyard', lambda t: t.get('craft') == 'boatbuilder' or t.get('waterway') == 'boatyard' or t.get('shop') == 'boat_repair' or 'boatyard' in scf(t)),
       ('sailmaker', lambda t: t.get('craft') == 'sailmaker' or 'sailmaker' in scf(t)),
       ('slipway', lambda t: t.get('leisure') == 'slipway' or 'slipway' in scf(t)),
       ('crane', lambda t: t.get('man_made') == 'crane' or 'boat_hoist' in scf(t)),
       ('laundry', lambda t: t.get('shop') == 'laundry' or 'laundrette' in scf(t)),
       ('harbourmaster', lambda t: t.get('office') == 'harbour_master' or 'harbour_master' in scf(t)),
       ('club', lambda t: t.get('club') == 'sailing' or 'nautical_club' in scf(t)),
       ('food', lambda t: t.get('amenity') in ('restaurant', 'cafe', 'pub', 'bar', 'fast_food')),
       ('shop', lambda t: t.get('shop') in ('supermarket', 'convenience')),
       ('atm', lambda t: t.get('amenity') == 'atm')]
def contact(t):
    return {'tel': t.get('phone') or t.get('contact:phone') or t.get('seamark:harbour:phone') or '',
            'web': t.get('website') or t.get('contact:website') or '', 'em': t.get('email') or t.get('contact:email') or '',
            'vhf': t.get('vhf') or t.get('vhf:channel') or ''}
def related(a, b):
    n, m, op = (a.get('name') or '').lower(), (b.get('name') or '').lower(), (a.get('operator') or '').lower()
    return bool(n and m and (m.startswith(n) or n.startswith(m)) or n and (b.get('operator') or '').lower() == n
                or op and (m == op or (b.get('operator') or '').lower() == op))
def metres(a, b):
    dy = (a[1] - b[1]) * 111320; dx = (a[0] - b[0]) * 111320 * math.cos(math.radians(a[1])); return math.hypot(dx, dy)

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

def is_chart(t):
    return bool(t.get('seamark:type') or t.get('leisure') in ('marina', 'slipway') or t.get('waterway') == 'fuel')
places, grid = [], {}
def cell(c): return (int(c[0] * 100), int(c[1] * 100))
for line in open(sys.argv[1], encoding='utf-8'):
    line = line.strip().lstrip('\x1e')
    if not line: continue
    f = json.loads(line); t = f.get('properties') or {}; g = f.get('geometry')
    if not g: continue
    c = g['coordinates'] if g['type'] == 'Point' else centroid(g)
    if not c: continue
    kinds = [k for k, fn in FAC if fn(t)]; ct = contact(t)
    if kinds or any(ct.values()) or is_chart(t):
        i = len(places); places.append((c, t, kinds, ct)); grid.setdefault(cell(c), []).append(i)
def enrich(c, t, props):
    found = {}; best = None
    cx, cy = cell(c)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for i in grid.get((cx + dx, cy + dy), []):
                pc, pt, kinds, ct = places[i]; d = metres(c, pc)
                if d > 450 or (pt.get('@id') == t.get('@id') and pt.get('@type') == t.get('@type')): continue
                for k in kinds:
                    o = found.setdefault(k, [k, round(d), pt.get('name', ''), 0]); o[3] += 1
                    if d < o[1]: o[1] = round(d); o[2] = pt.get('name', '')
                if pt is not t and any(ct.values()) and related(t, pt) and (best is None or d < best[0]): best = (d, pt, ct)
    keys = [k for k, _ in FAC]
    fac = sorted(found.values(), key=lambda o: keys.index(o[0]))
    if fac: props['fac'] = json.dumps(fac, separators=(',', ':'), ensure_ascii=False)
    if best and not any(contact(t).values()):
        _, pt, ct = best
        for a, b in (('rtel', 'tel'), ('rweb', 'web'), ('rem', 'em'), ('rvhf', 'vhf')):
            if ct[b]: props[a] = ct[b]
        props['rfrom'] = pt.get('name', '')
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
    if not g or not is_chart(t):
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
        if props['sym'] in ('marina', 'harbour', 'fuel'): enrich(c, t, props)
        mz = 9 if props['sym'] in ('light_major', 'marina', 'harbour') else 11 if props['sym'] in ('light_minor', 'card_n', 'card_e', 'card_s', 'card_w', 'isolated', 'safewater', 'wreck') else 12
        feat = {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': c}, 'properties': props, 'tippecanoe': {'minzoom': mz}}
    out.write(json.dumps(feat, separators=(',', ':')) + '\n')
    n += 1
print('seamark features:', n)
