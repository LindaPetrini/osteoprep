---
phase: 02-active-learning
plan: "03"
subsystem: ui, active-learning, database
tags: [fastapi, htmx, daisyui, sqlite, anthropic, exam, mcq, timer, jinja2]

# Dependency graph
requires:
  - phase: 02-active-learning/02-01
    provides: Phase 2 DB tables (exam_questions, practice_test_attempts, practice_test_answers), fsrs_service.get_due_count(), base.html with bottom nav, templates_config

provides:
  - Timed practice exam at /exam/practice with 22 Italian TOLC-B/TOLC-F MCQs, 90-minute countdown timer
  - Per-question AI explanations (correct + 3 wrong choices) via generate_exam_explanation() with generate-once-cache
  - Exam landing page at /exam showing format info and attempt history (last 5)
  - PracticeTestAttempt + PracticeTestAnswer rows persisted for every submission
  - Timer auto-submits via htmx.trigger() when remaining <= 0; time_expired flag preserved in DB

affects:
  - Any future phase displaying exam history or extending the exam practice loop
  - Phase 4 progress tracking (practice_test_attempts table is populated data)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Server-start-time anchor: start_time_epoch embedded in form data-start-time attribute; JS calculates remaining = startTime + duration - now for accurate countdown on slow connections
    - Generate-once-cache for exam explanations: check explanation_json IS NULL before calling Claude; result stored as JSON in exam_questions.explanation_json
    - htmx.trigger(form, 'submit') for programmatic form submission on timer expiry

key-files:
  created:
    - app/routers/exam.py
    - app/templates/exam.html
    - app/templates/exam_practice.html
    - app/templates/exam_results.html
    - seed_exam_questions.py
  modified:
    - app/services/claude.py (appended generate_exam_explanation() + EXAM_EXPLANATION_SYSTEM_PROMPT)
    - app/main.py (added exam router registration)

key-decisions:
  - "start_time_epoch embedded server-side in form data-start-time: JS reads it and calculates remaining = startTime + duration - Date.now()/1000 — guards against slow page loads resetting the timer"
  - "htmx.trigger(form, 'submit') used for timer auto-submit: more reliable than form.submit() which bypasses HTMX bindings"
  - "question_ids hidden field in form: ensures server can process all questions including unanswered ones (not just the submitted radio values)"
  - "generate-once-cache per exam question: explanation_json IS NULL check before Claude call, result flushed to DB immediately so concurrent submissions share cached explanations"

patterns-established:
  - "Timer anchor pattern: embed server-side Unix epoch in form data-attribute; JS reads it for drift-free countdown"
  - "Hidden question_ids pattern: include all exam question IDs as comma-separated hidden field so POST handler knows the full set regardless of which were answered"

requirements-completed: [EXAM-01, EXAM-02, EXAM-03, EXAM-04]

# Metrics
duration: 5min
completed: 2026-02-28
---

# Phase 2 Plan 03: Past Exam Practice Summary

**Timed practice exam at /exam/practice with 22 Italian TOLC-B/TOLC-F MCQs, 90-min countdown timer (htmx.trigger auto-submit), per-question AI explanations with generate-once-cache, and attempt history persisted to SQLite**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-28T17:58:45Z
- **Completed:** 2026-02-28T18:03:19Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- 22 Italian MCQ exam questions seeded (10 biology, 10 chemistry, 2 extra biology) matching TOLC-B/TOLC-F style
- Timed practice exam at /exam/practice: sticky countdown timer, 20 randomly sampled questions, auto-submit on expiry via htmx.trigger
- Per-question AI explanations generated on first submission (generate-once-cache: null check before Claude call, result stored in exam_questions.explanation_json)
- Exam landing page at /exam with format info and last-5 attempt history showing score and date
- PracticeTestAttempt + PracticeTestAnswer rows persisted for every submission including time_expired flag

## Task Commits

Each task was committed atomically:

1. **Task 1: Seed exam questions + add generate_exam_explanation()** - `1382a18` (feat)
2. **Task 2: Exam router, landing/practice/results templates, register router** - `aa1982b` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `seed_exam_questions.py` - Seeds 22 Italian TOLC-B/TOLC-F MCQs into exam_questions table; idempotent (skips existing by question text)
- `app/services/claude.py` - Appended generate_exam_explanation() with EXAM_EXPLANATION_SYSTEM_PROMPT using same XML-tag pattern as quiz variant
- `app/routers/exam.py` - GET /exam (landing + history), GET /exam/practice (random sample + server start time), POST /exam/submit (score + generate-once AI explanations + DB persist)
- `app/templates/exam.html` - Landing page with format card, "Inizia simulazione" button, last-5 attempt history table
- `app/templates/exam_practice.html` - Sticky header with countdown timer, 20 MCQ radio form, htmx.trigger auto-submit on expiry, 10-min warning banner, red timer at 5 min
- `app/templates/exam_results.html` - Per-question breakdown with colour-coded correct/wrong choices and AI explanations for each option; score summary with pass threshold colours
- `app/main.py` - Added exam router import and include_router call

## Decisions Made

- `start_time_epoch` embedded server-side as Unix epoch in `data-start-time` on the form. JS reads this and computes `remaining = startTime + duration - Math.floor(Date.now()/1000)` so the countdown is accurate even on slow connections where page load takes several seconds.
- `htmx.trigger(form, 'submit')` used for programmatic timer auto-submit rather than `form.submit()` — ensures HTMX processes the form normally and triggers hx-push-url and hx-target correctly.
- Hidden `question_ids` field in the form stores all exam question IDs as a comma-separated string. This lets the POST handler process all questions (including unanswered/skipped ones), not just those that had radio buttons selected.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None — server restart required after adding new router (systemctl restart osteoprep.service). This is normal expected behaviour with gunicorn/uvicorn static imports.

## User Setup Required

None - no external service configuration required. AI explanations are generated on first exam submission using the existing ANTHROPIC_API_KEY.

## Next Phase Readiness

- Full exam practice loop complete: land → start timed test → submit → see per-question AI explanations → history on landing
- practice_test_attempts and practice_test_answers tables populated with real data
- generate_exam_explanation() in claude service, generate-once-cache operational
- Ready for Plan 02-04 if applicable, or Phase 3

---
*Phase: 02-active-learning*
*Completed: 2026-02-28*
