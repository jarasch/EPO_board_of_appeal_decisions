#!/usr/bin/env bash
# Start the EPO Board of Appeal decisions web app (FastAPI: RAG vs GraphRAG).
#
# Usage: ./start_app.sh [--reload]
#   HOST / PORT env vars override the defaults (127.0.0.1:8000).
#   PYTHON overrides the interpreter (default: .venv/bin/python if present, else python3).
set -euo pipefail

cd "$(dirname "$0")"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"

if [[ -n "${PYTHON:-}" ]]; then
  :
elif [[ -x .venv/bin/python ]]; then
  PYTHON=.venv/bin/python
else
  PYTHON=python3
fi

# retrieval/db.py also calls load_dotenv(); exporting here lets us fail fast
# with a clear message instead of a KeyError on the first request.
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

missing=()
for var in NEO4J_URI NEO4J_USER NEO4J_PASSWORD OPENAI_API_KEY; do
  [[ -n "${!var:-}" ]] || missing+=("$var")
done
if (( ${#missing[@]} )); then
  echo "Missing required environment variables: ${missing[*]}" >&2
  echo "Add them to .env (or export them) and re-run." >&2
  exit 1
fi

if ! "$PYTHON" -c "import fastapi, uvicorn, neo4j, openai, dotenv" 2>/dev/null; then
  echo "Python dependencies missing for $PYTHON. Install with:" >&2
  echo "  $PYTHON -m pip install -r requirements.txt" >&2
  exit 1
fi

echo "Starting app on http://$HOST:$PORT (database: ${NEO4J_DATABASE:-neo4j})"
exec "$PYTHON" -m uvicorn app.main:app --host "$HOST" --port "$PORT" "$@"
