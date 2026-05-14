#!/bin/bash

# DNS 故障切換測試腳本（白名單 + Anchor 模式）
# 用於測試多供應商 DNS 的故障切換行為
# 白名單：只擋「回來的 DNS 回應」(inbound port 53)，不擋「出去的查詢」(outbound)
# 主規則集前置：規則寫在 /etc/pf.conf 內容「最前面」載入，先於 com.apple anchor 被評估；還原時 pfctl -f /etc/pf.conf
# Debug：日誌寫入 $DNS_TEST_DEBUG_LOG；失敗時會自動保留現場再清理

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置
DOMAIN="${1:-www.clouddeployment168.site}"
# Debug 日誌（驗證狀態與 pfctl 計數器），失敗時可查規則與 Packets 計數
DNS_TEST_DEBUG_LOG="/tmp/dns_test_debug.log"

# AWS Route 53 授權 DNS（截圖清單）
AWS_DNS_IPS=(
    "205.251.197.44"   # ns-1324.awsdns-37.org
    "205.251.199.48"   # ns-1840.awsdns-38.co.uk
    "205.251.192.236"  # ns-236.awsdns-29.com
    "205.251.195.65"   # ns-833.awsdns-40.net
)
# Google Domains / Cloud DNS 授權 DNS（截圖清單）
GOOGLE_DNS_IPS=(
    "216.239.32.108"   # ns-cloud-c1.googledomains.com
    "216.239.34.108"   # ns-cloud-c2.googledomains.com
    "216.239.36.108"   # ns-cloud-c3.googledomains.com
    "216.239.38.108"   # ns-cloud-c4.googledomains.com
)
# 常見遞迴 DNS（全面癱瘓時一併封鎖）
RECURSIVE_DNS_IPS=(
    "8.8.8.8"    # Google Public DNS
    "8.8.4.4"    # Google Public DNS
    "1.1.1.1"    # Cloudflare DNS
    "1.0.0.1"    # Cloudflare DNS
)
# 白名單「只讓 Google 過」：Google 權威 NS（4）+ Google 遞迴 8.8.8.8 / 8.8.4.4（共 6 個）
GOOGLE_WHITELIST_IPS=( "${GOOGLE_DNS_IPS[@]}" "8.8.8.8" "8.8.4.4" )
# 代表用（階段 1 與部分測試仍用第一組）
AWS_DNS="${AWS_DNS_IPS[0]}"
GOOGLE_DNS="${GOOGLE_DNS_IPS[0]}"
DEFAULT_DNS="8.8.8.8"  # 系統常用預設，僅用於階段 1 顯示

# 檢查是否為 macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo -e "${RED}❌ 此腳本目前僅支援 macOS（使用 pfctl）${NC}"
    echo "Linux 版本可以使用 iptables 或 firewall-cmd"
    exit 1
fi

# 檢查是否為 root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}⚠️  需要 root 權限來封鎖 DNS 伺服器${NC}"
    echo "請使用 sudo 執行此腳本"
    exit 1
fi

# 檢查 pfctl 是否可用
if ! command -v pfctl &> /dev/null; then
    echo -e "${RED}❌ 錯誤：pfctl 未安裝${NC}"
    echo "pfctl 是 macOS 內建的防火牆工具，應該已經安裝"
    exit 1
fi

# 檢查 pfctl 狀態
echo -e "${CYAN}🔍 檢查 pfctl 狀態...${NC}"
pfctl_status=$(pfctl -si 2>/dev/null | grep "Status:" | awk '{print $2}')
if [ "$pfctl_status" != "Enabled" ]; then
    echo -e "${YELLOW}⚠️  pfctl 未啟用，嘗試啟用...${NC}"
    pfctl -e 2>/dev/null || {
        echo -e "${RED}❌ 無法啟用 pfctl${NC}"
        echo "請檢查系統設定中的防火牆設定"
        exit 1
    }
    echo -e "${GREEN}✅ pfctl 已啟用${NC}"
else
    echo -e "${GREEN}✅ pfctl 已啟用${NC}"
fi

# 白名單具名表格（只放行此表內 IP 的 port 53，其餘 DNS 全擋）
ALLOWED_TABLE_NAME="allowed_dns_table"
# 主規則集前置模式：規則寫在 main 最前，不再使用 anchor
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 DNS 故障切換測試工具${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "測試域名：$DOMAIN"
echo "AWS Route 53 DNS（${#AWS_DNS_IPS[@]} 組）：${AWS_DNS_IPS[*]}"
echo "Google Domains DNS（${#GOOGLE_DNS_IPS[@]} 組）：${GOOGLE_DNS_IPS[*]}"
echo "白名單「只讓 Google 過」時放行（${#GOOGLE_WHITELIST_IPS[@]} 組）：${GOOGLE_WHITELIST_IPS[*]}"
echo "Debug 日誌（驗證失敗時請查看）：$DNS_TEST_DEBUG_LOG"
echo ""

# 函數：清除 DNS 快取
clear_dns_cache() {
    echo -e "${CYAN}🧹 清除 DNS 快取...${NC}"
    sudo dscacheutil -flushcache 2>/dev/null || true
    sudo killall -HUP mDNSResponder 2>/dev/null || true
    echo -e "${GREEN}✅ DNS 快取已清除${NC}"
}

# 函數：macOS 兼容的超時執行
run_with_timeout() {
    local timeout=$1
    shift
    local cmd="$@"
    
    # 檢查是否有 gtimeout（GNU coreutils，通過 brew install coreutils 安裝）
    if command -v gtimeout &> /dev/null; then
        gtimeout $timeout $cmd
        return $?
    fi
    
    # 使用背景進程和 kill 實現超時（macOS 兼容）
    # 創建臨時文件來存儲結果
    local result_file=$(mktemp)
    local exit_file=$(mktemp)
    
    # 在背景執行命令
    (
        eval "$cmd" > "$result_file" 2>&1
        echo $? > "$exit_file"
    ) &
    local pid=$!
    
    # 等待指定時間
    local count=0
    while [ $count -lt $timeout ]; do
        if ! kill -0 $pid 2>/dev/null; then
            # 進程已結束
            wait $pid 2>/dev/null
            local exit_code=$(cat "$exit_file" 2>/dev/null || echo "0")
            cat "$result_file" 2>/dev/null
            rm -f "$result_file" "$exit_file"
            return $exit_code
        fi
        sleep 1
        count=$((count + 1))
    done
    
    # 超時，殺死進程和子進程
    kill $pid 2>/dev/null
    pkill -P $pid 2>/dev/null
    wait $pid 2>/dev/null
    rm -f "$result_file" "$exit_file"
    return 124  # 超時退出碼
}

# 函數：測試 DNS 查詢
test_dns_query() {
    local dns_server=$1
    local description=$2
    local timeout=${3:-5}
    
    # 計算 nslookup 的 timeout（秒）
    local nslookup_timeout=$((timeout - 1))
    if [ $nslookup_timeout -lt 1 ]; then
        nslookup_timeout=1
    fi
    
    if [ -z "$dns_server" ]; then
        # 不指定 DNS 伺服器，使用系統預設
        echo -e "${CYAN}📡 測試 $description（系統自動選擇 DNS）...${NC}"
        local result=$(run_with_timeout $timeout nslookup -timeout=$nslookup_timeout $DOMAIN 2>&1)
    else
        echo -e "${CYAN}📡 測試 $description ($dns_server)...${NC}"
        local result=$(run_with_timeout $timeout nslookup -timeout=$nslookup_timeout $DOMAIN $dns_server 2>&1)
    fi
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        local ip=$(echo "$result" | grep -A 1 "Name:" | grep "Address:" | tail -1 | awk '{print $2}')
        if [ -n "$ip" ]; then
            echo -e "${GREEN}✅ 成功：解析到 $ip${NC}"
            echo "$result" | grep -A 5 "Name:" | head -6
            clear_dns_cache
            return 0
        else
            echo -e "${RED}❌ 失敗：無法取得 IP 位址${NC}"
            echo "查詢結果："
            echo "$result" | tail -5
            clear_dns_cache
            return 1
        fi
    else
        if [ $exit_code -eq 124 ]; then
            echo -e "${RED}❌ 失敗：查詢逾時${NC}"
            echo -e "${YELLOW}💡 查詢逾時，這可能是因為 DNS 被封鎖或無法連線${NC}"
        else
            echo -e "${RED}❌ 失敗：查詢錯誤（exit code: $exit_code）${NC}"
            echo "查詢結果："
            echo "$result" | tail -5
        fi
        clear_dns_cache
        return 1
    fi
}

# 函數：驗證封鎖是否生效（白名單模式：該 IP 不在放行表內 = 被封鎖）
# 測試方式：直接對該 IP:53 查詢（規則阻擋雙向 port 53：out=擋查詢封包，in=擋回應封包）
# 若仍得到結果，可能原因：本機/系統快取、DoH/DoT 走 443、或 nslookup/dig 使用系統解析器
verify_block() {
    local dns_ip=$1
    local description=$2
    
    echo -e "${CYAN}🔍 驗證 $description ($dns_ip) 是否被封鎖...${NC}"
    
    # 白名單：若 IP 在放行表內則未被擋；不在放行表內則已被擋
    local in_table=false
    if pfctl -t "$ALLOWED_TABLE_NAME" -T show 2>/dev/null | grep -q "^${dns_ip}$"; then
        in_table=true
    fi
    if [ "$in_table" = false ] && ! pfctl -sr 2>/dev/null | head -20 | grep -q "port.*53"; then
        echo -e "${YELLOW}⚠️  主規則集前幾行尚無 port 53 規則，請確認已執行封鎖${NC}"
    fi
    if [ "$in_table" = true ]; then
        echo -e "${RED}❌ $dns_ip 在白名單內，未被封鎖${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $dns_ip 不在白名單內，已被封鎖${NC}"
    fi
    
    # 實際測試：直接對該 IP 查詢（應失敗）。規則擋雙向 port 53，DNS 伺服器本身正常，但封包不應往返
    echo ""
    echo -e "${CYAN}測試：直接對 $dns_ip:53 查詢（阻擋雙向 port 53，預期逾時/失敗）...${NC}"
    
    local test_exit=0
    local test_result=""
    if command -v dig &>/dev/null; then
        test_result=$(run_with_timeout 4 dig @$dns_ip $DOMAIN A +short +time=2 +tries=1 2>&1)
        # 有回傳 IP = 查詢成功 = 封鎖未生效；無 IP 或逾時 = 封鎖生效
        if echo "$test_result" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
            test_exit=0
        else
            test_exit=1
        fi
    else
        test_result=$(run_with_timeout 4 nslookup -timeout=2 $DOMAIN $dns_ip 2>&1)
        test_exit=$?
    fi
    
    if [ $test_exit -ne 0 ] || echo "$test_result" | grep -qi "timeout\|timed out\|can't find\|connection refused\|SERVFAIL\|no servers could be reached"; then
        echo -e "${GREEN}✅ 封鎖生效：直接查詢 $dns_ip 失敗（預期行為）${NC}"
        return 0
    else
        echo -e "${RED}❌ 警告：直接查詢 $dns_ip 仍成功，可能為快取或規則未命中（如 IPv6）${NC}"
        echo "查詢結果："
        echo "$test_result" | head -5
        return 1
    fi
}

# 函數：使用 dig 測試（更詳細）
test_dns_dig() {
    local dns_server=$1
    local description=$2
    
    echo -e "${CYAN}📡 使用 dig 測試 $description ($dns_server)...${NC}"
    
    if command -v dig &> /dev/null; then
        dig @$dns_server $DOMAIN A +short +time=3 +tries=2 2>&1 | head -5
        local ip=$(dig @$dns_server $DOMAIN A +short +time=3 +tries=2 2>&1 | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
        if [ -n "$ip" ]; then
            echo -e "${GREEN}✅ 成功：解析到 $ip${NC}"
            return 0
        else
            echo -e "${RED}❌ 失敗：無法取得 IP 位址${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  dig 未安裝，使用 nslookup${NC}"
        test_dns_query "$dns_server" "$description"
    fi
}

# 函數：白名單模式 — 只放行指定 IP 的 port 53，其餘 DNS 全擋（含雙向 in/out）
# 用法：apply_dns_whitelist "描述" IP1 IP2 ... （空則全部 DNS 都擋）
# macOS：filter 必須在 scrub/anchor 之後；規則插入「最後一個 anchor/scrub 行」之後，並帶 quick 提高優先權
apply_dns_whitelist() {
    local desc=$1
    shift
    local allowed=("$@")
    local LOG_FILE="${DNS_TEST_DEBUG_LOG}"
    local temp_rules
    temp_rules=$(mktemp)
    local final_conf
    final_conf=$(mktemp)
    
    {
        echo "===== 執行測試: $desc [$(date)] ====="
        echo "嘗試套用白名單: 放行 ${#allowed[@]} 個 IP (其餘 DNS 全擋)"
    } >> "$LOG_FILE"
    
    if [ ${#allowed[@]} -eq 0 ]; then
        echo -e "${YELLOW}🚫 [白名單] $desc：全部 DNS 都擋（port 53）${NC}"
    else
        echo -e "${YELLOW}🚫 [白名單] $desc：只放行 ${#allowed[@]} 個 IP，其餘 DNS 全擋${NC}"
        echo -e "${CYAN}   放行：${allowed[*]}${NC}"
    fi
    
    if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        pfctl -e 2>/dev/null || { echo -e "${RED}❌ 無法啟用 pfctl${NC}"; rm -f "$temp_rules" "$final_conf"; return 1; }
    fi
    
    # 1. 準備測試規則（filter 必須在 anchor 之後；quick 確保優先於系統規則）
    #    雙向：pass in/out 放行白名單，block in/out 擋其餘 port 53；inet 避免 IPv4/IPv6 混亂
    if [ ${#allowed[@]} -gt 0 ]; then
        local ip_list=""
        for ip in "${allowed[@]}"; do ip_list="$ip_list $ip"; done
        {
            echo "table <$ALLOWED_TABLE_NAME> { $ip_list }"
            echo "pass in quick inet proto { udp, tcp } from <$ALLOWED_TABLE_NAME> port 53 to any"
            echo "pass out quick inet proto { udp, tcp } to <$ALLOWED_TABLE_NAME> port 53"
            echo "block in quick inet proto { udp, tcp } from any to any port 53"
            echo "block out quick inet proto { udp, tcp } from any to any port 53"
        } > "$temp_rules"
    else
        {
            echo "block in quick inet proto { udp, tcp } from any to any port 53"
            echo "block out quick inet proto { udp, tcp } from any to any port 53"
        } > "$temp_rules"
    fi
    
    # 2. 聰明合併：找出 /etc/pf.conf 最後一行 anchor 或 scrub，在該行「之後」插入我們的規則
    local main_conf="/etc/pf.conf"
    if [ ! -f "$main_conf" ]; then
        echo -e "${RED}❌ 找不到 $main_conf${NC}"
        rm -f "$temp_rules" "$final_conf"
        return 1
    fi
    local last_anchor_line
    last_anchor_line=$(grep -nE "anchor|scrub" "$main_conf" 2>/dev/null | tail -n 1 | cut -d: -f1)
    if [ -z "$last_anchor_line" ]; then last_anchor_line=1; fi
    sed "${last_anchor_line}r $temp_rules" "$main_conf" > "$final_conf"
    
    # 3. 語法檢查（-n）：只依 exit code 判斷；macOS 的 flush 警告不視為失敗
    local nf_out
    nf_out=$(pfctl -nf "$final_conf" 2>&1)
    echo "$nf_out" >> "$LOG_FILE"
    if [ $? -ne 0 ]; then
        if echo "$nf_out" | grep -qi "flushing"; then
            echo -e "${CYAN}   （偵測到 macOS flush 警告，仍嘗試載入規則）${NC}"
        else
            echo -e "${RED}❌ 規則語法/順序錯誤：${NC}"
            echo "$nf_out" | head -5 | sed 's/^/   /'
            echo -e "${CYAN}詳情請見 $LOG_FILE${NC}"
            rm -f "$temp_rules" "$final_conf"
            return 1
        fi
    fi
    if ! pfctl -f "$final_conf" 2>> "$LOG_FILE"; then
        echo -e "${RED}❌ 規則載入失敗，詳情請見 $LOG_FILE${NC}"
        tail -20 "$LOG_FILE" 2>/dev/null | sed 's/^/   /'
        rm -f "$temp_rules" "$final_conf"
        return 1
    fi
    
    # 4. 強制斷開狀態表，避免舊的 UDP/DNS 狀態讓封包溜過
    echo -e "${YELLOW}⚡ 清除防火牆狀態表 (pfctl -k 0.0.0.0/0)...${NC}"
    pfctl -k 0.0.0.0/0 2>/dev/null || true
    sleep 0.5
    
    # 5. 驗證與日誌
    {
        echo "主規則集順序 (pfctl -sr，前 30 行):"
        pfctl -sr 2>&1 | head -30
        echo "--- 規則匹配統計 (block/pass port 53) ---"
        pfctl -vsr 2>&1 | grep -A 3 "port 53" || true
    } >> "$LOG_FILE"
    
    local vsr_out
    vsr_out=$(pfctl -vsr 2>/dev/null)
    local block_packets
    block_packets=$(echo "$vsr_out" | grep -A1 "block.*53\|block.*port" | grep "Packets:" | sed 's/.*Packets: *\([0-9]*\).*/\1/' | tr '\n' ' ')
    echo "當前 block 規則攔截封包數 (Packets): ${block_packets:-0}" >> "$LOG_FILE"
    echo -e "${GREEN}✅ 規則順序校正成功並已載入（插入 anchor 之後）。${NC}"
    echo -e "${CYAN}   block 規則 Packets: ${block_packets:-0}（若 >0 代表有擋到） | Debug: $LOG_FILE${NC}"
    
    local main_rules
    main_rules=$(pfctl -sr 2>/dev/null)
    if ! echo "$main_rules" | grep -qE "block.*(port|53)|pass.*(port|53)"; then
        echo -e "${RED}❌ 主規則集中未見 port 53 規則${NC}"
        echo "$main_rules" | head -20
        rm -f "$temp_rules" "$final_conf"
        return 1
    fi
    echo -e "${GREEN}✅ 防火牆已更新：白名單已套用${NC}"
    
    echo -e "${CYAN}🧹 清除系統 DNS 快取...${NC}"
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    echo -e "${GREEN}✅ 快取已清除${NC}"
    rm -f "$temp_rules" "$final_conf"
}

# 封鎖單一 DNS（白名單模式下改為「只放行其他」；階段 2.2 用 block_google_only）
block_dns() {
    local dns_ip=$1
    local description=$2
    if [[ "$description" == *"Google"* ]]; then
        block_google_only
    else
        # 若需「只擋 AWS」可改為只放行 Google
        apply_dns_whitelist "只放行 Google（擋 $description）" "${GOOGLE_WHITELIST_IPS[@]}"
    fi
}

# 函數：解除封鎖（清除具名表格並重新載入預設規則）
unblock_dns() {
    local dns_ip=$1
    echo -e "${YELLOW}🔓 解除封鎖 $dns_ip...${NC}"
    _unblock_pf_table
    echo -e "${GREEN}✅ 已解除封鎖${NC}"
}

# 內部：主規則集前置模式 — 還原 /etc/pf.conf，移除我們前置的規則
_unblock_pf_table() {
    pfctl -t "$ALLOWED_TABLE_NAME" -T flush 2>/dev/null || true
    if [ -f /etc/pf.conf ]; then
        pfctl -f /etc/pf.conf 2>/dev/null || true
    fi
    pfctl -F states 2>/dev/null || true
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    sleep 1
}

# 函數：只讓 Google 過（白名單 = Google 權威 + 8.8.8.8/8.8.4.4），其餘 DNS 全擋
block_all_dns_ips() {
    local desc="$1"
    apply_dns_whitelist "只放行 Google (其餘全擋)" "${GOOGLE_WHITELIST_IPS[@]}"
}

# 函數：全部 DNS 都擋（白名單為空），全面癱瘓
block_all_dns_total() {
    local desc="$1"
    apply_dns_whitelist "$desc" 
}

# 函數：只擋 Google（白名單 = AWS + Cloudflare），用於階段 2.2（系統可從 AWS 或 Cloudflare 取得解析）
block_google_only() {
    local allow_ips=( "${AWS_DNS_IPS[@]}" "1.1.1.1" "1.0.0.1" )
    apply_dns_whitelist "只放行 AWS + Cloudflare（擋 Google）" "${allow_ips[@]}"
}

# 函數：只擋 Google，且只放行 AWS 權威 IP（用於 2.2 精準驗證「故障切換到 AWS」）
block_google_only_aws() {
    apply_dns_whitelist "只放行 AWS 權威（擋 Google，驗證切換到 AWS）" "${AWS_DNS_IPS[@]}"
}

# 函數：解除白名單、還原 pf
unblock_all_dns_ips() {
    echo -e "${YELLOW}🔓 解除白名單、還原 pf 規則...${NC}"
    _unblock_pf_table
    echo -e "${GREEN}✅ 已解除所有封鎖${NC}"
}

# 失敗時自動「保留現場」：把當前 pf 狀態寫入日誌並印在畫面上（腳本內建，不需手動下指令）
_dump_pf_state_for_debug() {
    local LOG_FILE="${DNS_TEST_DEBUG_LOG}"
    {
        echo ""
        echo "=== 保留現場：失敗時當前 pf 狀態 $(date) ==="
        echo "--- 主規則集完整順序 (pfctl -sr) ---"
        pfctl -sr 2>&1
        echo "--- 主規則集詳細計數 (pfctl -vsr，前 40 行) ---"
        pfctl -vsr 2>&1 | head -40
    } >> "$LOG_FILE"
    echo ""
    echo -e "${CYAN}🔍 保留現場已寫入日誌：$LOG_FILE${NC}"
    echo -e "${CYAN}   主規則集前幾行與計數：${NC}"
    pfctl -vsr 2>/dev/null | head -25 | sed 's/^/   /'
}

# 設為 1 時，cleanup 會先執行「保留現場」再解除封鎖（用於失敗時自動 dump）
DNS_TEST_FAILED=0

# 函數：清理（確保解除所有封鎖）
cleanup() {
    echo ""
    if [ "${DNS_TEST_FAILED:-0}" = "1" ]; then
        echo -e "${YELLOW}🧹 失敗結束，先保留現場再清理...${NC}"
        _dump_pf_state_for_debug
    fi
    echo -e "${YELLOW}🧹 清理中...${NC}"
    unblock_all_dns_ips
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 腳本結束時（正常結束或失敗）會自動執行 cleanup；失敗時會先保留現場再清理。
trap cleanup EXIT INT TERM

# ============================================
# 測試階段 1：基本功能測試
# ============================================
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 階段 1：基本功能測試${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${CYAN}1.1 測試系統預設 DNS ($DEFAULT_DNS)${NC}"
test_dns_query "$DEFAULT_DNS" "系統預設 DNS" || echo -e "${YELLOW}⚠️  系統 DNS 測試失敗（可能正常，繼續測試）${NC}"
echo ""

echo -e "${CYAN}1.2 測試 AWS DNS ($AWS_DNS)${NC}"
AWS_OK=false
if test_dns_query "$AWS_DNS" "AWS DNS"; then
    AWS_OK=true
fi
echo ""

echo -e "${CYAN}1.3 測試 Google DNS ($GOOGLE_DNS)${NC}"
GOOGLE_OK=false
if test_dns_query "$GOOGLE_DNS" "Google DNS"; then
    GOOGLE_OK=true
fi
echo ""

# 檢查基本測試結果
if [ "$AWS_OK" = false ] && [ "$GOOGLE_OK" = false ]; then
    echo -e "${RED}❌ 錯誤：兩個 DNS 伺服器都無法解析域名${NC}"
    echo "請確認："
    echo "  1. 域名是否正確：$DOMAIN"
    echo "  2. DNS 伺服器 IP 是否正確"
    echo "  3. 網路連線是否正常"
    exit 1
fi

echo -e "${GREEN}✅ 基本功能測試完成${NC}"
echo ""
read -p "按 Enter 繼續到「阻擋全部」驗證..." 

# ============================================
# 階段 1.5：阻擋全部驗證（先擋全部，確認 pf 規則有生效再測白名單）
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 階段 1.5：阻擋全部 DNS 驗證${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}💡 此階段會「阻擋全部」port 53（無白名單），用來確認 pf 規則是否真的生效。${NC}"
echo -e "${YELLOW}💡 若 nslookup 仍成功 → 規則未命中，請查看 Debug 日誌：$DNS_TEST_DEBUG_LOG${NC}"
echo ""
read -p "按 Enter 開始阻擋全部驗證..." 

clear_dns_cache
sleep 1

echo -e "${CYAN}🔒 套用「阻擋全部」port 53（無放行任何 IP）...${NC}"
block_all_dns_total "Block-all-verify"
sleep 1

echo ""
echo -e "${CYAN}🔍 驗證：對 $DEFAULT_DNS 查詢 $DOMAIN（預期應失敗或逾時）...${NC}"
BLOCK_ALL_WORKED=false
if run_with_timeout 5 nslookup "$DOMAIN" "$DEFAULT_DNS" &>/dev/null; then
    echo -e "${RED}❌ nslookup 仍成功 → 阻擋規則可能未生效，請檢查 $DNS_TEST_DEBUG_LOG 與主規則集順序${NC}"
    echo -e "${CYAN}   主規則集前 15 行：${NC}"
    pfctl -sr 2>/dev/null | head -15
    echo ""
    echo -e "${CYAN}   主規則集計數 (pfctl -vsr 前 15 行)：${NC}"
    pfctl -vsr 2>/dev/null | head -15
else
    echo -e "${GREEN}✅ nslookup 失敗/逾時 → 阻擋全部已生效，pf 規則正常${NC}"
    BLOCK_ALL_WORKED=true
fi

echo ""
echo -e "${CYAN}🔓 解除阻擋、還原 pf...${NC}"
unblock_all_dns_ips
sleep 1

if [ "$BLOCK_ALL_WORKED" = false ]; then
    echo ""
    echo -e "${YELLOW}⚠️  阻擋全部未生效，建議先查看 $DNS_TEST_DEBUG_LOG 再繼續。${NC}"
    read -p "是否仍要繼續到階段 2（故障切換測試）？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[yY]$ ]]; then
        echo "已結束。請檢查 pf 主規則集、com.apple anchor 順序或 IPv6。"
        exit 0
    fi
fi

echo ""
read -p "按 Enter 繼續到故障切換測試..." 

# ============================================
# 測試階段 2：故障切換測試
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 階段 2：故障切換測試${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}💡 提示：此測試會封鎖 DNS 伺服器來模擬故障${NC}"
echo -e "${YELLOW}💡 每個 DNS 會被封鎖 60 秒，期間會進行多次測試${NC}"
echo -e "${YELLOW}💡 驗證方式：直接對該 IP:53 查詢（dig/nslookup @server），規則阻擋雙向 port 53（查詢封包 + 回應封包）${NC}"
echo -e "${YELLOW}💡 若仍得到結果，可能為本機快取或系統解析器；建議同時用 Wireshark 觀察 port 53 封包${NC}"
echo ""
read -p "按 Enter 開始故障切換測試（每個 DNS 封鎖 60 秒）..." 

# 測試 2.1：同時封鎖兩組 DNS，測試系統是否切換
if [ "$AWS_OK" = true ] || [ "$GOOGLE_OK" = true ]; then
    echo ""
    echo -e "${CYAN}2.1 測試：同時封鎖 AWS 與 Google DNS，觀察系統行為（封鎖持續 60 秒）${NC}"
    echo ""
    
    # 先測試正常查詢
    echo "封鎖前的查詢（應該成功）："
    if [ "$AWS_OK" = true ]; then
        test_dns_query "$AWS_DNS" "AWS DNS（封鎖前）" 3
    fi
    if [ "$GOOGLE_OK" = true ]; then
        test_dns_query "$GOOGLE_DNS" "Google DNS（封鎖前）" 3
    fi
    echo ""
    
    # 清除 DNS 快取（重要！）
    echo ""
    echo -e "${CYAN}🧹 清除 DNS 快取...${NC}"
    sudo dscacheutil -flushcache 2>/dev/null || true
    sudo killall -HUP mDNSResponder 2>/dev/null || true
    echo -e "${GREEN}✅ DNS 快取已清除${NC}"
    sleep 1
    
    # 封鎖「全部 8 個 DNS」（兩組都阻擋）：白名單必須為空，不可放行 Google，否則驗證會誤判
    MAX_RETRIES=3
    RETRY_INTERVAL=2
    BLOCK_OK=false
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        echo -e "${CYAN}🔁 嘗試第 $attempt 次封鎖全部 DNS（權威 + 遞迴 8.8.8.8 等）...${NC}"
        block_all_dns_total "2.1 同時封鎖 AWS 與 Google"
        sleep $RETRY_INTERVAL
        echo ""
        echo -e "${CYAN}🔍 第 $attempt 次驗證封鎖規則（抽驗 AWS / Google 各一）...${NC}"
        if verify_block "$AWS_DNS" "AWS DNS" && verify_block "$GOOGLE_DNS" "Google DNS"; then
            BLOCK_OK=true
            break
        fi
        echo -e "${YELLOW}⚠️  第 $attempt 次封鎖驗證失敗，準備重試...${NC}"
        sleep $RETRY_INTERVAL
    done
    
    if [ "$BLOCK_OK" = true ]; then
            echo ""
            echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${BLUE}⏱️  開始 60 秒封鎖測試${NC}"
            echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            
            # 記錄開始時間
            BLOCK_START=$(date +%s)
            BLOCK_DURATION=60
            
            # 測試：直接查詢被封鎖的 DNS（應失敗）；再測「系統自動選擇」看有無回應
            echo -e "${CYAN}[0 秒] 測試：直接查詢被封鎖的 DNS（應失敗）${NC}"
            if [ "$AWS_OK" = true ]; then
                test_dns_query "$AWS_DNS" "AWS DNS（已封鎖）" 5 || echo -e "${GREEN}✅ 預期行為：查詢失敗（AWS 被封鎖）${NC}"
            fi
            if [ "$GOOGLE_OK" = true ]; then
                test_dns_query "$GOOGLE_DNS" "Google DNS（已封鎖）" 5 || echo -e "${GREEN}✅ 預期行為：查詢失敗（Google 被封鎖）${NC}"
            fi
            echo ""
            echo -e "${CYAN}[0 秒] 測試：系統自動選擇 DNS（兩組皆封鎖，觀察是否有回應）${NC}"
            test_dns_query "" "系統自動選擇（兩組皆封鎖）" 10 || echo -e "${GREEN}✅ 預期行為：兩組皆封鎖時解析失敗${NC}"
            echo ""
            
            # 每隔 60 秒測試一次系統自動切換（預期失敗時不觸發 set -e 退出）
            for i in {60..300..60}; do
                ELAPSED=$(($(date +%s) - BLOCK_START))
                REMAINING=$((BLOCK_DURATION - ELAPSED))
                
                if [ $REMAINING -le 0 ]; then
                    break
                fi
                
                echo -e "${CYAN}[$ELAPSED 秒] 測試：系統自動選擇 DNS（剩餘 $REMAINING 秒）${NC}"
                echo -e "${YELLOW}💡 觀察：系統是否會自動嘗試其他 DNS 伺服器${NC}"
                test_dns_query "" "系統自動選擇" 10 || true
                echo ""
                
                # 如果不是最後一次，等待到下一次測試時間
                if [ $REMAINING -gt 60 ]; then
                    sleep 60
                fi
            done
            
            # 最後一次測試
            ELAPSED=$(($(date +%s) - BLOCK_START))
            if [ $ELAPSED -lt $BLOCK_DURATION ]; then
                REMAINING=$((BLOCK_DURATION - ELAPSED))
                echo -e "${CYAN}[$ELAPSED 秒] 最後測試：系統自動選擇 DNS（剩餘 $REMAINING 秒）${NC}"
                test_dns_query "" "系統自動選擇" 10 || true
                echo ""
                
                # 等待到 60 秒
                if [ $REMAINING -gt 0 ]; then
                    echo -e "${YELLOW}⏳ 等待封鎖時間結束（剩餘 $REMAINING 秒）...${NC}"
                    sleep $REMAINING
                fi
            fi
            
            echo -e "${GREEN}✅ 60 秒封鎖測試完成${NC}"
            echo ""
        else
            echo -e "${RED}❌ 多次嘗試後仍無法確認封鎖兩組 DNS，停止此測試${NC}"
            echo -e "${YELLOW}💡 請檢查 pf 設定或手動下 pfctl 規則再重跑腳本${NC}"
            DNS_TEST_FAILED=1
            exit 1
        fi

    # 解除封鎖（全部 8 個 IP）
    unblock_all_dns_ips
    sleep 2
    
    # 驗證解除封鎖後是否恢復正常
    echo ""
    echo -e "${CYAN}驗證：解除封鎖後的查詢（應該恢復正常）${NC}"
    if [ "$AWS_OK" = true ]; then
        test_dns_query "$AWS_DNS" "AWS DNS（解除封鎖後）" 5
    fi
    if [ "$GOOGLE_OK" = true ]; then
        test_dns_query "$GOOGLE_DNS" "Google DNS（解除封鎖後）" 5
    fi
    echo ""
fi

# 測試 2.2：封鎖 Google DNS（4 組），只放行 AWS 權威，驗證「故障切換到 AWS」
if [ "$GOOGLE_OK" = true ]; then
    echo ""
    echo -e "${CYAN}2.2 測試：封鎖 Google Domains DNS（4 組），只放行 AWS 權威，觀察是否切換到 AWS（封鎖持續 60 秒）${NC}"
    echo -e "${YELLOW}💡 白名單僅 AWS 權威 4 組，無 8.8.8.8/Cloudflare，解析只能來自 AWS${NC}"
    echo ""
    
    # 先測試正常查詢
    echo "封鎖前的查詢（應該成功）："
    test_dns_query "$GOOGLE_DNS" "Google DNS（封鎖前）" 3
    echo ""
    
    # 清除 DNS 快取（重要！）
    echo ""
    echo -e "${CYAN}🧹 清除 DNS 快取...${NC}"
    sudo dscacheutil -flushcache 2>/dev/null || true
    sudo killall -HUP mDNSResponder 2>/dev/null || true
    echo -e "${GREEN}✅ DNS 快取已清除${NC}"
    sleep 1
    
    # 封鎖 Google DNS 全部 4 組（若未生效就持續嘗試）
    MAX_RETRIES=3
    RETRY_INTERVAL=2
    BLOCK_OK=false
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        echo -e "${CYAN}🔁 嘗試第 $attempt 次封鎖 Google DNS（4 組），只放行 AWS 權威...${NC}"
        block_google_only_aws
        sleep $RETRY_INTERVAL
        echo ""
        echo -e "${CYAN}🔍 第 $attempt 次驗證封鎖規則（Google 應失敗、AWS 可解析）...${NC}"
        if verify_block "$GOOGLE_DNS" "Google DNS"; then
            BLOCK_OK=true
            break
        fi
        echo -e "${YELLOW}⚠️  第 $attempt 次封鎖驗證失敗，準備重試...${NC}"
        sleep $RETRY_INTERVAL
    done
    
    if [ "$BLOCK_OK" = true ]; then
            echo ""
            echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${BLUE}⏱️  開始 60 秒封鎖測試${NC}"
            echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            
            # 記錄開始時間
            BLOCK_START=$(date +%s)
            BLOCK_DURATION=60
            
            # 測試被封鎖的 DNS（應該失敗）
            echo -e "${CYAN}[0 秒] 測試：直接查詢被封鎖的 DNS（應該失敗）${NC}"
            test_dns_query "$GOOGLE_DNS" "Google DNS（已封鎖）" 5 || echo -e "${GREEN}✅ 預期行為：查詢失敗（DNS 被封鎖）${NC}"
            echo ""
            
            # 每隔 60 秒測試一次系統自動切換
            for i in {60..300..60}; do
                ELAPSED=$(($(date +%s) - BLOCK_START))
                REMAINING=$((BLOCK_DURATION - ELAPSED))
                
                if [ $REMAINING -le 0 ]; then
                    break
                fi
                
                echo -e "${CYAN}[$ELAPSED 秒] 測試：系統自動選擇 DNS（剩餘 $REMAINING 秒）${NC}"
                echo -e "${YELLOW}💡 觀察：系統是否會自動切換到 AWS${NC}"
                test_dns_query "" "系統自動選擇" 10 || true
                echo ""
                
                # 如果不是最後一次，等待到下一次測試時間
                if [ $REMAINING -gt 60 ]; then
                    sleep 60
                fi
            done
            
            # 最後一次測試
            ELAPSED=$(($(date +%s) - BLOCK_START))
            if [ $ELAPSED -lt $BLOCK_DURATION ]; then
                REMAINING=$((BLOCK_DURATION - ELAPSED))
                echo -e "${CYAN}[$ELAPSED 秒] 最後測試：系統自動選擇 DNS（剩餘 $REMAINING 秒）${NC}"
                test_dns_query "" "系統自動選擇" 10 || true
                echo ""
                
                # 等待到 60 秒
                if [ $REMAINING -gt 0 ]; then
                    echo -e "${YELLOW}⏳ 等待封鎖時間結束（剩餘 $REMAINING 秒）...${NC}"
                    sleep $REMAINING
                fi
            fi
            
            echo -e "${GREEN}✅ 60 秒封鎖測試完成${NC}"
            echo ""
        else
            echo -e "${RED}❌ 多次嘗試後仍無法確認封鎖 Google DNS，停止此測試${NC}"
            echo -e "${YELLOW}💡 請檢查 pf 設定或手動下 pfctl 規則再重跑腳本${NC}"
            DNS_TEST_FAILED=1
            exit 1
        fi

    # 解除封鎖（Google 4 組）
    echo -e "${CYAN}🔓 解除封鎖 Google DNS（4 組）...${NC}"
    unblock_all_dns_ips
    sleep 2
    
    # 驗證解除封鎖後是否恢復正常
    echo ""
    echo -e "${CYAN}驗證：解除封鎖後的查詢（應該恢復正常）${NC}"
    test_dns_query "$GOOGLE_DNS" "Google DNS（解除封鎖後）" 5
    echo ""
else
    echo -e "${RED}❌ 無法封鎖 Google DNS（多次嘗試失敗），停止此測試${NC}"
    DNS_TEST_FAILED=1
    exit 1
fi

# ============================================
# 測試階段 3：全面封鎖測試（Total Blackout，兩組都阻擋）
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 階段 3：全面封鎖測試（Total Blackout）${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${YELLOW}💡 目標：同時封鎖 AWS 與 Google「全部 8 個 DNS」，確認系統完全無法解析域名${NC}"
echo -e "${YELLOW}💡 此階段會一併封鎖 8.8.8.8、8.8.4.4、1.1.1.1 等常見遞迴 DNS，確保真正全面癱瘓${NC}"
echo ""
read -p "按 Enter 開始全面封鎖測試（兩組都阻擋，看有沒有回應）..." 

# 再次清除 DNS 快取
echo ""
echo -e "${CYAN}🧹 再次清除 DNS 快取（全面封鎖前）...${NC}"
sudo dscacheutil -flushcache 2>/dev/null || true
sudo killall -HUP mDNSResponder 2>/dev/null || true
echo -e "${GREEN}✅ DNS 快取已清除${NC}"
sleep 1

echo ""
echo -e "${CYAN}🚫 同時封鎖全部 DNS（權威 NS + 8.8.8.8 等遞迴 DNS）...${NC}"
block_all_dns_total "全面封鎖"
sleep 2

echo ""
echo -e "${CYAN}🔍 驗證兩組 DNS 封鎖規則是否存在（抽驗各一）...${NC}"
VERIFY_AWS=false
VERIFY_GOOGLE=false
if verify_block "$AWS_DNS" "AWS DNS（全面封鎖）"; then
    VERIFY_AWS=true
fi
if verify_block "$GOOGLE_DNS" "Google DNS（全面封鎖）"; then
    VERIFY_GOOGLE=true
fi

if [ "$VERIFY_AWS" = true ] && [ "$VERIFY_GOOGLE" = true ]; then
    echo ""
    echo -e "${CYAN}📡 測試：系統自動選擇 DNS（兩組都阻擋，觀察是否有回應）${NC}"
    echo -e "${YELLOW}💡 預期結果：查詢應失敗，表示沒有其他隱藏 DNS 可用${NC}"
    if test_dns_query "" "系統自動選擇（全面封鎖）" 8; then
        echo -e "${RED}❌ 警告：在全面封鎖情況下仍然成功解析！${NC}"
        echo -e "${RED}   這代表系統可能使用了未在本腳本中列出的其他 DNS（例如 ISP 或公共 DNS）${NC}"
    else
        echo -e "${GREEN}✅ 查詢失敗（符合預期）：兩組都阻擋時系統無法解析域名${NC}"
    fi
else
    echo -e "${RED}❌ 無法確認兩組 DNS 均被成功封鎖，略過全面封鎖測試${NC}"
fi

# 在進行後續測試前先解除全面封鎖
echo ""
echo -e "${CYAN}🔓 解除全面封鎖規則，準備進入詳細查詢測試（dig）...${NC}"
unblock_all_dns_ips
sleep 2

# ============================================
# 測試階段 4：使用 dig 進行詳細測試
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 階段 4：詳細 DNS 查詢測試（使用 dig）${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

if command -v dig &> /dev/null; then
    echo -e "${CYAN}4.1 使用 dig 測試 AWS DNS${NC}"
    echo "完整查詢結果："
    dig @$AWS_DNS $DOMAIN A +noall +answer +stats
    echo ""
    
    echo -e "${CYAN}4.2 使用 dig 測試 Google DNS${NC}"
    echo "完整查詢結果："
    dig @$GOOGLE_DNS $DOMAIN A +noall +answer +stats
    echo ""
else
    echo -e "${YELLOW}⚠️  dig 未安裝，跳過詳細測試${NC}"
    echo "安裝方法：brew install bind"
fi

# ============================================
# 測試總結
# ============================================
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📊 測試總結${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo "測試域名：$DOMAIN"
echo ""

if [ "$AWS_OK" = true ]; then
    echo -e "${GREEN}✅ AWS DNS ($AWS_DNS)：正常${NC}"
else
    echo -e "${RED}❌ AWS DNS ($AWS_DNS)：異常${NC}"
fi

if [ "$GOOGLE_OK" = true ]; then
    echo -e "${GREEN}✅ Google DNS ($GOOGLE_DNS)：正常${NC}"
else
    echo -e "${RED}❌ Google DNS ($GOOGLE_DNS)：異常${NC}"
fi

echo ""
echo -e "${YELLOW}💡 建議：${NC}"
echo "1. 使用 Wireshark 觀察 DNS 封包，查看實際的查詢行為"
echo "2. 檢查系統 DNS 設定：scutil --dns"
echo "3. 查看 DNS 快取：dscacheutil -q host -a name $DOMAIN"
echo ""

# 最終檢查：確認白名單已解除（放行表為空或已還原）
echo -e "${CYAN}🔍 最終檢查：確認 DNS 白名單已解除...${NC}"
if pfctl -t "$ALLOWED_TABLE_NAME" -T show 2>/dev/null | grep -q .; then
    echo -e "${YELLOW}⚠️  警告：白名單表格中仍有 IP${NC}"
    pfctl -t "$ALLOWED_TABLE_NAME" -T show 2>/dev/null
    echo ""
    echo "正在清理..."
    cleanup
else
    echo -e "${GREEN}✅ 確認：所有 DNS 封鎖已解除${NC}"
fi
echo ""

echo -e "${GREEN}✅ 測試完成${NC}"
echo ""
