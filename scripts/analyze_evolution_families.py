
"""Analyse Pokémon evolution families across Generations I–IX."""

from collections import Counter, defaultdict
from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


# ----------------------------------------
# Read existing datasets
# ----------------------------------------

def read_csv(filename):
    with (DATA / filename).open(
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


master = read_csv("pokemon_master.csv")
edges = read_csv("evolution_relationships.csv")
families = read_csv("evolution_family_summary.csv")
eevee_edges = read_csv("eevee_evolutions.csv")


# ----------------------------------------
# Calculate species introduced per generation
# ----------------------------------------

generation_sizes = Counter(
    int(p["generation_number"])
    for p in master
)


# ----------------------------------------
# Reconstruct each evolutionary family
# ----------------------------------------

family_members = defaultdict(dict)
link_directions = defaultdict(Counter)

for edge in edges:

    chain = int(edge["chain_id"])
    parent = int(edge["from_id"])
    child = int(edge["to_id"])

    family_members[chain][parent] = int(
        edge["from_generation"]
    )

    family_members[chain][child] = int(
        edge["to_generation"]
    )

    direction = edge["relationship"]

    if direction != "same_generation":

        gen = int(edge["new_member_generation"])

        link_directions[gen][direction] += 1


# ----------------------------------------
# Count later additions to older families
# ----------------------------------------

added_species = Counter()
expanded_families = defaultdict(set)

for family in families:

    chain = int(family["chain_id"])
    first_gen = int(family["first_generation"])
    nodes = family_members.get(chain, {})

    expected_size = int(family["family_size"])

    # Families with one species have no evolution links.
    if expected_size == 1:

        if nodes:
            raise ValueError(
                f"Unexpected links in family {chain}"
            )

        continue

    if len(nodes) != expected_size:
        raise ValueError(
            f"Family {chain}: expected {expected_size} "
            f"species, found {len(nodes)}"
        )

    count_later = 0

    for species_id, gen in nodes.items():

        if gen > first_gen:

            count_later += 1
            added_species[gen] += 1
            expanded_families[gen].add(chain)

    if count_later != int(
        family["later_added_species"]
    ):
        raise ValueError(
            f"Later-member count mismatch: {chain}"
        )


# ----------------------------------------
# Summarise each generation
# ----------------------------------------

output = []

for gen in range(1, 10):

    joined = added_species[gen]
    total = generation_sizes[gen]

    output.append({
        "generation_number": gen,
        "new_species_total": total,
        "joined_existing_families": joined,
        "share_joining_existing_families_pct": (
            round(100 * joined / total, 1)
            if total else 0
        ),
        "families_expanded": len(
            expanded_families[gen]
        ),
        "new_evolution_links": (
            link_directions[gen]["later_evolution"]
        ),
        "new_pre_evolution_links": (
            link_directions[gen]["later_pre_evolution"]
        )
    })


# ----------------------------------------
# Save chart-ready summary
# ----------------------------------------

out_file = DATA / "evolution_generational_summary.csv"

with out_file.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=list(output[0])
    )

    writer.writeheader()
    writer.writerows(output)


# ----------------------------------------
# Print overall statistics
# ----------------------------------------

print("\nEVOLUTION FAMILY ANALYSIS (GEN I-IX)")
print("=" * 78)

print(f"Species in master: {len(master)}")
print(f"Evolution families: {len(families)}")
print(f"Evolution links: {len(edges)}")

print(
    "Families expanded in later generations:",
    sum(
        int(f["later_added_species"]) > 0
        for f in families
    )
)

print(
    "Species added to older families:",
    sum(added_species.values())
)


# ----------------------------------------
# Print generation comparison
# ----------------------------------------

print("\nNew species joining older evolution families:")

print(
    f"{'Gen':>3} "
    f"{'New species':>12} "
    f"{'Joined older':>13} "
    f"{'Share':>8} "
    f"{'Families':>9} "
    f"{'New evol.':>11} "
    f"{'New pre-evol.':>14}"
)

for row in output:

    print(
        f"{row['generation_number']:>3} "
        f"{row['new_species_total']:>12} "
        f"{row['joined_existing_families']:>13} "
        f"{row['share_joining_existing_families_pct']:>7.1f}% "
        f"{row['families_expanded']:>9} "
        f"{row['new_evolution_links']:>11} "
        f"{row['new_pre_evolution_links']:>14}"
    )


# ----------------------------------------
# Identify notable evolution families
# ----------------------------------------

print("\nFamilies with most later-generation members:")

top = sorted(
    (
        f for f in families
        if int(f["later_added_species"]) > 0
    ),
    key=lambda f: (
        -int(f["later_added_species"]),
        -int(f["family_size"]),
        f["root_species"]
    )
)[:12]

for f in top:

    print(
        f"  {f['root_species']:<18} "
        f"later additions: "
        f"{f['later_added_species']:<3} "
        f"total family: "
        f"{f['family_size']:<3} "
        f"first gen: "
        f"{f['first_generation']}"
    )


# ----------------------------------------
# Show Eevee evolution branches
# ----------------------------------------

print("\nEevee evolution branches:")

for e in sorted(
    eevee_edges,
    key=lambda r: (
        int(r["to_generation"]),
        int(r["to_id"])
    )
):

    print(
        f"  Gen {e['to_generation']}: "
        f"Eevee -> {e['to_name']}"
    )


# ----------------------------------------
# Final output
# ----------------------------------------

print(f"\nSaved: {out_file}")

print(
    "Note: 'Joined older' counts unique new species."
)

print(
    "Evolution and pre-evolution counts refer to "
    "cross-generation links, not all new family members."
)
