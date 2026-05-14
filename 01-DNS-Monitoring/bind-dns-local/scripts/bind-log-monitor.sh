#!/bin/bash
# -------------------------------------------------------------------------------
# BIND DNS 日誌監控腳本 v1.0 - 即時監控 BIND 查詢日誌
# 功能：
#   1. 即時顯示 BIND DNS 的查詢日誌
#   2. 統計查詢來源和查詢的域名
#   3. 識別查詢使用的上游 NS（AWS/Google）
#   4. 顯示查詢統計和趨勢
# 
# 用法：
#   bash ./bind-log-monitor.sh [選項]
#   
# 選項：
#   --container NAME    指定 BIND 容器名稱（預設：bind-dns-local）
#   --lines N           顯示最近 N 行日誌（預設：50）
#   --follow            持續監控模式
#   --stats             只顯示統計資訊
#   
# 範例：
#   bash ./bind-log-monitor.sh --follow
#   bash ./bind-log-monitor.sh --stats
#   bash ./bind-log-monitor.sh --container my-bind --lines 100
#
# 按 Ctrl+C 停止
# -------------------------------------------------------------------------------

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# 預設配置
CONTAINER_NAME="bind-dns-local"
LOG_LINES=50
FOLLOW_MODE=false
STATS_ONLY=false
FILTER_DOMAIN=""

# 解析參數
while [[ $# -gt 0 ]]; do
    case "$1" in
        --container)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        --lines)
            LOG_LINES="$2"
            shift 2
            ;;
        --follow|-f)
            FOLLOW_MODE=true
            shift
            ;;
        --stats|-s)
            STATS_ONLY=true
            shift
            ;;
        --domain|-d)
            FILTER_DOMAIN="$2"
            shift 2
            ;;
        --help|-h)
            echo "用法: $0 [選項]"
            echo ""
            echo "選項:"
            echo "  --container NAME    指定 BIND 容器名稱（預設：bind-dns-local）"
            echo "  --lines N           顯示最近 N 行日誌（預設：50）"
            echo "  --follow, -f        持續監控模式"
            echo "  --stats, -s         只顯示統計資訊"
            echo "  --domain, -d DOMAIN 只顯示特定域名的查詢"
            echo "  --help, -h          顯示此幫助訊息"
            echo ""
            echo "範例:"
            echo "  $0 --follow                              # 持續監控日誌"
            echo "  $0 --stats                               # 顯示統計資訊"
            echo "  $0 --lines 100                           # 顯示最近 100 行"
            echo "  $0 -f -d www.clouddeployment168.site     # 只監控特定域名"
            echo "  $0 -f -d www                             # 只監控包含 www 的域名"
            echo "  $0 --container my-bind -f                # 監控指定容器"
            exit 0
            ;;
        *)
            echo -e "${RED}未知選項: $1${NC}"
            echo "使用 --help 查看幫助"
            exit 1
            ;;
    esac
done

# 檢查 Docker 容器是否存在
check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo -e "${RED}錯誤: 找不到容器 '${CONTAINER_NAME}'${NC}"
        echo ""
        echo "可用的容器："
        docker ps --format "  - {{.Names}}"
        exit 1
    fi
}

# 清理函數
cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止監控...${NC}"
    echo -e "${GREEN}監控已停止${NC}"
    exit 0
}

trap cleanup INT TERM

# 顯示日誌（基本模式）
show_logs() {
    echo -e "${CYAN}顯示最近 ${LOG_LINES} 行日誌...${NC}\n"
    
    # 嘗試從容器中讀取日誌
    if docker exec "$CONTAINER_NAME" test -f /var/log/named/query.log 2>/dev/null; then
        docker exec "$CONTAINER_NAME" tail -n "$LOG_LINES" /var/log/named/query.log
    elif docker exec "$CONTAINER_NAME" test -f /var/log/query.log 2>/dev/null; then
        docker exec "$CONTAINER_NAME" tail -n "$LOG_LINES" /var/log/query.log
    else
        # 如果找不到日誌檔案，使用 docker logs
        echo -e "${YELLOW}注意: 找不到 query.log，使用 docker logs${NC}\n"
        docker logs --tail "$LOG_LINES" "$CONTAINER_NAME"
    fi
}

# 持續監控日誌
follow_logs() {
    echo -e "${CYAN}持續監控 BIND DNS 日誌...${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止${NC}\n"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 嘗試從容器中讀取日誌
    if docker exec "$CONTAINER_NAME" test -f /var/log/named/query.log 2>/dev/null; then
        docker exec "$CONTAINER_NAME" tail -f /var/log/named/query.log | while read -r line; do
            parse_and_display_log "$line"
        done
    elif docker exec "$CONTAINER_NAME" test -f /var/log/query.log 2>/dev/null; then
        docker exec "$CONTAINER_NAME" tail -f /var/log/query.log | while read -r line; do
            parse_and_display_log "$line"
        done
    else
        # 如果找不到日誌檔案，使用 docker logs
        echo -e "${YELLOW}注意: 找不到 query.log，使用 docker logs${NC}\n"
        docker logs -f "$CONTAINER_NAME" 2>&1 | while read -r line; do
            parse_and_display_log "$line"
        done
    fi
}

# 解析並顯示日誌行
parse_and_display_log() {
    local line="$1"
    
    # 跳過空行
    [ -z "$line" ] && return
    
    # 如果設定了域名過濾，檢查是否包含該域名
    if [ -n "$FILTER_DOMAIN" ]; then
        if ! echo "$line" | grep -q "$FILTER_DOMAIN"; then
            return
        fi
    fi
    
    # 解析查詢日誌（BIND 格式：client IP#port (domain): query: domain IN type）
    if echo "$line" | grep -q "query:"; then
        local client=$(echo "$line" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        local domain=$(echo "$line" | grep -oE 'query: [^ ]+' | cut -d' ' -f2)
        local qtype=$(echo "$line" | grep -oE 'IN [A-Z]+' | cut -d' ' -f2)
        
        if [ -n "$domain" ]; then
            echo -e "${GREEN}[查詢]${NC} ${CYAN}$client${NC} → ${YELLOW}$domain${NC} (${BLUE}$qtype${NC})"
        else
            echo "$line"
        fi
    # 解析轉發日誌（forwarding to upstream）
    elif echo "$line" | grep -q "forwarding\|forwarder"; then
        local upstream=$(echo "$line" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | tail -1)
        if [ -n "$upstream" ]; then
            # 識別是 AWS 還是 Google NS
            if echo "$upstream" | grep -qE '^205\.251\.'; then
                echo -e "${MAGENTA}[轉發]${NC} → ${GREEN}AWS NS${NC} ($upstream)"
            elif echo "$upstream" | grep -qE '^216\.239\.'; then
                echo -e "${MAGENTA}[轉發]${NC} → ${GREEN}Google NS${NC} ($upstream)"
            else
                echo -e "${MAGENTA}[轉發]${NC} → $upstream"
            fi
        else
            echo "$line"
        fi
    # 其他日誌
    else
        # 只顯示真正的錯誤日誌，過濾掉編譯資訊、取消的查詢等雜訊
        if echo "$line" | grep -qE "error|warning|failed|timeout"; then
            # 排除以下情況：
            # 1. 編譯資訊（built with）
            # 2. 取消的查詢（operation canceled）
            # 3. SERVFAIL（這是正常的 DNS 回應）
            if ! echo "$line" | grep -qE "built with|build_alias|CFLAGS|LDFLAGS|CPPFLAGS|operation canceled|SERVFAIL"; then
                echo -e "${RED}[錯誤]${NC} $line"
            fi
        fi
    fi
}

# 顯示統計資訊
show_stats() {
    echo -e "${CYAN}分析 BIND DNS 日誌統計...${NC}\n"
    
    local log_content=""
    
    # 獲取日誌內容
    if docker exec "$CONTAINER_NAME" test -f /var/log/named/query.log 2>/dev/null; then
        log_content=$(docker exec "$CONTAINER_NAME" cat /var/log/named/query.log 2>/dev/null || echo "")
    elif docker exec "$CONTAINER_NAME" test -f /var/log/query.log 2>/dev/null; then
        log_content=$(docker exec "$CONTAINER_NAME" cat /var/log/query.log 2>/dev/null || echo "")
    else
        log_content=$(docker logs "$CONTAINER_NAME" 2>&1)
    fi
    
    if [ -z "$log_content" ]; then
        echo -e "${YELLOW}沒有找到日誌內容${NC}"
        return
    fi
    
    # 統計查詢總數
    local total_queries=$(echo "$log_content" | grep -c "query:" || echo "0")
    
    # 統計最常查詢的域名（Top 10）
    echo -e "${YELLOW}最常查詢的域名 (Top 10):${NC}"
    echo "$log_content" | grep "query:" | grep -oE 'query: [^ ]+' | cut -d' ' -f2 | sort | uniq -c | sort -rn | head -10 | while read -r count domain; do
        echo -e "  ${GREEN}$count${NC} 次 - ${CYAN}$domain${NC}"
    done
    
    echo ""
    
    # 統計查詢類型
    echo -e "${YELLOW}查詢類型統計:${NC}"
    echo "$log_content" | grep "query:" | grep -oE 'IN [A-Z]+' | cut -d' ' -f2 | sort | uniq -c | sort -rn | while read -r count qtype; do
        echo -e "  ${GREEN}$count${NC} 次 - ${BLUE}$qtype${NC}"
    done
    
    echo ""
    
    # 統計查詢來源 IP（Top 10）
    echo -e "${YELLOW}查詢來源 IP (Top 10):${NC}"
    echo "$log_content" | grep "query:" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | sort | uniq -c | sort -rn | head -10 | while read -r count ip; do
        echo -e "  ${GREEN}$count${NC} 次 - ${CYAN}$ip${NC}"
    done
    
    echo ""
    
    # 統計上游 NS 使用情況
    echo -e "${YELLOW}上游 NS 使用統計:${NC}"
    local aws_count=$(echo "$log_content" | grep -c "205\.251\." || echo "0")
    local google_count=$(echo "$log_content" | grep -c "216\.239\." || echo "0")
    
    echo -e "  ${GREEN}AWS Route53:${NC} $aws_count 次"
    echo -e "  ${GREEN}Google Cloud DNS:${NC} $google_count 次"
    
    echo ""
    
    # 總計
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}總查詢次數: ${GREEN}$total_queries${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# 主程式
main() {
    clear
    echo -e "${GREEN}=== BIND DNS 日誌監控 v1.0 ===${NC}\n"
    echo -e "容器名稱: ${CYAN}${CONTAINER_NAME}${NC}"
    
    if [ -n "$FILTER_DOMAIN" ]; then
        echo -e "過濾域名: ${YELLOW}${FILTER_DOMAIN}${NC}"
    fi
    
    echo ""
    
    # 檢查容器
    check_container
    
    if [ "$STATS_ONLY" = true ]; then
        # 只顯示統計
        show_stats
    elif [ "$FOLLOW_MODE" = true ]; then
        # 持續監控模式
        follow_logs
    else
        # 顯示最近的日誌
        show_logs
    fi
}

main "$@"

