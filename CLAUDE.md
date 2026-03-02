# OsteoPrep — context for Claude on Mac

This is OsteoPrep, a FastAPI study app for Italian healthcare/osteopathy entrance exams.
You are running it locally on a Mac for offline use (e.g. on a flight).

## Stack
- FastAPI + HTMX + DaisyUI (Tailwind pre-compiled, no build step)
- SQLite (data/osteoprep.db) + SQLAlchemy async + Alembic
- Anthropic Claude haiku for AI content (won't work offline — fails gracefully)
- py-fsrs for spaced repetition

## Key paths
- App entry: `app/main.py`
- Templates: `app/templates/`
- Routers: `app/routers/` (pages, review, quiz, exam, chat, section_quiz)
- DB: `data/osteoprep.db`
- Run script: `./run_local.sh`

## Running offline
```bash
./run_local.sh
```
Starts on `0.0.0.0:8080`. Without `ANTHROPIC_API_KEY` set, AI features (chat, explanation
generation) fail gracefully — all quiz/review/exam/flashcard features work fine.

## Connecting phone via USB (no internet needed)
See `OFFLINE.md` for step-by-step USB cable connection instructions.

## Production server
The production app runs on a Hetzner server accessed via Tailscale:
https://ai-bot-server.tail18768e.ts.net/
Managed as a systemd service: `sudo systemctl restart osteoprep`

## What NOT to do
- Don't run `alembic upgrade head` unless you know what you're doing — DB is already migrated
- Don't set ANTHROPIC_API_KEY unless you have internet — calls will hang trying to reach the API
- Don't commit the .env file (it's excluded from rsync)
