---
phase: 02-active-learning
plan: "02"
subsystem: ui, active-learning, api
tags: [quiz, mcq, fastapi, htmx, daisyui, jinja2, sqlite, claude-haiku, spaced-repetition]

# Dependency graph
requires:
  - phase: 02-active-learning/02-01
    provides: quiz_questions and quiz_attempts tables, Topic/QuizQuestion/QuizAttempt ORM models, fsrs_service.get_due_count(), base.html dock nav, templates_config pattern

provides:
  - Topic quiz feature end-to-end at /topic/{slug}/quiz and /topic/{slug}/quiz/submit
  - generate_quiz_explanation() in app/services/claude.py using CORRECT/WRONG_0/1/2 XML tags and generate-once-cache pattern
  - 16 Italian MCQ questions seeded across 6 topic slugs (Biology + Chemistry)
  - Quiz page with 5 randomly sampled questions and radio-button choices
  - Results page with score card, per-choice explanations (green correct / red wrong), score history
  - "Fai un quiz su questo argomento" button on all topic pages

affects:
  - 02-active-learning (plans 03-04 may add more quiz questions or build on explanation pattern)
  - Any future exam/practice-test feature (generate-once-cache and XML-tag parsing pattern established)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Generate-once-cache for quiz explanations: check explanation_json IS NULL before calling Claude, persist result immediately via db.flush(), never regenerate
    - XML-tag parsing for quiz explanations: CORRECT/WRONG_0/WRONG_1/WRONG_2 tags parsed with re.search + DOTALL
    - Random question sampling: sample(list(all_questions), min(5, len(all_questions))) — always <= 5 questions
    - Graceful empty state: quiz page checks no_questions flag and renders friendly Italian message instead of 500/404
    - Form field naming: answer_{question_id} -> chosen_index (int), parsed in submit handler via key.startswith("answer_")

key-files:
  created:
    - seed_quiz_questions.py
    - app/routers/quiz.py
    - app/templates/quiz.html
    - app/templates/quiz_results.html
  modified:
    - app/services/claude.py (added generate_quiz_explanation() + QUIZ_EXPLANATION_SYSTEM_PROMPT)
    - app/templates/topic.html (added quiz entry button)
    - app/main.py (registered quiz router)

key-decisions:
  - "Radio button values use loop.index0 (Jinja2 zero-based loop counter), not enumerate filter which does not exist in Jinja2"
  - "Quiz submit handler uses answer_{question_id} form field naming — maps cleanly to DB question IDs regardless of display order"
  - "QuizAttempt saved BEFORE rendering results so score history is accurate on the results page (includes current attempt)"
  - "generate-once-cache: explanation_json IS NULL check in router — no duplicate Claude calls for questions already explained"

patterns-established:
  - "Empty-state guard: always handle zero-question topics with friendly UI rather than letting queries return empty and crash templates"
  - "Form field naming with entity ID: answer_{id} pattern lets submit handler look up DB records by ID without maintaining order"

requirements-completed: [QUIZ-01, QUIZ-02, QUIZ-03, QUIZ-04]

# Metrics
duration: 2min
completed: 2026-02-28
---

# Phase 2 Plan 02: Topic Quiz Summary

**End-to-end topic quiz: 16 seeded Italian MCQs, quiz router with random sampling, per-answer AI explanations using generate-once-cache, score persistence, and score history**

## Performance

- **Duration:** 2 min
- **Started:** 2026-02-28T17:58:24Z
- **Completed:** 2026-02-28T18:00:41Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Working quiz at /topic/{slug}/quiz: 5 randomly sampled Italian MCQ questions with radio-button choices per topic
- POST /topic/{slug}/quiz/submit scores the quiz, generates per-choice Claude explanations (generate-once-cache), saves QuizAttempt, and returns results page
- Results page shows score card (green/amber/red), per-question breakdown with colored per-choice explanations, and score history (last 10 attempts)
- "Fai un quiz su questo argomento" button added to all topic pages
- 16 Italian MCQs seeded across membrana-cellulare, nucleo-cellulare, mitocondri, dna-rna-proteine, legami-chimici, acidi-basi-ph, reazioni-chimiche

## Task Commits

Each task was committed atomically:

1. **Task 1: Seed quiz questions + generate_quiz_explanation() Claude service** - `a03078f` (feat)
2. **Task 2: Quiz router, templates, topic button, register router** - `e8883d6` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `seed_quiz_questions.py` - 16 Italian MCQs across 6 topic slugs, idempotent (skips existing rows)
- `app/services/claude.py` - Added generate_quiz_explanation() with QUIZ_EXPLANATION_SYSTEM_PROMPT (XML CORRECT/WRONG_0/1/2 tags)
- `app/routers/quiz.py` - GET /topic/{slug}/quiz (random 5 MCQs), POST /topic/{slug}/quiz/submit (score + explanations + history)
- `app/templates/quiz.html` - MCQ form with radio buttons (loop.index0 for zero-based values), friendly empty state
- `app/templates/quiz_results.html` - Score card, per-choice explanations (green/red coloring), score history table
- `app/templates/topic.html` - "Fai un quiz su questo argomento" button at bottom of topic page
- `app/main.py` - Registered quiz router

## Decisions Made

- Radio button values use `loop.index0` (Jinja2's built-in zero-based loop counter) not a non-existent `enumerate` filter. The plan template code had `{% for i, choice in q.choices|enumerate %}` which is invalid Jinja2 — fixed to `{% for choice in q.choices %}` with `value="{{ loop.index0 }}"`.
- `answer_{question_id}` form field naming lets the submit handler look up DB records by primary key regardless of display order, avoiding index-mapping bugs.
- QuizAttempt is saved before fetching score history so the history table on the results page includes the current attempt.
- `generate-once-cache`: the router checks `q.explanation_json is None` before calling Claude. On success, `db.flush()` persists the explanation immediately before rendering.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed invalid Jinja2 enumerate filter in quiz template**
- **Found during:** Task 2 (quiz.html creation)
- **Issue:** Plan template used `{% for i, choice in q.choices|enumerate %}` — Jinja2 has no `enumerate` filter. This would throw `TemplateAssertionError: No filter named 'enumerate'` at runtime.
- **Fix:** Changed to `{% for choice in q.choices %}` with `value="{{ loop.index0 }}"` to get zero-based index for radio button values.
- **Files modified:** app/templates/quiz.html
- **Verification:** Quiz page returns 200 and renders radio buttons with values 0-3.
- **Committed in:** e8883d6 (Task 2 commit)
- **Note:** The plan itself already documented this fix in a NOTE block — applied the correct pattern.

---

**Total deviations:** 1 auto-fixed (Rule 1 bug — invalid Jinja2 filter, caught from plan's own NOTE)
**Impact on plan:** Fix necessary for quiz form to render. No scope creep.

## Issues Encountered
- None — service restart required after adding quiz router (gunicorn does not hot-reload). Used `systemctl restart osteoprep`.

## User Setup Required
None - no external service configuration required. Quiz explanations call Claude API using existing ANTHROPIC_API_KEY.

## Next Phase Readiness
- Full quiz loop working: topic -> quiz -> submit -> results -> retry
- generate-once-cache for explanations ready for exam/practice-test features (plans 03-04)
- quiz_attempts table accumulating score history
- Ready for Plan 02-03 if exists, or Phase 3

---
*Phase: 02-active-learning*
*Completed: 2026-02-28*
