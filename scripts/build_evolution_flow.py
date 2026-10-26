
"""Create a generation-to-generation Pokémon evolution flow."""

from pathlib import Path
from collections import Counter, defaultdict
import csv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

ROMAN = [
    "I", "II", "III", "IV", "V",
    "VI", "VII", "VIII", "IX"
]

LEFT_X, RIGHT_X = 155, 575
NODE_WIDTH = 15
Y_TOP, Y_BOTTOM = 70, 530


def read_csv(filename):
    with (DATA / filename).open(
        encoding="utf-8-sig", newline=""
    ) as f:
        return list(csv.DictReader(f))


def write_csv(filename, rows, columns):
    with (DATA / filename).open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)


families = {
    int(r["chain_id"]): r
    for r in read_csv("evolution_family_summary.csv")
}

edges = read_csv("evolution_relationships.csv")
generations = read_csv(
    "evolution_generational_summary.csv"
)

# Collect every unique species in each family.
members = defaultdict(dict)

for r in edges:
    chain = int(r["chain_id"])

    members[chain][int(r["from_id"])] = int(
        r["from_generation"]
    )

    members[chain][int(r["to_id"])] = int(
        r["to_generation"]
    )


# Count members joining families from older generations.
flows = Counter()
joined = Counter()

for chain, family in families.items():

    first = int(family["first_generation"])
    expected_size = int(family["family_size"])
    nodes = members.get(chain, {})

    if expected_size == 1:
        if nodes:
            raise ValueError(
                f"Unexpected links in singleton family {chain}"
            )
        continue

    if len(nodes) != expected_size:
        raise ValueError(
            f"Family {chain}: incorrect member count"
        )

    later_count = 0

    for generation in nodes.values():

        if generation > first:
            flows[(first, generation)] += 1
            joined[generation] += 1
            later_count += 1

    if later_count != int(
        family["later_added_species"]
    ):
        raise ValueError(
            f"Family {chain}: incorrect later additions"
        )


# Compare results with the earlier analysis.
for row in generations:
    generation = int(row["generation_number"])

    expected = int(
        row["joined_existing_families"]
    )

    if joined[generation] != expected:
        raise ValueError(
            f"Generation {generation} count mismatch"
        )

assert sum(flows.values()) == 71


# Create totals for each side of the flow.
source_totals = Counter()
target_totals = Counter()

for (source, target), count in flows.items():
    source_totals[source] += count
    target_totals[target] += count

sources = sorted(
    g for g in range(1, 10)
    if source_totals[g] > 0
)

targets = sorted(
    g for g in range(1, 10)
    if target_totals[g] > 0
)


# Calculate proportional heights for the ribbons.
total = sum(flows.values())
height = Y_BOTTOM - Y_TOP
gap = 25

largest_gap_count = max(
    len(sources) - 1,
    len(targets) - 1
)

unit = min(
    5.0,
    (height - gap * largest_gap_count) / total
)

assert unit > 0


def positions(gens, counts):

    used = (
        sum(counts[g] * unit for g in gens)
        + gap * (len(gens) - 1)
    )

    y = Y_TOP + (height - used) / 2
    result = {}

    for gen in gens:

        h = counts[gen] * unit

        result[gen] = (y, y + h)

        y += h + gap

    return result


left = positions(sources, source_totals)
right = positions(targets, target_totals)


# Build node rectangles.
nodes = []

for side, gens, coords, totals, x in [
    ("source", sources, left, source_totals, LEFT_X),
    ("target", targets, right, target_totals, RIGHT_X)
]:

    for gen in gens:

        y0, y1 = coords[gen]

        nodes.append({
            "side": side,
            "generation": gen,
            "generation_label": f"Gen {ROMAN[gen-1]}",
            "total": totals[gen],
            "display_label": (
                f"Gen {ROMAN[gen-1]} · {totals[gen]}"
            ),
            "x0": x,
            "x1": x + NODE_WIDTH,
            "y0": round(y0, 3),
            "y1": round(y1, 3),
            "ymid": round((y0 + y1) / 2, 3)
        })


# Build curved ribbons between generation nodes.
source_cursor = {
    gen: left[gen][0]
    for gen in sources
}

target_cursor = {
    gen: right[gen][0]
    for gen in targets
}

links = []

for (source, target), count in sorted(flows.items()):

    thickness = unit * count

    sy0 = source_cursor[source]
    sy1 = sy0 + thickness

    ty0 = target_cursor[target]
    ty1 = ty0 + thickness

    source_cursor[source] = sy1
    target_cursor[target] = ty1

    x0 = LEFT_X + NODE_WIDTH
    x1 = RIGHT_X
    cx = (x0 + x1) / 2

    path = (
        f"M {x0:.2f},{sy0:.2f} "
        f"C {cx:.2f},{sy0:.2f} "
        f"{cx:.2f},{ty0:.2f} "
        f"{x1:.2f},{ty0:.2f} "
        f"L {x1:.2f},{ty1:.2f} "
        f"C {cx:.2f},{ty1:.2f} "
        f"{cx:.2f},{sy1:.2f} "
        f"{x0:.2f},{sy1:.2f} Z"
    )

    links.append({
        "source_generation": source,
        "target_generation": target,
        "source_label": f"Gen {ROMAN[source-1]}",
        "target_label": f"Gen {ROMAN[target-1]}",
        "species_count": count,
        "path": path
    })


write_csv(
    "evolution_flow_links.csv",
    links,
    [
        "source_generation",
        "target_generation",
        "source_label",
        "target_label",
        "species_count",
        "path"
    ]
)

write_csv(
    "evolution_flow_nodes.csv",
    nodes,
    [
        "side",
        "generation",
        "generation_label",
        "total",
        "display_label",
        "x0",
        "x1",
        "y0",
        "y1",
        "ymid"
    ]
)


print("\nEVOLUTION FLOW DATA CREATED")
print("Total later-added species:", total)
print("Generation-to-generation connections:", len(links))

print("\nOriginal family generations:")
for gen in sources:
    print(
        f"Gen {ROMAN[gen-1]}: "
        f"{source_totals[gen]} later additions"
    )

print("\nGenerations introducing those species:")
for gen in range(2, 10):
    print(
        f"Gen {ROMAN[gen-1]}: "
        f"{target_totals[gen]} species"
    )

print("\nSaved:")
print("data/evolution_flow_links.csv")
print("data/evolution_flow_nodes.csv")
