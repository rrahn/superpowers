# Overpass API — Query Cookbook

Ready-to-use Overpass QL queries organized by use case. Copy, adapt the area name, and run.

## Table of Contents

1. [Street Queries](#street-queries)
2. [Address Queries](#address-queries)
3. [Medical & Health POIs](#medical--health-pois)
4. [Transport POIs](#transport-pois)
5. [General POIs](#general-pois)
6. [Name Extraction for Autocomplete](#name-extraction-for-autocomplete)
7. [Proximity / Around Queries](#proximity--around-queries)
8. [Counting Elements](#counting-elements)
9. [Multi-Area Queries](#multi-area-queries)

---

## Street Queries

### All named streets in a city

```overpassql
[out:json][timeout:30];
area[name="München"][admin_level=6]->.city;
way(area.city)[highway][name];
out tags;
```

### Streets matching a prefix (autocomplete)

```overpassql
[out:csv("name";true;";")][timeout:25];
area[name="München"][admin_level=6]->.city;
way(area.city)[highway]["name"~"^Leopold",i];
out;
```

### Streets by type (only major roads)

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
way(area.city)[highway~"^(primary|secondary|tertiary|residential)$"][name];
out tags;
```

### Street with full geometry (for mapping)

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
way(area.city)[name="Leopoldstraße"][highway];
out geom;
```

---

## Address Queries

### All house numbers on a specific street

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)["addr:street"="Leopoldstraße"]["addr:housenumber"];
out center;
```

### House numbers as CSV (for autocomplete)

```overpassql
[out:csv("addr:housenumber","addr:street","addr:postcode";true;";")][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)["addr:street"="Leopoldstraße"]["addr:housenumber"];
out;
```

### All addresses in a postal code area

```overpassql
[out:json][timeout:30];
area[name="München"][admin_level=6]->.city;
nwr(area.city)["addr:postcode"="80539"]["addr:housenumber"];
out center;
```

### Full address lookup (street + number)

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)["addr:street"="Leopoldstraße"]["addr:housenumber"="42"];
out center;
```

### All addresses in a district/neighborhood

```overpassql
[out:json][timeout:30];
area[name="Schwabing-West"]->.district;
nwr(area.district)["addr:housenumber"];
out center;
```

---

## Medical & Health POIs

### Hospitals

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=hospital][name];
  nwr(area.city)[building=hospital][name];
);
out center;
```

### Doctors / general practitioners

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=doctors][name];
  nwr(area.city)[healthcare=doctor][name];
);
out center;
```

### Physiotherapy practices

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[healthcare=physiotherapist][name];
  nwr(area.city)[healthcare~"physiotherapy"][name];
  nwr(area.city)[amenity=clinic]["healthcare:speciality"~"physiotherapy"][name];
);
out center;
```

### Pharmacies

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)[amenity=pharmacy][name];
out center;
```

### All medical facilities combined

```overpassql
[out:json][timeout:30];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=hospital][name];
  nwr(area.city)[amenity=doctors][name];
  nwr(area.city)[amenity=clinic][name];
  nwr(area.city)[amenity=pharmacy][name];
  nwr(area.city)[healthcare=doctor][name];
  nwr(area.city)[healthcare=physiotherapist][name];
  nwr(area.city)[healthcare=occupational_therapist][name];
  nwr(area.city)[healthcare=psychotherapist][name];
  nwr(area.city)[healthcare=speech_therapist][name];
);
out center;
```

### Emergency rooms / urgent care

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=hospital][emergency=yes];
  nwr(area.city)[emergency=ambulance_station];
);
out center;
```

---

## Transport POIs

### Taxi stands

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)[amenity=taxi];
out center;
```

### Public transport stops

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  node(area.city)[highway=bus_stop];
  node(area.city)[railway=tram_stop];
  node(area.city)[railway=halt];
  node(area.city)[railway=station];
  node(area.city)[railway=subway_entrance];
);
out center;
```

### Parking facilities

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=parking];
  nwr(area.city)[amenity=parking_entrance];
);
out center;
```

---

## General POIs

### Hotels and accommodation

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[tourism=hotel][name];
  nwr(area.city)[tourism=guest_house][name];
  nwr(area.city)[tourism=hostel][name];
);
out center;
```

### Restaurants and cafés

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=restaurant][name];
  nwr(area.city)[amenity=cafe][name];
);
out center;
```

---

## Name Extraction for Autocomplete

### Unique street names (for type-ahead)

```overpassql
[out:csv("name";true;";")][timeout:30];
area[name="München"][admin_level=6]->.city;
way(area.city)[highway~"^(primary|secondary|tertiary|residential|living_street|pedestrian|unclassified)$"][name];
out;
```

Post-process: deduplicate names client-side (Overpass doesn't deduplicate CSV).

### Hospital names

```overpassql
[out:csv("name";true;";")][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)[amenity=hospital][name];
out;
```

### Doctor names

```overpassql
[out:csv("name","addr:street","addr:housenumber","opening_hours";true;";")][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  nwr(area.city)[amenity=doctors][name];
  nwr(area.city)[healthcare=doctor][name];
);
out;
```

### City/district names in a Bundesland

```overpassql
[out:csv("name","admin_level";true;";")][timeout:30];
area[name="Bayern"][admin_level=4]->.state;
rel(area.state)[boundary=administrative][admin_level~"^(6|8)$"][name];
out;
```

### Suburb/neighborhood names in a city

```overpassql
[out:csv("name";true;";")][timeout:25];
area[name="München"][admin_level=6]->.city;
(
  rel(area.city)[boundary=administrative][admin_level~"^(9|10|11)$"][name];
  rel(area.city)[place~"^(suburb|neighbourhood|quarter)$"][name];
);
out;
```

---

## Proximity / Around Queries

### Nearest hospital to coordinates

```overpassql
[out:json][timeout:25];
nwr(around:5000,48.1351,11.5820)[amenity=hospital][name];
out center;
```

Sort results client-side by distance (Overpass returns by quadtile, not distance).

### Doctors near an address

First geocode the address, then:

```overpassql
[out:json][timeout:25];
(
  nwr(around:1000,48.1547,11.5822)[amenity=doctors][name];
  nwr(around:1000,48.1547,11.5822)[healthcare=doctor][name];
);
out center;
```

### Pharmacies along a route (linestring)

```overpassql
[out:json][timeout:25];
nwr(around:500,48.135,11.582,48.140,11.590,48.150,11.600)[amenity=pharmacy];
out center;
```

---

## Counting Elements

### Count hospitals per district

```overpassql
[out:csv(::type,::id,name,admin_level,::count)][timeout:60];
area[name="München"][admin_level=6]->.city;
rel(area.city)[boundary=administrative][admin_level=9];
map_to_area;
foreach->.d(
  (.d;);out;
  (nwr(area.d)[amenity=hospital];);
  out count;
);
```

### Count addresses on a street

```overpassql
[out:json][timeout:25];
area[name="München"][admin_level=6]->.city;
nwr(area.city)["addr:street"="Leopoldstraße"]["addr:housenumber"];
out count;
```

---

## Multi-Area Queries

### POIs in multiple cities

```overpassql
[out:json][timeout:30];
(
  area[name="München"][admin_level=6];
  area[name="Nürnberg"][admin_level=6];
  area[name="Augsburg"][admin_level=6];
)->.cities;
nwr(area.cities)[amenity=hospital][name];
out center;
```

### All cities in a Bundesland with hospitals

```overpassql
[out:json][timeout:60];
area[name="Bayern"][admin_level=4]->.state;
rel(area.state)[boundary=administrative][admin_level=6];
map_to_area ->.districts;
nwr(area.districts)[amenity=hospital][name];
out center;
```
