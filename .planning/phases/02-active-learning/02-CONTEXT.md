# Phase 2: Active Learning - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning

<domain>
## Phase Boundary

User can reinforce knowledge through three distinct active learning modes:
1. FSRS-5 spaced repetition flashcard reviews (nomenclature cards, 7-day interval cap)
2. Topic quizzes (multiple-choice, AI-generated explanations per answer choice)
3. Past exam question practice (timed, Italian med entrance format)

No new explainer topics, no progress dashboard (Phase 3), no AI chat (Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Navigation structure
- Add a persistent **bottom nav bar with 3 tabs**: Topics | Review | Exam
- "Topics" tab contains the existing subject accordion (current home page)
- "Review" tab is the flashcard review queue
- "Exam" tab is the practice exam entry point
- The base layout (`base.html`) gains the bottom nav; existing topic pages are unchanged except for the quiz button addition

### Due-count visibility
- A numeric badge on the **Review tab** shows cards due today (e.g. "7")
- Badge is hidden when count is zero — no guilt when caught up
- Count is rendered server-side on each page load (no HTMX polling needed)

### Quiz entry point
- A **"Take a quiz" button** appears at the bottom of every topic page, after the explainer content
- Tapping it navigates to `/topic/{slug}/quiz` (full page, not inline fragment)
- Quiz is always available regardless of whether the user has read the explainer

### Session completion
- After a flashcard session or quiz: show a **results screen** (score, cards reviewed, next due date)
- Results screen has a single "Done" button that returns to the previous context (topic page or Review tab)
- No auto-redirect; user controls when to leave

### Flashcard reveal interaction
- Cards show the **front (term)** first
- A **"Show Answer" button** reveals the back (definition/explanation) — no tap-to-flip
- Rationale: tap-to-flip is ambiguous with scroll on mobile; explicit button is clearer
- After reveal, four rating buttons appear below the card: **Again | Hard | Good | Easy**
- Buttons are large (min 44px tap target), full-width row

### Flashcard session length
- **All due cards** are shown per session (no artificial cap)
- FSRS 7-day interval cap keeps the queue manageable; no need to paginate it further
- Session progress shown as "Card 4 of 12" at top

### Quiz format
- **5 questions per topic quiz**, randomly sampled from available questions for that topic
- All 4 answer choices shown; one correct
- After each answer: **immediate feedback** — show whether correct/incorrect + AI explanation for all choices (why correct is right, why each wrong option is wrong)
- Retakes always allowed; no lockout
- Quiz score (best attempt) saved to DB per topic per user session

### Exam question bank
- Seed the DB with **20 placeholder Italian-language MCQs** covering Biology and Chemistry (matching seed topics)
- Questions tagged with subject, topic slug (optional), and source year (nullable)
- Schema designed for easy bulk import: a `seed_exam_questions.py` script with well-documented CSV format
- Timed practice test: **60 questions / 90 minutes** (close to official MUR/TOLC-MED format)
- Visible countdown timer in the sticky header during exam
- **Auto-submit** when timer hits zero (matches real exam conditions)
- Warning shown at 10 minutes remaining
- Results: per-question breakdown with AI-generated explanation shown after submission

### Language
- All quiz and exam content in **Italian** (primary language for exam prep)
- Flashcard fronts/backs in Italian, with optional English shown as secondary if the topic has EN content
- UI chrome (buttons, labels) in Italian to match existing app language

### Claude's Discretion
- Exact FSRS-5 parameter initialization (use standard defaults: stability=1, difficulty=5, etc.)
- Card front/back content generation strategy (derive from existing topic content vs. separate Claude call)
- Database schema details for SRS state (due_date, stability, difficulty, reps, lapses)
- CSS animation choice for card reveal (simple show/hide vs. subtle fade)
- Exact DaisyUI components used (progress bar for session, badge for due count, etc.)
- How to handle zero-question state (no quiz questions seeded for a topic yet)
- Bottom nav bar icon choices

</decisions>

<specifics>
## Specific Ideas

- "You choose what's best" — full discretion delegated to Claude on all implementation decisions
- The 7-day interval cap is an explicit product requirement (CARD-02), not a technical default — must be enforced in the FSRS scheduling logic
- Exam questions should feel authentic to Italian medicina/professioni sanitarie entrance tests: Biology, Chemistry, Physics, Logic, General Culture
- Placeholder seed data should be realistic enough to demo the feature end-to-end

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `base.html`: 560px container, mobile-first layout — needs bottom nav bar added (and body padding-bottom to avoid content hidden behind it)
- `Topic` model (`app/models.py`): existing SQLAlchemy async pattern to follow for new models (Flashcard, SRSState, QuizQuestion, ExamQuestion, etc.)
- `generate_explainer()` in `app/services/claude.py`: XML-tag-based Claude call pattern — reuse for quiz explanation generation
- `app/routers/pages.py` + `app/routers/fragments.py`: established router split (full pages vs HTMX fragments) — new routes follow same pattern
- `templates_config.py`: Jinja2 env with markdown-it filter — available for rendering explanation markdown in quiz/exam results

### Established Patterns
- **Generate-once-cache**: check DB first, call Claude only when content IS NULL — apply same pattern to AI-generated quiz explanations
- **HTMX fragment endpoints**: `/subjects/{subject}/topics` and `/topic/{slug}/content` — follow same pattern for quiz submission and card rating
- **Async SQLAlchemy**: all DB access via `AsyncSession` + `async with AsyncSessionLocal()` — must be followed for all new DB operations
- **Background generation with semaphore**: pattern in `pages.py` `_generating` set — reusable if quiz explanation generation is async
- **Alembic migrations**: all schema changes via migration files (not `create_all`)

### Integration Points
- `base.html` — add bottom nav bar HTML + `pb-16` (or similar) to body to prevent content hidden behind fixed nav
- `app/main.py` — register new routers (flashcard router, quiz router, exam router)
- `app/models.py` — add new ORM models (keep in same file or split to `models/` package)
- `migrations/` — new Alembic revision for Phase 2 schema (Flashcard, SRSState, QuizQuestion, ExamQuestion, PracticeTestAttempt tables)
- `seed_topics.py` — pattern reference for new `seed_exam_questions.py`

</code_context>

<deferred>
## Deferred Ideas

- None surfaced — user delegated all decisions to Claude, discussion stayed within phase scope

</deferred>

---

*Phase: 02-active-learning*
*Context gathered: 2026-02-28*
