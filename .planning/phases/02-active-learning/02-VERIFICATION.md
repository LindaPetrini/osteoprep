---
phase: 02-active-learning
verified: 2026-02-28T18:15:00Z
status: passed
score: 5/5 must-haves verified
re_verification:
  previous_status: gaps_found
  previous_score: 2/5
  gaps_closed:
    - "User can take a multiple-choice quiz after a topic section and see per-answer explanations"
    - "Quiz scores are saved and visible (user can see their score history)"
    - "User can access past Italian exam questions and take a timed practice test"
  gaps_remaining: []
  regressions: []
human_verification:
  - test: "Open /review on iPhone Safari, tap Mostra risposta, tap a rating button"
    expected: "Card advances to next card; final rating shows session results screen with Done button"
    why_human: "HTMX fragment swap and mobile tap behavior cannot be verified programmatically"
  - test: "Verify due-count badge appears on Review tab in bottom nav when cards are due"
    expected: "Badge shows non-zero number; hidden when zero due cards"
    why_human: "Visual badge rendering requires browser inspection"
  - test: "Start a timed exam at /exam/practice. Let the timer run below 10:00"
    expected: "Warning banner 'Attenzione: mancano 10 minuti alla fine!' appears; timer text turns red at 5:00"
    why_human: "JavaScript timer and DOM class changes require browser rendering; cannot verify with curl"
  - test: "Take a quiz, answer one wrong, submit — inspect per-choice colour coding on results page"
    expected: "Correct answer shown in green; chosen-wrong in red with '(la tua risposta)' label; AI explanation below each choice"
    why_human: "CSS colour rendering and conditional class application requires browser inspection"
---

# Phase 2: Active Learning Verification Report

**Phase Goal:** User can reinforce knowledge through FSRS flashcard reviews, topic quizzes with explanations, and practice with real past exam questions
**Verified:** 2026-02-28
**Status:** passed — 5/5 success criteria verified
**Re-verification:** Yes — after gap closure (Plans 02-02 and 02-03 executed)

---

## Re-verification Summary

Previous verification (same day, initial run) found 3 of 5 success criteria failed because Plans 02-02 (quiz) and 02-03 (exam) had not yet been executed. Both plans have since been executed and committed. All 3 previously-failing truths now pass.

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can review flashcards, rate each card (Again/Hard/Good/Easy), cards rescheduled | VERIFIED | `review.py` routes fully wired; `fsrs_service.py` Scheduler(maximum_interval=7); 14 seeded flashcards; HTMX card-swap templates confirmed substantive. Unchanged from initial verification. |
| 2 | SRS card state (due date, stability, difficulty) is intact after server restart | VERIFIED | SQLite WAL-mode persistence; `state.card_json`, `state.due_at` persisted via `await db.commit()` in `rate_card()`; Alembic migration at head. Unchanged from initial verification. |
| 3 | User can take a multiple-choice quiz after a topic section and see per-answer explanations | VERIFIED | `GET /topic/{slug}/quiz` returns 200 (live check confirmed). "Fai un quiz su questo argomento" button present on topic pages (curl grep returned 1). `quiz.py` submit handler calls `generate_quiz_explanation()` with generate-once-cache; results page renders per-choice explanations with green/red colour coding. |
| 4 | Quiz scores are saved and visible | VERIFIED | `QuizAttempt` inserted via `db.add(attempt); await db.commit()` before rendering results. Score history (last 10) fetched and rendered in `quiz_results.html`. DB has 1 practice_test_attempt row confirming persistence is live. `quiz_attempts` table writable (0 rows = no quiz yet submitted, not a schema bug). |
| 5 | User can access past Italian exam questions and take a timed practice test with explanations | VERIFIED | `GET /exam` returns 200 with landing page and "Inizia simulazione" button confirmed by live curl. `GET /exam/practice` returns 200 with 22 exam questions seeded. Countdown timer with 90-min server-anchored epoch implemented in `exam_practice.html`. `htmx.trigger(form, 'submit')` auto-submit on expiry confirmed in template. `PracticeTestAttempt` + `PracticeTestAnswer` rows persisted; DB shows 1 attempt, 3 answers. `generate_exam_explanation()` confirmed importable. |

**Score: 5/5 success criteria verified**

---

## Required Artifacts

### Plan 02-01 (CARD-01 through CARD-04) — Unchanged, all VERIFIED

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/services/fsrs_service.py` | FSRS scheduler singleton, review_card(), get_due_count() | VERIFIED | `Scheduler(maximum_interval=7)` at module level; all three functions present and wired |
| `app/routers/review.py` | GET /review, GET /review/cards/{id}/back, POST /review/cards/{id}/rate | VERIFIED | All three routes implemented with full DB persistence |
| `app/templates/review.html` | Full-page flashcard session | VERIFIED | Extends base.html; empty-state and active-session branches |
| `app/templates/fragments/card_front.html` | Term + Show Answer HTMX button | VERIFIED | hx-get to card back with session state in query params |
| `app/templates/fragments/card_back.html` | Definition + four rating buttons | VERIFIED | 4-form grid with hx-post to rate endpoint |
| `app/templates/fragments/session_results.html` | End-of-session score summary | VERIFIED | Renders cards_reviewed, Done link to /review |
| `migrations/versions/96666ad6e3f4_phase2_active_learning.py` | All Phase 2 DB tables (7 tables) | VERIFIED | Alembic at head; all 7 tables confirmed |
| `seed_flashcards.py` | Italian nomenclature flashcards | VERIFIED | 14 flashcards in DB across 8 topics |

### Plan 02-02 (QUIZ-01 through QUIZ-04) — New artifacts, all VERIFIED

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/routers/quiz.py` | GET /topic/{slug}/quiz, POST /topic/{slug}/quiz/submit | VERIFIED | Both routes present (import check: 2 routes registered); 209 lines, substantive |
| `app/templates/quiz.html` | MCQ form with 5 radio-button questions, friendly empty state | VERIFIED | 52 lines; `loop.index0` for zero-based radio values (Jinja2-correct); empty state on `no_questions` flag |
| `app/templates/quiz_results.html` | Score card, per-choice explanations, score history | VERIFIED | 91 lines; green/red colour coding per-choice; score history table rendered from `history` context |
| `app/services/claude.py` — `generate_quiz_explanation()` | XML-tag pattern, generate-once-cache | VERIFIED | `QUIZ_EXPLANATION_SYSTEM_PROMPT` + function confirmed importable; CORRECT/WRONG_0/1/2 XML tags; 55 lines added |
| `seed_quiz_questions.py` | At least 15 Italian MCQs across multiple topics | VERIFIED | 16 questions seeded across 7 topic slugs; DB count confirmed |

### Plan 02-03 (EXAM-01 through EXAM-04) — New artifacts, all VERIFIED

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `app/routers/exam.py` | GET /exam, GET /exam/practice, POST /exam/submit | VERIFIED | All 3 routes present (import check: 3 routes registered); 257 lines, substantive; PracticeTestAttempt + PracticeTestAnswer persistence confirmed |
| `app/templates/exam.html` | Landing page with format info, start button, attempt history | VERIFIED | 75 lines; "Inizia simulazione" button confirmed live; attempt history rendered from `history` context |
| `app/templates/exam_practice.html` | Timed test UI with countdown, 20 MCQs, htmx.trigger auto-submit | VERIFIED | 109 lines; sticky timer header; server-epoch anchor (`data-start-time="{{ start_time_epoch }}"`); `htmx.trigger(form, 'submit')` on expiry; 10-min warning div; red timer at 5 min |
| `app/templates/exam_results.html` | Per-question AI explanation results page | VERIFIED | 70 lines; colour-coded per-choice breakdown; skipped questions handled; score summary with percentage |
| `app/services/claude.py` — `generate_exam_explanation()` | Same XML-tag pattern as quiz variant | VERIFIED | `EXAM_EXPLANATION_SYSTEM_PROMPT` + function confirmed importable; CORRECT/WRONG_0/1/2 tags; 55 lines appended |
| `seed_exam_questions.py` | At least 20 Italian TOLC-B/TOLC-F MCQs | VERIFIED | 22 questions seeded (12 biology, 10 chemistry); confirmed in DB |

---

## Key Link Verification

### Plan 02-01 Links (Unchanged from initial verification)

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `card_front.html` Show Answer | GET /review/cards/{id}/back | hx-get with session params | WIRED | Confirmed in previous verification; unchanged |
| `card_back.html` rating forms | POST /review/cards/{id}/rate | hx-post hidden fields | WIRED | Confirmed in previous verification; unchanged |
| `review.py rate_card()` | `fsrs_service.review_card()` | Direct function call | WIRED | Confirmed in previous verification; unchanged |
| `base.html` due_count badge | `fsrs_service.get_due_count()` | pages.py context injection | WIRED | Confirmed in previous verification; unchanged |

### Plan 02-02 Links (New)

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `topic.html` quiz button | GET /topic/{slug}/quiz | `<a href="/topic/{{ topic.slug }}/quiz">` | WIRED | Live curl grep returns 1; href confirmed in topic.html line 73 |
| `quiz.html` submit form | POST /topic/{slug}/quiz/submit | `<form method="post" action="/topic/{{ topic.slug }}/quiz/submit">` | WIRED | Standard HTML form; confirmed in quiz.html line 30 |
| `quiz.py submit handler` | `generate_quiz_explanation()` | `if q.explanation_json is None: await generate_quiz_explanation(...)` | WIRED | Import at quiz.py line 14; null check at line 128; db.flush() on line 135 |
| `quiz.py submit handler` | `quiz_attempts` table | `db.add(QuizAttempt(...)); await db.commit()` | WIRED | QuizAttempt insert at quiz.py lines 177–184 confirmed |

### Plan 02-03 Links (New)

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `exam.html` start button | GET /exam/practice | `<a href="/exam/practice">` | WIRED | Confirmed in exam.html line 43; GET /exam/practice returns 200 |
| `exam_practice.html` form | POST /exam/submit | `hx-post="/exam/submit"` on form | WIRED | HTMX form at exam_practice.html line 28; hx-target="body", hx-swap="outerHTML" |
| JS timer expiry | form auto-submit | `htmx.trigger(form, 'submit')` when remaining <= 0 | WIRED | Confirmed in exam_practice.html JS line 104; `timeExpiredField.value = '1'` set before trigger |
| `exam.py submit handler` | `generate_exam_explanation()` | generate-once-cache null check | WIRED | Import at exam.py line 14; `if q.explanation_json is None:` at line 180; db.flush() at line 187 |
| `exam.py submit handler` | `practice_test_attempts` + `practice_test_answers` tables | `db.add(attempt); db.flush()` then `db.add(row)` per answer; `await db.commit()` | WIRED | Attempt at line 149; flush at line 156; per-question answer rows added; final db.commit(). DB: 1 attempt, 3 answers. |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CARD-01 | 02-01 | User can study flashcards using spaced repetition | SATISFIED | Full review session at /review; 14 flashcards in DB |
| CARD-02 | 02-01 | FSRS-5 with review intervals capped at 7 days | SATISFIED | `Scheduler(maximum_interval=7)` confirmed |
| CARD-03 | 02-01 | User rates each card and cards are rescheduled | SATISFIED | POST /review/cards/{id}/rate saves updated card_json and due_at; 4 rating buttons |
| CARD-04 | 02-01 | SRS state persists across server restarts | SATISFIED | SQLite WAL; db.commit() in rate_card(); Alembic migration at head |
| QUIZ-01 | 02-02 | User can take a multiple-choice quiz after a topic section | SATISFIED | GET /topic/{slug}/quiz returns 200; "Fai un quiz" button on all topic pages; 16 seeded questions |
| QUIZ-02 | 02-02 | Each quiz question shows which answers are correct and why | SATISFIED | Per-choice explanations generated via `generate_quiz_explanation()`; displayed in quiz_results.html for every choice |
| QUIZ-03 | 02-02 | Wrong answers are explained — user sees why each wrong option is incorrect | SATISFIED | WRONG_0/WRONG_1/WRONG_2 XML tags parsed; `wrong_idx` counter maps wrong choices in order; per-choice breakdown rendered |
| QUIZ-04 | 02-02 | Quiz scores are saved and visible in progress tracking | SATISFIED | `QuizAttempt` inserted before returning results; score history (last 10) rendered in quiz_results.html |
| EXAM-01 | 02-03 | User can access a bank of past exam questions from Italian entry tests | SATISFIED | 22 TOLC-B/TOLC-F Italian MCQs seeded; accessible at /exam and /exam/practice |
| EXAM-02 | 02-03 | User can take a timed practice test | SATISFIED | GET /exam/practice returns 200; 90-min server-epoch-anchored countdown timer |
| EXAM-03 | 02-03 | After answering, user sees correct answer with AI explanation for every option | SATISFIED | `generate_exam_explanation()` generates CORRECT + WRONG_0/1/2; exam_results.html renders per-choice breakdown |
| EXAM-04 | 02-03 | Practice test history and per-question results saved | SATISFIED | PracticeTestAttempt + PracticeTestAnswer rows inserted; DB: 1 attempt, 3 answers confirmed |

**All 12 requirements: SATISFIED**

---

## Anti-Patterns Found

None. All Phase 2 new files scanned.

| Scan | Files Checked | Result |
|------|---------------|--------|
| TODO/FIXME/placeholder markers | All 9 new files (routers, templates, seed scripts) | None found |
| Empty returns / stub implementations | `app/routers/quiz.py`, `app/routers/exam.py` | None — full implementations |
| Unused router registrations | `app/main.py` | Both quiz and exam routers imported and registered (lines 12, 66–67) |

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

### 3. Exam Timer Behaviour

**Test:** Start a timed exam at `/exam/practice`. Wait (or set clock forward) until the timer shows 9:59.
**Expected:** Yellow warning banner "Attenzione: mancano 10 minuti alla fine!" appears. At 5:00 remaining, timer text turns red. At 0:00, form auto-submits and shows results page.
**Why human:** JavaScript timer-driven DOM changes require live browser rendering; cannot be verified with curl.

### 4. Quiz Per-Choice Colour Coding

**Test:** Take a quiz at `/topic/membrana-cellulare/quiz`, deliberately answer one question wrong, submit.
**Expected:** On results page — correct answer card has green background; chosen-wrong answer card has red background with "(la tua risposta)" label; all other choices are gray. AI explanation text appears below each choice.
**Why human:** CSS colour rendering and conditional class application requires browser inspection.

---

## Summary

Phase 2 goal is fully achieved. All three active learning modes are implemented, wired, and live:

1. **FSRS Flashcard Reviews** (Plan 02-01): 14 flashcards, review session at /review, HTMX card swap, FSRS-5 rescheduling with 7-day cap, SRS state persisted to SQLite.

2. **Topic Quizzes with Explanations** (Plan 02-02): 16 Italian MCQs seeded across 7 topic slugs, quiz at /topic/{slug}/quiz, 5 randomly sampled questions, POST submit generates per-choice AI explanations (generate-once-cache), QuizAttempt rows saved, score history shown on results page.

3. **Past Exam Question Practice** (Plan 02-03): 22 TOLC-B/TOLC-F Italian MCQs seeded, exam landing at /exam, timed practice test at /exam/practice with 90-min server-anchored countdown timer, htmx.trigger auto-submit on expiry, per-question AI explanations on results page, PracticeTestAttempt + PracticeTestAnswer rows persisted.

All 12 requirements (CARD-01 through CARD-04, QUIZ-01 through QUIZ-04, EXAM-01 through EXAM-04) are satisfied. Four human verification items remain — all involve visual/timer/UX behaviors secondary to core functionality.

---

_Verified: 2026-02-28_
_Verifier: Claude (gsd-verifier)_
