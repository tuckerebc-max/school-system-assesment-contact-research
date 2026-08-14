#!/usr/bin/env python3
"""Build a compact Markdown report from canonical batch results."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


REPORT_COLUMNS = (
    "State",
    "Formal School System Name",
    "Standardized Role Category",
    "Leader Full Name",
    "Exact Current Title",
    "Verified Direct Professional Email",
    "Best Public Office or Department Email",
    "Leadership Status",
    "Verification Status",
    "Research Notes",
)

URL_COLUMNS = (
    "Official Leadership Source URL",
    "Email Source URL",
    "Additional Verification URL",
    "Official Contact Page URL",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch", type=int, required=True)
    return parser.parse_args()


def clean_url(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    parts = urlsplit(value)
    query = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith("utm_")
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def md(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip().replace("|", r"\|")


def count_phrase(count: int, singular: str, plural: str | None = None) -> str:
    return f"{count} {singular if count == 1 else (plural or singular + 's')}"


def main() -> int:
    args = parse_args()
    with args.results.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("Results file is empty")
    missing = [column for column in REPORT_COLUMNS if column not in rows[0]]
    if missing:
        raise ValueError(f"Missing report columns: {', '.join(missing)}")

    district_count = len({row["NCES District ID"].zfill(7) for row in rows})
    direct_count = sum(
        1
        for row in rows
        if row["Verified Direct Professional Email"].strip()
        and row["Verified Direct Professional Email"].strip().casefold()
        != "not publicly located"
    )
    status_counts = Counter(row["Verification Status"].strip() for row in rows)

    source_numbers: dict[str, int] = {}
    row_sources: list[list[int]] = []
    for row in rows:
        numbers = []
        for column in URL_COLUMNS:
            url = clean_url(row.get(column, ""))
            if not url:
                continue
            if url not in source_numbers:
                source_numbers[url] = len(source_numbers) + 1
            numbers.append(source_numbers[url])
        row_sources.append(sorted(set(numbers)))

    lines = [
        f"# School System Leadership Email Research - Batch {args.batch:03d}",
        "",
        "## Scope and method",
        "",
        "This report applies the School System Assessment Contact Research protocol to the "
        "assigned districts. It prioritizes current, attributable public sources and does not "
        "generate or infer email addresses.",
        "",
        "## Batch research summary",
        "",
        f"This batch covers {count_phrase(district_count, 'school system')} and produces "
        f"{count_phrase(len(rows), 'role record')}. "
        f"{count_phrase(direct_count, 'record')} "
        f"{'includes' if direct_count == 1 else 'include'} a publicly attributable direct professional "
        "email. The detailed records preserve unsuccessful searches and transition risks through "
        "controlled verification statuses.",
        "",
        "## Leadership directory",
        "",
        "| " + " | ".join(REPORT_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REPORT_COLUMNS) + "|",
    ]
    for row, numbers in zip(rows, row_sources):
        output = dict(row)
        if numbers:
            citation = "[" + ", ".join(str(number) for number in numbers) + "]"
            output["Research Notes"] = (
                f"{output.get('Research Notes', '').strip()} {citation}".strip()
            )
        lines.append("| " + " | ".join(md(output.get(column, "")) for column in REPORT_COLUMNS) + " |")

    limits = []
    for status in (
        "PARTIALLY VERIFIED",
        "VERIFIED - OFFICE CONTACT ONLY",
        "ROLE NOT IDENTIFIED",
        "POSITION VACANT",
        "FUNCTION DISTRIBUTED",
    ):
        if status_counts[status]:
            limits.append(f"{status}: {status_counts[status]}")
    lines.extend(
        [
            "",
            "## Verification limits",
            "",
            "Records requiring qualification are summarized as follows: "
            + (", ".join(limits) if limits else "none."),
            "",
            "## Sources",
            "",
        ]
    )
    for url, number in sorted(source_numbers.items(), key=lambda item: item[1]):
        lines.append(f"{number}. {url}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
