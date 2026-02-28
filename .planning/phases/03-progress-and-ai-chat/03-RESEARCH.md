# Phase 3: Progress and AI Chat - Research

**Researched:** 2026-02-28
**Domain:** FastAPI SSE streaming, Anthropic SDK async streaming, HTMX SSE extension, progress dashboard queries
**Confidence:** HIGH

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CHAT-01 | User can open an AI chat interface to ask questions about any study topic | SSE endpoint + HTMX sse extension panel on topic pages |
| CHAT-02 | Chat responses stream in real time (SSE — no waiting for full response) | FastAPI StreamingResponse + AsyncAnthropic.messages.stream() async generator |
| CHAT-03 | Chat is context-aware — when accessed from a topic page, Claude knows which topic | topic_slug passed as hidden form field; injected into system prompt |
| CHAT-04 | User can ask about their own progress ("which topics am I weakest on?") and Claude can respond with context | DB progress summary serialized as JSON and injected into chat system prompt |
| PROG-01 | User can view a dashboard showing completed topics, quiz scores per subject, and SRS card counts (due today, learned, new) | SQLAlchemy aggregate queries over QuizAttempt, SRSState, Topic |
| PROG-02 | Each topic shows completion status (not started / reading / quiz passed) | Topic.content_it (reading) + QuizAttempt best score (quiz passed) — query in topic_list fragment |
</phase_requirements>

---

## Summary

Phase 3 adds two features to the existing FastAPI + HTMX + DaisyUI stack: a progress dashboard and a streaming AI chat panel. Both are well within the capabilities of the existing stack without new dependencies.

The streaming chat is the most technically novel piece. The Anthropic Python SDK (0.84.0, already installed) supports `AsyncAnthropic.messages.stream()` as an async context manager. Combining this with FastAPI's `StreamingResponse` and an async generator that yields `text/event-stream` SSE events creates a clean streaming pipeline. The HTMX SSE extension (htmx-ext-sse, CDN loaded) handles the client side — connecting to the SSE endpoint and appending streamed text chunks into the chat bubble's target div.

The progress dashboard is pure SQLAlchemy query work. All necessary data already exists in the DB: `QuizAttempt` (quiz scores), `SRSState` (card states), `Topic` (content generation status). A new `/progress` route and template gather this with a few aggregate queries. Topic completion status (PROG-02) is added to the existing `topic_list.html` fragment.

**Primary recommendation:** Use FastAPI `StreamingResponse` with an async generator yielding `data: <chunk>\n\n` SSE events, driven by `async for text in stream.text_stream:` from the Anthropic SDK. Load the HTMX SSE extension via CDN for the chat panel HTML.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| anthropic | 0.84.0 (installed) | Async streaming from Claude API | Already in use; `AsyncAnthropic.messages.stream()` provides `async text_stream` iterator |
| FastAPI | 0.115.14 (installed) | `StreamingResponse` for SSE endpoint | Native async generator support, no extra packages needed |
| HTMX SSE extension | 2.2.4 (CDN) | Client-side SSE connection + DOM swap | Official HTMX 2.x extension, replaces hx-sse from v1 |
| SQLAlchemy async | 2.0.47 (installed) | Aggregate progress queries | Already in use for all DB work |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `func.count()`, `func.avg()` | SQLAlchemy built-in | Aggregate quiz scores, SRS counts | Progress dashboard queries |
| `sse-starlette` | 2.x (PyPI) | SSE abstraction with reconnect/ping support | Only needed if raw StreamingResponse proves unreliable; current project doesn't need it |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw `StreamingResponse` | `sse-starlette` | sse-starlette adds reconnect/ping/close handling but adds a dependency; not needed for single-user app |
| HTMX SSE extension | Vanilla JS EventSource | JS EventSource is simpler but breaks the HTMX-only pattern; SSE extension keeps all interactivity declarative |
| DaisyUI chat bubbles | Custom CSS | DaisyUI has `.chat`, `.chat-bubble` classes — use them, no hand-rolling |

**Installation:** No new Python packages needed. Only the HTMX SSE extension CDN script tag in base.html.

---

## Architecture Patterns

### Recommended Project Structure

```
app/
├── routers/
│   ├── chat.py          # NEW: /chat/stream SSE endpoint + /chat form handler
│   ├── progress.py      # NEW: /progress dashboard page
│   └── fragments.py     # EXTEND: topic_list fragment adds completion status
├── services/
│   └── claude.py        # EXTEND: add stream_chat() async generator function
│   └── progress_service.py  # NEW: aggregate DB queries for dashboard
└── templates/
    ├── progress.html    # NEW: dashboard page
    └── fragments/
        ├── topic_list.html   # EXTEND: add completion badge
        └── chat_panel.html   # NEW: chat input + message stream target
```

### Pattern 1: FastAPI SSE Streaming with AsyncAnthropic

**What:** An async generator that calls `AsyncAnthropic.messages.stream()` and yields each text chunk as an SSE `data:` line.
**When to use:** CHAT-02 — the `/chat/stream` endpoint.

```python
# Source: Anthropic SDK docs (platform.claude.com/docs/en/api/messages-streaming)
# + FastAPI StreamingResponse pattern

from anthropic import AsyncAnthropic
from fastapi.responses import StreamingResponse

async def _stream_chat_generator(messages: list, system: str):
    """Async generator yielding SSE data lines from Claude streaming."""
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    async with client.messages.stream(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=system,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            # SSE format: "data: <chunk>\n\n"
            # Escape newlines in chunk so they don't break SSE framing
            chunk = text.replace("\n", "\\n")
            yield f"data: {chunk}\n\n"
    # Signal stream end
    yield "data: [DONE]\n\n"


@router.post("/chat/stream")
async def chat_stream(request: Request, ...):
    return StreamingResponse(
        _stream_chat_generator(messages, system),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Disable nginx buffering
        }
    )
```

### Pattern 2: HTMX SSE Chat Panel

**What:** HTMX SSE extension connecting to the streaming endpoint, appending text chunks into a chat bubble.
**When to use:** CHAT-01, CHAT-02 — the chat panel template.

```html
<!-- Source: https://htmx.org/extensions/sse/ (HTMX 2.x SSE extension docs) -->
<!-- Load SSE extension via CDN (add to base.html or chat panel) -->
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4/sse.js"></script>

<!-- Chat panel: user submits form, response streams into #chat-response -->
<form id="chat-form"
      hx-post="/chat/start"
      hx-target="#chat-response"
      hx-swap="innerHTML">
  <input type="hidden" name="topic_slug" value="{{ topic.slug }}">
  <input type="text" name="question" placeholder="Chiedi qualcosa...">
  <button type="submit">Invia</button>
</form>

<!-- SSE stream target: hx-ext="sse" connects to the stream URL returned by /chat/start -->
<div id="chat-response">
  <!-- After form submit, server returns this fragment which establishes SSE connection -->
</div>
```

The `/chat/start` POST endpoint returns an HTML fragment containing the SSE-connected element:

```html
<!-- Fragment returned by /chat/start -->
<div hx-ext="sse"
     sse-connect="/chat/stream?session_id={{ session_id }}"
     sse-swap="message"
     hx-swap="beforeend">
  <div class="chat chat-start">
    <div class="chat-bubble" id="response-{{ session_id }}"></div>
  </div>
</div>
```

**Alternative simpler approach (recommended for this project):** Since the chat is single-user and stateless, skip the session_id indirection. The form can POST directly with the question and topic_slug, and the response is the SSE stream itself — but this requires the form to submit to the streaming endpoint. The cleaner pattern:

1. Form submits via JS `fetch()` POST to get question + topic context
2. Use `EventSource` pointing to a GET endpoint with query params
3. OR: use HTMX `hx-post` to a `/chat/response` endpoint that returns an HTML fragment containing an `hx-ext="sse"` div that connects immediately

The recommended single-step approach: POST to `/chat/stream` (returns SSE directly). Client JS appends the text as it arrives into the chat bubble via EventSource — minimal JS, no HTMX needed for the stream itself. HTMX handles form submission and showing the chat UI; vanilla EventSource handles the stream.

### Pattern 3: Progress Dashboard Queries

**What:** SQLAlchemy aggregate queries to gather all progress metrics in one pass per subject.
**When to use:** PROG-01 — the `/progress` endpoint.

```python
# Source: SQLAlchemy 2.0 async patterns (project already uses these)
from sqlalchemy import func, select, case

# SRS counts: due today, learned (stability > 0), new (never reviewed)
# SRSState.card_json contains FSRS state — parse stability from JSON
# Simpler: due count already in fsrs_service.get_due_count()
# Total cards, learned cards (reviewed at least once) — count SRSState rows vs Flashcard rows

# Quiz accuracy per subject: join QuizAttempt -> Topic, avg(score/max_score) group by subject
result = await db.execute(
    select(
        Topic.subject,
        func.count(QuizAttempt.id).label("attempt_count"),
        func.avg(
            QuizAttempt.score * 1.0 / QuizAttempt.max_score
        ).label("avg_accuracy"),
    )
    .join(Topic, QuizAttempt.topic_slug == Topic.slug)
    .group_by(Topic.subject)
)
```

### Pattern 4: Topic Completion Status (PROG-02)

**What:** Add a completion badge to each topic row in `topic_list.html` based on quiz attempt history.
**When to use:** PROG-02 — extend the existing fragment.

Three states:
- **Not started**: `topic.content_it is None` (content not yet generated)
- **Reading**: `topic.content_it is not None` but no passing quiz attempt
- **Quiz passed**: Best QuizAttempt score >= threshold (e.g., >= 3/5)

The fragment currently receives `topics` as a list of `Topic` ORM objects. To add completion status, the fragment router needs to also query `QuizAttempt` best scores per slug and pass a dict.

```python
# In fragments.py — extend subject_topics_fragment()
best_scores_result = await db.execute(
    select(
        QuizAttempt.topic_slug,
        func.max(QuizAttempt.score * 1.0 / QuizAttempt.max_score).label("best_pct")
    )
    .where(QuizAttempt.topic_slug.in_([t.slug for t in topics]))
    .group_by(QuizAttempt.topic_slug)
)
best_scores = {row.topic_slug: row.best_pct for row in best_scores_result}
```

### Anti-Patterns to Avoid

- **Synchronous `client.messages.stream()`** in an async FastAPI endpoint: Always use `AsyncAnthropic`, never `Anthropic` (sync) in an async context — it will block the event loop.
- **Building a chat history store**: CHAT-04 asks for progress context in chat answers, not full conversation history. Keep it stateless — inject DB progress summary into the system prompt, no conversation turns to manage.
- **Markdown rendering server-side**: Chat responses will contain markdown. Render it client-side with a tiny JS parser (or simply use `<pre>` / accept raw text). Don't add markdown-to-HTML server rendering — the HTMX SSE extension appends text chunks directly; HTML rendering in streamed chunks is fragile.
- **SSE with POST + no session**: SSE requires a GET connection (EventSource API is GET-only). The form POST must either redirect to a GET SSE endpoint or return a fragment that initiates the GET SSE connection. Don't attempt to send the initial question in the SSE GET URL without sanitation.
- **Buffering middleware**: Gunicorn + uvicorn can buffer SSE responses. Add `X-Accel-Buffering: no` header and verify gunicorn is not adding a response buffer. The existing gunicorn config should be checked.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Streaming text from Anthropic | Custom httpx streaming parser | `AsyncAnthropic.messages.stream()` with `async for text in stream.text_stream` | SDK handles event parsing, retries, error events |
| SSE framing | Custom HTTP chunked response | FastAPI `StreamingResponse(media_type="text/event-stream")` | SSE protocol is simple but headers matter; StreamingResponse handles keep-alive |
| Chat UI component | Custom CSS chat bubbles | DaisyUI `.chat`, `.chat-bubble`, `.chat-start`, `.chat-end` classes | Already in static CSS; complete chat UI with zero new CSS |
| Progress aggregation | Custom Python loops over all rows | SQLAlchemy `func.count()`, `func.avg()`, `func.max()` with GROUP BY | DB-side aggregation is 100x faster; all patterns already in project |
| Topic completion logic | New DB model | Query `QuizAttempt` + check `topic.content_it` | All data already in DB, no migration needed |

**Key insight:** The entire phase is wiring existing pieces together. No new schemas (beyond maybe a ChatMessage table if history is wanted — but it's not required by CHAT-01 through CHAT-04). No new CSS. No new Python packages.

---

## Common Pitfalls

### Pitfall 1: EventSource Is GET-Only
**What goes wrong:** Developer tries to POST the user's question to the SSE endpoint. EventSource API in browsers only supports GET. HTMX SSE extension uses EventSource under the hood.
**Why it happens:** Confusion between "submit form" (POST) and "stream response" (GET SSE).
**How to avoid:** Two-step flow: (1) HTMX form POST to `/chat/response` which returns an HTML fragment containing an SSE-connected div with the session params encoded in the SSE GET URL as query params, OR (2) encode the question in a URL-safe GET param and point EventSource directly at `/chat/stream?q=...&topic=...`. For a single-user app with short questions, option 2 is simpler.
**Warning signs:** 405 Method Not Allowed on the SSE endpoint, or stream never connects.

### Pitfall 2: Gunicorn/Nginx Buffering Kills Streaming
**What goes wrong:** Streamed text appears all at once after full response completes, not word-by-word.
**Why it happens:** Gunicorn may buffer response chunks. The app runs behind gunicorn bound to Tailscale IP.
**How to avoid:** Add `X-Accel-Buffering: no` response header (disables nginx buffering if ever added). Check gunicorn config — `--worker-class uvicorn.workers.UvicornWorker` is correct for async FastAPI. Use `flush=True` equivalent — Python async generators automatically flush on each `yield` in uvicorn workers.
**Warning signs:** Stream appears all at once in browser developer tools.

### Pitfall 3: Newlines in SSE Data Break the Frame
**What goes wrong:** Claude's response contains `\n` characters. If yielded raw as `data: line1\nline2\n\n`, the SSE parser treats `line2` as a new SSE field, corrupting the stream.
**Why it happens:** SSE protocol uses `\n` as field delimiter and `\n\n` as message delimiter.
**How to avoid:** Either escape newlines in text chunks (`text.replace("\n", "\\n")`) before yielding, or use multi-line SSE format (`data: line1\ndata: line2\n\n` — each continuation prefixed with `data:`). The escape approach is simpler for this use case.
**Warning signs:** Streaming stops unexpectedly mid-sentence, or JavaScript console shows SSE parse errors.

### Pitfall 4: AsyncAnthropic Stream Context Manager Not Closed
**What goes wrong:** If client disconnects mid-stream, the `async with stream:` block may hang or leave the HTTP connection to Anthropic open.
**Why it happens:** Async generator not fully consumed + context manager not exited on generator throw.
**How to avoid:** Wrap the generator body in `try/except GeneratorExit:` and call `stream.close()` explicitly. FastAPI's `StreamingResponse` sends a `GeneratorExit` to the generator when the client disconnects.
**Warning signs:** Anthropic API costs accumulating even for abandoned requests.

### Pitfall 5: Progress Query N+1
**What goes wrong:** Loading topics then querying QuizAttempts per-topic in a loop — N+1 queries.
**Why it happens:** Natural "for each topic, check attempts" coding pattern.
**How to avoid:** Single aggregate query with `GROUP BY topic_slug` covering all topics in the subject, returning a dict keyed by slug. Pass to template as `best_scores` dict.
**Warning signs:** Slow topic list page, many `SELECT` statements in logs.

### Pitfall 6: SRS Card State Parsing for "Learned" Count
**What goes wrong:** Trying to parse FSRS state from `card_json` to determine "learned" status — the JSON schema is opaque and may change.
**Why it happens:** PROG-01 requires "learned" and "new" counts alongside "due today."
**How to avoid:** Operationalize simply: "new" = `Flashcard` rows with no `SRSState` row (never reviewed). "Learned" = `SRSState` rows where `due_at > now` (reviewed at least once, not due again). "Due" = existing `fsrs_service.get_due_count()`. This avoids parsing `card_json` entirely.
**Warning signs:** JSON parse errors from card_json, or counts that don't match what user sees in review session.

---

## Code Examples

### FastAPI SSE Endpoint — Streaming Claude Response

```python
# Source: Anthropic SDK docs (platform.claude.com/docs/en/api/messages-streaming)
# Source: FastAPI StreamingResponse (fastapi.tiangolo.com)

import os
from anthropic import AsyncAnthropic
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter()

async def _claude_sse_generator(question: str, system_prompt: str):
    """Yield SSE-formatted text chunks from Claude streaming."""
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    try:
        async with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": "user", "content": question}],
        ) as stream:
            async for text in stream.text_stream:
                # Escape newlines to preserve SSE framing
                safe = text.replace("\n", "\\n")
                yield f"data: {safe}\n\n"
    except GeneratorExit:
        pass  # Client disconnected — clean exit
    finally:
        yield "data: [DONE]\n\n"


@router.get("/chat/stream")
async def chat_stream(q: str, topic_slug: str = "", request: Request = None):
    system = build_chat_system_prompt(topic_slug)  # inject topic + progress context
    return StreamingResponse(
        _claude_sse_generator(q, system),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
```

### HTMX SSE Chat Panel — HTML Fragment

```html
<!-- Source: https://htmx.org/extensions/sse/ -->
<!-- Load ONCE in base.html or lazily when chat panel opens -->
<!-- <script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4/sse.js"></script> -->

<!-- Chat panel: hidden on page load, toggled open -->
<div id="chat-panel" class="card bg-base-100 border border-base-300">
  <div class="card-body p-3">
    <h3 class="font-semibold text-sm">Chiedi a Claude</h3>

    <!-- Message history container -->
    <div id="chat-messages" style="min-height: 100px; max-height: 300px; overflow-y: auto;">
      <!-- Messages appended here -->
    </div>

    <!-- SSE stream target: created dynamically after form submit -->
    <div id="chat-stream-target"></div>

    <!-- Input form — uses JS EventSource, not HTMX SSE ext, for POST→GET split -->
    <form id="chat-form" onsubmit="startChatStream(event)">
      <input type="hidden" name="topic_slug" value="{{ topic.slug }}">
      <input type="text" id="chat-input" name="question"
             class="input input-bordered input-sm w-full"
             placeholder="Fai una domanda...">
      <button type="submit" class="btn btn-primary btn-sm mt-2 w-full">Invia</button>
    </form>
  </div>
</div>

<script>
function startChatStream(e) {
  e.preventDefault();
  const form = e.target;
  const q = encodeURIComponent(form.question.value.trim());
  const slug = form.topic_slug.value;
  if (!q) return;

  // Create response bubble
  const bubble = document.createElement('div');
  bubble.className = 'chat chat-start';
  bubble.innerHTML = '<div class="chat-bubble chat-bubble-primary" id="current-response"></div>';
  document.getElementById('chat-messages').appendChild(bubble);
  const target = document.getElementById('current-response');

  // Open SSE stream
  const es = new EventSource(`/chat/stream?q=${q}&topic_slug=${slug}`);
  es.onmessage = (evt) => {
    if (evt.data === '[DONE]') { es.close(); return; }
    // Unescape newlines and append
    target.textContent += evt.data.replace(/\\n/g, '\n');
  };
  es.onerror = () => es.close();
  form.question.value = '';
}
</script>
```

### Progress Dashboard — DB Queries

```python
# Source: SQLAlchemy 2.0 docs — async aggregate queries (project patterns)
from sqlalchemy import func, select, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Topic, QuizAttempt, Flashcard, SRSState
from datetime import datetime, timezone

async def get_progress_summary(db: AsyncSession) -> dict:
    """Gather all data for the progress dashboard."""
    now = datetime.now(timezone.utc)

    # Topic counts by subject + completion
    topics_result = await db.execute(
        select(Topic.subject, func.count(Topic.id).label("total"),
               func.count(Topic.content_it).label("generated"))
        .group_by(Topic.subject)
        .order_by(Topic.subject)
    )
    topics_by_subject = topics_result.all()

    # Quiz accuracy per subject (best attempt per topic, avg across topics)
    quiz_result = await db.execute(
        select(
            Topic.subject,
            func.count(QuizAttempt.id).label("attempts"),
            func.avg(QuizAttempt.score * 1.0 / QuizAttempt.max_score).label("avg_accuracy"),
        )
        .join(Topic, QuizAttempt.topic_slug == Topic.slug)
        .group_by(Topic.subject)
    )
    quiz_by_subject = {row.subject: row for row in quiz_result}

    # SRS card counts
    total_cards = await db.scalar(select(func.count()).select_from(Flashcard))
    reviewed_cards = await db.scalar(select(func.count()).select_from(SRSState))
    new_cards = (total_cards or 0) - (reviewed_cards or 0)
    due_count = await fsrs_service.get_due_count(db)
    learned_cards = (reviewed_cards or 0) - due_count

    return {
        "topics_by_subject": topics_by_subject,
        "quiz_by_subject": quiz_by_subject,
        "srs": {
            "due": due_count,
            "learned": learned_cards,
            "new": new_cards,
            "total": total_cards or 0,
        }
    }
```

### Topic Completion Status — Fragment Extension

```python
# Extend subject_topics_fragment() in fragments.py
# Source: SQLAlchemy project patterns (existing codebase)

# After loading topics, query best quiz scores
slugs = [t.slug for t in topics]
if slugs:
    scores_result = await db.execute(
        select(
            QuizAttempt.topic_slug,
            func.max(QuizAttempt.score * 1.0 / QuizAttempt.max_score).label("best_pct"),
        )
        .where(QuizAttempt.topic_slug.in_(slugs))
        .group_by(QuizAttempt.topic_slug)
    )
    best_scores = {row.topic_slug: row.best_pct for row in scores_result}
else:
    best_scores = {}
```

```html
<!-- In topic_list.html — extend existing template -->
<!-- Completion badge logic:
     - quiz_passed: best_scores[topic.slug] >= 0.6
     - reading: topic.content_it is not None, no passing score
     - not_started: topic.content_it is None
-->
{% set best = best_scores.get(topic.slug, 0) %}
{% if best >= 0.6 %}
  <span class="badge badge-success badge-xs ml-auto">Completato</span>
{% elif topic.content_it %}
  <span class="badge badge-warning badge-xs ml-auto">In corso</span>
{% else %}
  <span class="badge badge-ghost badge-xs ml-auto">Non iniziato</span>
{% endif %}
```

### Chat System Prompt with Progress Context (CHAT-03 + CHAT-04)

```python
# Source: project claude.py patterns + REQUIREMENTS.md CHAT-03/04 spec

async def build_chat_system_prompt(
    topic_slug: str,
    db: AsyncSession,
) -> str:
    """Build context-aware system prompt for chat."""
    parts = [
        "Sei un assistente per la preparazione all'esame di professioni sanitarie e osteopatia.",
        "Rispondi in italiano. Sii conciso e focalizzato sull'esame.",
    ]

    # CHAT-03: Topic context
    if topic_slug:
        topic = await db.scalar(select(Topic).where(Topic.slug == topic_slug))
        if topic:
            parts.append(
                f"\nL'utente sta studiando: '{topic.title_it}' ({topic.title_en})."
                " Rispondi nel contesto di questo argomento."
            )

    # CHAT-04: Progress context (compact JSON summary)
    summary = await get_progress_summary(db)
    # Format weaknesses: subjects with avg_accuracy < 0.5
    weak = [
        s for s, q in summary["quiz_by_subject"].items()
        if q.avg_accuracy is not None and q.avg_accuracy < 0.5
    ]
    if weak:
        parts.append(f"\nArgomenti deboli dell'utente (punteggio quiz < 50%): {', '.join(weak)}.")
    parts.append(
        f"\nStato ripasso carte: {summary['srs']['due']} in scadenza oggi, "
        f"{summary['srs']['learned']} apprese, {summary['srs']['new']} nuove."
    )

    return "\n".join(parts)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| HTMX v1 `hx-sse` attribute | HTMX v2 SSE extension (`hx-ext="sse"`, `sse-connect`) | HTMX 2.0 (2024) | v1 attributes don't work in HTMX 2.0.4 (which this project uses) |
| Sync `anthropic.Anthropic().messages.stream()` | `AsyncAnthropic().messages.stream()` with `async with` | SDK design (always) | Must use async client in async FastAPI — sync blocks event loop |
| WebSocket for chat | SSE (Server-Sent Events) | Ongoing | SSE is simpler, works over HTTP, no upgrade needed — sufficient for one-way chat stream |
| `client.messages.create(stream=True)` (raw) | `client.messages.stream()` context manager | Anthropic SDK v0.7+ | stream() handles event parsing, text accumulation, and cleanup |

**Deprecated/outdated:**
- HTMX v1 `hx-sse` attribute: Does not exist in HTMX 2.0.4. Must use `hx-ext="sse"` with the htmx-ext-sse extension loaded.
- Sync Anthropic client in async context: Will block uvicorn worker, causing request queue backup.

---

## Open Questions

1. **Chat panel placement: slide-over vs. inline card**
   - What we know: The app is single-column mobile-first at 560px max-width. No existing modal/drawer pattern.
   - What's unclear: Whether a bottom slide-up panel or an inline card below topic content is preferable UX on mobile.
   - Recommendation: Use an inline card below the quiz button on topic pages, toggled by a "Chiedi a Claude" button. DaisyUI `collapse` or simple `hidden/block` toggle. No modal needed — simpler and avoids z-index issues on iOS Safari.

2. **Progress dashboard route: new tab in nav vs. subpage**
   - What we know: Nav has 3 tabs (Argomenti, Ripasso, Esame). Adding a 4th squeezes layout at 560px.
   - What's unclear: Whether to add a 4th nav tab or put progress as a link from the home page.
   - Recommendation: Add progress as a link/button at top of home index page rather than a 4th nav tab. Avoids nav layout changes and inline styling rework.

3. **Gunicorn worker type for SSE**
   - What we know: Service uses gunicorn bound to Tailscale IP. MEMORY.md mentions `.venv/bin/uvicorn` but service uses gunicorn.
   - What's unclear: Whether gunicorn is configured with `UvicornWorker` or default sync workers. Sync workers will NOT stream SSE.
   - Recommendation: Verify `/etc/systemd/system/osteoprep.service` uses `--worker-class uvicorn.workers.UvicornWorker`. If not, add it. This is a hard blocker for SSE streaming.

---

## Sources

### Primary (HIGH confidence)
- Anthropic SDK docs (platform.claude.com/docs/en/api/messages-streaming) — streaming API, async stream context manager, text_stream iterator
- GitHub anthropics/anthropic-sdk-python (github.com/anthropics/anthropic-sdk-python) — AsyncAnthropic async patterns
- HTMX SSE extension docs (htmx.org/extensions/sse/) — hx-ext="sse", sse-connect, sse-swap for HTMX 2.x
- FastAPI docs (fastapi.tiangolo.com) — StreamingResponse, media_type="text/event-stream"
- Project codebase (app/services/claude.py, app/routers/*, app/models.py) — existing patterns

### Secondary (MEDIUM confidence)
- WebSearch: FastAPI SSE streaming patterns — multiple Medium/blog posts corroborate StreamingResponse + async generator approach
- WebSearch: HTMX SSE chat examples — multiple 2025 articles confirm hx-ext="sse" as the HTMX 2.x approach

### Tertiary (LOW confidence)
- Specific gunicorn buffering behavior with SSE — based on general knowledge of gunicorn/nginx buffering; needs verification against actual service config

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Anthropic SDK 0.84.0 and FastAPI 0.115.14 both verified in installed packages; streaming APIs verified from official docs
- Architecture: HIGH — All patterns verified against official docs and existing codebase conventions
- Pitfalls: MEDIUM — SSE pitfalls from multiple sources; gunicorn/buffering pitfall is LOW (single source, needs service config check)

**Research date:** 2026-02-28
**Valid until:** 2026-03-30 (Anthropic SDK and HTMX extension are actively developed; streaming APIs stable)
