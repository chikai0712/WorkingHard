#!/bin/bash
# 每日稽核報告生成腳本

set -e

PROJECT_ID="${1:-$CI_PROJECT_ID}"
DATE="${2:-$(date -d yesterday +%Y-%m-%d)}"
GITLAB_URL="${GITLAB_URL:-https://gitlab.example.com}"
GITLAB_TOKEN="${GITLAB_TOKEN:-$CI_JOB_TOKEN}"
REPORT_EMAIL="${REPORT_EMAIL:-team@example.com}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ 請提供項目 ID"
  echo "用法: $0 <project_id> [date]"
  exit 1
fi

REPORT_FILE="audit_report_${DATE}.txt"

echo "=== 每日稽核報告 ===" > $REPORT_FILE
echo "日期: $DATE" >> $REPORT_FILE
echo "項目 ID: $PROJECT_ID" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 1. 代碼變更統計
echo "📝 代碼變更統計:" >> $REPORT_FILE
echo "-------------------" >> $REPORT_FILE
git log --since="$DATE 00:00:00" --until="$DATE 23:59:59" --pretty=format:"%h - %an, %ar : %s" >> $REPORT_FILE 2>/dev/null || echo "無變更" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 2. Merge Request 統計
echo "🔄 Merge Request 統計:" >> $REPORT_FILE
echo "-------------------" >> $REPORT_FILE
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects/$PROJECT_ID/merge_requests?created_after=${DATE}T00:00:00Z&created_before=${DATE}T23:59:59Z" \
  | jq -r '.[] | "\(.iid) - \(.author.name) - \(.title) - \(.state)"' >> $REPORT_FILE || echo "無 MR" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 3. 合併的 MR
echo "✅ 已合併的 MR:" >> $REPORT_FILE
echo "-------------------" >> $REPORT_FILE
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects/$PROJECT_ID/merge_requests?state=merged&updated_after=${DATE}T00:00:00Z&updated_before=${DATE}T23:59:59Z" \
  | jq -r '.[] | "\(.iid) - \(.title) - 合併者: \(.merged_by.name)"' >> $REPORT_FILE || echo "無合併" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 4. 稽核事件摘要
echo "🔍 稽核事件摘要:" >> $REPORT_FILE
echo "-------------------" >> $REPORT_FILE
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB_URL/api/v4/projects/$PROJECT_ID/audit_events?created_after=${DATE}T00:00:00Z&created_before=${DATE}T23:59:59Z" \
  | jq -r '.[] | "\(.created_at) - \(.user.name) - \(.details.action)"' >> $REPORT_FILE || echo "無事件" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 5. 分支操作
echo "🌿 分支操作:" >> $REPORT_FILE
echo "-------------------" >> $REPORT_FILE
git log --since="$DATE 00:00:00" --until="$DATE 23:59:59" --all --pretty=format:"%h - %an - %s" | grep -iE "branch|merge|delete" >> $REPORT_FILE 2>/dev/null || echo "無分支操作" >> $REPORT_FILE
echo "" >> $REPORT_FILE

# 顯示報告
cat $REPORT_FILE

# 發送郵件（如果配置了）
if command -v mail &> /dev/null && [ -n "$REPORT_EMAIL" ]; then
  mail -s "每日稽核報告 - $DATE" "$REPORT_EMAIL" < $REPORT_FILE
  echo "✅ 報告已發送到 $REPORT_EMAIL"
fi

