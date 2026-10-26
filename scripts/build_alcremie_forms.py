
"""Build Alcremie's 63 cosmetic form combinations.

The evolution conditions describe the original
Generation VIII Pokémon Sword and Shield games.

Output: data/alcremie_forms.csv
"""

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "alcremie_forms.csv"


# Cream name, time, spin direction, duration,
# and schematic colour for the visualisation.

CREAMS = [
    (
        "Vanilla Cream", "Day", "Clockwise",
        "Under 5 seconds", "#F4E6C5"
    ),
    (
        "Ruby Cream", "Day", "Counterclockwise",
        "Under 5 seconds", "#EAA6B9"
    ),
    (
        "Matcha Cream", "Night", "Clockwise",
        "Under 5 seconds", "#C8DDBA"
    ),
    (
        "Mint Cream", "Night", "Counterclockwise",
        "Over 5 seconds", "#A8DCD9"
    ),
    (
        "Lemon Cream", "Night", "Clockwise",
        "Over 5 seconds", "#F6DA74"
    ),
    (
        "Salted Cream", "Night", "Counterclockwise",
        "Under 5 seconds", "#D8E6F0"
    ),
    (
        "Ruby Swirl", "Day", "Counterclockwise",
        "Over 5 seconds", "#F5CDD0"
    ),
    (
        "Caramel Swirl", "Day", "Clockwise",
        "Over 5 seconds", "#EFCBA7"
    ),
    (
        "Rainbow Swirl", "Evening", "Either",
        "Over 10 seconds", "#D6C3EA"
    )
]

SWEETS = [
    "Strawberry",
    "Berry",
    "Love",
    "Star",
    "Clover",
    "Flower",
    "Ribbon"
]


# Build every cream-and-Sweet combination.

rows = []

for cream_order, cream_data in enumerate(CREAMS, 1):

    cream, tod, direction, duration, colour = cream_data

    for sweet_order, sweet in enumerate(SWEETS, 1):

        rows.append({
            "cream": cream,
            "cream_order": cream_order,
            "sweet": sweet,
            "sweet_order": sweet_order,
            "time_of_day": tod,
            "spin_direction": direction,
            "spin_duration": duration,
            "cream_colour": colour,
            "form_name": (
                f"{cream} Alcremie + {sweet} Sweet"
            ),
            "method": (
                f"{tod}; {direction.lower()} spin; "
                f"{duration.lower()}"
            )
        })


# Validate the combinations.

assert len(rows) == 63

assert len({
    (r["cream"], r["sweet"])
    for r in rows
}) == 63

assert all(
    sum(r["cream"] == c[0] for r in rows) == 7
    for c in CREAMS
)


# Save the CSV.

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with OUTPUT.open(
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=list(rows[0])
    )

    writer.writeheader()
    writer.writerows(rows)


print("Alcremie dataset created successfully!")
print("Cream appearances:", len(CREAMS))
print("Sweets:", len(SWEETS))
print("Total combinations:", len(rows))

print("\nEvolution conditions:")

for cream, tod, direction, duration, colour in CREAMS:
    print(
        f"{cream:<16} | {tod:<7} | "
        f"{direction:<16} | {duration}"
    )

print("\nSaved to:", OUTPUT)
