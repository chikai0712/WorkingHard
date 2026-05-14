#!/usr/bin/env bash
set -euo pipefail

ENV_FILE="${ENV_FILE:-$(dirname "$0")/.env.example}"
if [[ -f "$ENV_FILE" ]]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

PIPELINE_NAME="${PIPELINE_NAME:-example-service}"
CI_PROVIDER="${CI_PROVIDER:-github-actions}"
ARTIFACT_PATH="${ARTIFACT_PATH:-dist/}"
DEPLOY_ENV="${DEPLOY_ENV:-dev}"
DRY_RUN="${DRY_RUN:-true}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

GITHUB_TEMPLATE="$SCRIPT_DIR/github-actions-example.yml"
GITLAB_TEMPLATE="$SCRIPT_DIR/gitlab-ci-example.yml"

echo "[cicd] provider=$CI_PROVIDER pipeline=$PIPELINE_NAME env=$DEPLOY_ENV artifact=$ARTIFACT_PATH dry_run=$DRY_RUN"

echo "[cicd] Step 1: checkout"
echo "[cicd] Step 2: lint"
echo "[cicd] Step 3: test"
echo "[cicd] Step 4: build artifact"
echo "[cicd] Step 5: publish artifact metadata"

echo "[cicd] Available templates:"
echo "- GitHub Actions: $GITHUB_TEMPLATE"
echo "- GitLab CI: $GITLAB_TEMPLATE"

if [[ "$DRY_RUN" == "true" ]]; then
  echo "[cicd] Dry run only. No remote CI provider invoked."
fi
