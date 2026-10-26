
"""Audit TCGdex records; preliminary counts only."""

from pathlib import Path
from collections import Counter, defaultdict
import csv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCE = DATA / "tcg_set_classification_review.csv"

EN_NOT_EXPANSIONS = {
    "si1", "sp", "bog", "ex5.5", "exu", "ru1",
    "rc", "xy0", "xya", "sma", "swsh4.5sv",
    "swsh12.5gg", "sve", "mfb", "fut2020"
}

TRIPLET_SOURCE = (
    "https://www.pokemon-card.com/products/sv/sv1a.html"
)

SV4A_SOURCE = (
    "https://www.pokemon-card.com/ex/sv4a/index.html"
)

CELEBRATION_SOURCE = (
    "https://www.30th.pokemon-card.com/product/m6a"
)


def write_rows(path, rows, columns):
    with path.open(
        "w", encoding="utf-8-sig", newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)


# Load original classified catalogue.

with SOURCE.open(
    encoding="utf-8-sig", newline=""
) as f:
    original = list(csv.DictReader(f))

assert len(original) == 404
assert len({
    (r["language"], r["set_id"])
    for r in original
}) == len(original)


# Apply corrections and exclusion flags.

rows = []

for source in original:

    r = dict(source)

    r["decision"] = "keep_provisional"
    r["audit_note"] = "Candidate, not fully verified"
    r["official_source"] = ""

    if r["classification_status"] == "exclude_probable":

        r["decision"] = "exclude"
        r["audit_note"] = "Initial product-type exclusion"

    elif r["classification_status"] == "manual_review":

        r["decision"] = "manual_review"
        r["audit_note"] = "Unresolved classification"

    elif (
        r["language"] == "en"
        and r["set_id"] in EN_NOT_EXPANSIONS
    ):

        r["decision"] = "exclude"
        r["audit_note"] = (
            "Subset, collection or non-expansion product"
        )

    elif (
        r["language"] == "ja"
        and r["set_id"].startswith("CS")
        and r["set_name"] == "トリプレットビート"
        and r["release_date"] == "2024-04-26"
    ):

        r["decision"] = "exclude"
        r["audit_note"] = (
            "Suspect duplicate. Official Triplet Beat "
            "was released 2023-03-10."
        )
        r["official_source"] = TRIPLET_SOURCE

    # Correct SV4a using the official Japanese site.

    if (
        r["language"] == "ja"
        and r["set_id"] == "SV4a"
    ):

        r["set_name"] = "シャイニートレジャーex"
        r["decision"] = "keep_official_corrected"
        r["audit_note"] = "Official set name corrected"
        r["official_source"] = SV4A_SOURCE

    rows.append(r)


# Identify identical names on identical dates.
# Keep one representative for this preliminary
# frequency analysis, pending manual verification.

groups = defaultdict(list)

for r in rows:
    if r["decision"].startswith("keep"):
        key = (
            r["language"],
            r["release_date"],
            r["set_name"]
        )
        groups[key].append(r)

alias_groups = 0

for group in groups.values():

    if len(group) > 1:

        alias_groups += 1

        group.sort(
            key=lambda r: r["set_id"]
        )

        group[0]["audit_note"] += (
            "; retained one same-name/date alias"
        )

        for r in group[1:]:

            r["decision"] = "exclude_alias_provisional"

            r["audit_note"] = (
                "Possible duplicate of "
                + group[0]["set_id"]
            )


# Add Japanese 30th Celebration from official
# records if absent from the source catalogue.

if not any(
    r["language"] == "ja"
    and r["set_id"] == "M6a"
    for r in rows
):

    added = dict.fromkeys(rows[0].keys(), "")

    added.update({
        "language": "ja",
        "set_id": "M6a",
        "set_name": "30th CELEBRATION",
        "release_date": "2026-09-16",
        "release_year": "2026",
        "series_name": "ポケモンカードゲーム MEGA",
        "source_url": CELEBRATION_SOURCE,
        "classification_status": "expansion_candidate",
        "classification_reason": "Official expansion",
        "verified_against_official": "yes",
        "decision": "keep_official_added",
        "audit_note": "Added from official Japanese source",
        "official_source": CELEBRATION_SOURCE
    })

    rows.append(added)


# Build provisional retained set list.

retained = sorted(
    [
        r for r in rows
        if r["decision"].startswith("keep")
    ],
    key=lambda r: (
        r["language"],
        r["release_date"],
        r["set_id"]
    )
)


# Count distinct sets and launch dates by year.

summary = []

for language in ("en", "ja"):

    for year in range(1996, 2027):

        matched = [
            r for r in retained
            if (
                r["language"] == language
                and int(r["release_year"]) == year
            )
        ]

        summary.append({
            "language": language,
            "release_year": year,
            "sets_provisional": len(matched),
            "launch_dates_provisional": len({
                r["release_date"] for r in matched
            }),
            "note": (
                "Incomplete historical Japanese coverage"
                if language == "ja" and year < 2017
                else "Partial calendar year"
                if year == 2026
                else "Provisional; not fully verified"
            )
        })


# Export all three datasets.

write_rows(
    DATA / "tcg_expansion_audit.csv",
    rows,
    list(rows[0])
)

write_rows(
    DATA / "tcg_expansions_provisional.csv",
    retained,
    list(rows[0])
)

write_rows(
    DATA / "tcg_release_frequency_preview.csv",
    summary,
    list(summary[0])
)


# Print results.

print("\nTCG EXPANSION AUDIT (NOT FINAL COUNTS)")
print("=" * 52)

for language in ("en", "ja"):

    current = [
        r for r in rows
        if r["language"] == language
    ]

    keep = [
        r for r in retained
        if r["language"] == language
    ]

    print(
        language.upper(),
        "| kept:", len(keep),
        "| unique launch dates:",
        len({
            r["release_date"] for r in keep
        })
    )

    print(
        "Decisions:",
        dict(Counter(
            r["decision"] for r in current
        ))
    )

print(
    "Same-name/date alias groups:",
    alias_groups
)

print("\nRecent-year preview:")
print("Year | EN sets / dates | JA sets / dates")

for year in range(2021, 2027):

    en = next(
        r for r in summary
        if r["language"] == "en"
        and r["release_year"] == year
    )

    ja = next(
        r for r in summary
        if r["language"] == "ja"
        and r["release_year"] == year
    )

    print(
        f"{year} | "
        f"{en['sets_provisional']} / "
        f"{en['launch_dates_provisional']} | "
        f"{ja['sets_provisional']} / "
        f"{ja['launch_dates_provisional']}"
    )

print("\nSaved three files in data/:")
print("tcg_expansion_audit.csv")
print("tcg_expansions_provisional.csv")
print("tcg_release_frequency_preview.csv")

print(
    "\nDo not present these preliminary counts "
    "as final release-frequency statistics."
)
