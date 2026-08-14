#!/usr/bin/env python3
"""Build lightweight five-batch research rosters from prepared batch CSVs."""
from __future__ import annotations
import argparse
import csv
from pathlib import Path

ROLE_TARGETS = [
    ("Superintendent / Chief Executive", "superintendent; chief executive; district leadership"),
    ("Chief Academic Officer / Teaching and Learning", "academics; curriculum; instruction; teaching and learning"),
    ("Assessment, Accountability, Research, and Evaluation", "assessment; accountability; research; evaluation; data"),
    ("Student / Scholar Services", "student services; student support; counseling; scholar services"),
    ("Special Education / Exceptional Student Services", "special education; exceptional student services; SELPA"),
    ("Technology, Data, and Innovation", "technology; information systems; data; innovation"),
    ("Communications / Community Engagement", "communications; public information; community engagement"),
]

def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("work_dir", type=Path)
    parser.add_argument("--start-batch", type=int, required=True)
    parser.add_argument("--end-batch", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    if args.start_batch > args.end_batch or (args.end_batch - args.start_batch + 1) % 5:
        raise ValueError("Batch range must be a positive multiple of five")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for group_start in range(args.start_batch, args.end_batch + 1, 5):
        group_end = group_start + 4
        roster = []
        for batch in range(group_start, group_end + 1):
            path = args.work_dir / f"batch-{batch:03d}-input.csv"
            if not path.exists():
                raise FileNotFoundError(path)
            for district in read_csv(path):
                for role, keywords in ROLE_TARGETS:
                    roster.append({
                        "Workstream": f"Batches {group_start:02d}-{group_end:02d}",
                        "Batch Number": district.get("Batch Number", str(batch)),
                        "District Ordinal": district.get("District Ordinal", ""),
                        "NCES District ID": district.get("NCES District ID", ""),
                        "State District ID": district.get("State District ID", ""),
                        "State": district.get("State", ""),
                        "County Name": district.get("County Name", ""),
                        "City": district.get("City", ""),
                        "District Name": district.get("District Name", ""),
                        "Target Role": role,
                        "Likely Title Keywords": keywords,
                        "Candidate Official Name": "Not yet researched",
                        "Candidate Exact Title": "Not yet researched",
                        "Candidate Direct Email": "Not yet researched",
                        "Official Starting URL": "Not yet researched",
                        "Roster Status": "Queued for lightweight identification",
                        "Roster Notes": "Use official district/state staff sources; do not infer email addresses.",
                    })
        output = args.output_dir / f"roster-batches-{group_start:02d}-{group_end:02d}.csv"
        with output.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(roster[0]))
            writer.writeheader(); writer.writerows(roster)
        print(f"Wrote {len(roster)} roster rows: {output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
