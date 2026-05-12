#!/bin/bash

# 智能分區檢測腳本 - 優化版
# 功能：
# - 區分正常區和異常區域名
# - 優先檢測異常域名
# - 抽樣檢測正常域名
# - 狀態自動轉換

set -e

# 配置
API_TOKEN="uh5vlg4ttg3v5gwby5zgtqrciimahql5"
QUOTA_THRESHOLD=300
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUS_DB="$SCRIPT_DIR/domain_status.db"
NORMAL_SAMPLE_SIZE=3  # 每次抽樣正常域名數量
CONSECUTIVE_THRESHOLD=3  # 連續正常次數閾值

# 禁用代理
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY
unset all_proxy ALL_PROXY no_proxy NO_PROXY

# 初始化數據庫
init_database() {
    if [ ! -f "$STATUS_DB" ]; then
        echo "📊 初始化域名狀態數據庫..."
        sqlite3 "$STATUS_DB" << 'EOF'
CREATE TABLE IF NOT EXISTS domain_status (
    domain TEXT PRIMARY KEY,
    zone TEXT NOT NULL,  -- NORMAL_ZONE, ABNORMAL_ZONE
    status TEXT,  -- CLEAN, BLOCKED, TIMEOUT, WARNING, PARTIAL
    last_check TIMESTAMP,
    check_count INTEGER DEFAULT 0,
    consecutive_normal INTEGER DEFAULT 0,
    consecutive_abnormal INTEGER DEFAULT 0,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_status_change TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_zone ON domain_status(zone);
CREATE INDEX IF NOT EXISTS idx_status ON domain_status(status);
EOF
        echo "✅ 數據庫初始化完成"
    fi
}

# 導入域名列表到數據庫
import_domains() {
    local domains_file="$1"
    
    if [ ! -f "$domains_file" ]; then
        echo "❌ 找不到域名文件: $domains_file"
        return 1
    fi
    
    echo "📥 導入域名到數據庫..."
    
    while IFS= read -r domain || [ -n "$domain" ]; do
        domain=$(echo "$domain" | tr -d '\r\n[:space:]')
        [ -z "$domain" ] && continue
        [ "$domain" = "域名" ] && continue
        [[ "$domain" != *.* ]] && continue
        
        # 檢查域名是否已存在
        EXISTS=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status WHERE domain='$domain';")
        
        if [ "$EXISTS" -eq 0 ]; then
            # 新域名，默認放入異常區（需要首次檢測）
            sqlite3 "$STATUS_DB" "INSERT INTO domain_status (domain, zone, status) VALUES ('$domain', 'ABNORMAL_ZONE', 'PENDING');"
        fi
    done < "$domains_file"
    
    local total=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status;")
    echo "✅ 域名導入完成，總計: $total 個"
}

# 獲取異常區域名
get_abnormal_domains() {
    sqlite3 "$STATUS_DB" "SELECT domain FROM domain_status WHERE zone='ABNORMAL_ZONE';" | tr '\n' ' '
}

# 獲取正常區域名（隨機抽樣）
get_normal_sample() {
    sqlite3 "$STATUS_DB" "SELECT domain FROM domain_status WHERE zone='NORMAL_ZONE' ORDER BY RANDOM() LIMIT $NORMAL_SAMPLE_SIZE;" | tr '\n' ' '
}

# 更新域名狀態
update_domain_status() {
    local domain="$1"
    local status="$2"
    local current_zone=$(sqlite3 "$STATUS_DB" "SELECT zone FROM domain_status WHERE domain='$domain';")
    
    # 更新基本信息
    sqlite3 "$STATUS_DB" << EOF
UPDATE domain_status 
SET status='$status',
    last_check=CURRENT_TIMESTAMP,
    check_count=check_count+1
WHERE domain='$domain';
EOF
    
    # 狀態轉換邏輯
    if [ "$status" = "CLEAN" ]; then
        # 正常狀態
        sqlite3 "$STATUS_DB" << EOF
UPDATE domain_status 
SET consecutive_normal=consecutive_normal+1,
    consecutive_abnormal=0
WHERE domain='$domain';
EOF
        
        # 檢查是否需要從異常區移到正常區
        if [ "$current_zone" = "ABNORMAL_ZONE" ]; then
            local consecutive=$(sqlite3 "$STATUS_DB" "SELECT consecutive_normal FROM domain_status WHERE domain='$domain';")
            if [ "$consecutive" -ge "$CONSECUTIVE_THRESHOLD" ]; then
                sqlite3 "$STATUS_DB" << EOF
UPDATE domain_status 
SET zone='NORMAL_ZONE',
    last_status_change=CURRENT_TIMESTAMP,
    consecutive_normal=0
WHERE domain='$domain';
EOF
                echo "  ✅ $domain 已恢復正常，移至正常區"
            fi
        fi
    else
        # 異常狀態
        sqlite3 "$STATUS_DB" << EOF
UPDATE domain_status 
SET consecutive_abnormal=consecutive_abnormal+1,
    consecutive_normal=0
WHERE domain='$domain';
EOF
        
        # 檢查是否需要從正常區移到異常區
        if [ "$current_zone" = "NORMAL_ZONE" ]; then
            sqlite3 "$STATUS_DB" << EOF
UPDATE domain_status 
SET zone='ABNORMAL_ZONE',
    last_status_change=CURRENT_TIMESTAMP
WHERE domain='$domain';
EOF
            echo "  ⚠️  $domain 出現異常，移至異常區"
        fi
    fi
}

# 檢查 API 額度
check_quota() {
    local response=$(curl -s -H "Authorization: Bearer $API_TOKEN" \
        "https://api.globalping.io/v1/limits")
    
    if [ $? -ne 0 ]; then
        echo "0"
        return 1
    fi
    
    echo "$response" | python3 -c '
import sys, json
try:
    data = json.load(sys.stdin)
    print(data["rateLimit"]["measurements"]["create"]["remaining"])
except:
    print("0")
'
}

# 主檢測邏輯
main() {
    local domains_file="${1:-domains.txt}"
    
    echo "🚀 智能分區檢測系統"
    echo "========================================"
    echo ""
    
    # 初始化數據庫
    init_database
    
    # 導入域名
    if [ -f "$domains_file" ]; then
        import_domains "$domains_file"
    fi
    
    # 獲取統計信息
    local total=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status;")
    local abnormal=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status WHERE zone='ABNORMAL_ZONE';")
    local normal=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status WHERE zone='NORMAL_ZONE';")
    
    echo "📊 域名統計："
    echo "  總域名數: $total"
    echo "  異常區: $abnormal 個"
    echo "  正常區: $normal 個"
    echo ""
    
    # 檢查額度
    echo "🔍 檢查 API 額度..."
    local remaining=$(check_quota)
    
    echo "📊 當前剩餘額度: $remaining / 500"
    echo "🎯 執行閾值: $QUOTA_THRESHOLD"
    echo ""
    
    # 計算需要的額度
    local sample_size=$NORMAL_SAMPLE_SIZE
    if [ "$normal" -lt "$NORMAL_SAMPLE_SIZE" ]; then
        sample_size=$normal
    fi
    local needed=$((abnormal * 3 + sample_size * 3))
    
    echo "💡 本次檢測計劃："
    echo "  異常區域名: $abnormal 個 (${abnormal}×3 = $((abnormal * 3)) 次)"
    echo "  正常區抽樣: $sample_size 個 (${sample_size}×3 = $((sample_size * 3)) 次)"
    echo "  總計需要: $needed 次 API 調用"
    echo ""
    
    if [ "$remaining" -lt "$QUOTA_THRESHOLD" ]; then
        echo "⏳ 額度不足 ($remaining < $QUOTA_THRESHOLD)"
        echo "❌ 跳過本次檢測"
        exit 0
    fi
    
    if [ "$remaining" -lt "$needed" ]; then
        echo "⚠️  額度不足以完成完整檢測 ($remaining < $needed)"
        echo "💡 將只檢測部分域名"
    fi
    
    echo "✅ 額度充足，開始檢測..."
    echo ""
    
    # 獲取待檢測域名
    local abnormal_domains=$(get_abnormal_domains)
    local normal_domains=$(get_normal_sample)
    
    # 創建臨時域名文件
    local temp_domains=$(mktemp)
    echo "$abnormal_domains" | tr ' ' '\n' > "$temp_domains"
    echo "$normal_domains" | tr ' ' '\n' >> "$temp_domains"
    
    # 執行檢測
    if [ -f "$SCRIPT_DIR/id_globalping_multi_v3.3_Telegram.sh" ]; then
        echo "🔍 執行域名檢測..."
        bash "$SCRIPT_DIR/id_globalping_multi_v3.3_Telegram.sh" "$temp_domains"
        
        # TODO: 解析檢測結果並更新數據庫
        # 這裡需要修改檢測腳本輸出結構化數據
        
        echo ""
        echo "✅ 檢測完成"
    else
        echo "❌ 找不到檢測腳本"
        rm -f "$temp_domains"
        exit 1
    fi
    
    # 清理
    rm -f "$temp_domains"
    
    # 顯示更新後的統計
    abnormal=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status WHERE zone='ABNORMAL_ZONE';")
    normal=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status WHERE zone='NORMAL_ZONE';")
    
    echo ""
    echo "📊 更新後統計："
    echo "  異常區: $abnormal 個"
    echo "  正常區: $normal 個"
    
    # 檢測後額度
    remaining=$(check_quota)
    echo "  剩餘額度: $remaining / 500"
}

# 執行
main "$@"
