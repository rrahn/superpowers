---
name: overpass-api
description: Use when querying OpenStreetMap data via Overpass API — fetching streets, house numbers, addresses, POIs (hospitals, doctors, pharmacies, physiotherapy), or scoping queries to a specific city or region to reduce response size and latency
---

# Overpass API

Query OpenStreetMap data programmatically using Overpass QL. Returns nodes, ways, and relations matching search criteria like location, tags, and proximity.

## API Endpoint

```
POST https://overpass-api.de/api/interpreter
Content-Type: application/x-www-form-urlencoded

data=[out:json][timeout:25];
<your query here>
```

**Alternative instances** (no rate limit):
- `https://maps.mail.ru/osm/tools/overpass/api/interpreter`
- `https://overpass.private.coffee/api/interpreter`

**Rate limits (main instance):** <10,000 queries/day, <1 GB/day.

## Query Structure

Every Overpass QL query follows this pattern:

```
[out:json][timeout:25];       // Settings: output format, timeout
area[name="Berlin"]->.a;      // Step 1: Define search area
nwr(area.a)[amenity=hospital]; // Step 2: Query elements in area
out center;                    // Step 3: Output results
```

**Key concepts:**
- Statements end with `;`
- Sets: results flow through default set `_`, use `->.name` to store in named sets
- Types: `node`, `way`, `rel`, `nwr` (all three), `area`
- Filters chain with `[]` for tags, `()` for spatial

## Scoping Queries to a Region

**Always scope queries to an area or bounding box** to avoid timeouts and reduce data.

### By city/region name (area filter)

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
// ... query using (area.city) ...
```

`admin_level` values (Germany):
| Level | Meaning | Example |
|-------|---------|---------|
| 2 | Country | Deutschland |
| 4 | Bundesland | Bayern |
| 6 | Stadt/Landkreis | München |
| 8 | Gemeinde | Garching |

### By bounding box

```overpassql
[out:json][timeout:25];
// (south, west, north, east) in decimal degrees
node[amenity=hospital](48.0,11.3,48.3,11.8);
out center;
```

### Nested areas (area-in-area)

```overpassql
[out:json][timeout:25];
area[name="Bayern"]->.state;
rel(area.state)[name="München"];
map_to_area ->.city;
nwr(area.city)[amenity=doctors];
out center;
```

## Common Query Patterns

### Streets in a city

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
way(area.city)[highway][name];
out tags;
```

Output: all named streets. Use `out tags` for name-only (no geometry).

### House numbers in a street or area

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)["addr:street"="Leopoldstraße"]["addr:housenumber"];
out center;
```

### All addresses in a small area

```overpassql
[out:json][timeout:25];
area[name="Schwabing-West"]->.district;
nwr(area.district)["addr:housenumber"];
out center;
```

### POIs — hospitals, doctors, physiotherapy

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=hospital];
  nwr(area.city)[amenity=doctors];
  nwr(area.city)[amenity=clinic];
  nwr(area.city)[amenity=pharmacy];
  nwr(area.city)[healthcare=physiotherapist];
  nwr(area.city)[healthcare=doctor];
);
out center;
```

### Names for autocomplete (CSV output)

```overpassql
[out:csv("name";true;";")][timeout:25];
area[name="München"][admin_level=6]->.city;
way(area.city)[highway][name];
out;
```

Returns deduplicated street names as CSV — ideal for autocomplete lists.

### POI names for a region

```overpassql
[out:csv("name","amenity","healthcare";true;";")][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=hospital][name];
  nwr(area.city)[amenity=doctors][name];
  nwr(area.city)[healthcare=physiotherapist][name];
);
out;
```

### Nearby search (around)

```overpassql
[out:json][timeout:25];
// Find hospitals within 2km of a coordinate
nwr(around:2000,48.1351,11.5820)[amenity=hospital];
out center;
```

## Output Modes

| Mode | Use case |
|------|----------|
| `out;` or `out body;` | Full tags + structure (default) |
| `out center;` | Tags + center coordinate (best for POIs) |
| `out geom;` | Full geometry (ways with all node coords) |
| `out tags;` | Tags only, no coordinates |
| `out ids;` | IDs only |
| `out center qt;` | Center + sorted by quadtile (fastest) |

**Output format settings:**
- `[out:json]` — JSON (recommended for programmatic use)
- `[out:csv("name","amenity";true;";")]` — CSV with header
- `[out:xml]` — XML (default)

## Tag Filters

```overpassql
node["name"];                    // Has key "name"
node[!"name"];                   // Does NOT have key "name"
node["name"="Foo"];              // Exact match
node["name"!="Foo"];             // Not equal
node["name"~"^Haupt"];           // Regex: starts with "Haupt"
node["name"~"straße$",i];       // Regex case-insensitive: ends with "straße"
node[~"^addr:.*$"~"."];          // Any addr:* tag with any value
```

## Integration in n8n / Node.js

```javascript
// HTTP Request node or fetch()
const query = `
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)[amenity=hospital][name];
out center;
`;

const response = await fetch('https://overpass-api.de/api/interpreter', {
  method: 'POST',
  body: 'data=' + encodeURIComponent(query),
});
const data = await response.json();

// data.elements[] contains results with .tags.name, .lat, .lon, etc.
```

## Performance Guidelines

1. **Always scope with area or bbox** — never query globally
2. **Use `out center qt`** for POI lists — fastest sort, minimal data
3. **Use CSV output** for name lists — smallest response size
4. **Add `[timeout:25]`** — don't rely on server defaults
5. **Use `nwr` instead of separate `node` + `way` + `rel`** — one statement vs three
6. **Filter with `[name]`** to skip unnamed elements
7. **Limit with `out N`** — e.g., `out center 100` for first 100 results

## Detailed References

- **Query cookbook**: See [references/query-cookbook.md](references/query-cookbook.md) for complete ready-to-use queries for streets, addresses, POIs, and region lookups
- **OSM tag reference**: See [references/osm-tags.md](references/osm-tags.md) for comprehensive tag mappings for medical facilities, transport, and address data

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| No area/bbox → timeout | Always scope queries to a region |
| `area[name="Berlin"]` matches multiple | Add `[admin_level=6]` or `[boundary=administrative]` |
| Missing way geometry | Use `out geom;` or add `>;` after way query to recurse down to nodes |
| Querying `area(area)` | Not supported — use `nwr(area.x)` instead |
| German umlauts broken | Ensure UTF-8 encoding: `"Straße"` not `"Strasse"` |
| Huge response for street geometries | Use `out tags` if you only need names |
