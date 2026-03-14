#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

if [ $# -eq 0 ]; then
  echo "Uso: $0 <comando> [args...]"
  echo "Ejemplo: $0 pytest -q"
  exit 1
fi

TIMESTAMP="$(date +%F_%H-%M-%S)"
SAFE_NAME="$(printf '%s' "$1" | tr '/ :"' '____')"
LOG_FILE="$LOG_DIR/${TIMESTAMP}_${SAFE_NAME}.log"

{
  echo "===== COMMAND ====="
  printf '%q ' "$@"
  echo
  echo "===== START ====="
  date --iso-8601=seconds 2>/dev/null || date
  echo
} | tee "$LOG_FILE"

# Ejecuta mostrando en pantalla y guardando stdout+stderr
"$@" 2>&1 | tee -a "$LOG_FILE"

{
  echo
  echo "===== END ====="
  date --iso-8601=seconds 2>/dev/null || date
} | tee -a "$LOG_FILE"