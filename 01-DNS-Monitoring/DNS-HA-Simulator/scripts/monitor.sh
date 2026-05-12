#!/bin/sh
# ============================================
# DNS HA Controller - 自動故障偵測與切換
# ============================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置變數
MAIN_SERVICE_IP="${MAIN_SERVICE_IP:-172.20.0.10}"
BACKUP_SERVICE_IP="${BACKUP_SERVICE_IP:-172.20.0.20}"
DNS_SECONDARY_IP="${DNS_SECONDARY_IP:-172.20.0.101}"
CHECK_INTERVAL="${CHECK_INTERVAL:-5}"
ZONE_FILE="/zones/app.example.com.zone"
DOMAIN="app.example.com"

# 狀態追蹤
CURRENT_TARGET="main"
FAILURE_COUNT=0
SUCCESS_THRESHOLD=3

# 安裝必要工具（含時區資料）
apk add --no-cache bind-tools curl tzdata > /dev/null 2>&1
[ -n "$TZ" ] && ln -snf "/usr/share/zoneinfo/$TZ" /etc/localtime && echo "$TZ" > /etc/timezone

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_alert() {
    echo -e "${RED}[ALERT]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_service() {
    local ip=$1
    local timeout=2
    
    if wget --timeout=${timeout} --tries=1 --spider "http://${ip}/" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

update_dns_record() {
    local target_ip=$1
    local target_name=$2
    
    log_info "Updating DNS record for ${DOMAIN} to ${target_ip} (${target_name})..."
    
    if [ ! -f "${ZONE_FILE}" ]; then
        log_error "Zone file not found: ${ZONE_FILE}"
        return 1
    fi
    
    cp "${ZONE_FILE}" "${ZONE_FILE}.backup.$(date +%s)"
    sed -i "s/^app\.example\.com\.\s*IN\s*A\s*.*/app.example.com.    IN    A    ${target_ip}/" "${ZONE_FILE}"
    
    log_success "DNS record updated: ${DOMAIN} -> ${target_ip}"
    log_success "DNS zone file updated, server will auto-reload"
    return 0
}

simulate_api_call() {
    local target_ip=$1
    local target_name=$2
    
    log_info "Simulating API call to update DNS..."
    log_info "  API Endpoint: https://api.dns-provider.com/v1/zones/app.example.com/records"
    log_info "  Method: PATCH"
    log_info "  Payload: {\"type\":\"A\",\"name\":\"app\",\"content\":\"${target_ip}\"}"
    
    sleep 1
    log_success "API call completed (simulated)"
}

switch_to_backup() {
    if [ "${CURRENT_TARGET}" = "backup" ]; then
        return 0
    fi
    
    log_alert "=========================================="
    log_alert "FAILOVER TRIGGERED - Switching to Backup"
    log_alert "=========================================="
    
    simulate_api_call "${BACKUP_SERVICE_IP}" "backup"
    update_dns_record "${BACKUP_SERVICE_IP}" "backup"
    CURRENT_TARGET="backup"
    FAILURE_COUNT=0
    
    log_alert "Failover completed: ${DOMAIN} -> ${BACKUP_SERVICE_IP}"
}

switch_to_main() {
    if [ "${CURRENT_TARGET}" = "main" ]; then
        return 0
    fi
    
    log_alert "=========================================="
    log_alert "RECOVERY DETECTED - Switching to Main"
    log_alert "=========================================="
    
    simulate_api_call "${MAIN_SERVICE_IP}" "main"
    update_dns_record "${MAIN_SERVICE_IP}" "main"
    CURRENT_TARGET="main"
    FAILURE_COUNT=0
    
    log_alert "Recovery completed: ${DOMAIN} -> ${MAIN_SERVICE_IP}"
}

main_loop() {
    log_info "=========================================="
    log_info "DNS HA Controller Started"
    log_info "=========================================="
    log_info "Main Service IP: ${MAIN_SERVICE_IP}"
    log_info "Backup Service IP: ${BACKUP_SERVICE_IP}"
    log_info "DNS Secondary IP: ${DNS_SECONDARY_IP}"
    log_info "Check Interval: ${CHECK_INTERVAL} seconds"
    log_info "Current Target: ${CURRENT_TARGET}"
    log_info "=========================================="
    
    log_info "Initializing DNS to point to Main Service..."
    update_dns_record "${MAIN_SERVICE_IP}" "main"
    
    while true; do
        if check_service "${MAIN_SERVICE_IP}"; then
            if [ "${CURRENT_TARGET}" != "main" ]; then
                switch_to_main
            else
                FAILURE_COUNT=0
                log_success "Main Service OK (${MAIN_SERVICE_IP})"
            fi
        else
            FAILURE_COUNT=$((FAILURE_COUNT + 1))
            log_warn "Main Service FAILED (${MAIN_SERVICE_IP}) - Failure count: ${FAILURE_COUNT}"
            if [ "${FAILURE_COUNT}" -ge "${SUCCESS_THRESHOLD}" ]; then
                if [ "${CURRENT_TARGET}" != "backup" ]; then
                    switch_to_backup
                else
                    log_warn "Already on backup, checking backup service..."
                    if ! check_service "${BACKUP_SERVICE_IP}"; then
                        log_error "Backup service also failed! Manual intervention required."
                    fi
                fi
            fi
        fi
        sleep "${CHECK_INTERVAL}"
    done
}

main_loop
