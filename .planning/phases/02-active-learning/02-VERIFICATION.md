---
phase: 02-active-learning
verified: 2026-02-28T00:00:00Z
status: gaps_found
score: 2/5 must-haves verified
re_verification: false
gaps:
  - truth: "User can take a multiple-choice quiz after a topic section and see per-answer explanations"
    status: failed
    reason: "No quiz router, quiz templates, quiz questions seeded, or quiz UI exists. Only the DB schema (quiz_questions, quiz_attempts tables) was created in Plan 02-01. Plans 02-02 is not yet executed."
    artifacts:
      - path: "app/routers/quiz.py"
        issue: "File does not exist"
      - path: "app/templates/quiz.html"
        issue: "File does not exist"
      - path: "app/templates/fragments/quiz_question.html"
        issue: "File does not exist"
    missing:
      - "Quiz router with GET /topic/{slug}/quiz and POST /topic/{slug}/quiz/submit endpoints"
      - "Quiz page template rendering 5 MCQ questions"
      - "Per-answer explanation display (correct + why each wrong option is incorrect)"
      - "Seeded quiz questions in quiz_questions table (currently 0 rows)"
      - "Router registered in app/main.py"

  - truth: "Quiz scores are saved and visible (user can see their score history)"
    status: failed
    reason: "No quiz attempt persistence logic exists — no route to save QuizAttempt records, no UI to display score history. Table exists but is empty and unused."
    artifacts:
      - path: "app/routers/quiz.py"
        issue: "File does not exist — no quiz attempt save logic"
    missing:
      - "POST handler that writes QuizAttempt row on quiz submission"
      - "Score history display (visible somewhere — topic page or review page)"

  - truth: "User can access past Italian exam questions and take a timed practice test"
    status: failed
    reason: "No exam router, exam templates, seed exam questions, or timed practice UI exist. Only DB schema (exam_questions, practice_test_attempts, practice_test_answers) was created. Plan 02-03 is not yet executed."
    artifacts:
      - path: "app/routers/exam.py"
        issue: "File does not exist"
      - path: "app/templates/exam.html"
        issue: "File does not exist"
      - path: "seed_exam_questions.py"
        issue: "File does not exist"
    missing:
      - "Exam router with GET /exam (landing), GET /exam/practice (timed session), POST /exam/submit"
      - "Timed practice test UI with visible countdown (90 min / 60 questions format)"
      - "Auto-submit when timer hits zero"
      - "At least 20 seeded Italian-language MCQs in exam_questions table (currently 0 rows)"
      - "Per-question result breakdown with AI-generated explanations after submission"
      - "Practice test history saved to practice_test_attempts and practice_test_answers"
      - "Router registered in app/main.py"

human_verification:
  - test: "Open /review on iPhone Safari, tap Show Answer, tap a rating button"
    expected: "Card advances to next card; final rating shows session results screen with Done button"
    why_human: "HTMX fragment swap and mobile tap behavior cannot be verified programmatically"
  - test: "Verify due-count badge appears on Review tab in bottom nav when cards are due"
    expected: "Badge shows non-zero number; hidden when zero due cards"
    why_human: "Visual badge rendering requires browser inspection"
---

# Phase 2: Active Learning Verification Report

**Phase Goal:** User can reinforce knowledge through FSRS flashcard reviews, topic quizzes with explanations, and practice with real past exam questions
**Verified:** 2026-02-28
**Status:** gaps_found — 2 of 5 success criteria verified
**Re-verification:** No — initial verification

---

## Goal Achievement

The phase goal requires THREE distinct active learning modes. Only ONE (FSRS flashcard reviews) is fully implemented. Plans 02-02 (quiz) and 02-03 (exam) are listed in the ROADMAP but have not been executed.

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can review flashcards, rate each card (Again/Hard/Good/Easy), cards rescheduled — no card beyond 7 days | VERIFIED | `review.py` routes fully wired; `fsrs_service.py` Scheduler(maximum_interval=7) confirmed; 14 seeded flashcards in DB; card_front/back/session_results templates all substantive |
| 2 | SRS card state (due date, stability, difficulty) is intact after server restart | VERIFIED | SQLite WAL-mode persistence; `state.card_json`, `state.due_at`, `state.updated_at` persisted via `await db.commit()` in `rate_card()`; Alembic migration at head |
| 3 | User can take a multiple-choice quiz after a topic section and see per-answer explanations | FAILED | No quiz router, no quiz templates, no quiz questions in DB (0 rows); only schema exists |
| 4 | Quiz scores are saved and visible | FAILED | No quiz attempt save logic anywhere; quiz_attempts table has 0 rows and no route writes to it |
| 5 | User can access past Italian exam questions and take a timed practice test with explanations after | FAILED | No exam router, no exam templates, no seed questions (0 rows); only DB schema created |

**Score: 2/5 success criteria verified**

---

## Required Artifacts

### Plan 02-01 Artifacts (CARD-01 through CARD-04 only)

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/services/fsrs_service.py` | FSRS scheduler singleton, review_card(), new_card_json(), get_due_count() | VERIFIED | All three functions present; `_scheduler = Scheduler(maximum_interval=7)` at module level; imported and used in review.py and pages.py |
| `app/routers/review.py` | GET /review, GET /review/cards/{id}/back, POST /review/cards/{id}/rate | VERIFIED | All three routes implemented with full DB persistence; no stubs |
| `app/templates/review.html` | Full-page flashcard session with card-container div | VERIFIED | Extends base.html; empty-state and active-session branches; includes card_front fragment |
| `app/templates/fragments/card_front.html` | Term + Show Answer button (hx-get card back) | VERIFIED | Substantive: renders `flashcard.front_it`, hx-get with session state in query string, 44px button |
| `app/templates/fragments/card_back.html` | Definition + four rating buttons (Again/Hard/Good/Easy) | VERIFIED | Substantive: renders `flashcard.back_it`, 4-button grid with hx-post to rate endpoint, session state in hidden fields |
| `app/templates/fragments/session_results.html` | End-of-session score summary with Done button | VERIFIED | Renders `cards_reviewed`, Done link to `/review` |
| `migrations/versions/96666ad6e3f4_phase2_active_learning.py` | All Phase 2 DB tables (7 tables) | VERIFIED | All 7 tables present; `alembic current` confirms `96666ad6e3f4 (head)` |
| `seed_flashcards.py` | Seed 5-8 nomenclature flashcards per topic (40 total) | PARTIAL | File exists and is substantive with 14 flashcards across 8 topics. SUMMARY claims "14 seeded flashcards" vs plan target of "40 total" — plan said 40, delivered 14. DB confirms 14 rows in flashcards, 14 in srs_states. Functionally sufficient for demo. |

### Missing Artifacts (Plans 02-02 and 02-03 not yet executed)

| Artifact | Required By | Status |
|----------|-------------|--------|
| `app/routers/quiz.py` | QUIZ-01, QUIZ-02, QUIZ-03, QUIZ-04 | MISSING |
| `app/templates/quiz.html` | QUIZ-01, QUIZ-02, QUIZ-03 | MISSING |
| `app/routers/exam.py` | EXAM-01, EXAM-02, EXAM-03, EXAM-04 | MISSING |
| `app/templates/exam.html` | EXAM-01, EXAM-02 | MISSING |
| `seed_exam_questions.py` | EXAM-01 | MISSING |

---

## Key Link Verification (Plan 02-01)

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `card_front.html` Show Answer button | `GET /review/cards/{id}/back` | `hx-get` with session state in query params | WIRED | `hx-get="/review/cards/{{ srs_state.id }}/back?session_ids=...&current_index=...&total=..."` confirmed in template |
| `card_back.html` rating forms | `POST /review/cards/{id}/rate` | `hx-post` with hidden rating + session fields | WIRED | Each of 4 buttons has its own `<form hx-post="...">` with hidden `rating`, `session_ids`, `current_index`, `total` fields confirmed |
| `review.py rate_card()` | `fsrs_service.review_card()` | Direct function call with card_json and Rating enum | WIRED | `updated_json, due_at = fsrs_service.review_card(state.card_json, rating_enum)` at line 90 of review.py |
| `fsrs_service.py` | `Scheduler(maximum_interval=7)` | Module-level singleton instantiation | WIRED | `_scheduler = Scheduler(desired_retention=0.9, maximum_interval=7, enable_fuzzing=False)` confirmed; verified programmatically: `_scheduler.maximum_interval == 7` |
| `base.html` due_count badge | `fsrs_service.get_due_count()` | Server-side injection via pages.py home() and topic_page() | WIRED | Both routes in pages.py call `await fsrs_service.get_due_count(db)` and pass `due_count` to template context; base.html renders badge with `{% if due_count is defined and due_count and due_count > 0 %}` guard |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CARD-01 | 02-01-PLAN.md | User can study flashcards using spaced repetition | SATISFIED | Full review session at /review with HTMX fragment swap; 14 flashcards in DB |
| CARD-02 | 02-01-PLAN.md | FSRS-5 with review intervals capped at 7 days | SATISFIED | `Scheduler(maximum_interval=7)` confirmed; programmatic check passed (Easy rating yields max 6 days) |
| CARD-03 | 02-01-PLAN.md | User rates each card and cards are rescheduled | SATISFIED | POST /review/cards/{id}/rate saves updated card_json and due_at; 4 rating buttons (Di nuovo/Difficile/Bene/Facile) map to Rating 1-4 |
| CARD-04 | 02-01-PLAN.md | SRS state persists across server restarts | SATISFIED | SQLite WAL persistence; state saved via `await db.commit()` in rate_card(); Alembic migration confirmed |
| QUIZ-01 | (02-02 — not executed) | User can take a multiple-choice quiz after a topic section | BLOCKED | No implementation; quiz_questions table has 0 rows; no router/templates |
| QUIZ-02 | (02-02 — not executed) | Each quiz question shows which answers are correct and why | BLOCKED | No quiz UI exists; explanation_json field in schema but no generation logic |
| QUIZ-03 | (02-02 — not executed) | Wrong answers are explained | BLOCKED | No quiz UI exists |
| QUIZ-04 | (02-02 — not executed) | Quiz scores are saved and visible in progress tracking | BLOCKED | QuizAttempt table exists but empty; no save logic; no display logic |
| EXAM-01 | (02-03 — not executed) | User can access a bank of past exam questions | BLOCKED | exam_questions table has 0 rows; no exam router |
| EXAM-02 | (02-03 — not executed) | User can take a timed practice test | BLOCKED | No exam UI; no timer implementation |
| EXAM-03 | (02-03 — not executed) | After answering, user sees correct answer with AI explanation | BLOCKED | No exam results UI |
| EXAM-04 | (02-03 — not executed) | Practice test history and per-question results saved | BLOCKED | practice_test_attempts / practice_test_answers tables exist but empty; no save logic |

**Note on Orphaned Requirements:** QUIZ-01 through QUIZ-04 and EXAM-01 through EXAM-04 are mapped to Phase 2 in REQUIREMENTS.md traceability table. They do NOT appear in Plan 02-01's `requirements` frontmatter (which only claims CARD-01 through CARD-04). These 8 requirements are planned for Plans 02-02 and 02-03 per the ROADMAP, which are explicitly listed as pending. They are not orphaned — they have a home — but they are unimplemented.

---

## Anti-Patterns Found

No anti-patterns detected in Phase 2 created/modified files. All implementations are substantive with no TODO/FIXME markers, no placeholder returns, and no empty handlers.

| File | Pattern | Severity |
|------|---------|----------|
| (all scanned) | None found | — |

---

## Human Verification Required

### 1. Flashcard Review Flow End-to-End

**Test:** Open `/review` on iPhone Safari. Tap "Mostra risposta". Tap a rating button (e.g., "Bene").
**Expected:** Card back appears with 4 rating buttons. After rating, next card front appears (or session results if last card). Progress label ("Carta N di M") updates.
**Why human:** HTMX `outerHTML` swap and fragment replacement behavior requires browser rendering. Mobile tap interactions cannot be verified programmatically.

### 2. Due-Count Badge Visibility

**Test:** Ensure cards are due in DB, then load the home page `/`. Inspect the Review tab in the bottom nav.
**Expected:** Badge with a number appears on the Ripasso tab. After reviewing all cards, badge disappears.
**Why human:** Visual badge rendering and disappearance on count=0 requires browser inspection.

### 3. Session State Across Cards

**Test:** Start a review session with multiple due cards. Rate the first card, verify the next card loads and shows "Carta 2 di N" in the progress label.
**Expected:** Session state (session_ids, current_index, total) threads correctly through the GET query params and POST hidden fields.
**Why human:** Session state threading via HTMX query params is best verified by observing actual DOM transitions.

---

## Gaps Summary

Phase 2 goal achievement is **partial**: the flashcard review mode (Plans 02-01) is fully implemented and working. However, the phase goal explicitly includes three modes, and two are not yet implemented:

1. **Topic quizzes with explanations** (QUIZ-01 through QUIZ-04): No quiz router, templates, questions, or score-saving logic exists. Only the DB schema was created as a foundation. Plan 02-02 needs to execute.

2. **Past exam question practice** (EXAM-01 through EXAM-04): No exam router, templates, seed questions, timed-test UI, or result persistence exists. Only the DB schema was created. Plan 02-03 needs to execute.

The root cause is not a bug — these features were intentionally split into separate plans (02-02 and 02-03) that have not yet been executed. The ROADMAP correctly shows Phase 2 as "1/3 plans complete."

The phase goal will be achieved when Plans 02-02 and 02-03 are executed and verified.

---

_Verified: 2026-02-28_
_Verifier: Claude (gsd-verifier)_
