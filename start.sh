#!/bin/bash
# start.sh — Start Stylin' backend with uvicorn
# Usage: ./start.sh [port]

PORT=${1:-8000}
LOG_DIR="$(dirname "$0")/logs"
mkdir -p "$LOG_DIR"

echo "Starting Stylin' backend on port $PORT..."
cd "$(dirname "$0")"

nohup uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "$PORT" \
  --workers 2 \
  --log-level info \
  > "$LOG_DIR/uvicorn.log" 2>&1 &

echo "PID: $!"
echo "$!" > "$LOG_DIR/stylin.pid"
echo "Logs: $LOG_DIR/uvicorn.log"
