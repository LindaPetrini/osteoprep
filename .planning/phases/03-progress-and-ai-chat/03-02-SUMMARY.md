---
phase: 03-progress-and-ai-chat
plan: 02
subsystem: ai-chat
tags: [streaming, sse, chat, claude, fastapi, htmx]
dependency_graph:
  requires: [progress_service.get_progress_summary, AsyncAnthropic.messages.stream]
  provides: [stream_chat_generator, build_chat_system_prompt, GET /chat/stream, chat_panel]
  affects: [app/templates/topic.html, app/main.py]
tech_stack:
  added: [Server-Sent Events via vanilla EventSource, AsyncAnthropic streaming API]
  patterns: [SSE async generator, best-effort context injection, GeneratorExit handling]
key_files:
  created:
    - app/services/claude.py (stream_chat_generator, build_chat_system_prompt appended)
    - app/routers/chat.py
    - app/templates/fragments/chat_panel.html
  modified:
    - app/templates/topic.html
    - app/main.py
decisions:
  - "Vanilla JS EventSource (not HTMX SSE extension) — simpler, no extension CDN needed, GET-only constraint matches plan"
  - "Newline escaping in SSE: server escapes \\n to \\\\n, client unescapes — prevents SSE frame breaking"
  - "Progress context wrapped in try/except Exception: pass — chat never breaks if progress DB query fails"
  - "Local imports inside build_chat_system_prompt body — avoids circular import (progress_service -> models -> not claude)"
  - "GeneratorExit caught in stream_chat_generator — abandoned streams close cleanly via async context manager"
metrics:
  duration: "3 min"
  completed_date: "2026-02-28"
  tasks_completed: 2
  files_changed: 5
---

# Phase 3 Plan 02: Streaming AI Chat Summary

**One-liner:** SSE streaming chat with topic context injection using vanilla EventSource and Anthropic haiku streaming API.

## Tasks Completed

| # | Task | Commit | Key Files |
|---|------|--------|-----------|
| 1 | stream_chat_generator and build_chat_system_prompt in claude.py | 273f788 | app/services/claude.py |
| 2 | chat.py router, chat_panel.html, topic.html + main.py extension | f11d351 (pre-built in 03-01 docs commit) | app/routers/chat.py, app/templates/fragments/chat_panel.html, app/templates/topic.html, app/main.py |

## What Was Built

### app/services/claude.py — Two new functions appended

**`build_chat_system_prompt(topic_slug, db)`** — async function that:
- Injects topic title (IT + EN) into system prompt when called from a topic page (CHAT-03)
- Queries progress_service.get_progress_summary() for weak subjects (< 50% quiz accuracy) and SRS state (CHAT-04)
- Best-effort: progress context failure is silently swallowed — chat never breaks for a DB error

**`stream_chat_generator(question, system_prompt)`** — async generator that:
- Opens `client.messages.stream()` from the Anthropic SDK
- Yields `data: <chunk>\n\n` SSE frames, escaping `\n` → `\\n` to protect SSE framing
- Handles `GeneratorExit` (client disconnect) cleanly — stream context manager closes the Anthropic connection
- Yields `data: [DONE]\n\n` in `finally` block regardless of exit path

### app/routers/chat.py — GET /chat/stream SSE endpoint

- Accepts `q` (URL-encoded question) and `topic_slug` (optional) query params
- Empty `q` returns `[DONE]` immediately without hitting the API
- Returns `StreamingResponse` with `text/event-stream` media type and `X-Accel-Buffering: no` header

### app/templates/fragments/chat_panel.html — Self-contained chat UI

- Toggle button "Chiedi a Claude" shows/hides the panel via inline JS
- Chat history scrolling `<div>` with DaisyUI `.chat .chat-start/.chat-end` bubbles
- Form submit calls `startChatStream(event, topicSlug)` which:
  1. Appends user bubble to history
  2. Creates assistant bubble target element
  3. Opens `EventSource('/chat/stream?q=...&topic_slug=...')`
  4. Appends tokens to bubble on `onmessage`, unescaping `\\n` back to `\n`
  5. Calls `es.close()` on `[DONE]` or `onerror`
- `escapeHtml()` prevents XSS in user-typed question

### app/templates/topic.html — Chat panel included below quiz button

```html
{% include "fragments/chat_panel.html" %}
```

## Deviations from Plan

### Pre-existing work detected

**Task 2 files were already committed** in the previous session's `03-01` docs commit (f11d351). The previous agent pre-built `app/routers/chat.py`, `app/templates/fragments/chat_panel.html`, and the `topic.html` + `main.py` changes alongside the 03-01 docs. My edits to those files were no-ops (identical content already present).

**Only claude.py** (Task 1) required new work in this session.

None of these deviations indicate errors — the code is correct and verified.

## Verification Results

- GET /chat/stream?q=test returns HTTP 200 with `content-type: text/event-stream`
- GET /chat/stream?q=Cos%27%C3%A8+la+mitosi&topic_slug=cellula-eucariotica streams word-by-word data frames
- GET /topic/cellula-eucariotica contains "Chiedi a Claude" (2 occurrences: button + panel heading)
- `sudo systemctl status osteoprep` shows `active (running)` — no import errors
- Python import verification: `stream_chat_generator` is async generator function, `build_chat_system_prompt` is coroutine function

## Self-Check: PASSED

- [x] app/services/claude.py — contains stream_chat_generator and build_chat_system_prompt
- [x] app/routers/chat.py — GET /chat/stream endpoint registered
- [x] app/templates/fragments/chat_panel.html — chat panel with EventSource JS
- [x] app/templates/topic.html — includes chat_panel.html
- [x] app/main.py — chat router imported and included
- [x] Commit 273f788 — feat(03-02): add stream_chat_generator and build_chat_system_prompt
- [x] Service active (running) — no startup errors
