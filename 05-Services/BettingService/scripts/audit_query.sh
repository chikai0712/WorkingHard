#!/bin/bash
# GitLab 稽核查詢腳本

set -e

PROJECT_ID="${1:-$CI_PROJECT_ID}"
START_DATE="${2:-$(date -d '7 days ago' +%Y-%m-%d)}"
END_DATE="${3:-$(date +%Y-%m-%d)}"
GITLAB_URL="${GITLAB_URL:-https://gitlab.example.com}"
GITLAB_TOKEN="${GITLAB_TOKEN:-$CI_JOB_TOKEN}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ 請提供項目 ID"
  echo "用法: $0 <project_id> [start_date] [end_date]"
  exit 1
fi

echo "=== GitLab 稽核查詢 ==="
echo "項目 ID: $PROJECT_ID"
echo "開始日期: $START_DATE"
echo "結束日期: $END_DATE"
echo ""

# 查詢稽核事件
echo "📊 查詢稽核事件..."
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects/$PROJECT_ID/audit_events?created_after=${START_DATE}T00:00:00Z&created_before=${END_DATE}T23:59:59Z" \
  | jq -r '.[] | "\(.created_at) | \(.user.name) | \(.details.action) | \(.details.target_type // "N/A")"'

# 統計信息
echo ""
echo "📈 統計信息:"
TOTAL=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects/$PROJECT_ID/audit_events?created_after=${START_DATE}T00:00:00Z&created_before=${END_DATE}T23:59:59Z" \
  | jq '. | length')

echo "總事件數: $TOTAL"

# 按用戶統計
echo ""
echo "👥 按用戶統計:"
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects/$PROJECT_ID/audit_events?created_after=${START_DATE}T00:00:00Z&created_before=${END_DATE}T23:59:59Z" \
  | jq -r '.[] | .user.name' | sort | uniq -c | sort -rn

# 按操作類型統計
echo ""
echo "🔧 按操作類型統計:"
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects/$PROJECT_ID/audit_events?created_after=${START_DATE}T00:00:00Z&created_before=${END_DATE}T23:59:59Z" \
  | jq -r '.[] | .details.action' | sort | uniq -c | sort -rn

