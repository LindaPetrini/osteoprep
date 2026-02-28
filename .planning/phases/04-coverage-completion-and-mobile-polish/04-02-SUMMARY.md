---
phase: 04-coverage-completion-and-mobile-polish
plan: "02"
subsystem: database
tags: [sqlite, mcq, quiz, italian, biology, chemistry, physics, seeding]

# Dependency graph
requires:
  - phase: 04-01
    provides: topic rows for all 39 topics including 10 physics/math topics and mitocondri orphan fix
provides:
  - 231 Italian MCQ quiz questions covering all 40 topics (biology, chemistry, physics/math)
  - Every topic in the app now has >= 5 questions and a working /topic/{slug}/quiz endpoint
affects:
  - quiz router (quiz_questions table now fully populated)
  - exam router (exam question pool extended)
  - progress dashboard (more topics have quiz history potential)

# Tech tracking
tech-stack:
  added: []
  patterns: [dedup-seed-by-topic-slug-and-question-it]

key-files:
  created: []
  modified:
    - seed_quiz_questions.py

key-decisions:
  - "cellula-eucariotica (0 questions before plan) covered via Rule 2 auto-fix — plan listed 14 bio/chem topics but this topic was also at 0"
  - "Topics with 1-3 existing questions (membrana-cellulare, nucleo-cellulare, dna-rna-proteine, legami-chimici, acidi-basi-ph, reazioni-chimiche, mitocondri) topped up to 5+ for quiz variety"
  - "5-8 questions written per topic (quiz router samples up to 5 randomly — extra questions provide variety on repeat attempts)"

patterns-established:
  - "Seed script dedup pattern: skip INSERT if same (topic_slug, question_it) exists — safe to re-run"

requirements-completed: [QUIZ-01]

# Metrics
duration: 8min
completed: 2026-02-28
---

# Phase 4 Plan 02: Quiz Question Seeding Summary

**231 Italian MCQs (5-8 per topic) seeded across all 40 biology/chemistry/physics topics, giving every /topic/{slug}/quiz endpoint a working quiz**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-02-28T20:11:00Z
- **Completed:** 2026-02-28T20:19:14Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments

- All 40 topics now have >= 5 Italian MCQ questions (5-8 each), enabling quiz variety on repeat attempts
- 231 total questions inserted (215 new + 16 already existed from previous seeds)
- Physics/math topics covered: grandezze-fisiche, cinematica, dinamica, meccanica-fluidi, termodinamica, elettromagnetismo, algebra-aritmetica, funzioni, geometria, probabilita-statistica — all with 6-7 questions
- Biology and chemistry topics fully covered including previously-zero topics: mitosi-meiosi, respirazione-cellulare, fotosintesi, genetica-mendeliana, evoluzione-selezione, sistema-nervoso, tessuti-animali, sistemi-organo, virus-procarioti, biotecnologie-dna, atomo-struttura, tavola-periodica, ossidoriduzione, carboidrati, lipidi, proteine-struttura, enzimi, soluzioni-proprieta, equilibrio-chimico, nomenclatura-inorganica, chimica-organica

## Task Commits

Each task was committed atomically:

1. **Tasks 1 + 2: Add MCQ questions for all biology, chemistry and physics topics** - `de74105` (feat)

**Plan metadata:** (see final commit below)

## Files Created/Modified

- `/home/linda/projects/osteoprep/seed_quiz_questions.py` - Extended QUESTIONS list from 16 existing entries to 231 total; covers all 40 topics with 5-8 Italian MCQs each; seed() function and dedup logic unchanged

## Decisions Made

- `cellula-eucariotica` had 0 questions (not listed in plan's 14-topic list) — added 6 questions as Rule 2 auto-fix (missing critical: no quiz = broken /quiz endpoint for that topic)
- Topics with 1-3 existing questions topped up to 5+ so the quiz router's "sample 5 randomly" always works with full variety
- 5-8 questions written per topic (not exactly 5) to allow variety on re-attempts

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added questions for cellula-eucariotica**
- **Found during:** Task 1 (database scan before writing questions)
- **Issue:** cellula-eucariotica had 0 questions but was not in the plan's 14-topic list — /topic/cellula-eucariotica/quiz would 404 or return empty
- **Fix:** Wrote 6 Italian MCQ questions covering cell organelles, endoplasmic reticulum, lysosomes, cytoskeleton, Golgi apparatus, and mitochondria as eukaryote-specific organelles
- **Files modified:** seed_quiz_questions.py
- **Verification:** Final coverage check shows cellula-eucariotica: 6 OK
- **Committed in:** de74105 (task commit)

---

**Total deviations:** 1 auto-fixed (Rule 2 missing critical)
**Impact on plan:** Essential fix — cellula-eucariotica would have been the only topic with a broken quiz. No scope creep.

## Issues Encountered

None — seed script ran cleanly with no FK constraint errors. All topic slugs matched existing rows from 04-01.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 4 is now complete: topics seeded (04-01), quiz questions seeded (04-02), mobile polish applied (04-01)
- All 40 topics have working quizzes at /topic/{slug}/quiz
- 231 total questions in quiz_questions table; explanation_json remains NULL and is generated on first quiz submission via existing generate-once-cache pattern
- The app is ready for exam use

---
*Phase: 04-coverage-completion-and-mobile-polish*
*Completed: 2026-02-28*
