---
name: prd-validate
description: Lightweight lint and consistency check for a PRD (faster than full analysis)
argument-hint: <path-to-prd.md>
user-invocable: true
disable-model-invocation: true
allowed-tools: [Read, Glob, Grep]
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Goal

Perform a fast, mechanical lint check on a PRD file. Unlike `/prd-analyze` (which does deep semantic analysis), this checks structural and formatting issues only. Output is a pass/fail report displayed in the terminal — no files are modified.

## Execution Steps

### 1. Resolve PRD Path

- If `$ARGUMENTS` is empty, abort with: "Please provide a path to a PRD file. Example: `/prd-validate prd/my-feature/prd.md`"
- Read the file. If it does not exist, abort with a clear error message.

### 2. Run Lint Checks

Perform these mechanical checks (no semantic analysis):

#### A. Section Structure
- [ ] Has a top-level `#` heading (document title)
- [ ] All 12 required section headings are present (fuzzy match against template names)
- [ ] Section headings use `##` level (not `###` or deeper for top-level sections)
- [ ] Sections appear in template order (note any out-of-order sections)

#### B. Metadata Completeness
- [ ] Has **Version** field
- [ ] Has **Status** field (one of: Draft, In Review, Approved, Active Development)
- [ ] Has **Last Updated** date
- [ ] Has **Author** field
- [ ] Has a Revision History table

#### C. Placeholder Detection
- [ ] No `[NEEDS INPUT]` markers
- [ ] No `TODO` or `TBD` markers
- [ ] No `???` or `TKTK` markers
- [ ] No `<placeholder>` style markers
- [ ] No "to be determined" / "to be decided" phrases

#### D. Requirement Formatting
- [ ] Functional requirements have IDs (e.g., `FR-XXX-##`)
- [ ] Requirements have priority labels (P0/P1/P2 or Must/Should/Could)
- [ ] Acceptance criteria use Given/When/Then format (or equivalent structured format)

#### E. Table Integrity
- [ ] All markdown tables have header rows
- [ ] Tables are not broken (consistent column counts)
- [ ] KPI table exists with numeric targets

#### F. Content Indicators
- [ ] Document is not a stub (> 200 lines)
- [ ] No empty sections (heading followed immediately by another heading)
- [ ] Enumeration values are explicit (no "e.g." or "such as" in enum definitions)

### 3. Produce Validation Report

Output a Markdown report:

```
## PRD Validation Report

**File**: <path>
**Date**: <current date>
**Result**: PASS / FAIL (X issues)

---

### Checks

| # | Check | Result | Details |
|---|-------|--------|---------|
| 1 | Document title present | PASS | — |
| 2 | Required sections (12) | FAIL | Missing: Acceptance Criteria, Error States |
| 3 | Metadata: Version | PASS | v1.0 |
| 4 | Metadata: Status | PASS | Draft |
| 5 | Metadata: Date | PASS | 2026-01-31 |
| 6 | Metadata: Author | FAIL | Not found |
| 7 | Revision history | PASS | — |
| 8 | No placeholders | FAIL | 3 found: L42, L88, L156 |
| 9 | Requirement IDs | PASS | — |
| 10 | Priority labels | PASS | — |
| 11 | Acceptance criteria format | PASS | — |
| 12 | Table integrity | PASS | — |
| 13 | KPI table with targets | PASS | — |
| 14 | Not a stub (> 200 lines) | PASS | 1,329 lines |
| 15 | No empty sections | PASS | — |
| 16 | Enum completeness | PASS | — |

---

### Summary

- **Passed**: X / 16
- **Failed**: X / 16
- **Result**: PASS — PRD structure is valid / FAIL — X issues need attention

### Suggested Actions

- <For each FAIL, suggest the specific fix or relevant skill to run>
```

### 4. Pass/Fail Criteria

- **PASS** — All checks pass, or only non-critical checks fail (section order, enum completeness)
- **FAIL** — Any of these fail: missing required sections, missing metadata, placeholders present, no requirement IDs

## Operating Principles

- **NEVER modify files** — this is strictly read-only
- Keep it fast — use Grep for pattern matching, avoid reading the entire file line-by-line when possible
- This is a structural check, not a semantic one — do not evaluate content quality
- For deep quality analysis, recommend `/prd-analyze` instead
- Report line numbers for all issues so the user can navigate directly to problems
