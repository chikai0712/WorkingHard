#!/usr/bin/env bash
set -euo pipefail

IAC_TOOL="${IAC_TOOL:-terraform}"
WORKDIR="${1:-.}"
MODE="${2:-validate}"
BACKEND_FILE="${BACKEND_FILE:-$(dirname "$0")/backends/s3.backend.example.hcl}"
VAR_FILE="${VAR_FILE:-$(dirname "$0")/environments/dev/terraform.tfvars.example}"
PLAN_FILE="${PLAN_FILE:-tfplan}"

echo "[iac] tool=$IAC_TOOL workdir=$WORKDIR mode=$MODE"
echo "[iac] backend_file=$BACKEND_FILE"
echo "[iac] var_file=$VAR_FILE"
echo "[iac] plan_file=$PLAN_FILE"
echo "[iac] shared gates: source=fmt/validate/plan security=policy/risk health=post-apply verification"

case "$MODE" in
  fmt)
    echo "[iac][source-gate] Would run: $IAC_TOOL -chdir=$WORKDIR fmt -recursive"
    ;;
  init)
    echo "[iac] Would run: $IAC_TOOL -chdir=$WORKDIR init -backend-config=$BACKEND_FILE"
    ;;
  validate)
    echo "[iac][source-gate] Would run: $IAC_TOOL -chdir=$WORKDIR init -backend=false"
    echo "[iac][source-gate] Would run: $IAC_TOOL -chdir=$WORKDIR validate"
    ;;
  plan)
    echo "[iac][source-gate] Would run: $IAC_TOOL -chdir=$WORKDIR init -backend-config=$BACKEND_FILE"
    echo "[iac][source-gate] Would run: $IAC_TOOL -chdir=$WORKDIR plan -var-file=$VAR_FILE -out=$PLAN_FILE"
    echo "[iac][security-gate] Review plan risk, secret boundary, and policy findings before apply"
    ;;
  apply-dry-run)
    echo "[iac] No real apply in skeleton mode"
    echo "[iac] Review the generated plan first: $PLAN_FILE"
    echo "[iac][health-gate] After real apply, verify outputs, target health, and drift baseline"
    ;;
  *)
    echo "Usage: $0 [workdir] {fmt|init|validate|plan|apply-dry-run}" >&2
    exit 1
    ;;
esac
