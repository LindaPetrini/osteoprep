#!/usr/bin/env bash
# Run OsteoPrep locally for offline use (e.g. on a Mac during a flight)
# Access from phone: connect phone to Mac's Personal Hotspot, then open
#   http://<mac-ip>:8080
# Get Mac's IP: System Settings > Network > Wi-Fi or Hotspot interface
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV="$SCRIPT_DIR/.venv"
PYTHON="$VENV/bin/python"
UVICORN="$VENV/bin/uvicorn"

# --- Python check ---
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ via Homebrew: brew install python"
    exit 1
fi

PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJ=$(echo "$PY_VER" | cut -d. -f1)
PY_MIN=$(echo "$PY_VER" | cut -d. -f2)
if [ "$PY_MAJ" -lt 3 ] || { [ "$PY_MAJ" -eq 3 ] && [ "$PY_MIN" -lt 10 ]; }; then
    echo "ERROR: Python 3.10+ required (found $PY_VER). brew install python"
    exit 1
fi

# --- Venv setup ---
if [ ! -f "$PYTHON" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV"
fi

echo "Installing/checking dependencies..."
"$VENV/bin/pip" install -q -r requirements.txt

# --- Print access info ---
echo ""
echo "====================================="
echo "  OsteoPrep starting on port 8080"
echo "====================================="
if command -v ipconfig &>/dev/null; then
    # macOS
    IPS=$(ipconfig getifaddr en0 2>/dev/null || true)
    [ -z "$IPS" ] && IPS=$(ipconfig getifaddr bridge100 2>/dev/null || true)
    [ -n "$IPS" ] && echo "  Open on phone: http://$IPS:8080"
fi
echo "  Or use: http://localhost:8080 (Mac browser)"
echo "  AI features (chat, explanations) won't work offline — everything else does."
echo "====================================="
echo ""

# Run without ANTHROPIC_API_KEY so AI features fail fast (not hang waiting for network)
unset ANTHROPIC_API_KEY

exec "$UVICORN" app.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --loop asyncio \
    --log-level info
