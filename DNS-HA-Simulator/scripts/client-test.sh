#!/bin/sh
# ============================================
# DNS Client - 模擬玩家端持續連線測試
# ============================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
DOMAIN="${DOMAIN:-app.example.com}"
DNS_SERVER="${DNS_SERVER:-172.20.0.101}"
CHECK_INTERVAL="${CHECK_INTERVAL:-2}"

# 安裝必要工具（含時區資料）
apk add --no-cache bind-tools curl wget tzdata > /dev/null 2>&1
[ -n "$TZ" ] && ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime && echo "$TZ" > /etc/timezone

log_info() {
    echo -e "${BLUE}[CLIENT]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[CLIENT]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[CLIENT]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# DNS 解析
resolve_dns() {
    local domain=$1
    local dns_server=$2
    
    dig @"${dns_server}" "${domain}" +short +time=2 +tries=1 2>/dev/null | head -1
}

# 測試 HTTP 連線
test_http_connection() {
    local ip=$1
    local timeout=3
    
    local response=$(wget --timeout=${timeout} --tries=1 -qO- "http://${ip}/" 2>/dev/null || echo "FAILED")
    
    if [ "${response}" != "FAILED" ] && [ -n "${response}" ]; then
        echo "${response}"
        return 0
    else
        return 1
    fi
}

# 主測試循環
main_loop() {
    log_info "=========================================="
    log_info "DNS Client Started"
    log_info "=========================================="
    log_info "Domain: ${DOMAIN}"
    log_info "DNS Server: ${DNS_SERVER}"
    log_info "Check Interval: ${CHECK_INTERVAL} seconds"
    log_info "=========================================="
    
    local consecutive_failures=0
    local max_failures=5
    
    while true; do
        # DNS 解析
        local resolved_ip=$(resolve_dns "${DOMAIN}" "${DNS_SERVER}")
        
        if [ -z "${resolved_ip}" ]; then
            consecutive_failures=$((consecutive_failures + 1))
            log_error "❌ DNS Resolution FAILED - Cannot resolve ${DOMAIN}"
            
            if [ "${consecutive_failures}" -ge "${max_failures}" ]; then
                log_error "Multiple DNS failures detected. DNS server may be down."
            fi
        else
            log_info "DNS Resolution: ${DOMAIN} -> ${resolved_ip}"
            
            # 測試 HTTP 連線
            local response=$(test_http_connection "${resolved_ip}")
            
            if [ $? -eq 0 ]; then
                consecutive_failures=0
                
                case "${response}" in
                    *"Main Server OK"*)
                        log_success "✅ Name: Main-Server-OK <--- [$(date '+%H:%M:%S')]"
                        ;;
                    *"Backup Server Active"*)
                        log_success "✅ Name: Backup-Server-Active <--- [$(date '+%H:%M:%S')]"
                        ;;
                    *)
                        log_success "✅ Connection OK: ${response} <--- [$(date '+%H:%M:%S')]"
                        ;;
                esac
            else
                consecutive_failures=$((consecutive_failures + 1))
                log_error "❌ Connection Failed to ${resolved_ip} <--- [$(date '+%H:%M:%S')]"
                
                if [ "${consecutive_failures}" -ge "${max_failures}" ]; then
                    log_error "Multiple connection failures. Service may be down."
                fi
            fi
        fi
        
        sleep "${CHECK_INTERVAL}"
    done
}

main_loop
