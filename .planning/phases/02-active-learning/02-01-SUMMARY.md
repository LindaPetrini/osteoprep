---
phase: 02-active-learning
plan: "01"
subsystem: database, ui, active-learning
tags: [fsrs, spaced-repetition, sqlite, alembic, htmx, daisyui, flashcards, fastapi]

# Dependency graph
requires:
  - phase: 01-foundation-and-content-pipeline
    provides: Topic model, SQLite DB, Alembic migrations, FastAPI app structure, base.html layout, templates_config

provides:
  - FSRS flashcard review session at /review (front -> Show Answer -> back + 4 rating buttons -> next card or results)
  - py-fsrs 6.3.0 Scheduler singleton with maximum_interval=7 (enforces 7-day exam window cap)
  - All Phase 2 DB tables: flashcards, srs_states, quiz_questions, quiz_attempts, exam_questions, practice_test_attempts, practice_test_answers
  - DaisyUI dock bottom navigation on all pages with due-count badge on Review tab
  - 14 Italian nomenclature flashcards seeded across 8 topics, all due immediately

affects:
  - 02-active-learning (plans 02-04 use quiz_questions, exam_questions, practice_test_attempts tables)
  - Any future phases adding new page routes (must include active_tab and due_count context)

# Tech tracking
tech-stack:
  added:
    - fsrs==6.3.0 (py-fsrs spaced repetition scheduler)
  patterns:
    - FSRS module-level singleton: Scheduler created once at module import, never per-request
    - HTMX fragment swap: card-container div replaced outerHTML on Show Answer and on rating
    - Session state via hidden form fields: session_ids (comma-sep), current_index, total passed through GET query params to card_back, then embedded in card_back hidden fields for POST to rate
    - Due count injection: all page routes import fsrs_service.get_due_count() and pass due_count to templates

key-files:
  created:
    - app/services/fsrs_service.py
    - app/routers/review.py
    - app/templates/review.html
    - app/templates/fragments/card_front.html
    - app/templates/fragments/card_back.html
    - app/templates/fragments/session_results.html
    - seed_flashcards.py
    - migrations/versions/96666ad6e3f4_phase2_active_learning.py
  modified:
    - app/models.py (added 7 new ORM models)
    - app/templates/base.html (DaisyUI dock bottom nav + safe-area padding)
    - app/routers/pages.py (inject active_tab and due_count)
    - app/main.py (register review router)
    - requirements.txt (add fsrs==6.3.0)

key-decisions:
  - "card_back session state: GET /review/cards/{id}/back accepts session_ids, current_index, total as query params (not buried in query_params); card_front button appends these to hx-get URL"
  - "card_front fragment provides own #card-container wrapper so HTMX outerHTML swap works for both initial include and subsequent fragment returns"
  - "due_count uses Jinja2 'is defined' guard in base.html to handle routes that do not yet pass the context variable"
  - "maximum_interval=7 confirmed as direct Scheduler attribute in py-fsrs 6.3.0 (not scheduler.parameters.maximum_interval)"

patterns-established:
  - "Fragment wrapper pattern: HTMX-swapped fragments always include their own #card-container outer div to ensure outerHTML swap target is self-contained"
  - "Service singleton pattern: module-level _scheduler created once, all functions are pure or async, never instantiate per-request"
  - "Nav context injection: all page routes must inject active_tab and due_count for bottom nav to render correctly"

requirements-completed: [CARD-01, CARD-02, CARD-03, CARD-04]

# Metrics
duration: 5min
completed: 2026-02-28
---

# Phase 2 Plan 01: Active Learning Foundation Summary

**FSRS flashcard review with py-fsrs 6.3.0 (max_interval=7), all Phase 2 DB tables via Alembic, DaisyUI bottom nav with due-count badge, 14 seeded Italian nomenclature cards**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-28T17:28:23Z
- **Completed:** 2026-02-28T17:33:48Z
- **Tasks:** 2
- **Files modified:** 13

## Accomplishments
- All 7 Phase 2 DB tables (flashcards, srs_states, quiz_questions, quiz_attempts, exam_questions, practice_test_attempts, practice_test_answers) created via single Alembic migration
- Working FSRS flashcard review session at /review: front card -> Show Answer -> definition + 4 rating buttons (Di nuovo / Difficile / Bene / Facile) -> next card or session results
- DaisyUI dock bottom navigation on all pages with animated badge showing due card count
- 14 Italian nomenclature flashcards seeded across 8 Biology/Chemistry topics, all due immediately
- 7-day interval cap enforced: Scheduler(maximum_interval=7) confirmed, no card ever scheduled beyond exam window

## Task Commits

Each task was committed atomically:

1. **Task 1: Phase 2 DB schema — Alembic migration + models + py-fsrs install** - `a2a24e6` (feat)
2. **Task 2: FSRS service, flashcard seed, review router + templates, bottom nav** - `c7d2b2e` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `app/services/fsrs_service.py` - FSRS scheduler singleton with review_card(), new_card_json(), get_due_count()
- `app/routers/review.py` - GET /review, GET /review/cards/{id}/back, POST /review/cards/{id}/rate
- `app/templates/review.html` - Full review session page extending base.html
- `app/templates/fragments/card_front.html` - Term + Show Answer HTMX button, owns #card-container wrapper
- `app/templates/fragments/card_back.html` - Definition + four rating buttons with embedded session state
- `app/templates/fragments/session_results.html` - End-of-session score summary with Done button
- `seed_flashcards.py` - Seeds 14 Italian flashcards across 8 topics with immediate due dates
- `migrations/versions/96666ad6e3f4_phase2_active_learning.py` - All 7 Phase 2 tables
- `app/models.py` - Added Flashcard, SRSState, QuizQuestion, QuizAttempt, ExamQuestion, PracticeTestAttempt, PracticeTestAnswer
- `app/templates/base.html` - DaisyUI dock bottom nav with Argomenti/Ripasso/Esame, safe-area padding
- `app/routers/pages.py` - Inject active_tab="topics" and due_count into home and topic_page routes
- `app/main.py` - Register review router
- `requirements.txt` - Add fsrs==6.3.0

## Decisions Made

- Session state (session_ids, current_index, total) passed as GET query params to /review/cards/{id}/back, then embedded as hidden fields in card_back.html for POST to rate. This is cleaner than relying on request.query_params inside the template.
- card_front.html and card_back.html each provide their own `<div id="card-container">` wrapper so HTMX outerHTML swap is self-contained. review.html uses `{% include %}` without an extra wrapper to avoid double-nesting.
- `due_count` guard in base.html uses `{% if due_count is defined and due_count and due_count > 0 %}` to handle routes that do not yet pass due_count context (future routes for exam, etc.).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed double #card-container nesting in review.html**
- **Found during:** Task 2 (review template creation)
- **Issue:** Plan's review.html template wrapped `{% include "fragments/card_front.html" %}` in a `<div id="card-container">` but card_front.html also provides `<div id="card-container">` — HTMX outerHTML swap would fail with double nesting
- **Fix:** Removed the outer wrapper div from review.html; the fragment provides its own wrapper
- **Files modified:** app/templates/review.html
- **Verification:** curl /review shows single #card-container in DOM
- **Committed in:** c7d2b2e (Task 2 commit)

**2. [Rule 1 - Bug] Fixed plan verification command using wrong FSRS attribute path**
- **Found during:** Task 2 verification
- **Issue:** Plan's verification used `_scheduler.parameters.maximum_interval` but py-fsrs 6.3.0 exposes it as `_scheduler.maximum_interval` (parameters is a tuple of floats, not a named object)
- **Fix:** Verified using correct attribute `_scheduler.maximum_interval == 7`; functionality unchanged (scheduler correctly enforces 7-day cap)
- **Files modified:** None (verification-only fix, no code change needed)
- **Verification:** `.venv/bin/python -c "from app.services.fsrs_service import _scheduler; assert _scheduler.maximum_interval == 7"` passes

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs — template nesting and verification command path)
**Impact on plan:** Both fixes necessary for correctness. No scope creep.

## Issues Encountered
- None — server reload required restart (`systemctl reload` not applicable for gunicorn service; used restart instead)

## User Setup Required
None - no external service configuration required. All data is local SQLite.

## Next Phase Readiness
- Phase 2 DB foundation complete: all 7 tables migrated and verified
- FSRS review session working end-to-end: Show Answer, rate card, advance to next, session results
- SRS state persists across server restarts (SQLite WAL mode)
- Bottom nav on all pages, due-count badge accurate
- Ready for Plan 02-02: quiz mode (quiz_questions table already created)

---
*Phase: 02-active-learning*
*Completed: 2026-02-28*
