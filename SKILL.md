---
name: school-system-assessment-contact-research
description: Research current, publicly attributable school-system leadership contacts and emails from a district-universe workbook. Use when Codex must build lightweight official-staff rosters, organize workstreams of roughly five 25-district batches (~125 districts), identify leaders responsible for superintendent, academics, assessment/accountability, student services, special education, technology/data, communications, or school support, continue or resume prior work, audit evidence and Tier 1 coverage, or produce database-ready CSV/XLSX and exemplar-style Markdown/DOCX reports without guessing email addresses.
---

# School System Assessment Contact Research

Produce current, auditable leadership-contact research in resumable batches. Treat accuracy,
currentness, functional-role interpretation, and source transparency as more important than
apparent completeness.

## Read the applicable resources

- Read `references/research-protocol.md` before researching any district.
- Read `references/role-taxonomy.md` before mapping local titles to standardized roles.
- Read `references/output-schema.md` before creating, auditing, or merging result records.
- Use `assets/batch-report-template.md` when producing a human-readable batch report.

## Determine the operating mode

Interpret the user's request as one of:

- **Prepare**: Split a master workbook into stable batches and initialize progress files.
- **Roster**: Build a lightweight target roster for a consecutive five-batch workstream (~125 districts) before deep contact research.
- **Run batch N**: Research one specified batch.
- **Run rows X-Y**: Research an explicit district range.
- **Run state**: Research districts in a specified state while preserving workbook order.
- **Continue**: Resume at the first incomplete district-role combination.
- **Continuous**: Finalize each batch, save it, and proceed to the next batch until interrupted
  or the district universe is complete.
- **Audit**: Validate an existing batch without performing new research.
- **Merge**: Combine completed, audited batches into a cumulative dataset.

If the user supplies a workbook but no mode, prepare the batches and begin Batch 1. If progress
files already exist, default to Continue and preserve completed work.

## Prepare stable batches

1. Locate the district worksheet and verify its headers.
2. Use NCES District ID as the permanent district key. Never deduplicate by name alone.
3. Preserve original workbook order.
4. Default to 25 districts per deliverable batch.
5. Work internally in five-district checkpoints.
6. Run:

   `python scripts/prepare_batches.py INPUT.xlsx --output-dir WORK_DIR`

7. Do not overwrite an existing ledger unless the user explicitly requests a reset. Use
   `--force` only with clear authorization.

The preparation script creates a batch manifest, a district progress ledger, and one input CSV
for each batch. Keep these files with the research outputs rather than inside the installed skill.

## Build five-batch roster workstreams

Use five consecutive 25-district batches as the default workstream unit (approximately 125
districts). Keep the underlying 25-district CSVs unchanged, but create a separate roster file
for each workstream before deep research. Run:

`python scripts/build_roster_workstreams.py WORK_DIR --start-batch 26 --end-batch 40 --output-dir ROSTER_DIR`

The script writes one workstream CSV per five-batch group and one row per district-role target.
The lightweight roster is a research queue, not a verified-contact deliverable: leave names and
emails as `Not yet researched` until an official source is opened and attributable. For Batches
26–40, the default workstreams are 26–30, 31–35, and 36–40.

## Research a batch

For each five-district checkpoint:

1. Read the assigned district rows from the generated batch CSV.
2. Use the identifiers, address, city, county, and state only to identify the correct system.
3. Browse current public sources. Do not rely on model memory for identities, titles, emails,
   appointments, or leadership status.
4. Research every Tier 1 role to an allowed outcome.
5. Research Tier 2 roles systematically.
6. Include Tier 3 roles when clearly present.
7. Save canonical records after every five districts.
8. Update the progress ledger after each checkpoint.

Do not allow one difficult Tier 2 or Tier 3 role to block completion of the remaining districts.

## Apply evidence rules

- Prefer current official district sources.
- Use other government or authoritative institutional sources when needed.
- Use reputable secondary sources only to corroborate or resolve currentness.
- Open the underlying source; never cite search-result pages or snippets.
- Preserve the exact published title.
- Map roles by substantive responsibility rather than title keywords.
- Never construct, infer, or repair an email address from a naming pattern.
- Treat "verified" as publicly published and attributable, not mailbox-deliverability tested.
- Strip avoidable tracking parameters such as `utm_source` from stored URLs.
- Record conflicts, transitions, distributed responsibility, and limitations in Research Notes.

## Create canonical records

Create one row per district-role-leader combination using the exact schema and controlled values
in `references/output-schema.md`.

For every Tier 1 role, create either:

- a named leader record;
- `POSITION VACANT`;
- `FUNCTION DISTRIBUTED`; or
- `ROLE NOT IDENTIFIED`.

Use `Not publicly located` rather than a blank, placeholder, or fabricated email. When one
leader owns multiple target functions, create one row per standardized role and explain the
overlap.

## Audit before publication

Run:

`python scripts/audit_batch.py RESULTS.csv --expected-districts BATCH_INPUT.csv --output AUDIT.json`

Fix all audit errors before publication. Review warnings individually. The audit must confirm:

- every assigned district is represented;
- every Tier 1 role has an allowed outcome;
- every direct email has a supporting source URL;
- every named leader has a current identity/title source;
- statuses and controlled values are valid;
- district-role rows are not unintentionally duplicated;
- report totals reconcile with the detailed records.

## Update progress

After an audit passes, run:

`python scripts/progress.py mark-batch --ledger district-ledger.csv --manifest batch-manifest.csv --batch N --audit AUDIT.json --output-path OUTPUT_PATH`

Use:

`python scripts/progress.py next --ledger district-ledger.csv`

to locate the first incomplete district. Never mark a batch complete when its audit contains
errors.

## Produce batch deliverables

Produce, at minimum:

1. **Canonical CSV or XLSX** containing the complete schema and plain-text source URLs.
2. **Human-readable report** modeled on `assets/batch-report-template.md`.
3. **Audit JSON** with computed counts, errors, and warnings.
4. **Updated progress ledger and manifest**.

Generate the Markdown report with:

`python scripts/build_batch_report.py RESULTS.csv --output REPORT.md --batch N`

When the user requests DOCX, use the installed document-creation workflow to convert the
validated report into a polished DOCX, render every page, inspect the page images, and correct
layout defects before delivery. When the user requests XLSX, use the installed spreadsheet
workflow to create and visually verify it.

## Continue across batches

After delivering a completed batch:

1. Save all deliverables in a batch-specific folder.
2. Mark the batch complete only after its audit passes.
3. Read the next incomplete batch from the ledger.
4. In Continuous mode, start the next batch immediately.
5. If interrupted, report the last completed batch and the next district ordinal.

A skill provides deterministic resumption but does not create a background schedule by itself.
Use a Codex automation or task-orchestration layer when the user wants unattended work across
separate application sessions.

## Completion criteria

Complete a requested batch only when:

- all assigned districts have been researched;
- every Tier 1 role has an allowed outcome;
- canonical data is saved;
- the audit passes with no errors;
- summary counts are computed from the canonical data;
- the human-readable report is generated;
- progress points to the next unfinished district.
