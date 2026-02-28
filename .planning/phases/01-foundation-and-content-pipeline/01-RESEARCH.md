# Phase 1: Foundation and Content Pipeline - Research

**Researched:** 2026-02-28
**Domain:** FastAPI + HTMX + SQLite + Anthropic Claude API — server-side rendered web app with AI content pipeline
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Frontend approach**
- HTMX + Jinja2 templates served by FastAPI — no npm, no build step, no SPA framework
- HTMX handles dynamic content swaps (language toggle, explainer loading) with minimal JS
- Tailwind CSS via CDN for styling — no build tooling required
- This maximizes development speed under the 3-week deadline

**Topic browsing layout**
- Single home page with subject accordion — subjects (Biology, Chemistry, etc.) as collapsible sections
- Topics listed under each subject once expanded
- One tap to expand subject, one tap to open explainer — two-tap max to content
- No separate pages per subject

**Explainer presentation**
- One long scrolling page per topic — no pagination
- Sticky top header: topic name + IT | EN language toggle
- Uncertainty markers rendered as inline amber callout blocks within the text — visible in context, not footnotes or a disclaimer header

**Language toggle UX**
- IT | EN segmented control in the sticky explainer header
- Switching swaps content in-place via HTMX — no full page reload, no URL change
- Toggle state remembered in localStorage between visits

### Claude's Discretion
- Exact color palette and typography (keep it clean, readable, medical-study appropriate)
- SQLite schema column naming conventions
- Nginx/Uvicorn config details
- Error states (API failure during generation, network issues)
- Loading state while explainer is being generated for the first time
- Exact prompt engineering for uncertainty markers

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONT-01 | User can browse study topics organized by subject (Biology, Chemistry, Physics/Math, Logic) | Subject accordion on home page; topics table with `subject` column; seed data for initial topic list |
| CONT-02 | User can read an AI-generated explainer for each topic, generated on first access and cached in the database | Generate-once-cache pattern; topics table `content_it`/`content_en` columns; Claude API messages.create; AsyncAnthropic for non-blocking generation |
| CONT-03 | User can toggle between Italian and English versions of any explainer | HTMX `hx-get` + `hx-swap="innerHTML"` on toggle; language pref in localStorage; two content columns in DB |
| CONT-04 | Explainers include hallucination mitigation (AI expresses uncertainty where appropriate, links to authoritative sources where possible) | System prompt with explicit uncertainty permission; inline amber callout blocks for low-confidence claims; uncertainty instruction patterns from official Anthropic docs |
| PROG-03 | Progress data persists across sessions (server-side SQLite storage) | SQLite with WAL mode; aiosqlite async driver; all writes committed before response returns; server restart test on day 1 |
</phase_requirements>

---

## Summary

Phase 1 establishes the entire technical foundation that all later phases depend on. It involves three separable concerns: (1) project scaffold — FastAPI app, Nginx/Uvicorn, systemd, Tailscale HTTPS, static files; (2) SQLite schema and persistence layer — bilingual content columns, topic list seeding, WAL mode, Alembic migrations; and (3) AI content pipeline — generate-once-cache pattern using AsyncAnthropic, uncertainty-aware system prompt, and HTMX-driven topic browsing and language toggle UI.

The technical stack is fully locked by user decisions: FastAPI + Jinja2 + HTMX + Tailwind CDN + SQLite + aiosqlite + Anthropic Python SDK. All of these are verified current and well-documented. The generate-once-cache pattern (check DB for `content_it`/`content_en`, call Claude only when NULL, store result) is the critical architectural decision for this phase — it prevents API cost runaway and ensures subsequent page loads are instant.

Uncertainty markers (CONT-04) are best addressed at the system prompt level: explicitly instruct Claude to flag uncertain claims inline using a consistent format (e.g., a specific phrase or XML tag), then render those markers as amber callout blocks in the Jinja2 template. This is more reliable than post-processing the output and produces naturally integrated uncertainty markers rather than a disclaimer footer.

**Primary recommendation:** Build plans in two units — (01-01) scaffold + schema + infrastructure, then (01-02) topic browsing UI + content generation pipeline + language toggle. The schema must be locked before any content is generated because retrofitting bilingual columns is expensive.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115.x | HTTP API + Jinja2 template serving | Async-native; native Jinja2 support; first-class HTMX compatibility; standard for Python web + AI apps |
| Uvicorn | 0.32.x | ASGI server | Standard async server for FastAPI |
| Gunicorn | 23.x | Process manager for Uvicorn workers | Production process supervision; handles crashes and restarts; pairs with UvicornWorker |
| Jinja2 | 3.1.x | HTML templating | Built into Starlette (FastAPI base); server-side rendering for HTMX fragments |
| HTMX | 2.0.x | DOM partial updates without JS framework | 14KB CDN library; `hx-get`, `hx-swap`, `hx-target` handle all Phase 1 interactions |
| Tailwind CSS | 3.4.x | Utility CSS | CDN version requires zero build tooling; mobile-first |
| DaisyUI | 4.x | UI component library | Semantic components (accordion, card, btn, badge) via CDN; no JS conflicts; mobile-responsive |
| anthropic | 0.84.x | Claude API client | Official SDK; `AsyncAnthropic` for non-blocking generation; type-safe |
| SQLAlchemy | 2.0.x | ORM + async engine | Async-native in 2.0; maps to `sqlite+aiosqlite://` |
| aiosqlite | 0.20.x | Async SQLite driver | Required by SQLAlchemy async for SQLite; asyncio-compatible |
| Alembic | 1.13.x | DB schema migrations | Manage schema changes without wiping data; essential for multi-phase project |
| python-multipart | 0.0.12+ | Form parsing | Required for FastAPI form submissions |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| httpx | 0.27.x | HTTP client for testing | `TestClient` in FastAPI tests; async-compatible |
| python-dotenv | 1.0.x | `.env` file loading | Load `ANTHROPIC_API_KEY` from `.env` in development |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| HTMX | Alpine.js | Alpine.js is JS-only state management; HTMX handles server round-trips natively — better for SSR content swaps |
| HTMX | Vanilla JS fetch | More boilerplate; HTMX declarative attributes are faster to write and read |
| Tailwind CDN | PostCSS build | PostCSS adds 30+ minutes of tooling setup; CDN is identical in capability for this project size |
| DaisyUI | Custom CSS | DaisyUI accordion and card components are production-quality; custom CSS takes longer |
| aiosqlite direct | SQLAlchemy 2.0 async | aiosqlite direct is simpler but SQLAlchemy gives Alembic migration support — essential for multi-phase project |

**Installation:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "fastapi[standard]==0.115.*" "uvicorn[standard]==0.32.*" gunicorn \
    "sqlalchemy[asyncio]==2.0.*" aiosqlite alembic \
    "anthropic==0.84.*" python-multipart jinja2 \
    python-dotenv httpx
```

**Frontend assets (no npm needed — add to base template `<head>`):**
```html
<link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/htmx.org@2.0.4" defer></script>
```

---

## Architecture Patterns

### Recommended Project Structure
```
/root/projects/osteoprep/
├── app/
│   ├── main.py              # FastAPI app, lifespan, router registration
│   ├── database.py          # Async engine, session factory, lifespan init
│   ├── models.py            # SQLAlchemy ORM models (topics, settings)
│   ├── routers/
│   │   ├── pages.py         # Full-page HTML routes (GET / → home, GET /topic/{slug})
│   │   └── fragments.py     # HTMX fragment routes (GET /topic/{slug}/content?lang=it)
│   ├── services/
│   │   └── claude.py        # AsyncAnthropic client, prompt builders, generate_explainer()
│   └── templates/
│       ├── base.html        # Base layout: viewport meta, CDN includes, main content block
│       ├── index.html       # Home page: subject accordion listing topics
│       ├── topic.html       # Topic page: sticky header + explainer content block
│       └── fragments/
│           └── explainer_content.html  # HTMX partial: just the content body, swapped on lang toggle
├── static/
│   └── app.js               # Minimal JS: localStorage lang pref, accordion state
├── data/
│   └── osteoprep.db         # SQLite database file
├── migrations/              # Alembic migration files
│   ├── env.py
│   └── versions/
├── alembic.ini
├── .env                     # ANTHROPIC_API_KEY (gitignored)
├── requirements.txt
└── seed_topics.py           # One-time script to insert initial topic list
```

### Pattern 1: Generate-Once-Cache for Explainer Content

**What:** When a topic page is loaded, check the DB for existing `content_it`/`content_en`. If present, serve directly. If NULL (never generated), call Claude, store result, then serve. Subsequent requests never call Claude.

**When to use:** Every content field that is AI-generated. This is the core reliability and cost-control pattern for the entire app.

**Example:**
```python
# Source: verified pattern from .planning/research/ARCHITECTURE.md + official Anthropic SDK docs
# app/routers/pages.py

@router.get("/topic/{slug}", response_class=HTMLResponse)
async def topic_page(
    request: Request,
    slug: str,
    lang: str = "it",
    db: AsyncSession = Depends(get_db),
):
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    if topic is None:
        raise HTTPException(status_code=404)

    # Generate if missing — called at most once per topic per language
    content_field = "content_it" if lang == "it" else "content_en"
    if getattr(topic, content_field) is None:
        content = await generate_explainer(topic.title_it, lang)
        setattr(topic, content_field, content)
        if topic.generated_at is None:
            topic.generated_at = datetime.utcnow()
        await db.commit()

    return templates.TemplateResponse(
        request=request,
        name="topic.html",
        context={"topic": topic, "lang": lang},
    )
```

### Pattern 2: HTMX Language Toggle (In-Place Content Swap)

**What:** The IT | EN toggle sends an HTMX GET request to a fragment endpoint. The server returns only the content HTML (not a full page). HTMX swaps it into the content container. No full reload, no URL change.

**When to use:** Any content field that has two language variants (explainer body, topic title).

**Example:**
```html
<!-- Source: htmx.org/docs + verified in TestDriven.io FastAPI+HTMX tutorial -->
<!-- In topic.html: sticky header with language toggle -->
<div id="lang-toggle" class="flex gap-2">
  <button
    hx-get="/topic/{{ topic.slug }}/content?lang=it"
    hx-target="#explainer-content"
    hx-swap="innerHTML"
    onclick="localStorage.setItem('lang', 'it')"
    class="btn btn-sm {% if lang == 'it' %}btn-primary{% else %}btn-ghost{% endif %}">
    IT
  </button>
  <button
    hx-get="/topic/{{ topic.slug }}/content?lang=en"
    hx-target="#explainer-content"
    hx-swap="innerHTML"
    onclick="localStorage.setItem('lang', 'en')"
    class="btn btn-sm {% if lang == 'en' %}btn-primary{% else %}btn-ghost{% endif %}">
    EN
  </button>
</div>

<!-- Content container that HTMX replaces -->
<div id="explainer-content">
  {% include "fragments/explainer_content.html" %}
</div>
```

```python
# app/routers/fragments.py
@router.get("/topic/{slug}/content", response_class=HTMLResponse)
async def topic_content_fragment(
    request: Request,
    slug: str,
    lang: str = "it",
    db: AsyncSession = Depends(get_db),
):
    topic = await db.scalar(select(Topic).where(Topic.slug == slug))
    # Same generate-if-missing logic as full page route
    content_field = "content_it" if lang == "it" else "content_en"
    if getattr(topic, content_field) is None:
        content = await generate_explainer(topic.title_it, lang)
        setattr(topic, content_field, content)
        await db.commit()
    return templates.TemplateResponse(
        request=request,
        name="fragments/explainer_content.html",
        context={"topic": topic, "lang": lang},
    )
```

### Pattern 3: Subject Accordion (HTMX Lazy Load)

**What:** Subject sections are shown collapsed by default. Clicking a subject header triggers an HTMX GET to fetch its topic list. DaisyUI `collapse` component provides the expand/collapse CSS behavior.

**When to use:** Home page subject listing. Avoids fetching all topic lists on initial load.

**Example:**
```html
<!-- Source: DaisyUI collapse component docs + htmx.org lazy loading pattern -->
<!-- In index.html -->
{% for subject in subjects %}
<div class="collapse collapse-arrow bg-base-200 mb-2">
  <input type="checkbox" name="subject-{{ subject.slug }}" />
  <div class="collapse-title text-xl font-medium">
    {{ subject.name }}
  </div>
  <div class="collapse-content"
       hx-get="/subjects/{{ subject.slug }}/topics"
       hx-trigger="revealed"
       hx-swap="innerHTML">
    <span class="loading loading-spinner loading-sm"></span>
  </div>
</div>
{% endfor %}
```

`hx-trigger="revealed"` fires the HTMX request only when the element becomes visible — this lazy-loads the topic list without a separate JavaScript event listener.

### Pattern 4: FastAPI Lifespan for DB Initialization

**What:** Use `asynccontextmanager` lifespan to initialize the database (create tables, enable WAL mode) before the app starts accepting requests. This is the modern FastAPI pattern replacing deprecated `@app.on_event("startup")`.

**When to use:** All database setup — table creation, PRAGMA configuration, initial seed data checks.

**Example:**
```python
# Source: FastAPI official docs (fastapi.tiangolo.com/advanced/events) + verified 2025 pattern
# app/main.py

from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables, enable WAL mode
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: nothing needed for SQLite

app = FastAPI(lifespan=lifespan)
```

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import event

DATABASE_URL = "sqlite+aiosqlite:///./data/osteoprep.db"
engine = create_async_engine(DATABASE_URL, echo=False)

# WAL mode: enables concurrent reads while writing (important for async)
@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA synchronous=NORMAL")

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Pattern 5: Uncertainty Marker System Prompt

**What:** Instruct Claude in the system prompt to flag uncertain claims using a specific inline format. The Jinja2 template then renders those markers as amber callout blocks.

**When to use:** All explainer content generation calls. Must be in the system prompt (not the user prompt) so it applies to every generation.

**Example:**
```python
# Source: Anthropic official docs platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations
# app/services/claude.py

EXPLAINER_SYSTEM_PROMPT = """You are a study assistant for Italian osteopathy/medicine entry exams.
Generate clear, accurate explanations for exam topics.

IMPORTANT UNCERTAINTY RULES:
- If you are not certain about a specific fact, anatomy detail, or chemical value, wrap it in [UNCERTAIN: your text here]
- Never guess on numerical values (concentrations, measurements, counts) — state [UNCERTAIN: approximate value] instead
- Never fabricate Italian-specific curriculum details — if unsure, say so explicitly
- You may say "I am not certain about this specific detail" rather than inventing a confident answer

Generate the explanation in {lang}. Structure with clear headings and bullet points suitable for exam study."""

async def generate_explainer(title: str, lang: str) -> str:
    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = await client.messages.create(
        model="claude-haiku-4-5-20251001",  # Haiku: fast + cheap for content gen; use Sonnet for complex topics
        max_tokens=2048,
        system=EXPLAINER_SYSTEM_PROMPT.format(lang="Italian" if lang == "it" else "English"),
        messages=[{
            "role": "user",
            "content": f"Explain '{title}' for the Italian professioni sanitarie/osteopathy entry exam."
        }]
    )
    return message.content[0].text
```

Then in the Jinja2 template, render `[UNCERTAIN: ...]` blocks as amber callouts:
```python
# In app/main.py or a Jinja2 filter
import re

def render_uncertainty_markers(text: str) -> str:
    """Convert [UNCERTAIN: text] markers to amber callout HTML."""
    return re.sub(
        r'\[UNCERTAIN: ([^\]]+)\]',
        r'<span class="inline-block bg-amber-100 border border-amber-300 text-amber-800 '
        r'text-sm px-2 py-0.5 rounded mx-0.5">'
        r'<strong>?</strong> \1</span>',
        text
    )

templates.env.filters["uncertainty"] = render_uncertainty_markers
```

### Anti-Patterns to Avoid

- **Generating content on every request:** Never call `client.messages.create()` if `content_it` or `content_en` is already populated. Always check DB first.
- **Client-side Claude calls:** The API key must never reach the browser. All Claude calls go through FastAPI backend only.
- **Using `@app.on_event("startup")`:** This is deprecated. Use `asynccontextmanager` lifespan instead.
- **Mixing sync and async SQLite access:** Never use `sqlite3` directly in an async FastAPI route. Always use `aiosqlite` via SQLAlchemy's async session.
- **Skipping WAL mode:** Without WAL mode, a SQLite write blocks all reads. With async concurrency, this causes hung requests during content generation.
- **Storing language preference only in a cookie or query param:** Use `localStorage` for toggle state so it survives browser closes. The server reads the `lang` query param; JavaScript reads localStorage to set the initial state on page load.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTML partial updates | Custom fetch + innerHTML JS | HTMX `hx-get` + `hx-swap` | HTMX handles loading indicators, error states, request lifecycle out of the box |
| CSS accordion expand/collapse | Custom JS toggle | DaisyUI `collapse` component | Pure CSS, accessible, no JS needed, mobile-tested |
| Utility CSS | Custom stylesheet | Tailwind CDN | Writing custom CSS for a 3-week sprint wastes hours; Tailwind utilities cover every case |
| DB connection lifecycle | Manual open/close | SQLAlchemy `async_sessionmaker` + `Depends(get_db)` | Session cleanup, transaction handling, error rollback all managed automatically |
| Schema migrations | ALTER TABLE SQL scripts | Alembic | Manual migration scripts break on out-of-order application; Alembic tracks state |
| API key management | Hardcoded strings | `python-dotenv` + `os.environ` | Prevents key exposure in git history |
| iPhone Safari viewport issues | Custom JS scroll fix | Tailwind `overflow-y-auto` + DaisyUI mobile-first defaults | DaisyUI components are designed for Safari mobile; avoid `position: fixed` on scroll containers |

**Key insight:** HTMX + DaisyUI removes the need for almost all custom frontend code. The accordion, loading states, inline swaps, and responsive layout are provided by these libraries. Every hour spent writing custom CSS/JS is an hour not spent on content coverage.

---

## Common Pitfalls

### Pitfall 1: Bilingual Schema Not Established in Phase 1
**What goes wrong:** Content stored in a single `content` column. When language toggle is added (Phase 1 requirement), requires migrating the table and backfilling. Generated content may need to be re-generated in both languages.
**Why it happens:** Building English first and "adding Italian later" feels simpler.
**How to avoid:** The `topics` table MUST have `content_it TEXT` and `content_en TEXT` as separate columns from day one. Generate both on first access in a single Claude call (one prompt, JSON response with `it` and `en` keys).
**Warning signs:** Seeing `content TEXT` in a migration without a `_it` or `_en` suffix.

### Pitfall 2: Sticky Header Broken on iPhone Safari
**What goes wrong:** `position: sticky` breaks silently on iPhone Safari when any ancestor element has `overflow: hidden`, `overflow: auto`, or `overflow: scroll`. The sticky header scrolls away instead of staying fixed.
**Why it happens:** Tailwind's `overflow` utilities are commonly applied to layout containers. One `overflow-hidden` on a parent kills stickiness globally.
**How to avoid:** Test sticky header on actual iPhone Safari early. Structure the page so the sticky header's parent chain has no `overflow` property set. Use `overflow-y-auto` only on the body content, not on any ancestor of the sticky header.
**Warning signs:** Header sticks on desktop Chrome but scrolls on iPhone.

### Pitfall 3: HTMX SSE Bug on Safari iOS 17+ (Not Applicable to Phase 1)
**What goes wrong:** HTMX's SSE extension does not work on Safari iOS 17.4. (This affects Phase 3 AI chat streaming.)
**Why it happens:** WebKit SSE event handling regression. HTMX SSE extension relies on EventSource API.
**How to avoid:** Phase 1 does not use SSE — explainer generation is a synchronous blocking call. Flag this as a known issue for Phase 3 chat implementation. Workaround: use vanilla `EventSource` JavaScript, not HTMX SSE extension.
**Warning signs:** Only relevant in Phase 3 when streaming chat is added.

### Pitfall 4: `generate_explainer()` Called Concurrently for the Same Topic
**What goes wrong:** Two requests for the same uncached topic arrive simultaneously. Both find `content_it IS NULL`, both call Claude, both write to the DB. Two API calls made instead of one; second write silently overwrites first.
**Why it happens:** Async concurrency with no locking around the cache check + generate + write sequence.
**How to avoid:** Use a simple in-memory set of "currently generating" topic slugs. If a slug is in the set, the second request waits briefly and then reads from DB. For a single-user app this is overkill — practical mitigation is simply to show a loading indicator and make it visually obvious that only one tab should be open per topic during first generation.
**Warning signs:** Claude API call count is more than the number of unique topics.

### Pitfall 5: Alembic Not Initialized Before First DB Write
**What goes wrong:** The app creates tables via `create_all()` on startup. Later, a schema change needs to be made. Alembic has no migration history because it was never initialized before the first table creation, so it cannot determine what to diff against.
**Why it happens:** Skipping Alembic init because "we can always add it later."
**How to avoid:** Run `alembic init migrations` and set up `env.py` before writing any table creation code. The first migration should be `initial_schema`. Even if it's never used for this phase, it establishes the baseline for Phase 2 schema additions (flashcards, card_state).
**Warning signs:** `alembic revision --autogenerate` produces a migration that would drop all existing tables.

### Pitfall 6: Uncertainty Markers Never Appearing in Output
**What goes wrong:** The system prompt instructs Claude to use `[UNCERTAIN: ...]` markers, but Claude almost never produces them because the instruction lacks specificity about when to apply them. Explainers come out with confident-sounding but potentially wrong details.
**Why it happens:** Claude defaults to confident tone. The uncertainty instruction needs to give explicit examples of what kinds of claims should be marked.
**How to avoid:** The system prompt must include concrete examples: "Mark with [UNCERTAIN:] when stating specific numerical values (e.g., exact percentages, concentrations, molecular weights), obscure Italian curriculum specifics, or claims where standard sources disagree." Test by asking about a topic with known uncertainty (e.g., exact ATP yield from glycolysis — contested in recent literature).
**Warning signs:** Explainer contains specific numerical values without any uncertainty markers; "about 36-38 ATP" stated as exact "38 ATP".

---

## Code Examples

Verified patterns from official sources:

### SQLite WAL Mode via SQLAlchemy Event
```python
# Source: SQLAlchemy official docs + .planning/research/STACK.md (verified Feb 2026)
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///./data/osteoprep.db")

@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA synchronous=NORMAL")
```

### Claude Explainer Generation (Non-Streaming)
```python
# Source: Anthropic SDK docs platform.claude.com/docs/en/api/messages (verified Feb 2026)
from anthropic import AsyncAnthropic

async def generate_explainer(title: str, lang: str = "it") -> str:
    client = AsyncAnthropic()  # reads ANTHROPIC_API_KEY from env
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2048,
        system=EXPLAINER_SYSTEM_PROMPT.format(
            lang="Italian" if lang == "it" else "English"
        ),
        messages=[{"role": "user", "content": f"Explain: {title}"}]
    )
    return response.content[0].text
```

Note: For Phase 1, use `claude-haiku-4-5-20251001` (fastest, cheapest: $1/$5 per MTok). This is appropriate for cached explainer generation. If output quality is insufficient, switch to `claude-sonnet-4-6` ($3/$15 per MTok).

### Topics ORM Model (Bilingual Schema)
```python
# Source: verified pattern from .planning/research/ARCHITECTURE.md
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Topic(Base):
    __tablename__ = "topics"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title_it: Mapped[str] = mapped_column(String(200), nullable=False)
    title_en: Mapped[str] = mapped_column(String(200), nullable=False)
    subject: Mapped[str] = mapped_column(String(50), nullable=False)  # "biology"|"chemistry"|...
    order_in_subject: Mapped[int] = mapped_column(default=0)  # for sorted display
    content_it: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_en: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
```

### HTMX Loading Indicator Pattern
```html
<!-- Source: htmx.org/docs — htmx-indicator pattern -->
<!-- Shows spinner while HTMX request is in flight (e.g., first-time generation) -->
<div id="explainer-content" hx-indicator="#loading-indicator">
  {% include "fragments/explainer_content.html" %}
</div>
<div id="loading-indicator" class="htmx-indicator flex justify-center py-8">
  <span class="loading loading-spinner loading-lg text-primary"></span>
  <span class="ml-2 text-base-content/60">Generating explainer...</span>
</div>
```

### Nginx Config for Uvicorn Reverse Proxy
```nginx
# Source: FastAPI official docs + verified production pattern (Feb 2026)
# /etc/nginx/sites-available/osteoprep

server {
    listen 443 ssl;
    server_name <your-tailscale-hostname>.ts.net;

    ssl_certificate /etc/ssl/certs/tailscale-cert.pem;
    ssl_certificate_key /etc/ssl/private/tailscale-key.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        # Required for long-running Claude generation requests
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }
}
```

### Systemd Service File
```ini
# Source: verified Ubuntu systemd pattern (Feb 2026)
# /etc/systemd/system/osteoprep.service

[Unit]
Description=OsteoPrep FastAPI App
After=network.target

[Service]
User=root
WorkingDirectory=/root/projects/osteoprep
EnvironmentFile=/root/projects/osteoprep/.env
ExecStart=/root/projects/osteoprep/.venv/bin/gunicorn \
    -w 2 -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8080 \
    --timeout 120 \
    app.main:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Note: `--timeout 120` is required because Claude generation can take 10-30 seconds. Without this, Gunicorn's default 30-second worker timeout will kill in-progress generation requests.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@app.on_event("startup")` | `asynccontextmanager` lifespan | FastAPI 0.93+ | Deprecation warning eliminated; cleaner lifecycle management |
| SM-2 SRS algorithm | FSRS-5 (py-fsrs) | Anki adopted FSRS in 2023 | 20-30% fewer reviews for same retention — critical for 3-week deadline |
| `claude-3-haiku` model | `claude-haiku-4-5-20251001` | Feb 2026 | Old haiku deprecated April 2026; new haiku is faster with near-frontier intelligence |
| Gunicorn + UvicornWorker (mandatory) | Uvicorn `--workers N` (sufficient) | Uvicorn 0.30+ | Either works; Gunicorn still recommended for its mature process supervision |

**Deprecated/outdated:**
- `claude-3-haiku-20240307`: Deprecated, retiring April 19 2026. Migrate to `claude-haiku-4-5-20251001`.
- `@app.on_event("startup")`: Deprecated in FastAPI. Use `asynccontextmanager` lifespan.
- Tailwind v4 CDN (`@tailwindcss/browser@4`): v4 targets modern browsers only (Safari 16.4+). v3 CDN (`cdn.tailwindcss.com`) has broader compatibility and should be used for iPhone safety.

---

## Open Questions

1. **Nginx and Tailscale cert paths on this server**
   - What we know: Server has Tailscale running and is accessible on tailnet; `tailscale cert` can provision TLS certs
   - What's unclear: Whether Nginx is already installed; what port OsteoPrep should use relative to Open WebUI on port 3000
   - Recommendation: Plan 01-01 should verify Nginx status, determine port (8080 internal, expose via Nginx on 8443 or path-prefix), and run `tailscale cert` as a setup task

2. **Initial topic list scope for seeding**
   - What we know: Subjects are Biology, Chemistry, Physics/Math, Logic; the official MUR curriculum is available
   - What's unclear: Exact count of topics to seed in Phase 1 vs Phase 4
   - Recommendation: Seed 15-20 high-priority topics (Biology + Chemistry core topics) in Phase 1; Phase 4 completes full syllabus coverage. STATE.md notes: "Official MUR curriculum topic list should be seeded as DB checklist in Phase 1 to gate Phase 4 completion" — so seed the full checklist as stubs (no content yet) and generate content for core topics

3. **Both-languages-at-once generation vs lazy per-language**
   - What we know: Generating both IT and EN in one Claude call is possible (JSON response with `it` and `en` keys) and saves one API call
   - What's unclear: Whether the quality is better from one bilingual call or two separate language-specific calls
   - Recommendation: Generate both languages in a single call on first access. Prompt: "Return a JSON object with keys 'it' and 'en', each containing the full explanation in that language." This is simpler and uses one API call.

---

## Sources

### Primary (HIGH confidence)
- Anthropic models overview — `platform.claude.com/docs/en/about-claude/models/overview` — model IDs, pricing, current recommended models (Feb 2026)
- Anthropic reduce-hallucinations guide — `platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/reduce-hallucinations` — uncertainty marker techniques
- FastAPI templates docs — `fastapi.tiangolo.com/advanced/templates/` — Jinja2Templates setup pattern
- FastAPI SQL databases docs — `fastapi.tiangolo.com/tutorial/sql-databases/` — lifespan + ORM pattern
- HTMX docs — `htmx.org/docs/` — `hx-swap`, `hx-target`, `hx-indicator`, `hx-trigger="revealed"`
- `.planning/research/STACK.md` — verified complete tech stack with versions (Feb 2026)
- `.planning/research/ARCHITECTURE.md` — verified data models, API endpoints, data flow patterns (Feb 2026)
- `.planning/research/PITFALLS.md` — verified domain-specific pitfalls with mitigations (Feb 2026)

### Secondary (MEDIUM confidence)
- TestDriven.io FastAPI+HTMX tutorial — `testdriven.io/blog/fastapi-htmx/` — HTMX fragment return pattern
- DaisyUI collapse component — `daisyui.com` — accordion pattern for subject listing
- SQLite WAL mode docs — `sqlite.org/wal.html` — WAL mode benefits for async read/write concurrency
- Sling Academy: FastAPI aiosqlite patterns — verified aiosqlite context manager + PRAGMA WAL

### Tertiary (LOW confidence)
- HTMX SSE Safari iOS 17.4 bug — `github.com/bigskysoftware/htmx/issues/2388` — flagged but Phase 1 doesn't use SSE; relevant for Phase 3 planning only

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions verified against PyPI and official docs (Feb 2026)
- Architecture: HIGH — patterns verified against FastAPI and HTMX official docs; data models from ARCHITECTURE.md already validated
- Pitfalls: HIGH — bilingual schema, Safari sticky, WAL mode pitfalls all verified with official or authoritative sources
- Uncertainty markers: HIGH — Anthropic official hallucination reduction docs confirm the "allow I don't know" technique with examples

**Research date:** 2026-02-28
**Valid until:** 2026-03-28 (stable stack; Anthropic model IDs change frequently — recheck if generating content after this date)
