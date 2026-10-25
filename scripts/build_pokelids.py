import json
import pandas as pd
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

RAW_FILE = ROOT / "data" / "raw" / "pokelids_raw.json"
MASTER_FILE = ROOT / "data" / "pokemon_master.csv"

LOCATION_OUT = ROOT / "data" / "pokelids_locations.csv"
POKEMON_OUT = ROOT / "data" / "pokelids_pokemon.csv"


def clean_species_slug(url):
    """
    Convert the Pokemon URL ending into a name that can be matched
    against pokemon_master.csv.

    Examples:
    farfetch'd -> farfetchd
    flabébé    -> flabebe
    """
    if not url:
        return None

    slug = url.rstrip("/").split("/")[-1].lower()

    slug = slug.replace("’", "'").replace("‘", "'")

    slug = "".join(
        c for c in unicodedata.normalize("NFKD", slug)
        if not unicodedata.combining(c)
    )

    slug = slug.replace("'", "")

    slug = re.sub(r"[^a-z0-9-]+", "-", slug).strip("-")

    return slug


# --------------------------------------------------
# Load files
# --------------------------------------------------

with open(RAW_FILE, "r", encoding="utf-8") as f:
    raw = json.load(f)

master = pd.read_csv(MASTER_FILE)


# --------------------------------------------------
# 1. One row per Poké Lid
# --------------------------------------------------

location_rows = []

for lid in raw:

    pokemon_names = [
        p["name"]
        for p in lid.get("pokemon_list", [])
    ]

    location_rows.append({
        "manhole_no": lid["manhole_no"],
        "location": lid["name"],
        "prefecture": lid["pref_name"],
        "latitude": lid["lat"],
        "longitude": lid["lng"],
        "pokemon_count": len(pokemon_names),
        "pokemon_names": ", ".join(pokemon_names)
    })


locations = pd.DataFrame(location_rows)

locations.to_csv(
    LOCATION_OUT,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# 2. One row per Pokémon appearance
# --------------------------------------------------

pokemon_rows = []

for lid in raw:

    for pokemon in lid.get("pokemon_list", []):

        pokemon_rows.append({
            "manhole_no": lid["manhole_no"],
            "location": lid["name"],
            "prefecture": lid["pref_name"],
            "latitude": lid["lat"],
            "longitude": lid["lng"],
            "pokemon_display_name": pokemon["name"],
            "pokemon_species": clean_species_slug(
                pokemon.get("zukan_url")
            )
        })


pokemon = pd.DataFrame(pokemon_rows)


# --------------------------------------------------
# Join with existing Pokémon master data
# --------------------------------------------------

master_keep = master[
    [
        "name",
        "generation_number",
        "generation",
        "type1",
        "type2"
    ]
].copy()

master_keep = master_keep.rename(
    columns={"name": "pokemon_species"}
)


pokemon = pokemon.merge(
    master_keep,
    on="pokemon_species",
    how="left"
)


pokemon.to_csv(
    POKEMON_OUT,
    index=False,
    encoding="utf-8-sig"
)


# --------------------------------------------------
# Validation
# --------------------------------------------------

print("Poké Lid dataset created successfully.")
print("--------------------------------------")
print(f"Total Poké Lids: {len(locations)}")
print(f"Pokémon appearances: {len(pokemon)}")
print(f"Prefectures represented: {locations['prefecture'].nunique()}")

print("\nPoké Lids by prefecture:")
print(
    locations["prefecture"]
    .value_counts()
    .head(15)
)

print("\nMissing generation matches:")
missing = pokemon[
    pokemon["generation_number"].isna()
]

print(
    missing[
        ["pokemon_display_name", "pokemon_species"]
    ]
    .drop_duplicates()
    .to_string(index=False)
)

print("\nSaved:")
print(LOCATION_OUT)
print(POKEMON_OUT)