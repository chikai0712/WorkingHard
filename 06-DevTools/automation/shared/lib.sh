#!/usr/bin/env bash
set -euo pipefail

log() {
  local level="${1:-INFO}"
  shift || true
  printf '[%s] %s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$level" "$*"
}

retry() {
  local max_attempts="${1:-3}"
  shift
  local attempt=1
  until "$@"; do
    if (( attempt >= max_attempts )); then
      log ERROR "command failed after $attempt attempts: $*"
      return 1
    fi
    log WARN "retry $attempt/$max_attempts for command: $*"
    attempt=$((attempt + 1))
    sleep 1
  done
}
