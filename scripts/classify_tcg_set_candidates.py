
"""Classify TCG records for further research.

Input:
    data/tcg_set_release_candidates.csv

Output:
    data/tcg_set_classification_review.csv

This is preliminary classification, not final verification.
"""

from pathlib import Path
from collections import Counter
import csv

ROOT = Path(__file__).resolve().parent.parent

SOURCE = ROOT / "data" / "tcg_set_release_candidates.csv"

OUTPUT = ROOT / "data" / "tcg_set_classification_review.csv"


# -------------------------------------------
# Categories that are not ordinary expansions
# -------------------------------------------

EN_EXCLUDE_SERIES = {
    "Pokémon TCG Pocket": "Digital TCG",
    "Trainer kits": "Trainer kit",
    "McDonald's Collection": "Promotional distribution",
    "POP": "Promotional series",
    "Miscellaneous": "Mixed non-expansion catalogue"
}

EN_EXCLUDE_NAME = {
    "black star promo": "Promotional cards",
    "promotional": "Promotional collection",
    "promo": "Promotional collection",
    "trainer gallery": "Subset of an expansion",
    "classic collection": "Subset of an expansion",
    "jumbo": "Jumbo card catalogue"
}

JA_EXCLUDE_NAME = {
    "プロモ": "Promotional cards",
    "スターターセット": "Starter set",
    "スタートデッキ": "Starter deck",
    "デッキビルド": "Deck-building product"
}


# -------------------------------------------
# Preliminary classification rules
# -------------------------------------------

def classify(row):

    language = row["language"]

    name = row["set_name"]
    lower_name = name.casefold()

    if language == "en":

        series = row["series_name"]

        if series in EN_EXCLUDE_SERIES:
            return (
                "exclude_probable",
                EN_EXCLUDE_SERIES[series]
            )

        for keyword, reason in EN_EXCLUDE_NAME.items():

            if keyword in lower_name:
                return "exclude_probable", reason

        if row["set_id"] == "mee":
            return (
                "manual_review",
                "Check Mega Evolution Energy product"
            )

    elif language == "ja":

        for keyword, reason in JA_EXCLUDE_NAME.items():

            if keyword in name:
                return "exclude_probable", reason

    return (
        "expansion_candidate",
        "Verify against authoritative release catalogue"
    )


# -------------------------------------------
# Read existing source
# -------------------------------------------

with SOURCE.open(
    encoding="utf-8-sig",
    newline=""
) as file:

    rows = list(csv.DictReader(file))


# Check unique IDs within each language.
keys = {
    (row["language"], row["set_id"])
    for row in rows
}

assert len(keys) == len(rows), (
    "Duplicate set records detected"
)


# -------------------------------------------
# Classify the records
# -------------------------------------------

for row in rows:

    status, reason = classify(row)

    row["classification_status"] = status

    row["classification_reason"] = reason

    row["verified_against_official"] = "no"


# -------------------------------------------
# Save classification results
# -------------------------------------------

with OUTPUT.open(
    "w",
    encoding="utf-8-sig",
    newline=""
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=list(rows[0].keys())
    )

    writer.writeheader()
    writer.writerows(rows)


# -------------------------------------------
# Print summary
# -------------------------------------------

print("\nTCG SET CLASSIFICATION")
print("=" * 48)

for language in ["en", "ja"]:

    records = [
        r for r in rows
        if r["language"] == language
    ]

    counts = Counter(
        r["classification_status"]
        for r in records
    )

    print(f"\n{language.upper()} ({len(records)} records)")

    print(
        "Expansion candidates:",
        counts["expansion_candidate"]
    )

    print(
        "Manual review:",
        counts["manual_review"]
    )

    print(
        "Probable exclusions:",
        counts["exclude_probable"]
    )


print("\nSaved to:")
print(OUTPUT)

print("\nIMPORTANT:")
print("Candidates still require verification.")
print("Do not use preliminary counts as final releases.")
