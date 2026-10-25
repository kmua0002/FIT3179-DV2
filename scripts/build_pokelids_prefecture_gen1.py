
"""
Build the Chart 13 Japan prefecture Gen I Poké Lid choropleth data.

Inputs:
    data/pokelids_locations.csv
    data/pokelids_pokemon.csv
    data/geo/japan_prefectures.topojson

Output:
    data/pokelids_prefecture_gen1.csv

Each Poké Lid counts once if at least one featured
Pokémon species originally belongs to Generation I.

Prefectures without recorded lids have no percentage.
"""

from pathlib import Path
import json
import unicodedata
import pandas as pd


# --------------------------------------------------
# File paths
# --------------------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

LOCATIONS = DATA / "pokelids_locations.csv"
POKEMON = DATA / "pokelids_pokemon.csv"
BOUNDARIES = DATA / "geo" / "japan_prefectures.topojson"

OUTPUT = DATA / "pokelids_prefecture_gen1.csv"


# --------------------------------------------------
# Normalise prefecture names
# --------------------------------------------------

def normalise(text):
    """
    Remove accents so Hokkaidō matches Hokkaido.
    """

    text = unicodedata.normalize("NFKD", str(text))

    return "".join(
        c for c in text
        if not unicodedata.combining(c)
    ).strip().lower()


# --------------------------------------------------
# Load datasets
# --------------------------------------------------

locations = pd.read_csv(LOCATIONS)
pokemon = pd.read_csv(POKEMON)

with BOUNDARIES.open(encoding="utf-8") as f:
    topo = json.load(f)


# --------------------------------------------------
# Validate input data
# --------------------------------------------------

geometries = topo["objects"][
    "ne_10m_admin_1_states_provinces"
]["geometries"]

assert len(geometries) == 47, (
    "Expected exactly 47 Japan prefecture polygons"
)

assert locations["manhole_no"].is_unique, (
    "Duplicate Poké Lid IDs found"
)

assert locations["manhole_no"].notna().all(), (
    "Missing Poké Lid IDs"
)

assert pokemon["generation_number"].notna().all(), (
    "Some Pokémon have missing generation information"
)

assert set(pokemon["manhole_no"]) == set(locations["manhole_no"]), (
    "Pokémon and location IDs do not match"
)


# --------------------------------------------------
# Build prefecture lookup
# --------------------------------------------------

pref_lookup = {}

for geom in geometries:

    prop = geom["properties"]

    key = normalise(prop["name"])

    if key in pref_lookup:
        raise ValueError(
            f"Duplicate prefecture: {key}"
        )

    pref_lookup[key] = (
        prop["name"],
        prop["iso_3166_2"]
    )


# Check all prefecture names match

location_names = set(
    locations["prefecture"].map(normalise)
)

unmatched = location_names - set(pref_lookup)

if unmatched:
    raise ValueError(
        f"Unmatched prefectures: {sorted(unmatched)}"
    )


# --------------------------------------------------
# Identify Generation I Poké Lids
# --------------------------------------------------

gen1_lid_ids = set(
    pokemon.loc[
        pokemon["generation_number"] == 1,
        "manhole_no"
    ]
)


# --------------------------------------------------
# Calculate percentages per prefecture
# --------------------------------------------------

records = []

for norm_name, (map_name, iso_code) in sorted(
    pref_lookup.items()
):

    lids = set(
        locations.loc[
            locations["prefecture"]
            .map(normalise)
            .eq(norm_name),
            "manhole_no"
        ]
    )

    total = len(lids)

    gen1 = len(
        lids & gen1_lid_ids
    )

    if total > 0:
        share = round(100 * gen1 / total, 1)
    else:
        share = None

    records.append({

        "iso_3166_2": iso_code,

        "prefecture": map_name,

        "total_lids": total,

        "gen1_lids": gen1,

        "gen1_percent": share,

        "gen1_percent_label": (
            f"{share:.1f}%"
            if total > 0
            else "No records"
        ),

        "record_label": (
            f"{gen1} of {total} lids"
            if total > 0
            else "No recorded lids"
        )
    })


# --------------------------------------------------
# Create summary dataframe
# --------------------------------------------------

summary = pd.DataFrame(records)


# --------------------------------------------------
# Final validation
# --------------------------------------------------

assert len(summary) == 47

assert summary["iso_3166_2"].is_unique

assert int(summary["total_lids"].sum()) == 470

assert int(summary["gen1_lids"].sum()) == len(gen1_lid_ids)

assert summary["gen1_percent"].notna().sum() == 41


# --------------------------------------------------
# Save CSV
# --------------------------------------------------

summary.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# Print results
# --------------------------------------------------

print("Generation I prefecture dataset created successfully.")
print("-----------------------------------------------")

print(f"Total prefectures: {len(summary)}")

print(
    f"Prefectures with lids: "
    f"{(summary['total_lids'] > 0).sum()}"
)

print(
    f"Prefectures without lids: "
    f"{(summary['total_lids'] == 0).sum()}"
)

print(
    f"Generation I Poké Lids: "
    f"{len(gen1_lid_ids)} / {len(locations)}"
)

print(
    f"Overall percentage: "
    f"{100 * len(gen1_lid_ids) / len(locations):.1f}%"
)

print("\nSelected prefectures:")

print(
    summary[
        summary["prefecture"].isin(
            ["Hokkaidō", "Fukushima", "Mie", "Tokyo"]
        )
    ][
        [
            "prefecture",
            "gen1_lids",
            "total_lids",
            "gen1_percent"
        ]
    ].to_string(index=False)
)

print("\nSaved to:")
print(OUTPUT)
