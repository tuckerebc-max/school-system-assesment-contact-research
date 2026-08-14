#!/usr/bin/env python3
"""Update or query the district research progress ledger."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path


ROLE_TO_LEDGER = {
    "Superintendent / Chief Executive": "Superintendent / Chief Executive Status",
    "Chief Academic Officer / Teaching and Learning": (
        "Chief Academic Officer / Teaching and Learning Status"
    ),
    "Assessment, Accountability, Research, and Evaluation": (
        "Assessment, Accountability, Research, and Evaluation Status"
    ),
    "Student / Scholar Services": "Student / Scholar Services Status",
}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    sub = root.add_subparsers(dest="command", required=True)

    next_cmd = sub.add_parser("next")
    next_cmd.add_argument("--ledger", type=Path, required=True)

    checkpoint = sub.add_parser("checkpoint")
    checkpoint.add_argument("--ledger", type=Path, required=True)
    checkpoint.add_argument("--results", type=Path, required=True)

    mark = sub.add_parser("mark-batch")
    mark.add_argument("--ledger", type=Path, required=True)
    mark.add_argument("--manifest", type=Path, required=True)
    mark.add_argument("--batch", type=int, required=True)
    mark.add_argument("--audit", type=Path, required=True)
    mark.add_argument("--output-path", required=True)
    return root


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [
            {key: (value or "").strip() for key, value in row.items()} for row in reader
        ]


def write_csv_atomic(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def next_record(ledger: Path) -> int:
    _, rows = read_csv(ledger)
    candidates = [
        row
        for row in rows
        if row.get("District Status") not in {"Complete", "Researched - Pending Audit"}
    ]
    if not candidates:
        candidates = [
            row for row in rows if row.get("District Status") != "Complete"
        ]
    for row in candidates:
        missing_roles = [
            role
            for role, column in ROLE_TO_LEDGER.items()
            if not row.get(column, "").strip()
        ]
        print(
            json.dumps(
                {
                    "batch_number": int(row["Batch Number"]),
                    "district_ordinal": int(row["District Ordinal"]),
                    "source_row_number": int(row["Source Row Number"]),
                    "nces_district_id": row["NCES District ID"],
                    "district_name": row["Input District Name"],
                    "state": row["State"],
                    "district_status": row["District Status"],
                    "missing_tier1_roles": missing_roles,
                },
                indent=2,
            )
        )
        return 0
    print(json.dumps({"complete": True, "message": "All districts are complete."}))
    return 0


def checkpoint(ledger: Path, results: Path) -> int:
    ledger_fields, ledger_rows = read_csv(ledger)
    _, result_rows = read_csv(results)
    by_id = {row["NCES District ID"].zfill(7): row for row in ledger_rows}
    touched: set[str] = set()
    for result in result_rows:
        district_id = result.get("NCES District ID", "").zfill(7)
        role = result.get("Standardized Role Category", "")
        ledger_row = by_id.get(district_id)
        column = ROLE_TO_LEDGER.get(role)
        if ledger_row is None or column is None:
            continue
        ledger_row[column] = result.get("Verification Status", "")
        ledger_row["Last Research Date"] = (
            result.get("Research Completion Date") or date.today().isoformat()
        )
        touched.add(district_id)

    for district_id in touched:
        row = by_id[district_id]
        if all(row.get(column, "").strip() for column in ROLE_TO_LEDGER.values()):
            row["District Status"] = "Researched - Pending Audit"
        else:
            row["District Status"] = "Research In Progress"
    write_csv_atomic(ledger, ledger_fields, ledger_rows)
    print(json.dumps({"districts_updated": len(touched)}))
    return 0


def mark_batch(args: argparse.Namespace) -> int:
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    if not audit.get("passed"):
        raise ValueError("Audit did not pass; batch cannot be marked complete")

    ledger_fields, ledger_rows = read_csv(args.ledger)
    manifest_fields, manifest_rows = read_csv(args.manifest)
    completed_at = datetime.now(timezone.utc).isoformat()
    ledger_count = 0
    for row in ledger_rows:
        if int(row["Batch Number"]) == args.batch:
            ledger_count += 1
    summary = audit.get("summary", {})
    if (
        summary.get("districts_expected") != ledger_count
        or summary.get("districts_represented") != ledger_count
    ):
        raise ValueError(
            "Audit district counts do not match the full batch in the progress ledger"
        )
    for row in ledger_rows:
        if int(row["Batch Number"]) == args.batch:
            row["District Status"] = "Complete"
            row["QC Status"] = "Passed"
            row["Output Path"] = args.output_path
    manifest_count = 0
    for row in manifest_rows:
        if int(row["Batch Number"]) == args.batch:
            row["Status"] = "Complete"
            row["Completed At"] = completed_at
            row["Output Path"] = args.output_path
            manifest_count += 1
    if not ledger_count or manifest_count != 1:
        raise ValueError("Batch number was not found consistently in progress files")
    write_csv_atomic(args.ledger, ledger_fields, ledger_rows)
    write_csv_atomic(args.manifest, manifest_fields, manifest_rows)
    print(
        json.dumps(
            {
                "batch_number": args.batch,
                "districts_marked_complete": ledger_count,
                "completed_at": completed_at,
            }
        )
    )
    return 0


def main() -> int:
    args = parser().parse_args()
    if args.command == "next":
        return next_record(args.ledger)
    if args.command == "checkpoint":
        return checkpoint(args.ledger, args.results)
    return mark_batch(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
