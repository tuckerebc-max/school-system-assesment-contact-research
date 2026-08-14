# Output Schema and Controlled Values

## Canonical columns

Use these columns in this exact order:

1. `Batch Number`
2. `Source Row Number`
3. `NCES District ID`
4. `State District ID`
5. `State`
6. `Formal School System Name`
7. `School System Type`
8. `Standardized Role Category`
9. `Leader Full Name`
10. `Exact Current Title`
11. `Leadership Status`
12. `Verified Direct Professional Email`
13. `Best Public Office or Department Email`
14. `Official Contact Phone`
15. `Official Contact Page URL`
16. `Official Leadership Source URL`
17. `Email Source URL`
18. `Additional Verification URL`
19. `Verification Status`
20. `Research Completion Date`
21. `Research Notes`

## Field rules

- Preserve NCES District ID as a seven-character text identifier, including leading zeros.
- Use the two-letter postal abbreviation in State.
- Use the full current official system name.
- Preserve accents, hyphens, initials, and suffixes in names.
- Omit honorifics unless the organization consistently treats one as part of the displayed name.
- Transcribe the exact current title.
- Store one email per email field and no surrounding commentary.
- Lowercase email addresses unless the published address is case-sensitive.
- Store full plain-text source URLs.
- Use ISO date format `YYYY-MM-DD`.
- Keep notes concise and evidence-focused.

## School System Type

Use exactly one:

- `Traditional Public LEA`
- `County Public School System`
- `City Public School System`
- `Independent School District`
- `Public Charter LEA`
- `Charter Management Organization`
- `Private School System`
- `Diocesan School System`
- `State-Operated School System`
- `Other`

## Leadership Status

Use exactly one:

- `Permanent`
- `Interim`
- `Acting`
- `Incoming`
- `Outgoing`
- `Vacant`
- `Unclear`

## Verification Status

Use exactly one:

- `VERIFIED - CURRENT`
- `VERIFIED - EMAIL VIA SECONDARY OFFICIAL SOURCE`
- `VERIFIED - OFFICE CONTACT ONLY`
- `PARTIALLY VERIFIED`
- `ROLE NOT IDENTIFIED`
- `POSITION VACANT`
- `FUNCTION DISTRIBUTED`

Definitions:

- `VERIFIED - CURRENT`: Person, exact title, and contact information are supported by a current
  official source.
- `VERIFIED - EMAIL VIA SECONDARY OFFICIAL SOURCE`: Identity/title are confirmed by the system;
  email is published by another authoritative institution.
- `VERIFIED - OFFICE CONTACT ONLY`: Identity/title are confirmed, but only an office or
  department route is publicly available.
- `PARTIALLY VERIFIED`: One important element cannot be conclusively confirmed; explain it.
- `ROLE NOT IDENTIFIED`: No current systemwide leader was located after applying the stopping rule.
- `POSITION VACANT`: A reliable current source states that the position is vacant.
- `FUNCTION DISTRIBUTED`: No single leader owns the function; explain the division.

## Tier 1 outcome rows

For `ROLE NOT IDENTIFIED`, `POSITION VACANT`, or `FUNCTION DISTRIBUTED`, retain the district
identifiers, standardized role, research date, supporting sources, verification status, and notes.
Use the applicable status text for `Leader Full Name` when no person can be named.

## Audit rules

- Every expected district must be represented.
- Every Tier 1 category must have at least one allowed outcome per district.
- Every non-placeholder direct email must have an Email Source URL.
- Every named leader must have an Official Leadership Source URL.
- No source field may contain a search-engine result URL.
- Review duplicate district-role-leader keys.
- Compute all report counts from the canonical records.
