from pathlib import Path
import pandas as pd

# ---------------------------------------------------
# File locations
# ---------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUTPUT = ROOT / "data" / "pokemon_master.csv"


# ---------------------------------------------------
# Load PokéAPI tables
# ---------------------------------------------------

species = pd.read_csv(RAW / "pokemon_species.csv")
pokemon = pd.read_csv(RAW / "pokemon.csv")
pokemon_types = pd.read_csv(RAW / "pokemon_types.csv")
types = pd.read_csv(RAW / "types.csv")
pokemon_stats = pd.read_csv(RAW / "pokemon_stats.csv")
stats = pd.read_csv(RAW / "stats.csv")


# ---------------------------------------------------
# 1. Keep one default Pokémon per species
# ---------------------------------------------------

pokemon = pokemon[pokemon["is_default"] == 1].copy()

pokemon = pokemon.rename(
    columns={
        "id": "pokemon_id",
        "identifier": "pokemon_identifier"
    }
)

species = species.rename(
    columns={
        "id": "species_id",
        "identifier": "name"
    }
)


# ---------------------------------------------------
# 2. Combine Pokémon with species information
# ---------------------------------------------------

master = pokemon.merge(
    species[
        [
            "species_id",
            "name",
            "generation_id",
            "is_legendary",
            "is_mythical"
        ]
    ],
    on="species_id",
    how="inner"
)


# ---------------------------------------------------
# 3. Add Pokémon type names
# ---------------------------------------------------

type_map = types.set_index("id")["identifier"]

pokemon_types["type_name"] = pokemon_types["type_id"].map(type_map)

type_pivot = (
    pokemon_types
    .pivot_table(
        index="pokemon_id",
        columns="slot",
        values="type_name",
        aggfunc="first"
    )
    .rename(
        columns={
            1: "type1",
            2: "type2"
        }
    )
    .reset_index()
)

master = master.merge(
    type_pivot,
    on="pokemon_id",
    how="left"
)


# ---------------------------------------------------
# 4. Add base stats
# ---------------------------------------------------

stat_map = stats.set_index("id")["identifier"]

pokemon_stats["stat_name"] = pokemon_stats["stat_id"].map(stat_map)

wanted_stats = [
    "hp",
    "attack",
    "defense",
    "special-attack",
    "special-defense",
    "speed"
]

pokemon_stats = pokemon_stats[
    pokemon_stats["stat_name"].isin(wanted_stats)
]

stat_pivot = (
    pokemon_stats
    .pivot_table(
        index="pokemon_id",
        columns="stat_name",
        values="base_stat",
        aggfunc="first"
    )
    .reset_index()
)

stat_pivot = stat_pivot.rename(
    columns={
        "special-attack": "sp_attack",
        "special-defense": "sp_defense"
    }
)

master = master.merge(
    stat_pivot,
    on="pokemon_id",
    how="left"
)


# ---------------------------------------------------
# 5. Clean / derive useful fields
# ---------------------------------------------------

generation_names = {
    1: "Generation I",
    2: "Generation II",
    3: "Generation III",
    4: "Generation IV",
    5: "Generation V",
    6: "Generation VI",
    7: "Generation VII",
    8: "Generation VIII",
    9: "Generation IX"
}

master["generation_number"] = master["generation_id"]

master["generation"] = master["generation_id"].map(
    generation_names
)

# Number of types
master["type_count"] = master["type2"].notna().astype(int) + 1

# PokéAPI uses decimetres for height and hectograms for weight
master["height_m"] = master["height"] / 10
master["weight_kg"] = master["weight"] / 10

# Total of the six base stats
stat_columns = [
    "hp",
    "attack",
    "defense",
    "sp_attack",
    "sp_defense",
    "speed"
]

master["total_stats"] = master[stat_columns].sum(axis=1)

# A readable version for tooltips
master["display_name"] = (
    master["name"]
    .str.replace("-", " ", regex=False)
    .str.title()
)


# ---------------------------------------------------
# 6. Final columns
# ---------------------------------------------------

master = master[
    [
        "species_id",
        "name",
        "display_name",
        "generation_number",
        "generation",
        "type1",
        "type2",
        "type_count",
        "hp",
        "attack",
        "defense",
        "sp_attack",
        "sp_defense",
        "speed",
        "total_stats",
        "height_m",
        "weight_kg",
        "is_legendary",
        "is_mythical"
    ]
]

master = master.rename(
    columns={
        "species_id": "id"
    }
)

master = master.sort_values("id")


# ---------------------------------------------------
# 7. Save clean master dataset
# ---------------------------------------------------

master.to_csv(
    OUTPUT,
    index=False
)


# ---------------------------------------------------
# Validation output
# ---------------------------------------------------

print("\nPokemon master dataset created successfully.")
print("--------------------------------------------")
print(f"Total Pokemon: {len(master)}")

print("\nPokemon by generation:")
print(
    master.groupby(
        ["generation_number", "generation"]
    )
    .size()
    .to_string()
)

print("\nMissing values:")
print(master.isna().sum())

print(f"\nSaved to: {OUTPUT}")