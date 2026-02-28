# Phase 2: Active Learning - Research

**Researched:** 2026-02-28
**Domain:** FSRS spaced repetition, quiz/exam MCQ UI, HTMX form patterns, SQLAlchemy schema extension, Claude AI quiz generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Navigation structure**
- Add a persistent bottom nav bar with 3 tabs: Topics | Review | Exam
- "Topics" tab contains the existing subject accordion (current home page)
- "Review" tab is the flashcard review queue
- "Exam" tab is the practice exam entry point
- The base layout (`base.html`) gains the bottom nav; existing topic pages are unchanged except for the quiz button addition

**Due-count visibility**
- A numeric badge on the Review tab shows cards due today (e.g. "7")
- Badge is hidden when count is zero — no guilt when caught up
- Count is rendered server-side on each page load (no HTMX polling needed)

**Quiz entry point**
- A "Take a quiz" button appears at the bottom of every topic page, after the explainer content
- Tapping it navigates to `/topic/{slug}/quiz` (full page, not inline fragment)
- Quiz is always available regardless of whether the user has read the explainer

**Session completion**
- After a flashcard session or quiz: show a results screen (score, cards reviewed, next due date)
- Results screen has a single "Done" button that returns to the previous context (topic page or Review tab)
- No auto-redirect; user controls when to leave

**Flashcard reveal interaction**
- Cards show the front (term) first
- A "Show Answer" button reveals the back (definition/explanation) — no tap-to-flip
- After reveal, four rating buttons appear below the card: Again | Hard | Good | Easy
- Buttons are large (min 44px tap target), full-width row

**Flashcard session length**
- All due cards are shown per session (no artificial cap)
- FSRS 7-day interval cap keeps the queue manageable
- Session progress shown as "Card 4 of 12" at top

**Quiz format**
- 5 questions per topic quiz, randomly sampled
- All 4 answer choices shown; one correct
- After each answer: immediate feedback — show whether correct/incorrect + AI explanation for all choices
- Retakes always allowed; no lockout
- Quiz score (best attempt) saved to DB per topic per user session

**Exam question bank**
- Seed the DB with 20 placeholder Italian-language MCQs covering Biology and Chemistry
- Questions tagged with subject, topic slug (optional), and source year (nullable)
- Schema designed for easy bulk import: a `seed_exam_questions.py` script with well-documented CSV format
- Timed practice test: 60 questions / 90 minutes
- Visible countdown timer in the sticky header during exam
- Auto-submit when timer hits zero
- Warning shown at 10 minutes remaining
- Results: per-question breakdown with AI-generated explanation shown after submission

**Language**
- All quiz and exam content in Italian
- Flashcard fronts/backs in Italian, with optional English shown as secondary
- UI chrome (buttons, labels) in Italian to match existing app language

### Claude's Discretion
- Exact FSRS-5 parameter initialization (use standard defaults: stability=1, difficulty=5, etc.)
- Card front/back content generation strategy (derive from existing topic content vs. separate Claude call)
- Database schema details for SRS state (due_date, stability, difficulty, reps, lapses)
- CSS animation choice for card reveal (simple show/hide vs. subtle fade)
- Exact DaisyUI components used (progress bar for session, badge for due count, etc.)
- How to handle zero-question state (no quiz questions seeded for a topic yet)
- Bottom nav bar icon choices

### Deferred Ideas (OUT OF SCOPE)
- None surfaced — user delegated all decisions to Claude, discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QUIZ-01 | User can take a multiple-choice quiz after completing a topic section | "Take a quiz" button at bottom of topic page → `/topic/{slug}/quiz`; quiz page/fragment pattern established |
| QUIZ-02 | Each quiz question shows which answers are correct and why (AI-generated explanation per answer choice) | Claude generate-once-cache pattern; XML tag parsing; `QuizQuestion.explanation_it` JSON blob field |
| QUIZ-03 | Wrong answers are explained — user sees why each wrong option is incorrect | Same as QUIZ-02; explanation JSON stores per-choice rationale |
| QUIZ-04 | Quiz scores are saved and visible in progress tracking | `QuizAttempt` model (topic_slug, score, attempt_at); best-score query in progress phase |
| CARD-01 | User can study flashcards for nomenclature using spaced repetition | py-fsrs 6.3.0; `Flashcard` + `SRSState` models; Review tab in bottom nav |
| CARD-02 | SRS uses FSRS algorithm with review intervals capped at 7 days | `Scheduler(maximum_interval=7)` — confirmed available in py-fsrs |
| CARD-03 | User rates each card (Again / Hard / Good / Easy) and cards are rescheduled accordingly | `Rating.Again/Hard/Good/Easy`; HTMX POST to `/review/cards/{id}/rate`; scheduler.review_card() |
| CARD-04 | SRS state (due date, stability, difficulty) persists across server restarts | Card state stored in `srs_states` DB table (Text/JSON column); Card.to_json()/from_json() |
| EXAM-01 | User can access a bank of past exam questions | `ExamQuestion` model; seed script; `/exam` page listing available practice tests |
| EXAM-02 | User can take a timed practice test from the question bank | 60Q/90min; countdown timer in vanilla JS; auto-submit via htmx.trigger(); `/exam/start` + `/exam/submit` |
| EXAM-03 | After answering, user sees correct answer with AI-generated explanation | Claude generate-once-cache on explanation fields; results page after submit |
| EXAM-04 | User's practice test history and per-question results are saved | `PracticeTestAttempt` + `PracticeTestAnswer` models; persist before showing results |
</phase_requirements>

---

## Summary

Phase 2 introduces three active learning modes on top of the existing Phase 1 FastAPI/HTMX/DaisyUI stack. The technology choices are straightforward extensions of what already exists: py-fsrs 6.3.0 (pip install fsrs) for FSRS scheduling, the existing Anthropic `claude-haiku-4-5-20251001` model for quiz/exam explanations using the established generate-once-cache pattern, and DaisyUI's dock component for the bottom navigation bar. All three modes share the same SQLAlchemy async pattern and Alembic migration workflow established in Phase 1.

The most important implementation decision is the **7-day interval cap**: this is configured at `Scheduler(maximum_interval=7)` in py-fsrs — a first-class parameter, not a workaround. The library now ships as FSRS-6 (v6.3.0, October 2025) rather than FSRS-5, but the API is backward-compatible for the purposes of this project. SRS card state should be stored as a JSON Text column in SQLite (using `Card.to_json()`) rather than normalised columns, since py-fsrs's internal fields change between versions and JSON storage is the library's own recommended persistence pattern.

The countdown timer for the exam is the only component requiring meaningful client-side JavaScript — a small `setInterval` loop that submits the exam form via `htmx.trigger()` when the timer reaches zero. Everything else uses standard HTMX patterns (hx-post for quiz answer submission, hx-get for fragment loads). The exam question source context is important: TOLC-MED for Italian medicine was abolished in 2025; the target exam is now either the remaining TOLC variants (TOLC-B, TOLC-F) for professioni sanitarie, or the osteopathy-specific test format. The 20 placeholder seed questions should authentically reflect the professioni sanitarie Biology/Chemistry MCQ style, which uses 4 answer choices in Italian.

**Primary recommendation:** Use `Scheduler(maximum_interval=7)` from py-fsrs 6.3.0, store card state as JSON in a Text column, generate quiz/exam explanations with the same Claude pattern as explainers (XML tags, generate-once-cache), and use DaisyUI's `dock` component for bottom nav.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fsrs (py-fsrs) | 6.3.0 | FSRS spaced repetition scheduling | Official Python implementation; `maximum_interval` param; JSON serialization built-in |
| FastAPI | 0.115.14 | Backend framework (existing) | Already in project |
| HTMX | 2.0.4 | Hypermedia-driven UI updates (existing) | Already in project |
| DaisyUI | bundled (min.css) | Component library (existing) | Already in project |
| SQLAlchemy async | 2.0.47 | ORM with async sessions (existing) | Already in project |
| Alembic | 1.18.4 | Database migrations (existing) | Already in project |
| Anthropic SDK | 0.84.0 | Claude API for quiz/exam explanations (existing) | Already in project |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 (stdlib) | stdlib | Seed script for exam questions | seed_exam_questions.py — same pattern as seed_topics.py |
| json (stdlib) | stdlib | Card state serialization | Storing Card.to_json() output in DB Text column |
| datetime + timezone.utc | stdlib | FSRS requires UTC datetimes | All SRS due/review timestamps must be UTC |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| py-fsrs JSON storage | Individual columns (stability, difficulty, due, state) | Columns break when py-fsrs internals change; JSON storage is forward-compatible and library-recommended |
| Plain JS setInterval timer | Alpine.js | Alpine adds ~15KB CDN dependency for one timer; plain JS is simpler and we have no other Alpine uses |
| DaisyUI dock | Custom fixed bottom bar | Dock is purpose-built for this; saves CSS debugging on mobile safe-area-inset |

**Installation:**
```bash
pip install fsrs==6.3.0
```

Add to requirements.txt: `fsrs==6.3.0`

---

## Architecture Patterns

### Recommended Project Structure

```
app/
├── models.py              # Add: Flashcard, SRSState, QuizQuestion, QuizAttempt,
│                          #       ExamQuestion, PracticeTestAttempt, PracticeTestAnswer
├── routers/
│   ├── pages.py           # Existing + add quiz page, exam page routes
│   ├── fragments.py       # Existing + add quiz submit, card rate fragments
│   ├── review.py          # NEW: flashcard review session routes
│   ├── quiz.py            # NEW: topic quiz routes
│   └── exam.py            # NEW: practice exam routes
├── services/
│   ├── claude.py          # Existing + add generate_quiz_questions(), generate_exam_explanation()
│   └── fsrs_service.py    # NEW: Scheduler init, review_card wrapper, due count query
├── templates/
│   ├── base.html          # MODIFY: add dock nav, pb-20 on body container
│   ├── topic.html         # MODIFY: add "Take a quiz" button at bottom
│   ├── review.html        # NEW: flashcard session page
│   ├── quiz.html          # NEW: topic quiz page
│   ├── exam.html          # NEW: exam page (question display + timer)
│   ├── exam_results.html  # NEW: per-question results after exam submit
│   └── fragments/
│       ├── card_front.html      # NEW: card front + Show Answer button
│       ├── card_back.html       # NEW: card back + 4 rating buttons
│       ├── quiz_question.html   # NEW: question + choices
│       ├── quiz_feedback.html   # NEW: correct/incorrect + explanations
│       └── session_results.html # NEW: end-of-session score screen
migrations/
└── versions/
    └── {hash}_phase2_active_learning.py   # NEW: all Phase 2 tables
seed_exam_questions.py   # NEW: seed script, CSV import pattern
```

### Pattern 1: FSRS Service — Scheduler with 7-Day Cap

**What:** A singleton-style Scheduler instance configured with `maximum_interval=7`. All card reviews route through this single object.
**When to use:** Every flashcard rating action, due-count queries.

```python
# app/services/fsrs_service.py
from fsrs import Scheduler, Card, Rating
from datetime import datetime, timezone

# Module-level singleton — stateless scheduler, safe to share
_scheduler = Scheduler(
    desired_retention=0.9,
    maximum_interval=7,   # PRODUCT REQUIREMENT: keep within exam study window
    enable_fuzzing=False  # Deterministic for small queue
)

def review_card(card_json: str, rating: Rating) -> tuple[str, datetime]:
    """
    Apply a review rating to a card.
    Returns (updated_card_json, due_date_utc).
    """
    card = Card.from_json(card_json)
    card, _review_log = _scheduler.review_card(card, rating)
    return card.to_json(), card.due

def new_card_json() -> str:
    """Create a new Card and return its JSON for DB storage."""
    return Card().to_json()

async def get_due_count(db: AsyncSession) -> int:
    """Count flashcards due now (for badge on Review tab)."""
    now = datetime.now(timezone.utc)
    result = await db.execute(
        select(func.count()).select_from(SRSState)
        .where(SRSState.due_at <= now)
    )
    return result.scalar_one()
```

### Pattern 2: Card State Storage in DB

**What:** Store the entire `Card.to_json()` blob in a Text column alongside the extracted `due_at` datetime for efficient querying. The JSON blob is the source of truth for FSRS state; `due_at` is a denormalized index for the due-count query.
**When to use:** All flashcard models.

```python
# In app/models.py
class SRSState(Base):
    __tablename__ = "srs_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flashcard_id: Mapped[int] = mapped_column(Integer, ForeignKey("flashcards.id"), nullable=False, index=True)
    card_json: Mapped[str] = mapped_column(Text, nullable=False)  # Card.to_json() blob
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)  # denormalized for query
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
```

### Pattern 3: Generate-Once-Cache for Quiz/Exam Explanations

**What:** Extend the existing `generate_explainer()` pattern. Before calling Claude, check if `explanation_it` is already non-NULL in the DB. If NULL, call Claude with an XML-tagged prompt and store the result.
**When to use:** Quiz question explanation generation, exam question explanation generation.

```python
# app/services/claude.py (additions)
QUIZ_EXPLANATION_SYSTEM_PROMPT = """Sei un assistente per esami italiani.
Per una domanda a risposta multipla fornisci spiegazioni in italiano.

OUTPUT FORMAT — usa questi tag XML, nient'altro:
<CORRECT>
[Perché questa risposta è corretta — 2-3 frasi]
</CORRECT>
<WRONG_A>
[Perché l'opzione A è sbagliata — 1-2 frasi]
</WRONG_A>
<WRONG_B>[...]</WRONG_B>
<WRONG_C>[...]</WRONG_C>"""

async def generate_quiz_explanation(question_text: str, choices: list[str], correct_idx: int) -> dict[str, str]:
    """
    Returns {"correct": "...", "wrong_0": "...", "wrong_1": "...", "wrong_2": "..."}
    """
    # ... XML parse pattern identical to generate_explainer()
```

### Pattern 4: HTMX Fragment for Card Rating

**What:** Card flip and rating are HTMX fragment swaps, not full page loads. The card back + rating buttons form POSTs to `/review/cards/{id}/rate`, which returns either the next card fragment or the session results fragment.
**When to use:** Every flashcard review interaction.

```python
# app/routers/review.py
@router.post("/review/cards/{srs_state_id}/rate", response_class=HTMLResponse)
async def rate_card(
    request: Request,
    srs_state_id: int,
    rating: int = Form(...),   # 1=Again, 2=Hard, 3=Good, 4=Easy
    session_remaining: int = Form(...),  # hidden field: count of remaining card IDs
    db: AsyncSession = Depends(get_db),
):
    # 1. Load SRSState, apply rating via fsrs_service.review_card()
    # 2. Save updated card_json + due_at to DB
    # 3. If session_remaining > 0: return next card fragment
    # 4. If session_remaining == 0: return session results fragment
```

### Pattern 5: Exam Countdown Timer (Vanilla JS)

**What:** A small `setInterval` in a `<script>` block on the exam page. When the timer reaches zero, it calls `htmx.trigger('#exam-form', 'submit')` to programmatically submit the exam form. A warning div is made visible at 10-minute mark.
**When to use:** Only on the exam page.

```html
<!-- In exam.html — timer block at end of page -->
<script>
(function() {
  const DURATION_SECONDS = 90 * 60;  // 90 minutes
  let remaining = DURATION_SECONDS;
  const timerEl = document.getElementById('exam-timer');
  const warningEl = document.getElementById('exam-warning');

  const interval = setInterval(() => {
    remaining--;
    const m = Math.floor(remaining / 60);
    const s = remaining % 60;
    timerEl.textContent = `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;

    if (remaining === 600) {  // 10 minutes
      warningEl.classList.remove('hidden');
    }
    if (remaining <= 0) {
      clearInterval(interval);
      // Use htmx.trigger for reliable programmatic submission
      htmx.trigger(document.getElementById('exam-form'), 'submit');
    }
  }, 1000);
})();
</script>
```

### Pattern 6: Bottom Nav with DaisyUI Dock

**What:** DaisyUI `dock` component added to `base.html`, rendered as a fixed bottom bar. Active tab is determined server-side via `active_tab` context variable. Due-count badge rendered server-side.
**When to use:** All pages after Phase 2.

```html
<!-- In base.html — before closing </body> -->
<div class="dock dock-bottom">
  <a href="/" class="{% if active_tab == 'topics' %}dock-active{% endif %}">
    <svg><!-- book icon --></svg>
    <span class="dock-label">Argomenti</span>
  </a>

  <a href="/review" class="{% if active_tab == 'review' %}dock-active{% endif %} relative">
    <svg><!-- cards icon --></svg>
    <span class="dock-label">Ripasso</span>
    {% if due_count > 0 %}
    <span class="badge badge-primary badge-xs absolute -top-1 -right-1">{{ due_count }}</span>
    {% endif %}
  </a>

  <a href="/exam" class="{% if active_tab == 'exam' %}dock-active{% endif %}">
    <svg><!-- clipboard icon --></svg>
    <span class="dock-label">Esame</span>
  </a>
</div>
```

**IMPORTANT:** `base.html` content div needs `pb-20` (or `padding-bottom: 5rem`) added to prevent content being hidden behind the dock. Also requires `viewport-fit=cover` in the meta viewport tag for iPhone safe area — already present in base.html.

### Anti-Patterns to Avoid

- **Storing FSRS state as individual columns (stability, difficulty, reps, lapses, state):** These fields change between py-fsrs major versions. The `card_json` Text column approach is library-recommended and version-safe. Only `due_at` should be denormalized for indexing.
- **Creating a new Scheduler instance per request:** Scheduler is stateless and safe to share. Create once at module import.
- **Using `dispatchEvent()` instead of `htmx.trigger()` for exam auto-submit:** `dispatchEvent` only works once with HTMX; `htmx.trigger()` is the correct API for programmatic HTMX requests.
- **Calling Claude for quiz explanations on every quiz attempt:** Generate once, cache in DB (same as explainer pattern). Quiz explanations are deterministic per question — no need to regenerate.
- **Using `Base.metadata.create_all` for Phase 2 tables:** The project uses Alembic; always create a migration revision. `create_all` is present in `main.py` only as a fallback for development.
- **Polling for due count:** Due count is cheap (single COUNT query) and rendered server-side on each page load per the decision — no HTMX polling needed.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FSRS scheduling algorithm | Custom SM-2 or forgetting curve math | `fsrs` (py-fsrs 6.3.0) | FSRS-6 algorithm has 21 parameters tuned on 20M reviews; interval cap is a first-class feature |
| Interval cap enforcement | Custom clamp after scheduling | `Scheduler(maximum_interval=7)` | Built-in parameter; applying a clamp AFTER scheduling breaks the algorithm's stability model |
| Card JSON serialization | Custom dict serialization | `Card.to_json()` / `Card.from_json()` | Library handles all internal field names correctly; custom code breaks on upgrades |
| Countdown timer library | React/Vue component | Vanilla JS `setInterval` + `htmx.trigger()` | Project has no JS build step; 20 lines of plain JS is sufficient |
| Per-choice MCQ explanation storage | Custom parsing per response | JSON blob in `explanation_json` Text column | Stores `{"correct": "...", "wrong_a": "...", "wrong_b": "...", "wrong_c": "..."}` as a single field |

**Key insight:** py-fsrs does ALL the hard scheduling math. The application layer only needs to: (1) call `scheduler.review_card(card, rating)`, (2) save the updated `card.to_json()` and `card.due` to the database, and (3) query `due_at <= now()` to find cards due.

---

## Common Pitfalls

### Pitfall 1: FSRS requires UTC datetimes — naive datetimes silently produce wrong results
**What goes wrong:** FSRS scheduling calculations break if `datetime.now()` (naive) is passed instead of `datetime.now(timezone.utc)` (timezone-aware). Cards may schedule in the past or far future.
**Why it happens:** Python's `datetime.now()` returns a naive datetime; SQLite also stores datetimes as strings without timezone info.
**How to avoid:** Always use `datetime.now(timezone.utc)` in all SRS-related code. When reading `due_at` back from SQLite, ensure it's compared against UTC.
**Warning signs:** Cards appear due immediately after review, or never appear due.

### Pitfall 2: The 7-day cap is set on the Scheduler, not applied as a post-hoc clamp
**What goes wrong:** If code applies `min(scheduled_interval, 7)` after calling `scheduler.review_card()`, it overrides the scheduler's stability model, causing cards to be rescheduled incorrectly on future reviews.
**Why it happens:** Developers assume interval cap = truncate the output.
**How to avoid:** Set `Scheduler(maximum_interval=7)` once at module load. Never touch the interval after the scheduler returns the card.
**Warning signs:** Card stability values increase correctly but intervals always seem too aggressive.

### Pitfall 3: base.html content hidden behind dock
**What goes wrong:** The last few items in topic/quiz pages are hidden behind the 64px dock bar. Users can't tap the "Show Answer" or "Done" buttons.
**Why it happens:** The dock is `position: fixed` at bottom; the content container needs bottom padding.
**How to avoid:** Add `padding-bottom: 5rem` (or `pb-20`) to the content container div in `base.html`. Also add `padding-bottom: env(safe-area-inset-bottom)` for iPhone notch.
**Warning signs:** Review visible during development on desktop but buttons cut off on iPhone.

### Pitfall 4: Tailwind purged CSS — new classes silently don't apply
**What goes wrong:** Adding new DaisyUI/Tailwind classes in templates (like `dock`, `dock-active`, `dock-label`) has no visual effect because the bundled `tailwind.min.css` is pre-compiled and doesn't include new utility classes.
**Why it happens:** The project uses a pre-compiled static `tailwind.min.css`, not a JIT build.
**How to avoid:** Use DaisyUI semantic class names (which are already in `daisyui.min.css`) rather than Tailwind utilities for new components. For layout changes (like padding), use inline `style=""` attributes — this is already the established pattern in the project (see `base.html` content div: `style="max-width: 560px; margin: 0 auto; padding: 1rem 1.5rem;"`).
**Warning signs:** CSS class applied in template but no visual change on page.

### Pitfall 5: Quiz question availability — topics may have zero seeded questions
**What goes wrong:** Navigating to `/topic/{slug}/quiz` when no `QuizQuestion` rows exist for that topic results in an empty quiz or a 500 error.
**Why it happens:** Quiz questions require a separate seed/generation step that hasn't run yet.
**How to avoid:** The quiz page handler must check `len(questions) == 0` and return a "Nessuna domanda disponibile per questo argomento" empty state, with a friendly message. Do NOT raise 404 — the topic exists, just no questions yet.
**Warning signs:** Empty white page or traceback on first quiz attempt.

### Pitfall 6: Exam auto-submit fires before page is fully rendered
**What goes wrong:** The `setInterval` starts immediately on page load, but if page rendering takes 2-3 seconds on a slow connection, the timer runs fast.
**Why it happens:** Timer starts at `DOMContentLoaded`, which fires after the 90-minute clock should start from the server's perspective.
**How to avoid:** Embed the exam start timestamp (UTC epoch seconds) in the page as a `data-` attribute on the form. Calculate remaining time as `start_time + duration - now` on each tick.
**Warning signs:** Users on slow connections get less than 90 minutes of exam time.

### Pitfall 7: Claude quiz generation — ensure Italian language output
**What goes wrong:** Claude generates quiz questions in English even when the topic title is in Italian.
**Why it happens:** Default Claude behavior tends toward English.
**How to avoid:** Add explicit Italian instruction to the system prompt. Use the topic's `title_it` (not `title_en`) in the user message. Validate output has Italian characters (e.g., contains accented letters or common Italian words).
**Warning signs:** Quiz questions appear in English on the Italian-language exam.

---

## Code Examples

Verified patterns from official sources and existing codebase:

### FSRS: Initialize Scheduler with 7-Day Cap
```python
# Source: https://github.com/open-spaced-repetition/py-fsrs
from fsrs import Scheduler, Card, Rating
from datetime import datetime, timezone

scheduler = Scheduler(
    desired_retention=0.9,
    maximum_interval=7,      # PRODUCT REQUIREMENT: cap for exam prep window
    enable_fuzzing=False,
)

# Create new card
card = Card()
card_json = card.to_json()   # Store this in DB

# On review
card = Card.from_json(card_json)
card, review_log = scheduler.review_card(card, Rating.Good)
updated_card_json = card.to_json()   # Save back to DB
due_utc = card.due                    # datetime with timezone.utc
```

### FSRS: Rating enum values
```python
# Source: https://pypi.org/project/fsrs/
from fsrs import Rating
# Rating.Again = 1  (forgot/wrong)
# Rating.Hard  = 2  (correct but hard)
# Rating.Good  = 3  (correct, typical)
# Rating.Easy  = 4  (too easy)
```

### SQLAlchemy: New ORM Models (following existing models.py pattern)
```python
# Source: app/models.py existing pattern
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Boolean
from datetime import datetime
from app.database import Base

class Flashcard(Base):
    __tablename__ = "flashcards"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_slug: Mapped[str] = mapped_column(String(100), ForeignKey("topics.slug"), nullable=False, index=True)
    front_it: Mapped[str] = mapped_column(Text, nullable=False)   # term in Italian
    back_it: Mapped[str] = mapped_column(Text, nullable=False)    # definition in Italian
    front_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    back_en: Mapped[str | None] = mapped_column(Text, nullable=True)

class SRSState(Base):
    __tablename__ = "srs_states"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flashcard_id: Mapped[int] = mapped_column(Integer, ForeignKey("flashcards.id"), nullable=False, index=True, unique=True)
    card_json: Mapped[str] = mapped_column(Text, nullable=False)  # Card.to_json() blob
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class QuizQuestion(Base):
    __tablename__ = "quiz_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_slug: Mapped[str] = mapped_column(String(100), ForeignKey("topics.slug"), nullable=False, index=True)
    question_it: Mapped[str] = mapped_column(Text, nullable=False)
    # choices stored as JSON: ["opzione A", "opzione B", "opzione C", "opzione D"]
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-3
    # explanations stored as JSON: {"correct": "...", "wrong_0": "...", "wrong_1": "...", "wrong_2": "..."}
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # NULL = not yet generated
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic_slug: Mapped[str] = mapped_column(String(100), ForeignKey("topics.slug"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False)    # 0-5
    max_score: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    attempted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

class ExamQuestion(Base):
    __tablename__ = "exam_questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    topic_slug: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # optional
    source_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    question_it: Mapped[str] = mapped_column(Text, nullable=False)
    choices_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON list of 4 strings
    correct_index: Mapped[int] = mapped_column(Integer, nullable=False)
    explanation_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # NULL = not generated
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class PracticeTestAttempt(Base):
    __tablename__ = "practice_test_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    time_expired: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL until submitted

class PracticeTestAnswer(Base):
    __tablename__ = "practice_test_answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("practice_test_attempts.id"), nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("exam_questions.id"), nullable=False)
    chosen_index: Mapped[int | None] = mapped_column(Integer, nullable=True)  # NULL = skipped/timed out
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
```

### Alembic: Single migration for all Phase 2 tables
```python
# migrations/versions/{hash}_phase2_active_learning.py
# Source: existing b16bd4264820_initial_schema.py pattern

def upgrade() -> None:
    op.create_table('flashcards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic_slug', sa.String(100), sa.ForeignKey('topics.slug'), nullable=False),
        sa.Column('front_it', sa.Text(), nullable=False),
        sa.Column('back_it', sa.Text(), nullable=False),
        sa.Column('front_en', sa.Text(), nullable=True),
        sa.Column('back_en', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_flashcards_topic_slug', 'flashcards', ['topic_slug'])
    # ... repeat for srs_states, quiz_questions, quiz_attempts, exam_questions,
    #     practice_test_attempts, practice_test_answers
```

### DaisyUI Dock (Bottom Navigation) — confirmed HTML structure
```html
<!-- Source: https://daisyui.com/components/dock/ -->
<!-- Place directly in base.html before </body> -->
<div class="dock">
  <button class="dock-active">
    <svg><!-- icon --></svg>
    <span class="dock-label">Argomenti</span>
  </button>
  <button>
    <svg><!-- icon --></svg>
    <span class="dock-label">Ripasso</span>
  </button>
  <button>
    <svg><!-- icon --></svg>
    <span class="dock-label">Esame</span>
  </button>
</div>
```
Note: Use `<a href="...">` instead of `<button>` for navigation. The `dock-active` class marks the current tab.

### HTMX: Show Answer fragment swap
```html
<!-- card_front.html fragment -->
<div id="card-container">
  <div class="card bg-base-100 shadow-sm border border-base-300 min-h-[200px] flex items-center justify-center p-6">
    <p class="text-lg font-semibold text-center">{{ flashcard.front_it }}</p>
  </div>
  <button
    class="btn btn-primary w-full mt-4 min-h-[44px]"
    hx-get="/review/cards/{{ srs_state.id }}/back"
    hx-target="#card-container"
    hx-swap="outerHTML">
    Mostra risposta
  </button>
</div>
```

### Existing Claude service: XML-tag pattern to follow
```python
# Source: app/services/claude.py — generate_explainer() pattern to reuse
response = await client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=2048,
    system=QUIZ_EXPLANATION_SYSTEM_PROMPT,
    messages=[{"role": "user", "content": f"Domanda: {question_text}\n..."}]
)
raw = response.content[0].text
# Parse XML tags with re.search — same approach as generate_explainer()
```

### seed_exam_questions.py pattern
```python
# Pattern: follows seed_topics.py exactly (synchronous sqlite3)
# CSV format (documented at top of file):
# question_it,choice_a,choice_b,choice_c,choice_d,correct_index,subject,topic_slug,source_year
# "Quale base azotata non si trova nel DNA?","Adenina","Uracile","Timina","Guanina",1,"biology","dna-rna-proteine",
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SM-2 algorithm (Anki classic) | FSRS-6 (21 parameters) | 2022-2025 | Significantly more accurate; available in py-fsrs |
| FSRS-5 (py-fsrs < 6.x) | FSRS-6 (py-fsrs 6.3.0) | October 2025 | Added short-term review parameters; API backward-compatible |
| TOLC-MED exam format (60Q / 100 min) | Filter semester (no entrance exam) | 2025 | Italian medicine abandoned entrance tests; professioni sanitarie still use entrance exams |
| Separate questions per health profession | Unified professioni sanitarie test | Ongoing | Biology and Chemistry are core for all health profession programs |

**Deprecated/outdated:**
- `fsrs4anki` JavaScript library: archived/superseded by py-fsrs for Python projects
- TOLC-MED (medicine, Italian): abolished 2025 — professioni sanitarie entrance tests (TOLC-B/TOLC-F-style) are still active

---

## Open Questions

1. **Which TOLC exam variant do professioni sanitarie programs currently use?**
   - What we know: TOLC-MED (medicine) is abolished in 2025. Health profession programs still require entrance exams. TOLC-B and TOLC-F cover Biology/Chemistry/Physics/Math/Logic.
   - What's unclear: Whether the target program (osteopathy) uses TOLC-B, TOLC-F, or a university-specific test. The CONTEXT.md says "professioni sanitarie" broadly.
   - Recommendation: Seed the 20 placeholder exam questions to match TOLC-B/TOLC-F style (4 choices, Biology and Chemistry, Italian) — this is the most common format and can always be updated. The exam format concern does not block implementation.

2. **Flashcard content generation strategy (delegated to Claude's discretion)**
   - What we know: Topics have `content_it` (schematic notes) that already contains key terms, definitions, and data.
   - What's unclear: Whether to extract cards automatically from `content_it` using a Claude call, or require manual seeding.
   - Recommendation: For Phase 2, seed a hardcoded set of 5-8 flashcards per topic in a `seed_flashcards.py` script (similar to `seed_topics.py`), focused on nomenclature terms visible in the seed topic list (cell parts, chemical compound names). Auto-generation via Claude can be Phase 4. This avoids complexity and API cost.

3. **py-fsrs FSRS-6 vs FSRS-5 API differences**
   - What we know: py-fsrs v6.3.0 uses FSRS-6 internally. API is backward-compatible for `Scheduler`, `Card`, `Rating` usage.
   - What's unclear: Whether `Card.from_json()` from a FSRS-5-era card JSON (if any existed) would break in FSRS-6.
   - Recommendation: Not a concern for this project — no existing card data exists. Start fresh with v6.3.0.

---

## Sources

### Primary (HIGH confidence)
- [open-spaced-repetition/py-fsrs GitHub README](https://github.com/open-spaced-repetition/py-fsrs) — Scheduler API, Card fields, maximum_interval, JSON serialization
- [PyPI fsrs 6.3.0](https://pypi.org/project/fsrs/) — current version (6.3.0, October 13 2025), Python >=3.10 requirement
- [DaisyUI dock component](https://daisyui.com/components/dock/) — dock, dock-active, dock-label class names, viewport-fit requirement
- Existing codebase: `app/models.py`, `app/services/claude.py`, `app/routers/pages.py`, `app/routers/fragments.py`, `app/templates/base.html`, `seed_topics.py` — all architectural patterns confirmed by direct code reading

### Secondary (MEDIUM confidence)
- [HTMX hx-trigger documentation](https://htmx.org/attributes/hx-trigger/) + GitHub issue — `htmx.trigger()` preferred over `dispatchEvent()` for programmatic events (confirmed by HTMX issue #1638)
- Web search results on TOLC-MED abolition 2025 — multiple sources confirm filter semester reform; professioni sanitarie still uses entrance exams
- Web search results on py-fsrs maximum_interval parameter — confirmed as `Scheduler(maximum_interval=N)` with default 36500

### Tertiary (LOW confidence)
- TOLC-PS exam format specifics — conflicting/incomplete search results; the specific test format for the user's target program (osteopathy) is uncertain; treat seed questions as illustrative placeholders

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — py-fsrs v6.3.0 confirmed on PyPI; all other libraries already in project
- Architecture: HIGH — patterns directly derived from existing codebase + verified library APIs
- Pitfalls: HIGH (UTC/7-day cap/Tailwind) MEDIUM (exam timer, Claude Italian output)

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (py-fsrs is stable; HTMX/DaisyUI are stable; AI API model version pinned)
