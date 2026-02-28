# Architecture Patterns: OsteoPrep

**Domain:** AI-powered single-user exam preparation web app
**Researched:** 2026-02-28
**Overall confidence:** HIGH (well-understood patterns, verified against multiple sources)

---

## Recommended Architecture

A monolithic Python backend (FastAPI) serves a lightweight mobile-first frontend (Vanilla JS or HTMX). There is no build step, no separate frontend server, and no auth layer. All data lives in SQLite on the same Hetzner server. Claude API is called server-side so the API key never touches the browser.

```
iPhone Browser (Safari)
       |
       | HTTPS
       v
FastAPI Server (port 8080 or similar)
   |          |            |
   |          |            |
Static     REST API    SSE Stream
(HTML/CSS/JS)  endpoints  /api/chat/stream
                  |
         ┌────────┴────────┐
         |                 |
      SQLite          Claude API
    (local file)     (Anthropic)
```

### No separate frontend build pipeline. Why:
- The exam is in 3 weeks — zero time for webpack/vite/typescript transpile setup
- A single HTML file + vanilla JS is sufficient for a mobile study tool
- FastAPI serves static files natively via `StaticFiles`

---

## Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| **Static Frontend** | HTML pages, CSS, browser JS | Backend REST API, SSE stream |
| **FastAPI Router** | Route HTTP requests, validate input, return responses | DB layer, Claude service, SRS engine |
| **DB Layer (SQLAlchemy)** | CRUD for all persistent state | SQLite file on disk |
| **Claude Service** | Build prompts, call Anthropic API, stream responses back | Anthropic API (outbound), FastAPI router (inbound) |
| **SRS Engine** | Run FSRS algorithm, compute next-review dates, update card state | DB layer (read/write card state) |
| **Content Store** | Cache AI-generated content (topics, explanations, quiz questions) | DB layer |

**Golden rule:** The SRS engine is pure logic — it takes a card state + a rating and returns a new card state. It does not touch the DB directly. The router calls it and then persists the result. This makes the algorithm testable without a DB.

---

## Data Models

### `topics`
Represents one exam topic (e.g., "Cellular Respiration", "Anatomia del cuore").

```sql
id            INTEGER PRIMARY KEY
slug          TEXT UNIQUE NOT NULL       -- e.g. "cellular-respiration"
title_it      TEXT NOT NULL              -- Italian title
title_en      TEXT NOT NULL              -- English title
subject       TEXT NOT NULL              -- "biology" | "chemistry" | "anatomy"
generated_at  DATETIME                   -- NULL = not yet generated
content_it    TEXT                       -- Markdown explanation in Italian
content_en    TEXT                       -- Markdown explanation in English
```

### `flashcards`
One card = one front/back pair. Linked to a topic.

```sql
id            INTEGER PRIMARY KEY
topic_id      INTEGER REFERENCES topics(id)
front_it      TEXT NOT NULL
front_en      TEXT NOT NULL
back_it       TEXT NOT NULL
back_en       TEXT NOT NULL
card_type     TEXT NOT NULL              -- "terminology" | "concept" | "formula"
created_at    DATETIME DEFAULT now
```

### `card_state`
One row per flashcard. Stores all FSRS scheduler state. This is what the SRS engine reads and updates.

```sql
id                INTEGER PRIMARY KEY
flashcard_id      INTEGER UNIQUE REFERENCES flashcards(id)
-- FSRS fields (serialized from py-fsrs Card object)
stability         REAL DEFAULT 0.0       -- memory stability in days
difficulty        REAL DEFAULT 0.0       -- item difficulty 0-1
elapsed_days      INTEGER DEFAULT 0
scheduled_days    INTEGER DEFAULT 0
reps              INTEGER DEFAULT 0      -- total repetitions
lapses            INTEGER DEFAULT 0      -- times forgotten
state             TEXT DEFAULT 'New'     -- New | Learning | Review | Relearning
due               DATETIME               -- next review timestamp
last_review       DATETIME
```

Note: py-fsrs Card objects are JSON-serializable. The entire FSRS state can be stored as a JSON blob in a single column if the schema above feels verbose. However, explicit columns allow SQL queries like "cards due today" without deserializing.

### `review_log`
Audit trail of every card review. Used for analytics and FSRS optimizer (future).

```sql
id                INTEGER PRIMARY KEY
flashcard_id      INTEGER REFERENCES flashcards(id)
rating            INTEGER NOT NULL       -- 1=Again, 2=Hard, 3=Good, 4=Easy
reviewed_at       DATETIME DEFAULT now
scheduled_days    INTEGER                -- what the algorithm predicted
elapsed_days      INTEGER                -- actual days since last review
state_before      TEXT                   -- state before this review
state_after       TEXT                   -- state after this review
```

### `quiz_questions`
Generated multiple-choice questions (from topics or past-exam import).

```sql
id            INTEGER PRIMARY KEY
topic_id      INTEGER REFERENCES topics(id)  -- NULL if from past exam bank
source        TEXT NOT NULL              -- "generated" | "past_exam"
exam_year     INTEGER                    -- NULL if generated
question_it   TEXT NOT NULL
question_en   TEXT
option_a_it   TEXT NOT NULL
option_b_it   TEXT NOT NULL
option_c_it   TEXT NOT NULL
option_d_it   TEXT NOT NULL
option_a_en   TEXT
option_b_en   TEXT
option_c_en   TEXT
option_d_en   TEXT
correct       TEXT NOT NULL              -- "a" | "b" | "c" | "d"
explanation_it TEXT
explanation_en TEXT
difficulty    TEXT                       -- "easy" | "medium" | "hard"
```

### `quiz_attempts`
Every time the user answers a question.

```sql
id              INTEGER PRIMARY KEY
question_id     INTEGER REFERENCES quiz_questions(id)
selected        TEXT NOT NULL            -- "a" | "b" | "c" | "d"
is_correct      BOOLEAN NOT NULL
attempted_at    DATETIME DEFAULT now
session_id      TEXT                     -- groups attempts into a session
```

### `study_sessions`
A session begins when the user starts studying and closes on exit or inactivity.

```sql
id              TEXT PRIMARY KEY         -- UUID or timestamp string
started_at      DATETIME DEFAULT now
ended_at        DATETIME
mode            TEXT                     -- "flashcards" | "quiz" | "reading" | "chat"
topic_id        INTEGER                  -- NULL for mixed sessions
cards_reviewed  INTEGER DEFAULT 0
questions_answered INTEGER DEFAULT 0
```

### `settings`
Single-row table for user preferences.

```sql
key   TEXT PRIMARY KEY
value TEXT
```

Key examples: `language` (it/en), `daily_card_limit`, `desired_retention` (FSRS target, default 0.9).

---

## Data Flow Diagrams

### 1. Generating and Displaying a Topic Explanation

```
User taps "Biology: Cellular Respiration"
  -> GET /api/topics/cellular-respiration
     -> DB: SELECT content_it FROM topics WHERE slug = ?
     -> IF content is NULL:
          POST /api/topics/cellular-respiration/generate
            -> Claude Service: build prompt with topic + language
            -> Anthropic API: POST /v1/messages (sync, not streaming)
            -> response saved to topics.content_it
            -> return content to frontend
     -> ELSE return cached content directly (no Claude call)
  <- HTML rendered in browser
```

**Key point:** Content is generated once and cached in SQLite. Subsequent visits are instant with zero API cost.

### 2. Flashcard SRS Review Session

```
User opens "Review Due Cards"
  -> GET /api/cards/due
     -> DB: SELECT * FROM card_state WHERE due <= now() ORDER BY due LIMIT 20
     -> JOIN flashcards for front/back content
  <- Browser renders card stack (front only)

User rates a card (Again / Hard / Good / Easy)
  -> POST /api/cards/{id}/review  {rating: 3}
     -> DB: load card_state for this card
     -> SRS Engine: fsrs.repeat(card, rating, now)  -- pure function
     -> DB: UPDATE card_state with new stability, difficulty, due, state
     -> DB: INSERT INTO review_log (...)
  <- {next_due: "2026-03-05", new_state: "Review"}
```

### 3. AI Chat Interface

```
User types a question in chat
  -> POST /api/chat/stream  {message: "...", context_topic: "cellular-respiration"}
     -> Claude Service:
          system_prompt: "You are a study assistant for Italian exam prep..."
          context: topic content (if specified) [cached via Claude prompt caching]
          user message appended
     -> client.messages.stream() via Anthropic SDK
     -> FastAPI StreamingResponse (text/event-stream / SSE)
  <- Browser EventSource reads chunks
     -> appends text to chat bubble incrementally
```

**Streaming is essential for chat** — without it, the user stares at a blank screen for 5-10 seconds before any response appears. SSE is the right mechanism: it works over a normal HTTP connection, is natively supported by browser `EventSource` API, and does not require WebSockets.

### 4. Quiz Flow

```
User starts a quiz for topic X
  -> GET /api/quiz?topic=cellular-respiration&count=10
     -> DB: SELECT questions WHERE topic_id = X ORDER BY RANDOM() LIMIT 10
     -> IF fewer than 10 available:
          Claude Service: generate_questions(topic, count_needed)
          -> DB: INSERT new questions
  <- 10 questions returned

User answers each question
  -> POST /api/quiz/answer  {question_id: X, selected: "b"}
     -> DB: check correct answer
     -> DB: INSERT quiz_attempt
  <- {correct: false, explanation: "..."}
```

---

## API Endpoints

```
# Content
GET  /api/topics                          -- list all topics
GET  /api/topics/{slug}                   -- get topic with content (generates if missing)
POST /api/topics/{slug}/regenerate        -- force regeneration

# Flashcards
GET  /api/cards/due                       -- cards due for review today
GET  /api/cards/topic/{topic_id}          -- all cards for a topic
POST /api/cards/{id}/review               -- submit rating (1-4), returns updated state
GET  /api/cards/stats                     -- overall SRS statistics

# Quiz
GET  /api/quiz                            -- get quiz questions (topic optional, generates if needed)
POST /api/quiz/answer                     -- submit an answer
GET  /api/quiz/history                    -- past quiz performance

# Chat
POST /api/chat/stream                     -- SSE streaming chat endpoint

# Progress
GET  /api/progress                        -- overall study statistics
GET  /api/progress/topic/{topic_id}       -- per-topic progress

# Settings
GET  /api/settings
PUT  /api/settings
```

---

## SRS Algorithm: FSRS vs SM-2 Decision

**Use FSRS via py-fsrs.** Rationale:

- FSRS was validated on 700M real reviews from 20,000 users (source: open-spaced-repetition). SM-2 was created in 1987 with much less data.
- For a 3-week exam sprint, FSRS delivers 20-30% fewer daily reviews with the same retention — critical when time is scarce.
- py-fsrs is a PyPI package (`pip install fsrs`), integrates in ~20 lines.
- Card objects are JSON-serializable — trivial to store in SQLite.
- Default `desired_retention=0.9` is appropriate for exam prep (90% recall target).

**FSRS card lifecycle:**
```
New Card
  |
  v  (first review)
Learning  <-- rating: Again resets here
  |
  v  (passes learning steps: 1min, 10min)
Review  <-- normal long-interval reviews happen here
  |
  v  (forgot: rating=Again)
Relearning --> back to Review after relearning steps
```

**What the SRS engine does per review:**
```python
from fsrs import Scheduler, Card, Rating

scheduler = Scheduler(desired_retention=0.9)
card = load_card_from_db(card_id)  # deserialize stored state
rating = Rating.Good  # from user input (1=Again, 2=Hard, 3=Good, 4=Easy)

scheduling_cards = scheduler.repeat(card, datetime.now(timezone.utc))
updated_card = scheduling_cards[rating].card
review_log = scheduling_cards[rating].review_log

save_card_to_db(card_id, updated_card)
save_review_log(card_id, review_log)
```

**Columns needed per card state:** stability (float), difficulty (float), elapsed_days (int), scheduled_days (int), reps (int), lapses (int), state (New/Learning/Review/Relearning), due (datetime).

---

## Bilingual Content Strategy

The language toggle switches the UI locale and which content fields are used. Two strategies:

**Option A (Recommended): Dual-column storage**
- Topics table has `content_it` and `content_en` columns
- Flashcards have `front_it`, `front_en`, `back_it`, `back_en`
- Language preference stored in settings table
- Claude generates both languages in a single API call (one prompt, two-language response)
- No runtime translation needed — content retrieved directly

**Option B: Translate-on-demand**
- Store only Italian (exam language), translate to English when English is selected
- Requires additional Claude calls, adds latency, more complex

Use Option A. The exam topics are finite. Generating both languages once upfront during the "generate topic" phase is straightforward: the prompt instructs Claude to return a JSON object with `it` and `en` keys.

---

## Suggested Build Order (3-Week Timeline)

The goal is a usable study tool on day 1, with depth added progressively.

### Week 1: Spine (Days 1-5)

Goal: Can view topic content and read explanations. Everything else builds on this.

1. **Day 1-2:** Project scaffold
   - FastAPI app with SQLite (SQLAlchemy models)
   - Static file serving, mobile-friendly base HTML/CSS template
   - Health check endpoint, basic topic list

2. **Day 2-3:** Content generation pipeline
   - `topics` table, `GET /api/topics/{slug}` endpoint
   - Claude Service module: prompt templates for topic explanations
   - Generate-and-cache pattern (one Claude call, stored forever)
   - Topic list page with subject groupings

3. **Day 4-5:** Reading UI
   - Topic detail page renders markdown explanation
   - Language toggle (it/en) wired to settings API
   - Mobile layout: large text, good contrast, swipe-friendly navigation

**Milestone:** User can read AI-generated explanations for all main topic areas.

### Week 2: Active Learning (Days 6-12)

Goal: Quizzes and flashcards working end-to-end.

4. **Day 6-7:** Flashcard generation + display
   - `flashcards` table, flashcard generation from topic content
   - Flash card UI: tap to flip, topic-browsable deck

5. **Day 8-9:** SRS engine
   - `card_state` table, `review_log` table
   - py-fsrs integration as a pure-logic module
   - `GET /api/cards/due`, `POST /api/cards/{id}/review`
   - Due card review session UI

6. **Day 10-11:** Quiz system
   - `quiz_questions` table, quiz generation from topics
   - Quiz UI: multiple choice, immediate feedback, explanation on wrong answer
   - `quiz_attempts` table, session tracking

7. **Day 12:** Past exam questions
   - Import mechanism for manually seeded past paper questions (JSON or direct SQL insert)
   - Past exam quiz mode separate from generated quizzes

**Milestone:** Full study loop: read → flashcard review → quiz.

### Week 3: Polish + AI Chat (Days 13-21)

Goal: Chat assistant, progress tracking, and exam-day readiness.

8. **Day 13-14:** AI Chat
   - SSE streaming endpoint
   - Chat UI: conversation thread, typing indicator, context-aware (can reference current topic)
   - Prompt caching for topic system prompts (reduces latency and cost)

9. **Day 15-16:** Progress tracking
   - Dashboard: topics covered, SRS due/total, quiz accuracy by subject
   - Study session logging

10. **Day 17-18:** Content completeness pass
    - Verify all Italian exam topic areas are in the topic list and generated
    - Fill gaps, regenerate any thin explanations

11. **Day 19-20:** Mobile polish
    - Test on iPhone Safari specifically
    - Touch targets ≥ 44px, no horizontal scroll, readable font sizes
    - Viewport meta tag, iOS safe areas

12. **Day 21:** Buffer / bug fixing

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Regenerating Content on Every Request
**What goes wrong:** Each topic page visit calls Claude → slow, expensive, unpredictable.
**Instead:** Generate once, store in DB, serve from DB. Provide an explicit "regenerate" button if needed.

### Anti-Pattern 2: Client-Side Claude API Calls
**What goes wrong:** API key exposed in browser, CORS issues, no server-side control.
**Instead:** All Claude calls go through the FastAPI backend. Browser never sees the API key.

### Anti-Pattern 3: Building Auth / User System
**What goes wrong:** Wasted days on login/session management that provides zero exam-prep value.
**Instead:** Single-user app on a private server, accessible only via Tailscale or direct IP. No auth needed.

### Anti-Pattern 4: React/Next.js Frontend
**What goes wrong:** Build toolchain setup, TypeScript config, hydration issues — all wasted time for a single-user study tool.
**Instead:** Vanilla HTML + JavaScript or HTMX. FastAPI's Jinja2 templating is sufficient. Pages load instantly, no build step.

### Anti-Pattern 5: SM-2 Instead of FSRS
**What goes wrong:** 20-30% more daily reviews needed for same retention. Suboptimal for a 3-week sprint.
**Instead:** FSRS via py-fsrs. Same install complexity, measurably better scheduling.

### Anti-Pattern 6: Storing Quiz Questions Only in Memory
**What goes wrong:** No history, no analytics, regenerated every session.
**Instead:** All generated questions go to the `quiz_questions` table immediately. Once generated, they are served from DB.

---

## Scalability Considerations

This app is single-user, so scalability is not a concern. However, these design choices keep it maintainable:

| Concern | Approach |
|---------|----------|
| Claude API costs | Cache everything — generate once per topic, use cached prompts for chat |
| SQLite concurrency | Single user, no concurrency problem. `check_same_thread=False` is sufficient |
| Response latency | Streaming SSE for chat; cached content for topic pages; `due <= now()` indexed query for SRS |
| DB backup | SQLite is a single file — easy to back up with cron to `/root/backups/` |

---

## Technology Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend framework | FastAPI | Async-native, SSE support, Pydantic validation, fast dev speed |
| Database | SQLite via SQLAlchemy | Zero setup, single file, sufficient for single user |
| SRS algorithm | FSRS (py-fsrs) | 20-30% more efficient than SM-2, pip-installable, JSON-serializable state |
| Frontend | Vanilla JS + HTMX (optional) | No build step, iPhone Safari compatible, instant load |
| Claude streaming | FastAPI StreamingResponse + SSE | Native browser EventSource support, no WebSocket complexity |
| Content caching | DB-level (generate once, store) | Zero re-generation cost, instant subsequent loads |
| Bilingual content | Dual columns generated together | Single Claude call for both languages, no runtime translation |

---

## Sources

- SM-2 algorithm data model: [Tegaru SM-2 Explained](https://tegaru.app/en/blog/sm2-algorithm-explained), [RemNote SM-2 docs](https://help.remnote.com/en/articles/6026144-the-anki-sm-2-spaced-repetition-algorithm)
- FSRS vs SM-2 comparison: [MemoForge FSRS guide](https://memoforge.app/blog/fsrs-vs-sm2-anki-algorithm-guide-2025/), [Brainscape comparison](https://www.brainscape.com/academy/comparing-spaced-repetition-algorithms/)
- py-fsrs Python library: [GitHub open-spaced-repetition/py-fsrs](https://github.com/open-spaced-repetition/py-fsrs), [PyPI fsrs](https://pypi.org/project/fsrs/)
- FastAPI + SQLite patterns: [FastAPI SQL docs](https://fastapi.tiangolo.com/tutorial/sql-databases/), [SQLite FastAPI tutorial](https://timberry.dev/adding-an-sqlite-backend-to-fastapi)
- Claude streaming / SSE: [Anthropic Streaming Docs](https://platform.claude.com/docs/en/build-with-claude/streaming)
- Claude prompt caching: [Anthropic Prompt Caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)
- FSRS awesome list: [awesome-fsrs](https://github.com/open-spaced-repetition/awesome-fsrs)
