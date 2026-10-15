# OpenHelm themes

OpenHelm lists every release in this repository tagged `theme-<id>` under **Setup → More themes**, with a one-tap download.
A release needs one asset, `theme.json`. The first line of the release description is shown under the theme name.

```json
{
  "name": "Teak & Brass",
  "sub": "Warm wood tones",
  "sw": ["#2b1a0e", "#c9a227", "#e8d5a8"],
  "layout": "standard",
  "vars": {
    "day":   { "--accent": "#8a5a2b", "--route": "#b5121b" },
    "dusk":  { "--bg": "#1e130a", "--glass": "rgba(43,26,14,.88)", "--glass-2": "rgba(60,38,20,.92)",
               "--accent": "#c9a227", "--accent-fg": "#1a1405", "--route": "#e8b04a" },
    "night": {}
  }
}
```

- `vars` sets colours per display mode. Keys: `--bg --glass --glass-2 --solid --line --fg --muted --dim --accent --accent-fg --cyan --good --warn --bad --route --track --ais --mark`.
- Only plain colours are accepted (`#rgb`, `#rrggbb`, `#rrggbbaa`, `rgb()`, `rgba()`); anything else is ignored.
- Leave `night` empty to keep the red night-vision colours.
- `layout` (optional): `standard`, `left` or `big`.
- `sw`: up to three swatch colours for the theme card.

Planned (shown in the app as "Available soon"): `teak`, `racing`, `midnight`, `paper`. Publishing a release with one of these ids makes it downloadable.
