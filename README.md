# OpenHelm Charts

Free offline nautical chart packs for the **OpenHelm** Android chart plotter.

Each pack is an MBTiles vector tile file (OpenMapTiles schema plus `seamark`, `depth_area`, `depth_contour` and `sounding` layers), published as a release tagged `charts-<id>`. The app lists these releases in **Offline → chart packs** and downloads them with one tap.

## Areas

**United Kingdom – coast:** Bristol Channel & South Wales · English Channel, Solent & Dover Strait · South West England & Scilly · Thames Estuary & East Anglia · North East England · East Scotland · North Scotland, Orkney & Shetland · West Scotland, Clyde & Hebrides · Irish Sea & Isle of Man · Northern Ireland · West Wales & Anglesey

**United Kingdom – sea areas:** Western Approaches & Celtic Sea · Malin, Hebrides & Bailey · North Sea · Fair Isle & Shetland

Packs cover the sea plus a narrow strip of land along the coast; inland areas are left out to keep downloads small. Europe will follow.

## Data

- Coastline, land, harbours, seamarks and marinas: © [OpenStreetMap](https://www.openstreetmap.org/copyright) contributors (ODbL), tiles via [OpenMapTiles](https://openmaptiles.org/) schema and [Planetiler](https://github.com/onthegomap/planetiler)
- Depths: [EMODnet Bathymetry](https://emodnet.ec.europa.eu/en/bathymetry) Digital Terrain Model, relative to Lowest Astronomical Tide (chart datum)

## Building

`Actions → Build UK chart packs → Run workflow` rebuilds every UK pack and publishes each as a release. `Build chart pack` builds a single custom area.

**Not for navigation.** These charts are not official and may be incomplete or out of date. Always carry official charts.
