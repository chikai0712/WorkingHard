#!/bin/bash

# 域名狀態管理工具
# 用於查看和管理域名分區狀態

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STATUS_DB="$SCRIPT_DIR/domain_status.db"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 顯示統計信息
show_stats() {
    echo "📊 域名狀態統計"
    echo "========================================"
    
    local total=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status;")
    local abnormal=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status WHERE zone='ABNORMAL_ZONE';")
    local normal=$(sqlite3 "$STATUS_DB" "SELECT COUNT(*) FROM domain_status WHERE zone='NORMAL_ZONE';")
    
    echo "總域名數: $total"
    echo "異常區: $abnormal 個"
    echo "正常區: $normal 個"
    echo ""
    
    echo "狀態分布："
    sqlite3 "$STATUS_DB" << 'EOF'
SELECT 
    status,
    COUNT(*) as count,
    zone
FROM domain_status 
GROUP BY status, zone
ORDER BY zone, count DESC;
EOF
}

# 列出異常區域名
list_abnormal() {
    echo "🚨 異常區域名列表"
    echo "========================================"
    
    sqlite3 -header -column "$STATUS_DB" << 'EOF'
SELECT 
    domain,
    status,
    consecutive_abnormal as '連續異常',
    datetime(last_check, 'localtime') as '最後檢測'
FROM domain_status 
WHERE zone='ABNORMAL_ZONE'
ORDER BY consecutive_abnormal DESC, last_check DESC
LIMIT 50;
EOF
}

# 列出正常區域名
list_normal() {
    echo "✅ 正常區域名列表"
    echo "========================================"
    
    sqlite3 -header -column "$STATUS_DB" << 'EOF'
SELECT 
    domain,
    status,
    check_count as '檢測次數',
    datetime(last_check, 'localtime') as '最後檢測'
FROM domain_status 
WHERE zone='NORMAL_ZONE'
ORDER BY last_check DESC
LIMIT 50;
EOF
}

# 查看最近狀態變化
show_recent_changes() {
    echo "🔄 最近狀態變化"
    echo "========================================"
    
    sqlite3 -header -column "$STATUS_DB" << 'EOF'
SELECT 
    domain,
    zone,
    status,
    datetime(last_status_change, 'localtime') as '變化時間'
FROM domain_status 
WHERE last_status_change IS NOT NULL
ORDER BY last_status_change DESC
LIMIT 20;
EOF
}

# 手動移動域名
move_domain() {
    local domain="$1"
    local target_zone="$2"
    
    if [ -z "$domain" ] || [ -z "$target_zone" ]; then
        echo "用法: $0 move <域名> <NORMAL_ZONE|ABNORMAL_ZONE>"
        return 1
    fi
    
    sqlite3 "$STATUS_DB" << EOF
UPDATE domain_status 
SET zone='$target_zone',
    last_status_change=CURRENT_TIMESTAMP
WHERE domain='$domain';
EOF
    
    echo "✅ $domain 已移至 $target_zone"
}

# 重置域名狀態
reset_domain() {
    local domain="$1"
    
    if [ -z "$domain" ]; then
        echo "用法: $0 reset <域名>"
        return 1
    fi
    
    sqlite3 "$STATUS_DB" << EOF
UPDATE domain_status 
SET consecutive_normal=0,
    consecutive_abnormal=0,
    last_status_change=CURRENT_TIMESTAMP
WHERE domain='$domain';
EOF
    
    echo "✅ $domain 狀態已重置"
}

# 導出報告
export_report() {
    local output_file="${1:-domain_report.csv}"
    
    sqlite3 -header -csv "$STATUS_DB" << 'EOF' > "$output_file"
SELECT 
    domain,
    zone,
    status,
    check_count,
    consecutive_normal,
    consecutive_abnormal,
    datetime(first_seen, 'localtime') as first_seen,
    datetime(last_check, 'localtime') as last_check,
    datetime(last_status_change, 'localtime') as last_status_change
FROM domain_status 
ORDER BY zone, status, domain;
EOF
    
    echo "✅ 報告已導出到: $output_file"
}

# 主菜單
case "${1:-stats}" in
    stats)
        show_stats
        ;;
    abnormal)
        list_abnormal
        ;;
    normal)
        list_normal
        ;;
    changes)
        show_recent_changes
        ;;
    move)
        move_domain "$2" "$3"
        ;;
    reset)
        reset_domain "$2"
        ;;
    export)
        export_report "$2"
        ;;
    *)
        echo "域名狀態管理工具"
        echo ""
        echo "用法: $0 <命令> [參數]"
        echo ""
        echo "命令："
        echo "  stats          顯示統計信息"
        echo "  abnormal       列出異常區域名"
        echo "  normal         列出正常區域名"
        echo "  changes        查看最近狀態變化"
        echo "  move <域名> <區域>  手動移動域名"
        echo "  reset <域名>   重置域名狀態"
        echo "  export [文件]  導出報告"
        ;;
esac
