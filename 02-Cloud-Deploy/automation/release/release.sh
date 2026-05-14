#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-$(dirname "$0")/.env.example}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

ACTION="${1:-status}"
APP_NAME="${APP_NAME:-example-web}"
TARGET_ENV="${TARGET_ENV:-dev}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
DEPLOY_STRATEGY="${DEPLOY_STRATEGY:-rolling}"
DRY_RUN="${DRY_RUN:-true}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
MANIFEST_FILE="$SCRIPT_DIR/release-manifest.example.yaml"
ENVIRONMENTS_FILE="$SCRIPT_DIR/environments.example.yaml"
VERSIONS_FILE="$SCRIPT_DIR/versions.example.env"

case "$ACTION" in
  build)
    echo "[release] build $APP_NAME:$IMAGE_TAG"
    ;;
  deploy)
    echo "[release] deploy $APP_NAME to $TARGET_ENV using $DEPLOY_STRATEGY"
    ;;
  rollback)
    echo "[release] rollback $APP_NAME in $TARGET_ENV to previous known-good release"
    ;;
  status)
    echo "[release] status app=$APP_NAME env=$TARGET_ENV strategy=$DEPLOY_STRATEGY dry_run=$DRY_RUN"
    ;;
  *)
    echo "Usage: $0 {build|deploy|rollback|status}" >&2
    exit 1
    ;;
esac

echo "[release] Metadata templates:"
echo "- manifest: $MANIFEST_FILE"
echo "- environments: $ENVIRONMENTS_FILE"
echo "- versions: $VERSIONS_FILE"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[release] Dry run only. No artifact registry or deployment target touched."
fi
