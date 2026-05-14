#!/usr/bin/env bash
set -euo pipefail

MIGRATION_TOOL="${MIGRATION_TOOL:-flyway}"
ACTION="${1:-info}"
TARGET_ENV="${TARGET_ENV:-dev}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="$SCRIPT_DIR/flyway.conf.example"
PRECHECK_FILE="$SCRIPT_DIR/precheck.example.sql"
POSTCHECK_FILE="$SCRIPT_DIR/postcheck.example.sql"
ROLLBACK_GUIDE="$SCRIPT_DIR/rollback-guidelines.md"
SQL_DIR="$SCRIPT_DIR/sql"

echo "[migration] tool=$MIGRATION_TOOL action=$ACTION env=$TARGET_ENV"
echo "[migration] Skeleton mode only; no database connection performed"
echo "[migration] Templates:"
echo "- config: $CONFIG_FILE"
echo "- precheck: $PRECHECK_FILE"
echo "- postcheck: $POSTCHECK_FILE"
echo "- rollback: $ROLLBACK_GUIDE"
echo "- sql dir: $SQL_DIR"
