
"""Build a provisional Pokemon TCG release calendar.

Input:
  data/tcg_expansions_provisional.csv

Outputs:
  data/tcg_release_sets_2017_2025.csv
  data/tcg_release_events_2017_2025.csv
  data/tcg_release_calendar_2017_2025.csv

The original source dataset is not modified.
"""

from pathlib import Path
from collections import Counter, defaultdict
from datetime import date
import csv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

SOURCE = DATA / "tcg_expansions_provisional.csv"

FIRST_YEAR = 2017
LAST_YEAR = 2025

# Verified using The Pokemon Company's official
# Black Bolt / White Flare release announcement.

CORRECTIONS = {
    ("en", "sv10.5b"): (
        "2025-07-18",
        "Official Pokemon Company launch date"
    ),
    ("en", "sv10.5w"): (
        "2025-07-18",
        "Official Pokemon Company launch date"
    )
}


def read_csv(path):
    with path.open(
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, columns):
    with path.open(
        "w",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        writer = csv.DictWriter(
            f, fieldnames=columns
        )
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------------------
# Load and validate the input
# ----------------------------------------

source = read_csv(SOURCE)

keys = {
    (r["language"], r["set_id"])
    for r in source
}

assert len(keys) == len(source), (
    "Duplicate set identifiers found"
)


# ----------------------------------------
# Prepare set-level records
# ----------------------------------------

sets = []

for original in source:

    row = dict(original)

    language = row["language"]

    if language not in ("en", "ja"):
        continue

    release_date = date.fromisoformat(
        row["release_date"]
    )

    if not (
        FIRST_YEAR <= release_date.year <= LAST_YEAR
    ):
        continue

    correction = CORRECTIONS.get(
        (language, row["set_id"])
    )

    row["date_audit"] = "As catalogued"

    if correction:

        print(
            f"Correcting {language}/{row['set_id']}: "
            f"{row['release_date']} -> {correction[0]}"
        )

        row["release_date"] = correction[0]
        row["release_year"] = correction[0][:4]
        row["date_audit"] = correction[1]

        release_date = date.fromisoformat(
            row["release_date"]
        )

    row["release_month"] = release_date.month

    row["expansion_scope"] = (
        "Provisional physical expansion candidate"
    )

    sets.append(row)


# ----------------------------------------
# Group sets by distinct release date
# ----------------------------------------

by_event = defaultdict(list)

for row in sets:

    key = (
        row["language"],
        row["release_date"]
    )

    by_event[key].append(row)


events = []

for (language, release_date), items in sorted(
    by_event.items()
):

    d = date.fromisoformat(release_date)

    events.append({

        "language": language,

        "release_date": release_date,

        "release_year": d.year,

        "release_month": d.month,

        "sets_launched": len(items),

        "set_ids": "; ".join(
            r["set_id"] for r in items
        ),

        "set_names": "; ".join(
            r["set_name"] for r in items
        )
    })


# ----------------------------------------
# Calculate monthly release frequencies
# ----------------------------------------

month_sets = Counter(
    (
        r["language"],
        int(r["release_year"]),
        int(r["release_month"])
    )
    for r in sets
)

month_events = Counter(
    (
        r["language"],
        int(r["release_year"]),
        int(r["release_month"])
    )
    for r in events
)

calendar = []

for language in ("en", "ja"):

    for year in range(
        FIRST_YEAR,
        LAST_YEAR + 1
    ):

        for month in range(1, 13):

            key = (language, year, month)

            calendar.append({

                "language": language,

                "market_label": (
                    "English catalogue"
                    if language == "en"
                    else "Japanese catalogue"
                ),

                "release_year": year,

                "release_month": month,

                "month_label": date(
                    year, month, 1
                ).strftime("%b"),

                "sets_launched": month_sets[key],

                "distinct_launch_dates": (
                    month_events[key]
                )
            })


# ----------------------------------------
# Validate results
# ----------------------------------------

assert len(calendar) == 9 * 12 * 2

assert sum(
    r["sets_launched"]
    for r in calendar
) == len(sets)

assert sum(
    r["distinct_launch_dates"]
    for r in calendar
) == len(events)


# ----------------------------------------
# Save output files
# ----------------------------------------

write_csv(
    DATA / "tcg_release_sets_2017_2025.csv",
    sets,
    list(sets[0])
)

write_csv(
    DATA / "tcg_release_events_2017_2025.csv",
    events,
    list(events[0])
)

write_csv(
    DATA / "tcg_release_calendar_2017_2025.csv",
    calendar,
    list(calendar[0])
)


# ----------------------------------------
# Print summary
# ----------------------------------------

print("\nTCG RELEASE CALENDAR: 2017-2025")
print("=" * 58)

print(
    "Year | English sets/dates | Japanese sets/dates"
)

for year in range(
    FIRST_YEAR,
    LAST_YEAR + 1
):

    en_sets = sum(
        int(r["release_year"]) == year
        and r["language"] == "en"
        for r in sets
    )

    ja_sets = sum(
        int(r["release_year"]) == year
        and r["language"] == "ja"
        for r in sets
    )

    en_dates = sum(
        int(r["release_year"]) == year
        and r["language"] == "en"
        for r in events
    )

    ja_dates = sum(
        int(r["release_year"]) == year
        and r["language"] == "ja"
        for r in events
    )

    print(
        f"{year} | "
        f"{en_sets}/{en_dates} | "
        f"{ja_sets}/{ja_dates}"
    )


print("\nCreated:")

print("data/tcg_release_sets_2017_2025.csv")
print("data/tcg_release_events_2017_2025.csv")
print("data/tcg_release_calendar_2017_2025.csv")

print(
    "\nNote: These remain catalogued, "
    "provisional release counts."
)
