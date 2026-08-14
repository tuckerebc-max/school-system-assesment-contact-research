#!/usr/bin/env python3
"""Audit a canonical school-system contact research batch."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


REQUIRED_COLUMNS = (
    "Batch Number",
    "Source Row Number",
    "NCES District ID",
    "State District ID",
    "State",
    "Formal School System Name",
    "School System Type",
    "Standardized Role Category",
    "Leader Full Name",
    "Exact Current Title",
    "Leadership Status",
    "Verified Direct Professional Email",
    "Best Public Office or Department Email",
    "Official Contact Phone",
    "Official Contact Page URL",
    "Official Leadership Source URL",
    "Email Source URL",
    "Additional Verification URL",
    "Verification Status",
    "Research Completion Date",
    "Research Notes",
)

TIER1_ROLES = (
    "Superintendent / Chief Executive",
    "Chief Academic Officer / Teaching and Learning",
    "Assessment, Accountability, Research, and Evaluation",
    "Student / Scholar Services",
)

ALLOWED_ROLES = TIER1_ROLES + (
    "Special Education / Exceptional Student Services",
    "Technology, Data, and Innovation",
    "Communications / Community Engagement",
    "School Leadership / School Support",
)

ALLOWED_VERIFICATION = {
    "VERIFIED - CURRENT",
    "VERIFIED - EMAIL VIA SECONDARY OFFICIAL SOURCE",
    "VERIFIED - OFFICE CONTACT ONLY",
    "PARTIALLY VERIFIED",
    "ROLE NOT IDENTIFIED",
    "POSITION VACANT",
    "FUNCTION DISTRIBUTED",
}

ALLOWED_LEADERSHIP = {
    "Permanent",
    "Interim",
    "Acting",
    "Incoming",
    "Outgoing",
    "Vacant",
    "Unclear",
}

ALLOWED_SYSTEM_TYPES = {
    "Traditional Public LEA",
    "County Public School System",
    "City Public School System",
    "Independent School District",
    "Public Charter LEA",
    "Charter Management Organization",
    "Private School System",
    "Diocesan School System",
    "State-Operated School System",
    "Other",
}

OUTCOME_STATUSES = {"ROLE NOT IDENTIFIED", "POSITION VACANT", "FUNCTION DISTRIBUTED"}
NOT_PUBLIC = "not publicly located"
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PLACEHOLDER_RE = re.compile(
    r"(^|\b)(tbd|\[name\]|\[email\]|unknown person|first(name)?[._-]?last(name)?@)",
    re.IGNORECASE,
)
SEARCH_HOSTS = {
    "google.com",
    "www.google.com",
    "bing.com",
    "www.bing.com",
    "search.yahoo.com",
    "duckduckgo.com",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--expected-districts", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), [
            {key: (value or "").strip() for key, value in row.items()} for row in reader
        ]


def normalized_status(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("—", "-").replace("–", "-")).strip()


def valid_url(value: str) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def add_issue(container: list[dict], code: str, message: str, **context) -> None:
    container.append({"code": code, "message": message, **context})


def main() -> int:
    args = parse_args()
    fields, rows = read_csv(args.results)
    expected_fields, expected_rows = read_csv(args.expected_districts)
    errors: list[dict] = []
    warnings: list[dict] = []

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fields]
    if missing_columns:
        add_issue(
            errors,
            "missing_columns",
            "Canonical result columns are missing.",
            columns=missing_columns,
        )
    if "NCES District ID" not in expected_fields:
        add_issue(
            errors,
            "expected_file_missing_id",
            "Expected-district file lacks NCES District ID.",
        )

    expected_ids = {
        row.get("NCES District ID", "").zfill(7)
        for row in expected_rows
        if row.get("NCES District ID", "")
    }
    result_ids = {
        row.get("NCES District ID", "").zfill(7)
        for row in rows
        if row.get("NCES District ID", "")
    }
    for district_id in sorted(expected_ids - result_ids):
        add_issue(
            errors,
            "district_missing",
            "Expected district has no result records.",
            nces_district_id=district_id,
        )
    for district_id in sorted(result_ids - expected_ids):
        add_issue(
            errors,
            "unexpected_district",
            "Result contains a district outside the assigned batch.",
            nces_district_id=district_id,
        )

    coverage: dict[str, set[str]] = defaultdict(set)
    seen_keys: set[tuple[str, str, str]] = set()
    status_counts: Counter[str] = Counter()
    direct_email_count = 0

    for row_number, row in enumerate(rows, start=2):
        district_id = row.get("NCES District ID", "").zfill(7)
        role = row.get("Standardized Role Category", "")
        verification = normalized_status(row.get("Verification Status", ""))
        leadership = row.get("Leadership Status", "")
        system_type = row.get("School System Type", "")
        leader = row.get("Leader Full Name", "")
        direct_email = row.get("Verified Direct Professional Email", "")
        office_email = row.get("Best Public Office or Department Email", "")
        leadership_url = row.get("Official Leadership Source URL", "")
        email_url = row.get("Email Source URL", "")
        completion_date = row.get("Research Completion Date", "")

        if not district_id.strip("0"):
            add_issue(errors, "missing_id", "NCES District ID is missing.", row=row_number)
        if role not in ALLOWED_ROLES:
            add_issue(
                errors,
                "invalid_role",
                "Standardized role is not controlled.",
                row=row_number,
                value=role,
            )
        else:
            coverage[district_id].add(role)
        if verification not in ALLOWED_VERIFICATION:
            add_issue(
                errors,
                "invalid_verification_status",
                "Verification status is not controlled.",
                row=row_number,
                value=verification,
            )
        else:
            status_counts[verification] += 1
        if leadership not in ALLOWED_LEADERSHIP:
            add_issue(
                errors,
                "invalid_leadership_status",
                "Leadership status is not controlled.",
                row=row_number,
                value=leadership,
            )
        if system_type not in ALLOWED_SYSTEM_TYPES:
            add_issue(
                errors,
                "invalid_system_type",
                "School System Type is not controlled.",
                row=row_number,
                value=system_type,
            )
        if PLACEHOLDER_RE.search(leader) or PLACEHOLDER_RE.search(direct_email):
            add_issue(
                errors,
                "placeholder",
                "Placeholder or inferred-pattern text is prohibited.",
                row=row_number,
            )

        for field_name, email in (
            ("Verified Direct Professional Email", direct_email),
            ("Best Public Office or Department Email", office_email),
        ):
            if email and email.casefold() != NOT_PUBLIC and not EMAIL_RE.match(email):
                add_issue(
                    errors,
                    "invalid_email",
                    "Email field must contain one valid address or 'Not publicly located'.",
                    row=row_number,
                    field=field_name,
                    value=email,
                )
        if direct_email and direct_email.casefold() != NOT_PUBLIC:
            direct_email_count += 1
            if not valid_url(email_url):
                add_issue(
                    errors,
                    "direct_email_without_source",
                    "Direct email lacks a valid Email Source URL.",
                    row=row_number,
                )

        if verification not in OUTCOME_STATUSES and not valid_url(leadership_url):
            add_issue(
                errors,
                "leader_without_source",
                "Named leader lacks a valid official identity/title source.",
                row=row_number,
            )
        if not completion_date or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", completion_date):
            add_issue(
                errors,
                "invalid_research_date",
                "Research Completion Date must use YYYY-MM-DD.",
                row=row_number,
                value=completion_date,
            )

        for field_name in (
            "Official Contact Page URL",
            "Official Leadership Source URL",
            "Email Source URL",
            "Additional Verification URL",
        ):
            value = row.get(field_name, "")
            if not value:
                continue
            if not valid_url(value):
                add_issue(
                    errors,
                    "invalid_url",
                    "Source field is not a valid HTTP(S) URL.",
                    row=row_number,
                    field=field_name,
                    value=value,
                )
                continue
            parsed = urlparse(value)
            if parsed.netloc.casefold() in SEARCH_HOSTS:
                add_issue(
                    errors,
                    "search_result_url",
                    "Cite the underlying source rather than a search page.",
                    row=row_number,
                    field=field_name,
                )
            if "utm_" in parsed.query.casefold():
                add_issue(
                    warnings,
                    "tracking_parameter",
                    "Remove avoidable tracking parameters from the stored URL.",
                    row=row_number,
                    field=field_name,
                )

        key = (district_id, role, leader.casefold())
        if key in seen_keys:
            add_issue(
                warnings,
                "duplicate_record",
                "Duplicate district-role-leader key requires review.",
                row=row_number,
                key=key,
            )
        seen_keys.add(key)

    for district_id in sorted(expected_ids):
        for role in TIER1_ROLES:
            if role not in coverage[district_id]:
                add_issue(
                    errors,
                    "tier1_missing",
                    "Tier 1 role has no record or allowed outcome.",
                    nces_district_id=district_id,
                    role=role,
                )

    summary = {
        "districts_expected": len(expected_ids),
        "districts_represented": len(result_ids & expected_ids),
        "role_records": len(rows),
        "verified_direct_emails": direct_email_count,
        "verification_status_counts": dict(sorted(status_counts.items())),
    }
    result = {
        "passed": not errors,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "results_file": str(args.results.resolve()),
        "expected_districts_file": str(args.expected_districts.resolve()),
        "summary": summary,
        "errors": errors,
        "warnings": warnings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"passed": result["passed"], **summary}))
    if errors:
        print(f"Audit failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Audit passed with {len(warnings)} warning(s).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
