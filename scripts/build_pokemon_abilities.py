
"""Build Pokémon Ability datasets for Generations I–IX.

Outputs:
    data/abilities_master.csv
    data/abilities_generation_summary.csv

Source snapshots:
    data/raw/pokeapi_abilities_source.csv
    data/raw/pokeapi_ability_names_source.csv
"""

from collections import Counter
from pathlib import Path
from urllib.request import Request, urlopen
import csv
import time

# ----------------------------------------
# Paths and source URLs
# ----------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RAW = DATA / "raw"

RAW.mkdir(parents=True, exist_ok=True)

BASE = (
    "https://raw.githubusercontent.com/"
    "PokeAPI/pokeapi/master/data/v2/csv/"
)

SOURCES = {
    "abilities.csv": (
        RAW / "pokeapi_abilities_source.csv"
    ),
    "ability_names.csv": (
        RAW / "pokeapi_ability_names_source.csv"
    )
}

ROMAN = [
    "I", "II", "III", "IV", "V",
    "VI", "VII", "VIII", "IX"
]


# ----------------------------------------
# Download source data once
# ----------------------------------------

def download_if_missing(filename, destination):

    if destination.exists():
        print(
            f"Using cached source: "
            f"{destination.name}"
        )
        return

    url = BASE + filename

    for attempt in range(3):

        try:
            request = Request(
                url,
                headers={
                    "User-Agent":
                    "FIT3179-Pokemon-DV2-Education/1.0"
                }
            )

            with urlopen(
                request, timeout=30
            ) as response:

                contents = response.read()

            destination.write_bytes(contents)

            print(f"Downloaded: {filename}")
            return

        except Exception as error:

            if attempt == 2:
                raise RuntimeError(
                    f"Could not download {url}"
                ) from error

            time.sleep(2 ** (attempt + 1))


def read_csv(path):

    with path.open(
        encoding="utf-8-sig",
        newline=""
    ) as stream:

        return list(csv.DictReader(stream))


def write_csv(path, rows, columns):

    with path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as stream:

        writer = csv.DictWriter(
            stream,
            fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------
# Download and load source CSVs
# ----------------------------------------

for filename, destination in SOURCES.items():

    download_if_missing(
        filename, destination
    )

raw_abilities = read_csv(
    SOURCES["abilities.csv"]
)

raw_names = read_csv(
    SOURCES["ability_names.csv"]
)


# ----------------------------------------
# Get English Ability names
# ----------------------------------------

# PokéAPI language ID 9 = English.

english_names = {}

for row in raw_names:

    if row["local_language_id"] == "9":

        ability_id = int(row["ability_id"])

        if ability_id in english_names:
            raise ValueError(
                f"Duplicate name: {ability_id}"
            )

        english_names[ability_id] = row["name"]


# ----------------------------------------
# Select main-series Abilities
# ----------------------------------------

master = []
seen_ids = set()

ignored_spin_off = 0
ignored_other_generations = 0

for row in raw_abilities:

    ability_id = int(row["id"])

    generation = int(
        row["generation_id"]
    )

    if ability_id in seen_ids:
        raise ValueError(
            f"Duplicate Ability ID: {ability_id}"
        )

    seen_ids.add(ability_id)

    # Exclude abilities from spin-off games.

    if row["is_main_series"] != "1":

        ignored_spin_off += 1
        continue

    # Our story covers Generations I–IX.

    if not 1 <= generation <= 9:

        ignored_other_generations += 1
        continue

    ability_name = english_names.get(
        ability_id,
        row["identifier"]
        .replace("-", " ")
        .title()
    )

    master.append({
        "ability_id": ability_id,
        "ability_name": ability_name,
        "identifier": row["identifier"],
        "generation_number": generation,
        "generation": (
            f"Gen {ROMAN[generation - 1]}"
        )
    })


master.sort(
    key=lambda row: row["ability_id"]
)


# ----------------------------------------
# Count Abilities by introduction generation
# ----------------------------------------

counts = Counter(
    row["generation_number"]
    for row in master
)

assert counts[1] == 0
assert counts[2] == 0
assert counts[3] > 0

assert len(master) == len({
    row["ability_id"]
    for row in master
})


# ----------------------------------------
# Calculate cumulative Ability counts
# ----------------------------------------

summary = []
cumulative = 0

for generation in range(1, 10):

    introduced = counts[generation]

    cumulative += introduced

    summary.append({

        "generation_number": generation,

        "generation": (
            f"Gen {ROMAN[generation - 1]}"
        ),

        "abilities_introduced": introduced,

        "cumulative_abilities": cumulative,

        "share_of_total_pct": round(
            100 * introduced / len(master), 1
        )
    })

assert cumulative == len(master)


# ----------------------------------------
# Export final datasets
# ----------------------------------------

write_csv(
    DATA / "abilities_master.csv",
    master,
    [
        "ability_id",
        "ability_name",
        "identifier",
        "generation_number",
        "generation"
    ]
)

write_csv(
    DATA / "abilities_generation_summary.csv",
    summary,
    [
        "generation_number",
        "generation",
        "abilities_introduced",
        "cumulative_abilities",
        "share_of_total_pct"
    ]
)


# ----------------------------------------
# Display analysis
# ----------------------------------------

print(
    "\nPOKEMON ABILITIES — GENERATIONS I–IX"
)

print("=" * 52)

print(
    f"Raw source records: {len(raw_abilities)}"
)

print(
    f"Excluded non-main-series: "
    f"{ignored_spin_off}"
)

print(
    f"Excluded outside Gen I–IX: "
    f"{ignored_other_generations}"
)

print(
    f"Main-series Abilities included: "
    f"{len(master)}"
)

print(
    "\nGeneration  New abilities  Cumulative"
)

for row in summary:

    print(
        f"{row['generation']:>10}  "
        f"{row['abilities_introduced']:>13}  "
        f"{row['cumulative_abilities']:>10}"
    )


largest = max(
    summary,
    key=lambda row: row[
        "abilities_introduced"
    ]
)

print(
    f"\nLargest introduction: "
    f"{largest['generation']} "
    f"({largest['abilities_introduced']} Abilities)"
)

print("\nCreated:")
print("data/abilities_master.csv")
print("data/abilities_generation_summary.csv")

print(
    "\nSource files saved in data/raw/"
)

print(
    "Note: Generation IX includes abilities "
    "present in the downloaded source snapshot."
)
