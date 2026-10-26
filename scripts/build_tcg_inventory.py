
"""Collect English and Japanese TCG set records.

This creates an exploratory inventory, NOT final
release-frequency counts. We must classify which
sets are actual expansions before charting.

Outputs:
    data/raw/tcgdex_en_ja_sets_all.csv
    data/tcg_set_release_candidates.csv
"""

from pathlib import Path
from datetime import date
from urllib.request import Request, urlopen
from urllib.parse import quote
import csv
import json
import time

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
CACHE = ROOT / ".cache" / "tcgdex"

RAW.mkdir(parents=True, exist_ok=True)
CACHE.mkdir(parents=True, exist_ok=True)

BASE = "https://api.tcgdex.net/v2"
CUTOFF = date(2026, 10, 26)


def get_json(url, cache_path):

    if cache_path.exists():
        return json.loads(
            cache_path.read_text(encoding="utf-8")
        )

    for attempt in range(5):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "FIT3179-Pokemon-DV2/1.0",
                    "Accept": "application/json"
                }
            )

            with urlopen(req, timeout=35) as res:
                data = json.load(res)

            cache_path.parent.mkdir(
                parents=True, exist_ok=True
            )

            cache_path.write_text(
                json.dumps(data, ensure_ascii=False),
                encoding="utf-8"
            )

            time.sleep(0.12)
            return data

        except Exception as exc:
            if attempt == 4:
                raise RuntimeError(
                    f"Could not fetch {url}: {exc}"
                ) from exc

            time.sleep(2 ** attempt)


def write_csv(path, rows, columns):

    with path.open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:

        writer = csv.DictWriter(
            f, fieldnames=columns
        )

        writer.writeheader()
        writer.writerows(rows)


columns = [
    "language",
    "set_id",
    "set_name",
    "release_date",
    "release_year",
    "series_id",
    "series_name",
    "card_count_total",
    "source_url",
    "review_status"
]

rows = []

# EN = English-language catalogue
# JA = Japanese-language catalogue

for lang in ("en", "ja"):

    index_url = f"{BASE}/{lang}/sets"

    listing = get_json(
        index_url,
        CACHE / lang / "sets_index.json"
    )

    if not isinstance(listing, list):
        raise ValueError(
            f"Unexpected listing format: {lang}"
        )

    print(
        f"\n{lang}: {len(listing)} set IDs found"
    )

    for i, brief in enumerate(listing, 1):

        set_id = str(brief["id"])
        encoded_id = quote(set_id, safe="")

        url = (
            f"{BASE}/{lang}/sets/{encoded_id}"
        )

        detail = get_json(
            url,
            CACHE / lang / (encoded_id + ".json")
        )

        release = detail.get(
            "releaseDate", ""
        ) or ""

        year = ""

        if release:
            try:
                when = date.fromisoformat(release)
                year = when.year

            except ValueError:
                release = ""

        series = detail.get("serie") or {}
        cards = detail.get("cardCount") or {}

        rows.append({
            "language": lang,
            "set_id": set_id,
            "set_name": detail.get(
                "name", brief.get("name", "")
            ),
            "release_date": release,
            "release_year": year,
            "series_id": series.get("id", ""),
            "series_name": series.get("name", ""),
            "card_count_total": cards.get(
                "total", ""
            ),
            "source_url": url,
            "review_status": "unclassified"
        })

        if i % 50 == 0 or i == len(listing):
            print(
                f"  {lang}: {i}/{len(listing)} "
                f"records collected"
            )


# Save complete source catalogue.

all_path = (
    RAW / "tcgdex_en_ja_sets_all.csv"
)

write_csv(all_path, rows, columns)


# Include only dated records released by
# 26 October 2026 for initial review.

candidates = [
    row for row in rows
    if (
        row["release_date"]
        and date.fromisoformat(
            row["release_date"]
        ) <= CUTOFF
    )
]

candidates.sort(
    key=lambda row: (
        row["language"],
        row["release_date"],
        row["set_id"]
    )
)

review_path = (
    ROOT / "data"
    / "tcg_set_release_candidates.csv"
)

write_csv(
    review_path, candidates, columns
)


# Print results.

print("\nTCG SOURCE INVENTORY")
print("=" * 48)

for lang in ("en", "ja"):

    source_n = sum(
        row["language"] == lang
        for row in rows
    )

    accepted_n = sum(
        row["language"] == lang
        for row in candidates
    )

    print(
        f"{lang}: {source_n} catalogue entries, "
        f"{accepted_n} dated on/before {CUTOFF}"
    )

print("\nSaved:")
print("data/raw/tcgdex_en_ja_sets_all.csv")
print("data/tcg_set_release_candidates.csv")

print(
    "\nThese records still require classification "
    "before calculating expansion frequency."
)

print(
    "Japanese and English sets must not be "
    "automatically matched by name or ID."
)
