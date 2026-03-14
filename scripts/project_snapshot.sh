#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

TIMESTAMP="$(date +%F_%H-%M-%S)"
OUT_DIR="$LOG_DIR/${TIMESTAMP}_snapshot"
mkdir -p "$OUT_DIR"

git -C "$PROJECT_ROOT" status > "$OUT_DIR/git_status.txt" 2>&1 || true
git -C "$PROJECT_ROOT" diff > "$OUT_DIR/git_diff.patch" 2>&1 || true
git -C "$PROJECT_ROOT" diff --cached > "$OUT_DIR/git_diff_cached.patch" 2>&1 || true
git -C "$PROJECT_ROOT" log --oneline -n 20 > "$OUT_DIR/git_log_oneline.txt" 2>&1 || true

{
  echo "Snapshot generado en: $OUT_DIR"
  echo "Archivos:"
  ls -1 "$OUT_DIR"
} 