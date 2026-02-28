# Technology Stack

**Project:** OsteoPrep — Italian Osteopathy/Medicine Entry Exam Prep App
**Researched:** 2026-02-28
**Overall confidence:** HIGH (all choices verified against current PyPI, official docs, community consensus)

---

## Recommended Stack

### Backend Framework

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| FastAPI | 0.115.x (latest: 0.115.14) | HTTP API + server-side rendering | Async-native Python framework; native Jinja2 template support; automatic OpenAPI docs; first-class streaming for Claude SSE responses; ideal for single-developer projects |
| Uvicorn | 0.32.x | ASGI server | The standard ASGI runner for FastAPI; async-first; pairs with Gunicorn for process management in production |
| Gunicorn | 23.x | Process manager | Manages Uvicorn workers; handles restarts/crashes; needed for production reliability on Hetzner |
| Jinja2 | 3.1.x | HTML templating | Built into Starlette (FastAPI's base); server-side rendering for HTMX fragments; zero JS build step |
| python-multipart | 0.0.12+ | Form parsing | Required for FastAPI form submissions |

**Why FastAPI over alternatives:**
- **Not Next.js**: Next.js is a React full-stack framework requiring Node.js, npm toolchain, and TypeScript/JSX expertise. For a Python-backend project with Claude API, it adds unnecessary complexity and a separate runtime.
- **Not Flask**: Flask lacks native async support. Claude streaming requires `async def` endpoints. FastAPI's async-first design is the right match.
- **Not Express.js**: Node.js would mean writing the AI integration layer in JS rather than Python, where the Anthropic SDK is more mature and better documented.

### AI Integration

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| anthropic | 0.84.0 (Feb 2026) | Claude API client | Official Anthropic Python SDK; AsyncAnthropic client for non-blocking requests; built-in streaming via `client.messages.stream()`; type-safe |

**Claude streaming pattern** (FastAPI + AsyncAnthropic):
```python
from anthropic import AsyncAnthropic
from fastapi.responses import StreamingResponse

client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

@app.get("/explain/{topic}")
async def explain_topic(topic: str):
    async def stream_response():
        async with client.messages.stream(
            model="claude-opus-4-6",
            max_tokens=1024,
            messages=[{"role": "user", "content": f"Explain {topic} for Italian medicine entry exam"}]
        ) as stream:
            async for text in stream.text_stream:
                yield f"data: {text}\n\n"
    return StreamingResponse(stream_response(), media_type="text/event-stream")
```

**Why not LangChain:** Adds abstraction overhead with no benefit for a single-provider, single-use-case app. Use the Anthropic SDK directly.

### Database

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| SQLite | 3.45+ (bundled with Python) | Primary data store | Zero-configuration, single-file, no separate process; perfect for single-user; runs on the same server thread; WAL mode enables concurrent async reads |
| SQLAlchemy | 2.0.x | ORM + query builder | Async-native in 2.0; maps to `sqlite+aiosqlite://`; handles schema migrations cleanly |
| aiosqlite | 0.20.x | Async SQLite driver | Wraps SQLite for use with asyncio; required by SQLAlchemy async for SQLite backend |
| Alembic | 1.13.x | Schema migrations | Manages DB schema changes across development without wiping data |

**Connection string:** `sqlite+aiosqlite:///./data/osteoprep.db`

**WAL mode setup** (run on app startup):
```python
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine

engine = create_async_engine("sqlite+aiosqlite:///./data/osteoprep.db")

@event.listens_for(engine.sync_engine, "connect")
def set_wal_mode(dbapi_conn, _):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA synchronous=NORMAL")
```

**Why not PostgreSQL:** PostgreSQL requires a separate running process, authentication configuration, and backup strategy. For a single-user app on a 3-week timeline, that complexity is pure overhead. SQLite with WAL mode handles concurrent async reads perfectly. Migrate to PostgreSQL only if the app goes multi-user.

### Spaced Repetition (SRS)

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| py-fsrs | 6.x (fsrs on PyPI) | SRS scheduling algorithm | Modern FSRS-5 algorithm; supersedes SM-2; actively maintained by Open Spaced Repetition org; same algorithm Anki uses since 2023; 4-button rating (Again/Hard/Good/Easy) |

**Why FSRS over SM-2:**
- SM-2 (1987) uses a fixed formula. FSRS (Free Spaced Repetition Scheduler) is a machine-learning-derived algorithm that models memory more accurately.
- `supermemo2` PyPI package has not been updated since 2021. `py-fsrs` is actively maintained.
- FSRS has an Optimizer class that can tune weights based on actual review history — useful if the user studies beyond the 3-week exam window.

**Core SRS data model:**
```python
# SQLAlchemy model
class Flashcard(Base):
    __tablename__ = "flashcards"
    id: Mapped[int] = mapped_column(primary_key=True)
    topic: Mapped[str]
    front: Mapped[str]
    back: Mapped[str]
    # FSRS state fields
    stability: Mapped[float] = mapped_column(default=0.0)
    difficulty: Mapped[float] = mapped_column(default=0.0)
    due: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    last_review: Mapped[Optional[datetime]]
    state: Mapped[int] = mapped_column(default=0)  # 0=New,1=Learning,2=Review,3=Relearning
    reps: Mapped[int] = mapped_column(default=0)
```

### Frontend

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| HTMX | 2.0.x | DOM updates via server HTML | 14KB JS library; enables partial page updates (card flips, quiz answers, SRS ratings) without a build step; request/response paradigm fits server-side rendering |
| TailwindCSS | 3.4.x (CDN play.min.css) | Utility CSS | Mobile-first utility classes; zero build pipeline via CDN version for this project size |
| DaisyUI | 4.x (CDN) | Component library | Semantic components (card, btn, badge, progress, modal) that compose naturally with HTMX; pure CSS no JS conflicts; mobile-responsive out of the box |

**Why HTMX over React:**
- React requires a JS build pipeline (npm, webpack/vite), TypeScript, JSX, component state management. For a single-developer 3-week project, this is architectural overhead that adds days to setup.
- HTMX lets the backend (FastAPI + Jinja2) remain the source of truth. Card state, quiz logic, and SRS scheduling live in Python — where the code already is.
- HTMX's `hx-get`, `hx-post`, `hx-swap` handle every interaction this app needs: flipping flashcards, submitting quiz answers, loading topic sections, showing AI explanations.
- The DaisyUI card component is exactly right for flashcard UI with zero custom CSS.

**Why CDN over build pipeline:**
This is a private, single-user app. Bundling Tailwind/DaisyUI via PostCSS adds 30+ minutes of setup and an ongoing build step with no production benefit. Use CDN for the 3-week exam sprint; optimise later if needed.

### Serving Infrastructure

| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Nginx | 1.24.x (Ubuntu apt) | Reverse proxy | Routes HTTPS traffic from port 443 to internal Uvicorn port; handles TLS termination; already likely installed for Open WebUI |
| Tailscale | Current | Private HTTPS access from iPhone | Server is already on Tailscale; `tailscale cert` provisions a valid HTTPS certificate for the MagicDNS hostname; iPhone must be on same tailnet |
| systemd | OS-managed | Process supervision | Runs Gunicorn/Uvicorn as a system service; auto-restart on crash; starts on boot |

**Port assignment:** Use port 8080 internally (Uvicorn), expose as port 8443 or route via Nginx on 443. Open WebUI already occupies port 3000 — do not conflict.

**Deployment topology:**
```
iPhone browser (Tailscale connected)
        |
   [HTTPS / Tailscale MagicDNS]
        |
   Nginx (443) on Hetzner server
        |
   Uvicorn (127.0.0.1:8080)
        |
   FastAPI app (Python)
        |
   SQLite file (./data/osteoprep.db)
```

**Systemd service file pattern:**
```ini
[Unit]
Description=OsteoPrep FastAPI App
After=network.target

[Service]
User=root
WorkingDirectory=/root/projects/osteoprep
ExecStart=/root/projects/osteoprep/.venv/bin/gunicorn \
    -w 2 -k uvicorn.workers.UvicornWorker \
    --bind 127.0.0.1:8080 \
    app.main:app
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Backend | FastAPI | Flask | No native async; Claude streaming requires async; Flask-async is bolted on |
| Backend | FastAPI | Django | Too heavy for a single-user app; ORM and admin layer unnecessary overhead |
| Backend | FastAPI | Next.js (full-stack) | Node.js runtime; React build pipeline; JS-based Claude SDK less mature |
| Database | SQLite + aiosqlite | PostgreSQL | Requires separate process, auth, backup; no benefit for single-user |
| Database | SQLite + aiosqlite | Redis | In-memory only (data lost on restart unless persisted); overkill for SRS state |
| Frontend | HTMX + DaisyUI | React + Tailwind | npm build pipeline; React component state management for no benefit; adds 1-2 days setup |
| Frontend | HTMX + DaisyUI | Vanilla JS | More boilerplate for partial updates; HTMX is cleaner for server-rendered fragments |
| SRS | py-fsrs (FSRS-5) | supermemo2 (SM-2) | SM-2 package unmaintained since 2021; FSRS is more accurate and actively developed |
| SRS | py-fsrs (FSRS-5) | Custom SM-2 impl | No reason to reimplement what py-fsrs already handles correctly |
| Serving | Nginx + Tailscale | Direct port exposure | Port 91.98.143.115:8080 is unencrypted HTTP; Tailscale provides authenticated HTTPS without public cert complexity |

---

## Installation

```bash
# Create virtualenv
cd /root/projects/osteoprep
python3 -m venv .venv
source .venv/bin/activate

# Core backend
pip install "fastapi[standard]==0.115.*"
pip install "uvicorn[standard]==0.32.*"
pip install gunicorn
pip install "sqlalchemy[asyncio]==2.0.*"
pip install aiosqlite
pip install alembic
pip install "anthropic==0.84.*"
pip install python-multipart
pip install jinja2

# SRS
pip install fsrs

# Dev tools
pip install httpx  # for testing FastAPI endpoints
```

**Frontend assets (no npm needed):**
```html
<!-- In base template <head> -->
<link href="https://cdn.jsdelivr.net/npm/daisyui@4/dist/full.min.css" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://unpkg.com/htmx.org@2.0.4" defer></script>
```

---

## Mobile (iPhone) Access

1. Ensure iPhone is connected to same Tailscale tailnet as the Hetzner server.
2. Run `tailscale cert $(tailscale status --json | jq -r '.Self.DNSName | rtrimstr(".")' )` on server to provision TLS cert.
3. Configure Nginx with the Tailscale-provisioned cert.
4. Access app via `https://<machine-name>.your-tailnet.ts.net/` in Safari on iPhone.
5. App is inaccessible to the public internet — only accessible within the tailnet.

**Mobile-responsive requirements** (must verify in each template):
- Use `<meta name="viewport" content="width=device-width, initial-scale=1">` in base template.
- DaisyUI components are mobile-first by default.
- Flashcard flip interaction must work with touch (HTMX `hx-trigger="click"` handles both tap and click).
- Avoid hover-only interactions — use tap/click events throughout.
- Minimum tap target size: 44x44px (DaisyUI `btn` class meets this by default).

---

## Sources

- FastAPI official docs: https://fastapi.tiangolo.com/deployment/server-workers/
- Anthropic Python SDK: https://github.com/anthropics/anthropic-sdk-python
- py-fsrs (FSRS algorithm): https://github.com/open-spaced-repetition/py-fsrs
- DaisyUI + HTMX guide: https://daisyui.com/docs/install/htmx/
- FastAPI + HTMX + DaisyUI reference app: https://github.com/sunscrapers/fastapi-htmx-daisyui
- Tailscale HTTPS certs: https://tailscale.com/docs/how-to/set-up-https-certificates
- SQLite vs PostgreSQL comparison: https://www.datacamp.com/blog/sqlite-vs-postgresql-detailed-comparison
- FastAPI Nginx Ubuntu deployment (2025): https://docs.vultr.com/how-to-deploy-a-fastapi-application-with-gunicorn-and-nginx-on-ubuntu-2404

**Confidence levels:**
- FastAPI + Uvicorn + Gunicorn: HIGH (official docs, widely deployed)
- Anthropic SDK 0.84.0 version: HIGH (PyPI confirmed Feb 2026)
- SQLite + aiosqlite + SQLAlchemy 2.0: HIGH (official SQLAlchemy docs + multiple tutorials)
- py-fsrs / FSRS-5 algorithm: HIGH (active GitHub, PyPI maintained, Anki adopted)
- HTMX + DaisyUI + Tailwind CDN: HIGH (official HTMX/DaisyUI docs, reference implementation exists)
- Tailscale HTTPS for iPhone: HIGH (official Tailscale docs)
