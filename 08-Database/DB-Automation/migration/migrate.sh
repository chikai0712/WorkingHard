#!/usr/bin/env bash
set -euo pipefail

PRESET_MIGRATION_TOOL="${MIGRATION_TOOL-}"
PRESET_TARGET_ENV="${TARGET_ENV-}"
PRESET_DB_ENGINE="${DB_ENGINE-}"
MIGRATION_TOOL="${PRESET_MIGRATION_TOOL:-flyway}"
ACTION="${1:-info}"
TARGET_ENV="${PRESET_TARGET_ENV:-dev}"
DB_ENGINE="${PRESET_DB_ENGINE:-mssql}"
SUMMARY_OUT="${SUMMARY_OUT:-}"
EVIDENCE_OUT="${EVIDENCE_OUT:-}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/flyway.conf.example"
PRECHECK_FILE="$SCRIPT_DIR/precheck.example.sql"
POSTCHECK_FILE="$SCRIPT_DIR/postcheck.example.sql"
ROLLBACK_GUIDE="$SCRIPT_DIR/rollback-guidelines.md"
SQL_DIR="$SCRIPT_DIR/sql"

if [[ "$DB_ENGINE" == "mysql" ]]; then
  CONFIG_FILE="$SCRIPT_DIR/flyway.mysql.conf.example"
  PRECHECK_FILE="$SCRIPT_DIR/precheck.mysql.example.sql"
  POSTCHECK_FILE="$SCRIPT_DIR/postcheck.mysql.example.sql"
  SQL_DIR="$SCRIPT_DIR/sql/V001__init_example"
fi

emit_summary() {
  local summary_file="$1"
  cat > "$summary_file" <<EOF
{
  "event_id": "migration-summary-local",
  "module": "migration",
  "stage": "$ACTION",
  "status": "warning",
  "summary": "Migration command ran in skeleton mode; precheck and rollback readiness still require operator review.",
  "possible_causes": [
    "Pending approval gate",
    "No real database connection in skeleton mode"
  ],
  "rollback_reference": [
    "$ROLLBACK_GUIDE"
  ],
  "recommended_policy": "hold",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

emit_mysql_precheck_evidence() {
  local evidence_file="$1"
  cat > "$evidence_file" <<EOF
{
  "event_id": "mysql-precheck-evidence-local",
  "module": "migration",
  "engine": "mysql",
  "evidence_type": "db-check",
  "stage": "precheck",
  "status": "warning",
  "summary": "MySQL precheck skeleton ran locally; replica lag and metadata lock checks still require operator review.",
  "checks": [
    {
      "name": "replica_lag_seconds",
      "status": "warning",
      "value": 0,
      "notes": "Placeholder value in skeleton mode"
    },
    {
      "name": "metadata_lock_risk",
      "status": "warning",
      "value": true,
      "notes": "Operator must review before execution"
    }
  ],
  "recommended_checks": [
    "Review precheck SQL template",
    "Validate replication lag before apply",
    "Confirm metadata lock window"
  ],
  "recommended_policy": "hold",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

emit_mysql_postcheck_evidence() {
  local evidence_file="$1"
  cat > "$evidence_file" <<EOF
{
  "event_id": "mysql-postcheck-evidence-local",
  "module": "migration",
  "engine": "mysql",
  "evidence_type": "db-check",
  "stage": "postcheck",
  "status": "warning",
  "summary": "MySQL postcheck skeleton ran locally; smoke query and replica catch-up evidence still require operator review.",
  "checks": [
    {
      "name": "schema_object_validation",
      "status": "ok",
      "value": true,
      "notes": "Placeholder success in skeleton mode"
    },
    {
      "name": "replica_catch_up",
      "status": "warning",
      "value": false,
      "notes": "Operator must confirm replica baseline recovery"
    }
  ],
  "recommended_checks": [
    "Review postcheck SQL template",
    "Attach smoke query evidence",
    "Confirm application compatibility before close"
  ],
  "recommended_policy": "hold",
  "updated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

echo "[migration] tool=$MIGRATION_TOOL action=$ACTION env=$TARGET_ENV engine=$DB_ENGINE"
echo "[migration] Skeleton mode only; no database connection performed"
echo "[migration] Templates:"
echo "- config: $CONFIG_FILE"
echo "- precheck: $PRECHECK_FILE"
echo "- postcheck: $POSTCHECK_FILE"
echo "- rollback: $ROLLBACK_GUIDE"
echo "- sql dir: $SQL_DIR"

if [[ -n "$SUMMARY_OUT" ]]; then
  emit_summary "$SUMMARY_OUT"
  echo "[migration] summary written to $SUMMARY_OUT"
fi

if [[ -n "$EVIDENCE_OUT" && "$DB_ENGINE" == "mysql" ]]; then
  if [[ "$ACTION" == "precheck" ]]; then
    emit_mysql_precheck_evidence "$EVIDENCE_OUT"
    echo "[migration] mysql precheck evidence written to $EVIDENCE_OUT"
  elif [[ "$ACTION" == "postcheck" ]]; then
    emit_mysql_postcheck_evidence "$EVIDENCE_OUT"
    echo "[migration] mysql postcheck evidence written to $EVIDENCE_OUT"
  else
    echo "[migration] evidence output only supported for mysql precheck/postcheck skeleton actions"
  fi
fi
