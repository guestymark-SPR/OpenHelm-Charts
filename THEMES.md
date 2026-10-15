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
- `boxes` (optional): colours of the boxes around the chart per mode (`day`, `dusk`): `top`, `side`, `bottom`, `panel`.
- `chart` (optional): `almanac` or `std` chart style to switch to when the theme is chosen.

To publish: add `themes/<id>.json` and push; the *Publish themes* workflow creates or updates the `theme-<id>` release.

Published: `plotter-black`, `race-red`, `chart-blue`, `sail-teal`. Planned (shown in the app as "Available soon"): `teak`, `racing`, `midnight`, `paper`. Publishing a release with one of these ids makes it downloadable.

## Extra fields (app build 51 and later)

| Field | What it does |
|---|---|
| `style` | Switches on a whole look built into the app. Only `"futuristic"` exists so far: chamfered neon panels, scanlines, glowing figures, the side menu centred, and the navigation card moved to the top. |
| `sound` | The button sound the theme uses: `tick`, `click`, `tap`, `pop`, `beep`, `ping`, `chime`, `blip` or `none`. The skipper's own choice comes back when they change theme. |
| `fonts` | Free fonts from Fontsource as `"family:weight"`, for `display` (labels and headings) and `ui` (text and figures), e.g. `"orbitron:700"`. The publishing workflow downloads them and puts them inside `theme.json`, so they work offline. |

Installed themes can be uninstalled in Settings → Themes (the Uninstall button in the download list, or ✕ on the theme card).
