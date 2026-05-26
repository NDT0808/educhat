#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BACKEND_PORT="${BACKEND_PORT:-1820}"
FRONTEND_PORT="${FRONTEND_PORT:-1818}"
BACKEND_HOST="${BACKEND_HOST:-127.0.0.1}"
FRONTEND_HOST="${FRONTEND_HOST:-127.0.0.1}"
CONDA_ENV="${CONDA_ENV:-educhat-be}"

kill_port() {
  local port="$1"
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    pids="$(fuser "$port"/tcp 2>/dev/null || true)"
  fi

  if [ -n "$pids" ]; then
    echo "Killing process on port $port (PID: $pids)"
    kill $pids 2>/dev/null || true
    sleep 0.2
    kill -9 $pids 2>/dev/null || true
  fi
}

resolve_python() {
  if [ -n "${PYTHON_BIN:-}" ]; then
    echo "$PYTHON_BIN"
    return
  fi

  if command -v conda >/dev/null 2>&1; then
    local conda_base
    conda_base="$(conda info --base 2>/dev/null || true)"
    if [ -n "$conda_base" ] && [ -x "$conda_base/envs/$CONDA_ENV/bin/python" ]; then
      echo "$conda_base/envs/$CONDA_ENV/bin/python"
      return
    fi
  fi

  if [ -x "$HOME/miniconda3/envs/$CONDA_ENV/bin/python" ]; then
    echo "$HOME/miniconda3/envs/$CONDA_ENV/bin/python"
    return
  fi

  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return
  fi

  echo "python"
}

echo "Cleaning up ports $FRONTEND_PORT and $BACKEND_PORT..."
kill_port "$FRONTEND_PORT"
kill_port "$BACKEND_PORT"

PYTHON="$(resolve_python)"
echo "Using Python: $PYTHON"

echo "Starting Backend on $BACKEND_HOST:$BACKEND_PORT..."
cd "$PROJECT_ROOT/services/llm"

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  . ".env"
  set +a
fi

if [ -z "${DB_PATH:-}" ] || [ ! -f "${DB_PATH:-}" ]; then
  export DB_PATH="$PROJECT_ROOT/data/hmu_schedules.db"
fi

export SKIP_RERANKER="${SKIP_RERANKER:-1}"
export CORS_ORIGINS="${CORS_ORIGINS:-http://localhost:$FRONTEND_PORT,http://127.0.0.1:$FRONTEND_PORT}"
export PYTHONPATH="$PROJECT_ROOT/services/llm/src:$PROJECT_ROOT/libs/common/src:${PYTHONPATH:-}"

nohup "$PYTHON" -m uvicorn llm.main:app --host "$BACKEND_HOST" --port "$BACKEND_PORT" \
  > "$PROJECT_ROOT/services/llm/backend.log" 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID $BACKEND_PID"

cd "$PROJECT_ROOT/ui"
echo "Starting Frontend on $FRONTEND_HOST:$FRONTEND_PORT..."

if [ ! -d "node_modules" ]; then
  echo "Installing frontend dependencies..."
  npm install
fi

API_PROXY_TARGET="${API_PROXY_TARGET:-http://$BACKEND_HOST:$BACKEND_PORT}" \
nohup npm run dev -- --port "$FRONTEND_PORT" --host "$FRONTEND_HOST" \
  > "$PROJECT_ROOT/ui/frontend.log" 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID $FRONTEND_PID"

echo "Development environment started."
echo "Frontend: http://localhost:$FRONTEND_PORT"
echo "Backend: http://localhost:$BACKEND_PORT"
echo "Logs:"
echo "  $PROJECT_ROOT/services/llm/backend.log"
echo "  $PROJECT_ROOT/ui/frontend.log"
