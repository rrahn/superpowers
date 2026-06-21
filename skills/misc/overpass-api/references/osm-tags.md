# OSM Tag Reference — Addresses, Medical, Transport

Comprehensive tag mappings for querying addresses, medical facilities, and transport-related POIs via Overpass API.

## Table of Contents

1. [Address Tags](#address-tags)
2. [Street / Highway Tags](#street--highway-tags)
3. [Medical & Health Tags](#medical--health-tags)
4. [Transport Tags](#transport-tags)
5. [Emergency Tags](#emergency-tags)
6. [German-Specific Tags](#german-specific-tags)

---

## Address Tags

| Tag | Description | Example Value |
|-----|------------|---------------|
| `addr:street` | Street name | `Leopoldstraße` |
| `addr:housenumber` | House number | `42`, `12a`, `1-3` |
| `addr:postcode` | Postal code | `80539` |
| `addr:city` | City name | `München` |
| `addr:suburb` | District/suburb | `Schwabing` |
| `addr:country` | Country code | `DE` |
| `addr:full` | Full address string | `Leopoldstraße 42, 80539 München` |
| `addr:place` | Place name (instead of street) | `Am Dorfplatz` |
| `addr:unit` | Apartment/unit number | `3. OG` |
| `addr:floor` | Floor number | `2` |
| `addr:door` | Door identifier | `links` |

### Query pattern: all addr:* tags

```overpassql
nwr[~"^addr:.*$"~"."](area.city);
```

---

## Street / Highway Tags

### Highway types (most relevant for street queries)

| Tag Value | Description | German Equivalent |
|-----------|------------|-------------------|
| `highway=motorway` | Autobahn | Autobahn |
| `highway=trunk` | Important national road | Bundesstraße |
| `highway=primary` | Major road | Landesstraße |
| `highway=secondary` | Secondary road | Kreisstraße |
| `highway=tertiary` | Local connector | Gemeindestraße |
| `highway=residential` | Residential street | Wohnstraße |
| `highway=living_street` | Traffic-calmed | Verkehrsberuhigter Bereich |
| `highway=pedestrian` | Pedestrian zone | Fußgängerzone |
| `highway=unclassified` | Minor public road | Sonstige Straße |
| `highway=service` | Access/service road | Zufahrt |

### Useful street regex filter

```overpassql
// Named streets excluding service roads and paths
way(area.city)[highway~"^(primary|secondary|tertiary|residential|living_street|pedestrian|unclassified)$"][name];
```

---

## Medical & Health Tags

### Primary medical facility tags

| Tag | Description | Notes |
|-----|------------|-------|
| `amenity=hospital` | Hospital | Often a way/relation, not node |
| `amenity=doctors` | Doctor's office | Most common for GP practices |
| `amenity=clinic` | Clinic | General medical clinic |
| `amenity=pharmacy` | Pharmacy / Apotheke | |
| `amenity=dentist` | Dentist | Zahnarzt |
| `amenity=veterinary` | Veterinary | Tierarzt |

### Healthcare tags (more specific)

| Tag | Description | Notes |
|-----|------------|-------|
| `healthcare=doctor` | Doctor (alternate tag) | Use alongside `amenity=doctors` |
| `healthcare=hospital` | Hospital (alternate) | Rarely used, prefer `amenity=hospital` |
| `healthcare=clinic` | Clinic (alternate) | |
| `healthcare=physiotherapist` | Physiotherapy practice | **Primary tag for Physio** |
| `healthcare=occupational_therapist` | Occupational therapy | Ergotherapie |
| `healthcare=psychotherapist` | Psychotherapist | Psychotherapeut |
| `healthcare=speech_therapist` | Speech therapy | Logopädie |
| `healthcare=midwife` | Midwife practice | Hebamme |
| `healthcare=optometrist` | Optometrist | Augenoptiker |
| `healthcare=podiatrist` | Podiatrist | Podologe |
| `healthcare=laboratory` | Medical laboratory | Labor |
| `healthcare=rehabilitation` | Rehab center | Rehaklinik |
| `healthcare=blood_donation` | Blood donation center | Blutspende |
| `healthcare=birthing_center` | Birthing center | Geburtshaus |

### Healthcare speciality (sub-tag)

Use `healthcare:speciality=*` for specific medical specialities:

| Value | Description |
|-------|------------|
| `healthcare:speciality=general` | Allgemeinmedizin |
| `healthcare:speciality=internal` | Innere Medizin |
| `healthcare:speciality=surgery` | Chirurgie |
| `healthcare:speciality=orthopaedics` | Orthopädie |
| `healthcare:speciality=gynaecology` | Gynäkologie |
| `healthcare:speciality=paediatrics` | Kinderheilkunde |
| `healthcare:speciality=cardiology` | Kardiologie |
| `healthcare:speciality=dermatology` | Dermatologie |
| `healthcare:speciality=neurology` | Neurologie |
| `healthcare:speciality=ophthalmology` | Augenheilkunde |
| `healthcare:speciality=radiology` | Radiologie |
| `healthcare:speciality=urology` | Urologie |
| `healthcare:speciality=psychiatry` | Psychiatrie |
| `healthcare:speciality=physiotherapy` | Physiotherapie (on clinics) |

### Query: all healthcare facilities

```overpassql
(
  nwr(area.city)[amenity~"^(hospital|doctors|clinic|pharmacy|dentist)$"][name];
  nwr(area.city)[healthcare][name];
);
```

---

## Transport Tags

### Taxi & ride services

| Tag | Description |
|-----|------------|
| `amenity=taxi` | Taxi stand / Taxistand |
| `office=taxi` | Taxi office |

### Public transport

| Tag | Description |
|-----|------------|
| `highway=bus_stop` | Bus stop |
| `railway=tram_stop` | Tram stop |
| `railway=station` | Train station |
| `railway=halt` | Small train stop |
| `railway=subway_entrance` | U-Bahn entrance |
| `public_transport=stop_position` | Generic stop position |
| `public_transport=platform` | Platform |
| `public_transport=station` | Station |

### Parking

| Tag | Description |
|-----|------------|
| `amenity=parking` | Parking lot/garage |
| `amenity=parking_entrance` | Parking entrance |
| `amenity=parking_space` | Individual parking space |
| `amenity=bicycle_parking` | Bicycle parking |

### Wheelchair accessibility

| Tag | Value | Meaning |
|-----|-------|---------|
| `wheelchair` | `yes` | Fully accessible |
| `wheelchair` | `limited` | Partially accessible |
| `wheelchair` | `no` | Not accessible |

**Relevant for Krankentransport:** Filter accessible facilities:

```overpassql
nwr(area.city)[amenity=hospital][wheelchair~"^(yes|limited)$"];
```

---

## Emergency Tags

| Tag | Description |
|-----|------------|
| `emergency=yes` | Facility has emergency department |
| `emergency=ambulance_station` | Ambulance station |
| `emergency=defibrillator` | AED location |
| `amenity=fire_station` | Fire station |
| `amenity=police` | Police station |

### Query: hospitals with emergency department

```overpassql
nwr(area.city)[amenity=hospital][emergency=yes][name];
out center;
```

---

## German-Specific Tags

### Administrative boundaries

| `admin_level` | German Entity |
|--------------|---------------|
| 2 | Bundesrepublik Deutschland |
| 4 | Bundesland (Bayern, NRW, etc.) |
| 5 | Regierungsbezirk |
| 6 | Landkreis / kreisfreie Stadt |
| 7 | Amt / Samtgemeinde / Verwaltungsgemeinschaft |
| 8 | Gemeinde / Stadt |
| 9 | Stadtbezirk |
| 10 | Stadtteil / Ortsteil |
| 11 | Stadtviertel |

### Query: all Gemeinden in a Landkreis

```overpassql
[out:csv("name","admin_level";true;";")][timeout:30];
area[name="Landkreis München"][admin_level=6]->.lk;
rel(area.lk)[boundary=administrative][admin_level=8][name];
out;
```

### Place tags (settlements)

| Tag | Description |
|-----|------------|
| `place=city` | Stadt (>100k) |
| `place=town` | Kleinstadt (10k-100k) |
| `place=village` | Dorf (200-10k) |
| `place=hamlet` | Weiler (<200) |
| `place=suburb` | Stadtteil |
| `place=neighbourhood` | Wohnviertel |
| `place=quarter` | Quartier |

### Query: all place names in a Landkreis

```overpassql
[out:csv("name","place";true;";")][timeout:30];
area[name="Landkreis München"][admin_level=6]->.lk;
node(area.lk)[place~"^(city|town|village|hamlet|suburb)$"][name];
out;
```

### Opening hours

Many medical facilities have `opening_hours` tagged:

```overpassql
nwr(area.city)[amenity=doctors][name][opening_hours];
out center;
```

Value format: `Mo-Fr 08:00-18:00; Sa 09:00-12:00`
