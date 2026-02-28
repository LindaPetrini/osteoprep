---
phase: 01-foundation-and-content-pipeline
plan: "01"
subsystem: infra
tags: [fastapi, sqlalchemy, sqlite, alembic, gunicorn, nginx, uvicorn, jinja2, htmx, tailwind, daisyui]

# Dependency graph
requires: []
provides:
  - FastAPI application scaffold with async SQLAlchemy + aiosqlite engine
  - Bilingual Topic ORM model (title_it/en, content_it/en, slug, subject) with WAL SQLite
  - Alembic migration history initialized (initial_schema revision b16bd4264820)
  - 20 topic stubs seeded (Biology x10, Chemistry x10), content fields NULL awaiting generation
  - Production server: gunicorn + UvicornWorker on 127.0.0.1:8080
  - Nginx TLS reverse proxy on port 8443 (Tailscale cert)
  - Systemd service (osteoprep.service) enabled, auto-restart on crash
affects:
  - 01-02 (topic browsing UI and AI explainer generation depend on Topic model and running server)
  - All subsequent phases (database schema is locked — bilingual columns must not be removed)

# Tech tracking
tech-stack:
  added:
    - fastapi==0.115.14
    - sqlalchemy[asyncio]==2.0.47
    - aiosqlite==0.22.1
    - alembic==1.18.4
    - gunicorn==25.1.0
    - uvicorn[standard]==0.32.1
    - anthropic==0.84.0
    - jinja2==3.1.6
    - python-dotenv==1.2.1
    - httpx==0.28.1
  patterns:
    - "templates_config.py separates Jinja2Templates instantiation to avoid circular imports between main.py and routers"
    - "Async SQLAlchemy engine with WAL pragma set via sync_engine connect event"
    - "Alembic manages schema migrations; main.py lifespan create_all is fallback only"
    - "Seed script uses synchronous sqlite3 (not async) for simplicity as a one-time script"
    - "Gunicorn with UvicornWorker for production ASGI; 120s timeout for AI generation requests"

key-files:
  created:
    - app/main.py
    - app/database.py
    - app/models.py
    - app/templates_config.py
    - app/routers/pages.py
    - app/routers/fragments.py
    - app/templates/base.html
    - app/templates/index.html
    - static/app.js
    - migrations/env.py
    - migrations/versions/b16bd4264820_initial_schema.py
    - alembic.ini
    - seed_topics.py
    - requirements.txt
    - /etc/systemd/system/osteoprep.service
    - /etc/nginx/sites-available/osteoprep
  modified:
    - .gitignore

key-decisions:
  - "templates_config.py pattern used to avoid circular import between main.py (imports routers) and routers (need templates)"
  - "Tailscale TLS cert obtained and placed at /etc/nginx/certs/ for Nginx HTTPS on port 8443"
  - "Port 8443 (not 443/80) avoids conflicts with Open WebUI on port 3000 and other services"
  - "WAL mode set via SQLAlchemy sync_engine connect event — confirmed active via engine query"

patterns-established:
  - "Circular import avoidance: shared Jinja2 templates instance lives in app/templates_config.py"
  - "Async SQLAlchemy engine with WAL + NORMAL synchronous for concurrent reads during async writes"
  - "Alembic-first schema management: create_all in lifespan is fallback only, not primary"

requirements-completed: [CONT-01, PROG-03]

# Metrics
duration: 4min
completed: 2026-02-28
---

# Phase 01 Plan 01: Project Scaffold and Production Infrastructure Summary

**FastAPI + async SQLite (WAL) foundation with bilingual Topic schema, Alembic migrations, Gunicorn/Nginx/systemd production stack serving HTTPS on Tailscale port 8443**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-28T15:25:59Z
- **Completed:** 2026-02-28T15:30:08Z
- **Tasks:** 2
- **Files modified:** 18 (project) + 3 (system)

## Accomplishments
- FastAPI app scaffold with async SQLAlchemy engine (WAL mode), Jinja2 templates, HTMX + DaisyUI frontend stack
- Bilingual Topic model with locked schema (title_it/en, content_it/en, slug, subject) — schema is stable for all subsequent plans
- Alembic initialized with initial_schema migration applied; 20 topic stubs seeded (content=NULL, ready for Plan 02 generation)
- Production server live: gunicorn + UvicornWorker on port 8080, Nginx TLS proxy on 8443, systemd service enabled with auto-restart

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold, SQLite schema, and Alembic initialization** - `784eba8` (feat)
2. **Task 2: Production server setup (Nginx reverse proxy + systemd service)** - `7505a4b` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `app/main.py` - FastAPI app instance, lifespan, static mount, router registration
- `app/database.py` - Async SQLAlchemy engine with WAL pragma, session factory, get_db dependency
- `app/models.py` - Topic ORM model with bilingual schema (content_it/en nullable for lazy generation)
- `app/templates_config.py` - Jinja2Templates singleton + uncertainty marker filter (avoids circular import)
- `app/routers/pages.py` - Home route returning subject list from DB
- `app/routers/fragments.py` - Empty stub for Plan 02 HTMX fragments
- `app/templates/base.html` - HTML base with DaisyUI, Tailwind CDN, HTMX
- `app/templates/index.html` - Subject accordion list with HTMX lazy-load
- `static/app.js` - Language preference stub (extended in Plan 02)
- `migrations/env.py` - Alembic env configured with models and sync URL
- `migrations/versions/b16bd4264820_initial_schema.py` - Creates topics table with all indexes
- `alembic.ini` - Alembic configuration
- `seed_topics.py` - One-time seed for 20 Biology/Chemistry topic stubs
- `requirements.txt` - Pinned dependencies (52 packages)
- `/etc/systemd/system/osteoprep.service` - Gunicorn service, 120s timeout, Restart=always
- `/etc/nginx/sites-available/osteoprep` - TLS proxy on 8443 with Tailscale cert
- `.gitignore` - Added .venv/, data/osteoprep.db, gunicorn.ctl, *.sock

## Decisions Made
- **templates_config.py pattern:** Jinja2Templates must be instantiated in a separate module so both main.py (which registers routes) and routers can import it without circular dependency
- **Port 8443 with Tailscale TLS:** Tailscale cert was available (ai-bot-server.tail18768e.ts.net), enabling real HTTPS; port 8443 avoids conflict with Open WebUI on 3000
- **WAL mode via event listener:** `@event.listens_for(engine.sync_engine, "connect")` sets WAL at connection time — verified via async engine query returning 'wal'

## Deviations from Plan

None - plan executed exactly as written. The Tailscale cert was available so the TLS nginx config (vs fallback HTTP) was used as the plan preferred.

## Issues Encountered

- The `alembic init migrations` command failed initially because the `migrations/versions/` directory had already been created by the directory setup step. Fixed by removing the empty directory and re-running alembic init.
- Direct `sqlite3.connect()` check for WAL mode returns 'delete' until a SQLAlchemy connection triggers the pragma event. WAL mode confirmed active via async engine PRAGMA query.

## User Setup Required

None — ANTHROPIC_API_KEY already present in /root/projects/osteoprep/.env (used in Plan 02).

## Next Phase Readiness

- Plan 02 (topic browsing UI + AI explainer generation) can proceed immediately
- Server is live at https://ai-bot-server.tail18768e.ts.net:8443/ on Tailscale network
- Topic stubs seeded, content_it/content_en = NULL — ready for on-demand generation
- Uncertainty marker Jinja2 filter is registered in templates_config.py, ready for Plan 02 use

---
*Phase: 01-foundation-and-content-pipeline*
*Completed: 2026-02-28*
