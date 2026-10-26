
from pathlib import Path
import csv
import json
import re
import time
from urllib.request import Request, urlopen

# ----------------------------------------
# Paths
# ----------------------------------------

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = ROOT / ".cache" / "pokeapi_evolution_chains"

CACHE.mkdir(parents=True, exist_ok=True)

BASE = "https://pokeapi.co/api/v2/evolution-chain/"


# ----------------------------------------
# Download and cache PokéAPI data
# ----------------------------------------

def fetch(url, cache_file):
    if cache_file.exists():
        return json.loads(
            cache_file.read_text(encoding="utf-8")
        )

    for attempt in range(5):
        try:
            request = Request(
                url,
                headers={
                    "User-Agent": "FIT3179-education-data-project/1.0"
                }
            )

            with urlopen(request, timeout=25) as response:
                result = json.load(response)

            cache_file.write_text(
                json.dumps(result, ensure_ascii=False),
                encoding="utf-8"
            )

            time.sleep(0.12)
            return result

        except Exception as error:
            if attempt == 4:
                raise RuntimeError(
                    f"Could not retrieve {url}"
                ) from error

            time.sleep(2 ** attempt)


def species_id(url):
    match = re.search(
        r"/pokemon-species/(\d+)/?",
        url
    )

    if not match:
        raise ValueError(
            f"Unrecognised species URL: {url}"
        )

    return int(match.group(1))


def write_csv(path, rows, fields):
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fields
        )

        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------
# Load existing master dataset
# ----------------------------------------

with (
    DATA / "pokemon_master.csv"
).open(encoding="utf-8-sig", newline="") as file:

    species = {
        int(row["id"]): row
        for row in csv.DictReader(file)
    }

assert len(species) == 1025, (
    "Expected 1,025 species in pokemon_master.csv"
)


# ----------------------------------------
# Retrieve evolution-chain catalogue
# ----------------------------------------

index = fetch(
    BASE + "?limit=2000",
    CACHE / "chain_index.json"
)

if index["next"] is not None:
    raise RuntimeError(
        "Evolution-chain index was not fully retrieved"
    )

chain_urls = [
    entry["url"]
    for entry in index["results"]
]


# ----------------------------------------
# Extract evolution relationships
# ----------------------------------------

edges = []
families = []

for position, url in enumerate(chain_urls, start=1):

    chain_id = int(
        url.rstrip("/").rsplit("/", 1)[1]
    )

    payload = fetch(
        url,
        CACHE / f"chain_{chain_id}.json"
    )

    family_nodes = set()
    family_edges = []

    def visit(node, parent_id=None):

        node_id = species_id(
            node["species"]["url"]
        )

        if node_id in species:
            family_nodes.add(node_id)

        if parent_id in species and node_id in species:

            parent = species[parent_id]
            child = species[node_id]

            pgen = int(
                parent["generation_number"]
            )

            cgen = int(
                child["generation_number"]
            )

            if cgen > pgen:
                relationship = "later_evolution"

            elif pgen > cgen:
                relationship = "later_pre_evolution"

            else:
                relationship = "same_generation"

            triggers = sorted({
                detail.get("trigger", {}).get(
                    "name", "unknown"
                )
                for detail in (
                    node.get("evolution_details") or []
                )
                if detail.get("trigger")
            })

            family_edges.append({
                "chain_id": chain_id,
                "from_id": parent_id,
                "from_name": parent["display_name"],
                "from_generation": pgen,
                "to_id": node_id,
                "to_name": child["display_name"],
                "to_generation": cgen,
                "relationship": relationship,
                "new_member_generation": max(
                    pgen, cgen
                ),
                "evolution_triggers": "; ".join(
                    triggers
                )
            })

        for next_node in node.get(
            "evolves_to", []
        ):
            visit(next_node, node_id)

    visit(payload["chain"])

    if family_nodes:

        member_generations = [
            int(species[i]["generation_number"])
            for i in family_nodes
        ]

        first_gen = min(member_generations)

        families.append({
            "chain_id": chain_id,
            "root_species": payload["chain"][
                "species"
            ]["name"],
            "family_size": len(family_nodes),
            "first_generation": first_gen,
            "latest_generation": max(
                member_generations
            ),
            "later_added_species": sum(
                gen > first_gen
                for gen in member_generations
            ),
            "cross_generation_links": sum(
                e["relationship"] != "same_generation"
                for e in family_edges
            ),
            "later_evolution_links": sum(
                e["relationship"] == "later_evolution"
                for e in family_edges
            ),
            "later_pre_evolution_links": sum(
                e["relationship"] == "later_pre_evolution"
                for e in family_edges
            )
        })

        edges.extend(family_edges)

    if (
        position % 50 == 0
        or position == len(chain_urls)
    ):
        print(
            f"Evolution chains processed: "
            f"{position}/{len(chain_urls)}"
        )


# ----------------------------------------
# Export CSV files
# ----------------------------------------

edge_fields = [
    "chain_id",
    "from_id",
    "from_name",
    "from_generation",
    "to_id",
    "to_name",
    "to_generation",
    "relationship",
    "new_member_generation",
    "evolution_triggers"
]

family_fields = [
    "chain_id",
    "root_species",
    "family_size",
    "first_generation",
    "latest_generation",
    "later_added_species",
    "cross_generation_links",
    "later_evolution_links",
    "later_pre_evolution_links"
]

write_csv(
    DATA / "evolution_relationships.csv",
    edges,
    edge_fields
)

write_csv(
    DATA / "evolution_family_summary.csv",
    families,
    family_fields
)

eevee = sorted(
    [
        edge
        for edge in edges
        if edge["from_id"] == 133
    ],
    key=lambda edge: (
        edge["to_generation"],
        edge["to_id"]
    )
)

write_csv(
    DATA / "eevee_evolutions.csv",
    eevee,
    edge_fields
)


# ----------------------------------------
# Results
# ----------------------------------------

print("\nEvolution dataset created successfully.")

print(f"Family records: {len(families)}")
print(f"Evolution links: {len(edges)}")

print(
    "Families gaining later-generation members:",
    sum(
        f["later_added_species"] > 0
        for f in families
    )
)

print(f"Eevee evolutions: {len(eevee)}")

print("\nSaved:")
print("data/evolution_relationships.csv")
print("data/evolution_family_summary.csv")
print("data/eevee_evolutions.csv")
