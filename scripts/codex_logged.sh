#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP="$(date +%F_%H-%M-%S)"
LOG_FILE="$LOG_DIR/${TIMESTAMP}_codex_session.log"

echo "Se va a guardar la sesión en:"
echo "  $LOG_FILE"
echo
echo "Para terminar la captura, salí de Codex y luego de la subshell si aplica."
echo

if ! command -v script >/dev/null 2>&1; then
  echo "Error: el comando 'script' no está instalado."
  echo "En Ubuntu/Debian suele venir con util-linux."
  exit 1
fi

# -q: quiet
# -f: flush inmediato
script -q -f "$LOG_FILE" -c "cd \"$PROJECT_ROOT\" && codex"