#!/bin/bash

# Slack 通知函數庫
# 在檢測腳本中 source 此文件使用

# 載入 Slack 配置
load_slack_config() {
    local config_file="${1:-/opt/globalping-checker/slack-config.env}"
    
    if [ -f "$config_file" ]; then
        source "$config_file"
        return 0
    else
        return 1
    fi
}

# 發送 Slack 消息
send_slack_message() {
    local message="$1"
    local color="${2:-good}"  # good, warning, danger
    
    if [ -z "$SLACK_WEBHOOK_URL" ] || [ "$SLACK_ENABLED" != "true" ]; then
        return 0
    fi
    
    local payload=$(cat <<EOF
{
    "username": "${SLACK_BOT_NAME:-Globalping Checker}",
    "channel": "${SLACK_CHANNEL:-#general}",
    "attachments": [
        {
            "color": "$color",
            "text": "$message",
            "footer": "Globalping Checker",
            "ts": $(date +%s)
        }
    ]
}
EOF
)
    
    curl -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "$SLACK_WEBHOOK_URL" \
        --silent --output /dev/null
}

# 發送檢測結果摘要
send_slack_summary() {
    local total="$1"
    local clean="$2"
    local blocked="$3"
    local timeout="$4"
    local warning="$5"
    local partial="$6"
    local api_error="$7"
    
    if [ -z "$SLACK_WEBHOOK_URL" ] || [ "$SLACK_ENABLED" != "true" ]; then
        return 0
    fi
    
    # 根據結果決定顏色
    local color="good"
    if [ "$blocked" -gt 0 ] || [ "$api_error" -gt 0 ]; then
        color="danger"
    elif [ "$timeout" -gt 0 ] || [ "$warning" -gt 0 ] || [ "$partial" -gt 0 ]; then
        color="warning"
    fi
    
    # 檢查通知級別
    if [ "$SLACK_NOTIFY_LEVEL" = "critical" ]; then
        if [ "$blocked" -eq 0 ] && [ "$api_error" -eq 0 ]; then
            return 0
        fi
    elif [ "$SLACK_NOTIFY_LEVEL" = "errors" ]; then
        if [ "$blocked" -eq 0 ] && [ "$timeout" -eq 0 ] && [ "$warning" -eq 0 ] && [ "$partial" -eq 0 ] && [ "$api_error" -eq 0 ]; then
            return 0
        fi
    fi
    
    local payload=$(cat <<EOF
{
    "username": "${SLACK_BOT_NAME:-Globalping Checker}",
    "channel": "${SLACK_CHANNEL:-#general}",
    "blocks": [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🔍 域名檢測報告"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*總域名數:*\n$total"
                },
                {
                    "type": "mrkdwn",
                    "text": "*檢測時間:*\n$(date '+%Y-%m-%d %H:%M:%S')"
                }
            ]
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "✅ *正常連通:*\n$clean"
                },
                {
                    "type": "mrkdwn",
                    "text": "🚨 *DNS 污染:*\n$blocked"
                },
                {
                    "type": "mrkdwn",
                    "text": "⚠️ *完全超時:*\n$timeout"
                },
                {
                    "type": "mrkdwn",
                    "text": "⚠️ *服務異常:*\n$warning"
                },
                {
                    "type": "mrkdwn",
                    "text": "🔄 *部分異常:*\n$partial"
                },
                {
                    "type": "mrkdwn",
                    "text": "❌ *檢測失敗:*\n$api_error"
                }
            ]
        }
    ]
}
EOF
)
    
    curl -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "$SLACK_WEBHOOK_URL" \
        --silent --output /dev/null
}

# 發送單個域名檢測結果
send_slack_domain_result() {
    local domain="$1"
    local status="$2"
    local details="$3"
    
    if [ -z "$SLACK_WEBHOOK_URL" ] || [ "$SLACK_ENABLED" != "true" ]; then
        return 0
    fi
    
    # 只在錯誤時通知（根據配置）
    if [ "$SLACK_NOTIFY_LEVEL" = "critical" ]; then
        if [ "$status" != "BLOCKED" ] && [ "$status" != "API_ERROR" ]; then
            return 0
        fi
    elif [ "$SLACK_NOTIFY_LEVEL" = "errors" ]; then
        if [ "$status" = "CLEAN" ]; then
            return 0
        fi
    fi
    
    local color="good"
    local icon="✅"
    
    case "$status" in
        BLOCKED)
            color="danger"
            icon="🚨"
            ;;
        TIMEOUT)
            color="warning"
            icon="⚠️"
            ;;
        WARNING)
            color="warning"
            icon="⚠️"
            ;;
        PARTIAL)
            color="warning"
            icon="🔄"
            ;;
        API_ERROR)
            color="danger"
            icon="❌"
            ;;
    esac
    
    local message="$icon *$domain* - $status\n$details"
    
    send_slack_message "$message" "$color"
}

# 發送檢測開始通知
send_slack_start() {
    local total="$1"
    
    if [ -z "$SLACK_WEBHOOK_URL" ] || [ "$SLACK_ENABLED" != "true" ]; then
        return 0
    fi
    
    send_slack_message "🚀 開始檢測 $total 個域名..." "good"
}

# 發送檢測完成通知
send_slack_complete() {
    send_slack_message "✅ 域名檢測已完成" "good"
}

# 導出函數
export -f load_slack_config
export -f send_slack_message
export -f send_slack_summary
export -f send_slack_domain_result
export -f send_slack_start
export -f send_slack_complete
