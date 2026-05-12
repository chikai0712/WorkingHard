#!/bin/bash

# Telegram 通知函數庫
# 在檢測腳本中 source 此文件使用

# 載入 Telegram 配置
load_telegram_config() {
    local config_file="${1:-telegram-config.env}"
    
    if [ -f "$config_file" ]; then
        source "$config_file"
        return 0
    else
        return 1
    fi
}

# 發送 Telegram 消息
send_telegram_message() {
    local message="$1"
    local parse_mode="${2:-Markdown}"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_ENABLED" != "true" ]; then
        return 0
    fi
    
    local api_url="https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage"
    
    # 轉義特殊字符（如果使用 Markdown）
    if [ "$parse_mode" = "Markdown" ]; then
        message=$(echo "$message" | sed 's/_/\\_/g')
    fi
    
    curl -s -X POST "$api_url" \
        -d "chat_id=$TELEGRAM_CHAT_ID" \
        -d "text=$message" \
        -d "parse_mode=$parse_mode" \
        --output /dev/null
}

# 發送檢測結果摘要
send_telegram_summary() {
    local total="$1"
    local clean="$2"
    local blocked="$3"
    local timeout="$4"
    local warning="$5"
    local partial="$6"
    local api_error="$7"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_ENABLED" != "true" ]; then
        return 0
    fi
    
    # 檢查通知級別
    if [ "$TELEGRAM_NOTIFY_LEVEL" = "critical" ]; then
        if [ "$blocked" -eq 0 ] && [ "$api_error" -eq 0 ]; then
            return 0
        fi
    elif [ "$TELEGRAM_NOTIFY_LEVEL" = "errors" ]; then
        if [ "$blocked" -eq 0 ] && [ "$timeout" -eq 0 ] && [ "$warning" -eq 0 ] && [ "$partial" -eq 0 ] && [ "$api_error" -eq 0 ]; then
            return 0
        fi
    fi
    
    # 決定狀態圖標
    local status_icon="✅"
    if [ "$blocked" -gt 0 ] || [ "$api_error" -gt 0 ]; then
        status_icon="🚨"
    elif [ "$timeout" -gt 0 ] || [ "$warning" -gt 0 ] || [ "$partial" -gt 0 ]; then
        status_icon="⚠️"
    fi
    
    local message="$status_icon *域名檢測報告*

📊 *檢測統計*
總域名數: \`$total\`
檢測時間: \`$(date '+%Y-%m-%d %H:%M:%S')\`

📈 *檢測結果*
✅ 正常連通: \`$clean\`
🚨 DNS 污染: \`$blocked\`
⚠️ 完全超時: \`$timeout\`
⚠️ 服務異常: \`$warning\`
🔄 部分異常: \`$partial\`
❌ 檢測失敗: \`$api_error\`"
    
    send_telegram_message "$message" "Markdown"
}

# 發送單個域名檢測結果
send_telegram_domain_result() {
    local domain="$1"
    local status="$2"
    local details="$3"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_ENABLED" != "true" ]; then
        return 0
    fi
    
    # 只在錯誤時通知（根據配置）
    if [ "$TELEGRAM_NOTIFY_LEVEL" = "critical" ]; then
        if [ "$status" != "BLOCKED" ] && [ "$status" != "API_ERROR" ]; then
            return 0
        fi
    elif [ "$TELEGRAM_NOTIFY_LEVEL" = "errors" ]; then
        if [ "$status" = "CLEAN" ]; then
            return 0
        fi
    fi
    
    local icon="✅"
    
    case "$status" in
        BLOCKED)
            icon="🚨"
            ;;
        TIMEOUT)
            icon="⚠️"
            ;;
        WARNING)
            icon="⚠️"
            ;;
        PARTIAL)
            icon="🔄"
            ;;
        API_ERROR)
            icon="❌"
            ;;
    esac
    
    local message="$icon *$domain* - \`$status\`

$details"
    
    send_telegram_message "$message" "Markdown"
}

# 發送檢測開始通知
send_telegram_start() {
    local total="$1"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_ENABLED" != "true" ]; then
        return 0
    fi
    
    local message="🚀 *開始域名檢測*

總域名數: \`$total\`
開始時間: \`$(date '+%Y-%m-%d %H:%M:%S')\`"
    
    send_telegram_message "$message" "Markdown"
}

# 發送檢測完成通知
send_telegram_complete() {
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_ENABLED" != "true" ]; then
        return 0
    fi
    
    local message="✅ *域名檢測已完成*

完成時間: \`$(date '+%Y-%m-%d %H:%M:%S')\`"
    
    send_telegram_message "$message" "Markdown"
}

# 發送錯誤通知
send_telegram_error() {
    local error_message="$1"
    
    if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$TELEGRAM_CHAT_ID" ] || [ "$TELEGRAM_ENABLED" != "true" ]; then
        return 0
    fi
    
    local message="❌ *檢測錯誤*

$error_message

時間: \`$(date '+%Y-%m-%d %H:%M:%S')\`"
    
    send_telegram_message "$message" "Markdown"
}

# 導出函數
export -f load_telegram_config
export -f send_telegram_message
export -f send_telegram_summary
export -f send_telegram_domain_result
export -f send_telegram_start
export -f send_telegram_complete
export -f send_telegram_error
