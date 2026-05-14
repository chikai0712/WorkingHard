#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-$(dirname "$0")/.env.example}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

DB_ENGINE="${DB_ENGINE:-mssql}"
BACKUP_PATH="${BACKUP_PATH:-/backups/example.bak}"
VERIFY_MODE="${VERIFY_MODE:-checksum}"
DRY_RUN="${DRY_RUN:-true}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
METADATA_FILE="$SCRIPT_DIR/backup-metadata.example.json"
RETENTION_POLICY_FILE="$SCRIPT_DIR/retention-policy.example.yaml"
RESTORE_CHECKLIST="$SCRIPT_DIR/checklists/restore-drill-checklist.md"

echo "[backup-recovery] engine=$DB_ENGINE backup=$BACKUP_PATH mode=$VERIFY_MODE dry_run=$DRY_RUN"
echo "[backup-recovery] Step 1: validate backup file presence"
echo "[backup-recovery] Step 2: validate metadata / checksum"
echo "[backup-recovery] Step 3: simulate restore verification checklist"
echo "[backup-recovery] Templates:"
echo "- metadata: $METADATA_FILE"
echo "- retention policy: $RETENTION_POLICY_FILE"
echo "- restore checklist: $RESTORE_CHECKLIST"
