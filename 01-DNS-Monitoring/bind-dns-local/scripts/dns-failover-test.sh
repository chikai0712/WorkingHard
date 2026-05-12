#!/bin/bash
# -------------------------------------------------------------------------------
# DNS Failover 測試腳本 - 模擬 AWS/Google NS 異常場景
# 功能：在本機防火牆阻擋特定 DNS 服務商，測試網站解析的 failover 行為
# 
# 使用場景：
#   1. 在 AWS 上部署兩台 EC2：
#      - EC2-1: 顯示 "我是 AWS 3.3.3.3" (假設 IP 為 3.3.3.3)
#      - EC2-2: 顯示 "我是 Google 2.2.2.2" (假設 IP 為 2.2.2.2)
#   2. 域名同時配置 AWS Route53 和 Google Cloud DNS 作為 NS
#   3. 本腳本模擬阻擋其中一個 NS，觀察系統是否切換到另一個
#
# 用法：
#   sudo bash ./dns-failover-test.sh [域名] [AWS_IP] [Google_IP] [阻擋時間(秒)]
#   例如：sudo bash ./dns-failover-test.sh www.example.com 3.3.3.3 2.2.2.2 60
#
# 預設值：
#   DOMAIN="www.clouddeployment168.site"
#   AWS_EC2_IP="35.74.79.10"  # 實際 AWS EC2 IP
#   GCP_EC2_IP="35.78.244.92"  # 實際 Google EC2 IP
#   BLOCK_DURATION=180  # 阻擋持續時間（秒），預設 3 分鐘
# -------------------------------------------------------------------------------

set -e

# 配置區域
DOMAIN="${1:-www.clouddeployment168.site}"
AWS_EC2_IP="${2:-35.74.79.10}"
GCP_EC2_IP="${3:-35.78.244.92}"
BLOCK_DURATION="${4:-180}"  # 阻擋持續時間（秒），預設 3 分鐘

# AWS Route53 NS IPs
AWS_NS=("205.251.197.44" "205.251.199.48" "205.251.192.236" "205.251.195.65")
# Google Cloud DNS NS IPs
GCP_NS=("216.239.32.108" "216.239.34.108" "216.239.36.108" "216.239.38.108")

# 測試超時設定（秒）
DNS_TIMEOUT="${DNS_TIMEOUT:-5}"
CURL_TIMEOUT="${CURL_TIMEOUT:-10}"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日誌路徑
LOG="/tmp/dns_failover_test_$(date +%Y%m%d_%H%M%S).log"
DEBUG_LOG="/tmp/dns_failover_debug.log"
ERROR_LOG="/tmp/dns_failover_errors.log"

# 白名單表格名稱
ALLOWED_TABLE_NAME="allowed_dns_table"

# -------------------------------------------------------------------------------
# 清理函數（trap 時自動呼叫，參考 dig-trace-failover.sh）
# -------------------------------------------------------------------------------
cleanup() {
    echo -e "\n${YELLOW}正在還原防火牆 (pfctl -F all)...${NC}"
    pfctl -F all 2>/dev/null || true
    
    echo -e "${YELLOW}清除 DNS 快取...${NC}"
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    
    echo -e "${GREEN}防火牆已重置，DNS 快取已清除${NC}"
    echo -e "${CYAN}提示：如需完全重置環境，可執行：${NC}"
    echo -e "${CYAN}  docker restart bind-dns-local${NC}"
}

trap cleanup EXIT

# -------------------------------------------------------------------------------
# 套用防火牆規則（參考 dig-trace-failover.sh 的成功方法）
# 使用 pfctl -f 直接載入規則文件，而不是合併到 /etc/pf.conf
# -------------------------------------------------------------------------------
apply_block_aws_only() {
    echo -e "${CYAN}封鎖 AWS 的 4 個 NS，Google NS 保持暢通${NC}"
    echo "AWS NS IP: ${AWS_NS[*]}"
    
    if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        pfctl -e 2>/dev/null || {
            echo -e "${RED}[FAIL] 無法啟用 pfctl${NC}"
            return 1
        }
    fi
    
    local tmp_rules
    tmp_rules=$(mktemp)
    for ip in "${AWS_NS[@]}"; do
        echo "block drop out quick inet proto udp from any to $ip port 53"
        echo "block drop out quick inet proto tcp from any to $ip port 53"
    done > "$tmp_rules"
    
    pfctl -nf "$tmp_rules" 2>/dev/null || {
        echo -e "${RED}[FAIL] 規則語法錯誤${NC}"
        rm -f "$tmp_rules"
        return 1
    }
    
    pfctl -f "$tmp_rules" 2>> "$DEBUG_LOG"
    rm -f "$tmp_rules"
    
    for ip in "${AWS_NS[@]}"; do
        pfctl -k "$ip" 2>/dev/null || true
    done
    
    echo -e "${GREEN}AWS NS 已封鎖，Google NS 保持暢通${NC}"
}

apply_block_google_only() {
    echo -e "${CYAN}封鎖 Google 的 4 個 NS，AWS NS 保持暢通${NC}"
    echo "Google NS IP: ${GCP_NS[*]}"
    
    if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        pfctl -e 2>/dev/null || {
            echo -e "${RED}[FAIL] 無法啟用 pfctl${NC}"
            return 1
        }
    fi
    
    local tmp_rules
    tmp_rules=$(mktemp)
    for ip in "${GCP_NS[@]}"; do
        echo "block drop out quick inet proto udp from any to $ip port 53"
        echo "block drop out quick inet proto tcp from any to $ip port 53"
    done > "$tmp_rules"
    
    pfctl -nf "$tmp_rules" 2>/dev/null || {
        echo -e "${RED}[FAIL] 規則語法錯誤${NC}"
        rm -f "$tmp_rules"
        return 1
    }
    
    pfctl -f "$tmp_rules" 2>> "$DEBUG_LOG"
    rm -f "$tmp_rules"
    
    for ip in "${GCP_NS[@]}"; do
        pfctl -k "$ip" 2>/dev/null || true
    done
    
    echo -e "${GREEN}Google NS 已封鎖，AWS NS 保持暢通${NC}"
}

# -------------------------------------------------------------------------------
# 清除 DNS 快取
# -------------------------------------------------------------------------------
flush_dns_cache() {
    echo -e "${CYAN}清除系統 DNS 快取...${NC}"
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}[OK] 快取已清除${NC}"
}

# -------------------------------------------------------------------------------
# 解析 time 的 real 秒數（參考 dig-trace-failover.sh）
# -------------------------------------------------------------------------------
parse_real_seconds() {
    local line="$1"
    local min=0
    local sec=0
    if [[ "$line" =~ real[[:space:]]+([0-9]+)m([0-9.]+)s ]]; then
        min="${BASH_REMATCH[1]}"
        sec="${BASH_REMATCH[2]}"
    fi
    echo "$min $sec" | awk '{ printf "%.3f", $1*60 + $2 }'
}

# -------------------------------------------------------------------------------
# 使用 dig +trace 測試（參考 dig-trace-failover.sh 的核心方法）
# 這是關鍵：dig +trace 會繞過系統 DNS，由本機從根開始遞回查詢
# -------------------------------------------------------------------------------
test_dig_trace() {
    local domain=$1
    local expected_ip=$2
    local timeout=${3:-5}
    
    echo -e "${CYAN}執行: time dig +trace +nodnssec $domain${NC}"
    echo -e "${YELLOW}請看輸出最後「Received ... from x.x.x.x」→ 應來自可用的 NS${NC}"
    echo ""
    
    local time_tmp
    time_tmp=$(mktemp)
    set +e
    { time dig +trace +nodnssec "$domain" 2>&1 ; } 2> "$time_tmp"
    set -e
    
    echo ""
    echo -e "${CYAN}---------- 時間統計 (time) ----------${NC}"
    cat "$time_tmp"
    
    local real_sec=""
    if real_line=$(grep '^real' "$time_tmp" 2>/dev/null); then
        real_sec=$(parse_real_seconds "$real_line")
        echo ""
        echo -e "${CYAN}---------- 解讀 (real = ${real_sec}s) ----------${NC}"
        if awk -v r="$real_sec" 'BEGIN { exit (r < 0.5 ? 0 : 1) }' 2>/dev/null; then
            echo -e "${GREEN}real < 0.5 秒：dig 採用了並行查詢或快速失敗，故障切換幾乎無感${NC}"
        elif awk -v r="$real_sec" 'BEGIN { exit (r >= 1 && r <= 2.5 ? 0 : 1) }' 2>/dev/null; then
            echo -e "${YELLOW}real 約 1~2.5 秒：標準 Timeout。dig 嘗試連被擋的 NS、等待逾時後才問備用 NS${NC}"
        elif awk -v r="$real_sec" 'BEGIN { exit (r > 4 ? 0 : 1) }' 2>/dev/null; then
            echo -e "${YELLOW}real > 4 秒：重試了多次才成功${NC}"
        fi
    fi
    
    rm -f "$time_tmp"
    
    # 提取解析出的 IP
    local result_ip
    result_ip=$(dig +short "$domain" A +time="$timeout" 2>/dev/null | grep -E '^[0-9.]+$' | head -1)
    
    if [ -n "$result_ip" ]; then
        if [ "$result_ip" = "$expected_ip" ]; then
            echo -e "${GREEN}[OK] 解析成功，IP: $result_ip (符合預期)${NC}"
            echo "$result_ip"
            return 0
        else
            echo -e "${YELLOW}[!] 解析成功但 IP 不符預期: $result_ip (預期: $expected_ip)${NC}"
            echo "$result_ip"
            return 0
        fi
    else
        echo -e "${RED}[FAIL] 無法解析${NC}"
        return 1
    fi
}

# -------------------------------------------------------------------------------
# 測試 DNS 解析（簡單版本，用於快速驗證）
# -------------------------------------------------------------------------------
test_dns_resolve() {
    local domain=$1
    local timeout=${2:-5}
    local result ip

    result=$(dig +short "$domain" A +time="$timeout" 2>&1) || true
    ip=$(echo "$result" | grep -E '^[0-9.]+$' | head -1)

    if [ -n "$ip" ]; then
        echo -e "  DNS 解析: ${GREEN}成功${NC}  IP: $ip"
        echo "$ip"
        return 0
    else
        echo -e "  DNS 解析: ${RED}失敗${NC}"
        {
            echo "--- [$(date '+%Y-%m-%d %H:%M:%S')] DNS 解析失敗 ---"
            echo "domain=$domain"
            dig "$domain" A +time=2 2>&1 || true
            echo ""
        } >> "$ERROR_LOG"
        return 1
    fi
}

# -------------------------------------------------------------------------------
# 測試 HTTP 連線（驗證實際網站內容）
# -------------------------------------------------------------------------------
test_http_connection() {
    local url=$1
    local expected_ip=$2
    local timeout=${3:-10}
    local result content ip

    echo -e "  測試 HTTP 連線: $url"
    result=$(curl -s -w "\n%{http_code}\n%{time_total}" --connect-timeout "$timeout" --max-time "$timeout" "$url" 2>&1) || true

    http_code=$(echo "$result" | tail -2 | head -1)
    time_total=$(echo "$result" | tail -1)
    content=$(echo "$result" | head -n -2)

    # 從回應中提取 IP（假設網站顯示 "我是 AWS 3.3.3.3" 或 "我是 Google 2.2.2.2"）
    if echo "$content" | grep -q "AWS\|Google"; then
        if echo "$content" | grep -q "AWS"; then
            ip=$(echo "$content" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1)
            echo -e "  網站內容: ${CYAN}我是 AWS $ip${NC}"
        elif echo "$content" | grep -q "Google"; then
            ip=$(echo "$content" | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | head -1)
            echo -e "  網站內容: ${CYAN}我是 Google $ip${NC}"
        fi

        if [ "$http_code" = "200" ]; then
            echo -e "  HTTP 狀態: ${GREEN}$http_code${NC}  耗時: ${time_total}s"
            return 0
        else
            echo -e "  HTTP 狀態: ${YELLOW}$http_code${NC}  耗時: ${time_total}s"
            return 1
        fi
    else
        echo -e "  HTTP 狀態: ${YELLOW}$http_code${NC}  耗時: ${time_total}s"
        echo -e "  ${YELLOW}警告: 無法從內容判斷是 AWS 還是 Google${NC}"
        return 1
    fi
}

# -------------------------------------------------------------------------------
# 主測試流程
# -------------------------------------------------------------------------------
main() {
    [ "$(id -u)" -ne 0 ] && echo -e "${RED}請使用 sudo 執行${NC}" && exit 1

    exec 1> >(tee -a "$LOG") 2>&1

    clear
    echo -e "${GREEN}=== DNS Failover 測試（AWS/Google NS 異常模擬）===${NC}"
    echo -e "域名: ${CYAN}$DOMAIN${NC}"
    echo -e "預期 AWS EC2 IP: ${CYAN}$AWS_EC2_IP${NC} (顯示: 我是 AWS $AWS_EC2_IP)"
    echo -e "預期 Google EC2 IP: ${CYAN}$GCP_EC2_IP${NC} (顯示: 我是 Google $GCP_EC2_IP)"
    echo -e "阻擋持續時間: ${CYAN}$BLOCK_DURATION 秒 ($(($BLOCK_DURATION/60)) 分鐘)${NC}"
    echo -e "LOG: ${CYAN}$LOG${NC}"
    echo -e "Debug: ${CYAN}$DEBUG_LOG${NC}"
    echo -e "錯誤 LOG: ${CYAN}$ERROR_LOG${NC}\n"

    local PHASE_URL="https://$DOMAIN"
    local AWS_ONLY=("${AWS_NS[@]}")
    local GCP_ONLY=("${GCP_NS[@]}")

    # -------------------------------------------------------------------------
    # 步驟 1：基準測試（無阻擋）
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 1: 基準測試（無阻擋）━━━${NC}"
    echo -e "目標：確認域名可正常解析並連線\n"
    
    # 清除所有防火牆規則（還原到無阻擋狀態）
    pfctl -F all 2>/dev/null || true
    flush_dns_cache

    echo -e "測試 DNS 解析..."
    local baseline_ip
    baseline_ip=$(test_dns_resolve "$DOMAIN" "$DNS_TIMEOUT")
    if [ -n "$baseline_ip" ]; then
        echo -e "${GREEN}[OK] 基準測試：DNS 解析成功，IP: $baseline_ip${NC}\n"
    else
        echo -e "${RED}[FAIL] 基準測試：DNS 解析失敗，請檢查域名配置${NC}\n"
        exit 1
    fi

    # -------------------------------------------------------------------------
    # 步驟 2：阻擋 AWS NS，只放行 Google NS（使用 dig +trace）
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 2: 阻擋 AWS NS，驗證 Google NS 接手 ━━━${NC}"
    echo -e "預期：使用 dig +trace 應從 Google NS 解析到 Google EC2 ($GCP_EC2_IP)\n"
    
    apply_block_aws_only
    flush_dns_cache

    echo -e "使用 dig +trace 測試（繞過系統 DNS，從根開始遞回）..."
    local google_ip
    google_ip=$(test_dig_trace "$DOMAIN" "$GCP_EC2_IP" "$DNS_TIMEOUT")
    
    if [ -n "$google_ip" ]; then
        if [ "$google_ip" = "$GCP_EC2_IP" ]; then
            echo -e "${GREEN}[OK] 成功切換到 Google NS，IP: $google_ip${NC}"
        else
            echo -e "${YELLOW}[!] 解析成功但 IP 不符預期: $google_ip (預期: $GCP_EC2_IP)${NC}"
        fi
        
        echo -e "\n測試 HTTP 連線..."
        if test_http_connection "$PHASE_URL" "$GCP_EC2_IP" "$CURL_TIMEOUT"; then
            echo -e "${GREEN}[OK] HTTP 連線成功，應顯示「我是 Google $GCP_EC2_IP」${NC}\n"
        else
            echo -e "${YELLOW}[!] HTTP 連線失敗或內容不符預期${NC}\n"
        fi
    else
        echo -e "${RED}[FAIL] 無法解析，可能原因：${NC}"
        echo -e "  1. Google NS 配置不正確"
        echo -e "  2. 防火牆規則未生效"
        echo -e "  錯誤詳情: $ERROR_LOG\n"
    fi
    
    # 持續阻擋指定時間，讓使用者有時間觀察和測試
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}持續阻擋 AWS NS，維持 $BLOCK_DURATION 秒 ($(($BLOCK_DURATION/60)) 分鐘)${NC}"
    echo -e "${CYAN}在此期間，你可以：${NC}"
    echo -e "  - 測試網站連線: curl http://$DOMAIN"
    echo -e "  - 測試 DNS 解析: dig $DOMAIN"
    echo -e "  - 在瀏覽器訪問: http://$DOMAIN"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 倒數計時
    local remaining=$BLOCK_DURATION
    while [ $remaining -gt 0 ]; do
        printf "\r${YELLOW}剩餘時間: %02d:%02d${NC} " $((remaining/60)) $((remaining%60))
        sleep 1
        remaining=$((remaining-1))
    done
    printf "\r${GREEN}✅ $BLOCK_DURATION 秒已完成${NC}                    \n\n"
    
    # 清除防火牆規則，準備下一個測試
    echo -e "${YELLOW}清除當前防火牆規則...${NC}"
    pfctl -F all 2>/dev/null || true
    flush_dns_cache
    echo -e "${GREEN}✅ 環境已重置${NC}\n"

    # -------------------------------------------------------------------------
    # 步驟 3：阻擋 Google NS，只放行 AWS NS（使用 dig +trace）
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 3: 阻擋 Google NS，驗證 AWS NS 接手 ━━━${NC}"
    echo -e "預期：使用 dig +trace 應從 AWS NS 解析到 AWS EC2 ($AWS_EC2_IP)\n"
    
    apply_block_google_only
    flush_dns_cache

    echo -e "使用 dig +trace 測試（繞過系統 DNS，從根開始遞回）..."
    local aws_ip
    aws_ip=$(test_dig_trace "$DOMAIN" "$AWS_EC2_IP" "$DNS_TIMEOUT")
    
    if [ -n "$aws_ip" ]; then
        if [ "$aws_ip" = "$AWS_EC2_IP" ]; then
            echo -e "${GREEN}[OK] 成功切換到 AWS NS，IP: $aws_ip${NC}"
        else
            echo -e "${YELLOW}[!] 解析成功但 IP 不符預期: $aws_ip (預期: $AWS_EC2_IP)${NC}"
        fi
        
        echo -e "\n測試 HTTP 連線..."
        if test_http_connection "$PHASE_URL" "$AWS_EC2_IP" "$CURL_TIMEOUT"; then
            echo -e "${GREEN}[OK] HTTP 連線成功，應顯示「我是 AWS $AWS_EC2_IP」${NC}\n"
        else
            echo -e "${YELLOW}[!] HTTP 連線失敗或內容不符預期${NC}\n"
        fi
    else
        echo -e "${RED}[FAIL] 無法解析，可能原因：${NC}"
        echo -e "  1. AWS NS 配置不正確"
        echo -e "  2. 防火牆規則未生效"
        echo -e "  錯誤詳情: $ERROR_LOG\n"
    fi
    
    # 持續阻擋指定時間，讓使用者有時間觀察和測試
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}持續阻擋 Google NS，維持 $BLOCK_DURATION 秒 ($(($BLOCK_DURATION/60)) 分鐘)${NC}"
    echo -e "${CYAN}在此期間，你可以：${NC}"
    echo -e "  - 測試網站連線: curl http://$DOMAIN"
    echo -e "  - 測試 DNS 解析: dig $DOMAIN"
    echo -e "  - 在瀏覽器訪問: http://$DOMAIN"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
    
    # 倒數計時
    local remaining=$BLOCK_DURATION
    while [ $remaining -gt 0 ]; do
        printf "\r${YELLOW}剩餘時間: %02d:%02d${NC} " $((remaining/60)) $((remaining%60))
        sleep 1
        remaining=$((remaining-1))
    done
    printf "\r${GREEN}✅ $BLOCK_DURATION 秒已完成${NC}                    \n\n"

    # -------------------------------------------------------------------------
    # 步驟 4：使用 nslookup 測試真實使用者等待時間
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 4: nslookup 測試（真實使用者等待時間）━━━${NC}"
    echo -e "nslookup 會走系統 DNS 設定，更能反映真實上網體驗\n"
    
    apply_block_aws_only
    flush_dns_cache
    
    echo -e "執行: time nslookup $DOMAIN"
    local time_tmp
    time_tmp=$(mktemp)
    set +e
    { time nslookup "$DOMAIN" 2>&1 ; } 2> "$time_tmp"
    set -e
    
    echo ""
    echo -e "${CYAN}---------- 時間統計 (time) — 真實使用者等待時間 ----------${NC}"
    cat "$time_tmp"
    if real_line=$(grep '^real' "$time_tmp" 2>/dev/null); then
        real_sec=$(parse_real_seconds "$real_line")
        echo -e "${GREEN}real = ${real_sec}s（系統解析器：從按下 Enter 到看到結果）${NC}"
    fi
    rm -f "$time_tmp"
    echo ""

    echo -e "\n${GREEN}測試完成${NC}"
    echo -e "完整日誌: ${CYAN}$LOG${NC}"
}

main "$@"
