#!/bin/bash

# Slack 通知配置腳本

echo "🔧 配置 Slack 通知..."
echo ""

# 檢查是否已有配置
CONFIG_FILE="slack-config.env"

if [ -f "$CONFIG_FILE" ]; then
    echo "⚠️  已存在 Slack 配置"
    read -p "是否要重新配置? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "取消配置"
        exit 0
    fi
fi

echo "請提供 Slack Webhook URL"
echo ""
echo "如何獲取 Webhook URL："
echo "1. 訪問 https://api.slack.com/apps"
echo "2. 創建新應用或選擇現有應用"
echo "3. 啟用 Incoming Webhooks"
echo "4. 添加 Webhook 到工作區"
echo "5. 複製 Webhook URL"
echo ""

read -p "輸入 Slack Webhook URL: " WEBHOOK_URL

if [ -z "$WEBHOOK_URL" ]; then
    echo "❌ Webhook URL 不能為空"
    exit 1
fi

# 驗證 URL 格式
if [[ ! "$WEBHOOK_URL" =~ ^https://hooks.slack.com/services/ ]]; then
    echo "⚠️  URL 格式可能不正確"
    read -p "是否繼續? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
read -p "輸入通知頻道名稱（可選，例如: #monitoring）: " CHANNEL
read -p "輸入機器人名稱（可選，例如: Globalping Bot）: " BOT_NAME

# 創建配置文件
cat > "$CONFIG_FILE" << EOF
# Slack 通知配置

# Webhook URL（必填）
SLACK_WEBHOOK_URL="$WEBHOOK_URL"

# 頻道名稱（可選）
SLACK_CHANNEL="${CHANNEL:-#general}"

# 機器人名稱（可選）
SLACK_BOT_NAME="${BOT_NAME:-Globalping Checker}"

# 通知級別
# all: 所有檢測都通知
# errors: 只通知錯誤（BLOCKED, TIMEOUT, WARNING, PARTIAL, API_ERROR）
# critical: 只通知嚴重錯誤（BLOCKED, API_ERROR）
SLACK_NOTIFY_LEVEL="errors"

# 是否啟用通知
SLACK_ENABLED="true"
EOF

echo ""
echo "✅ 配置已保存到 $CONFIG_FILE"
echo ""

# 測試通知
echo "🧪 測試 Slack 通知..."
echo ""

TEST_MESSAGE='{
  "text": "✅ Globalping Checker Slack 通知測試",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "🧪 測試通知"
      }
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Slack 通知已成功配置！*\n\n從現在開始，域名檢測結果會自動發送到此頻道。"
      }
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "配置時間: '"$(date '+%Y-%m-%d %H:%M:%S')"'"
        }
      ]
    }
  ]
}'

if curl -X POST -H 'Content-type: application/json' \
    --data "$TEST_MESSAGE" \
    "$WEBHOOK_URL" 2>/dev/null; then
    echo ""
    echo "✅ 測試通知已發送！"
    echo "   請檢查 Slack 頻道是否收到測試消息"
else
    echo ""
    echo "❌ 測試通知發送失敗"
    echo "   請檢查 Webhook URL 是否正確"
fi

echo ""
echo "========================================"
echo "配置完成"
echo "========================================"
echo ""
echo "配置文件: $CONFIG_FILE"
echo ""
echo "下一步："
echo "  1. 測試通知:"
echo "     ./id_globalping_multi_v3.2_Slack.sh test_2_domains.txt"
echo ""
echo "  2. 部署到 EC2:"
echo "     scp $CONFIG_FILE ec2-user@YOUR_IP:/tmp/"
echo "     ssh ec2-user@YOUR_IP 'sudo mv /tmp/$CONFIG_FILE /opt/globalping-checker/'"
echo ""
