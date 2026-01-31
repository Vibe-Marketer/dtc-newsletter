---
phase: 06-product-factory
plan: 04
subsystem: product-factory
tags: [fpdf2, gspread, google-auth, pdf-generation, google-sheets, generators]

# Dependency graph
requires:
  - phase: 06-01
    provides: Base generator class with ProductSpec -> GeneratedProduct contract
provides:
  - PDF generator using fpdf2 for professional frameworks/guides
  - Google Sheets generator with online/offline mode support
  - Both generators inherit from BaseGenerator abstract class
affects: [06-product-factory, product-pipeline, lead-magnets]

# Tech tracking
tech-stack:
  added:
    - fpdf2>=2.8.0
    - gspread>=6.0.0
    - google-auth>=2.0.0
  patterns:
    - Graceful degradation (Sheets offline mode when no credentials)
    - Claude integration for content generation with fallback defaults
    - PDF magic byte validation (%PDF header check)

key-files:
  created:
    - execution/generators/pdf.py
    - execution/generators/sheets.py
    - tests/test_pdf_generator.py
    - tests/test_sheets_generator.py
  modified:
    - requirements.txt
    - execution/generators/__init__.py

key-decisions:
  - "PDF styling: FrameworkPDF class with chapters, bullets, numbered lists, callout boxes"
  - "Sheets offline mode: JSON definition + MANUAL_SETUP.md when no credentials"
  - "Sheets online mode: Create actual Google Sheet with anyone-can-view sharing"
  - "Both generators use Claude for content structure with fallback defaults"

patterns-established:
  - "External library generators inherit BaseGenerator and handle library unavailability gracefully"
  - "Validation checks file format (PDF magic bytes) and minimum content size"
  - "Generators produce README.md documenting the generated product"

# Metrics
duration: 28min
completed: 2026-01-31
---

# Phase 6 Plan 04: External Library Generators Summary

**PDF generator using fpdf2 with professional styling (chapters, callouts, lists) and Sheets generator with online/offline modes for graceful credential handling**

## Performance

- **Duration:** 28 min
- **Started:** 2026-01-31T15:47:57Z
- **Completed:** 2026-01-31T16:16:37Z
- **Tasks:** 2
- **Files modified:** 6 files (4 created, 2 modified)

## Accomplishments

- Created PdfGenerator with FrameworkPDF class supporting chapters, bullet lists, numbered lists, and callout boxes (tip, warning, note)
- Implemented PDF validation checking %PDF magic bytes and minimum size (1KB)
- Created SheetsGenerator with dual-mode operation: online (creates actual Google Sheet) and offline (JSON definition + manual instructions)
- Added graceful degradation for Sheets when credentials unavailable
- Added fpdf2, gspread, and google-auth dependencies to requirements.txt
- 60 new tests (29 PDF + 31 Sheets), 886 total tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Create PDF generator with fpdf2** - `6f49854` (feat)
2. **Task 2: Create Sheets generator with gspread** - `4c3433b` (feat)

## Files Created/Modified

- `execution/generators/pdf.py` - FrameworkPDF class and PdfGenerator with Claude integration
- `execution/generators/sheets.py` - SheetsGenerator with online/offline modes, SCOPES, manual instruction generation
- `tests/test_pdf_generator.py` - 29 tests for PDF generation and validation
- `tests/test_sheets_generator.py` - 31 tests for Sheets generation, validation, and credential handling
- `requirements.txt` - Added fpdf2, gspread, google-auth dependencies
- `execution/generators/__init__.py` - Exported PdfGenerator and SheetsGenerator

## Decisions Made

1. **PDF styling approach:** Custom FrameworkPDF class extending FPDF with header(), footer(), chapter_title(), bullet_list(), numbered_list(), callout_box() methods
2. **Sheets dual-mode:** Online mode creates actual Google Sheet with sharing; offline mode generates JSON definition + step-by-step MANUAL_SETUP.md
3. **Credential handling:** Sheets checks for credentials file from env var GOOGLE_SERVICE_ACCOUNT_JSON or "service_account.json" default
4. **Claude fallback:** Both generators use Claude for content structure but fall back to sensible defaults if unavailable

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed fpdf2 deprecation warnings**
- **Found during:** Task 1 (PDF generator tests)
- **Issue:** fpdf2 deprecated `ln` parameter in cell() method
- **Fix:** Updated to use `new_x=XPos.LMARGIN, new_y=YPos.NEXT` for new lines
- **Files modified:** execution/generators/pdf.py
- **Verification:** Tests pass with no deprecation warnings
- **Committed in:** 6f49854 (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (blocking - deprecation fix)
**Impact on plan:** Minimal - just updated API usage to non-deprecated methods.

## Issues Encountered

None.

## User Setup Required

**External services require manual configuration.** See the plan frontmatter for:
- Environment variable: `GOOGLE_SERVICE_ACCOUNT_JSON` pointing to service account JSON key
- Dashboard configuration: Enable Sheets API and Drive API in Google Cloud Console

Note: Sheets generator works in offline mode without credentials, generating JSON definitions and manual setup instructions.

## Next Phase Readiness

- PDF and Sheets generators ready for use in product pipeline
- Both generators integrate with Claude for AI-assisted content generation
- 60 tests added for external-dependency generators
- Ready for 06-05-PLAN.md (GPT config and prompt pack generators) or product factory orchestrator

---
*Phase: 06-product-factory*
*Completed: 2026-01-31*
