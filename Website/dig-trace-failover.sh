#!/bin/bash
# ==============================================================================
# dig +trace 遞回 Failover 驗證腳本
# ==============================================================================
# 核心概念：你無法控制 8.8.8.8 與 AWS 之間的網路。若只在本地封鎖 AWS NS，
# 然後問 8.8.8.8，8.8.8.8 仍可連上 AWS，回傳給你的結果仍是正常的。
# 解決方案：讓「你的電腦」扮演遞回解析器 → 使用 dig +trace。
# 加上 +trace 時，dig 會繞過系統 DNS，由本機從根 (.) 一層層往下問，
# 此時防火牆規則會生效（發出請求的是你的電腦）。
#
# 流程：
#   A. 只封鎖 AWS → 清快取 → time dig +trace → 預期從 Google 拿到 2.2.2.2
#   B. 反向：換為只封鎖 Google → 清快取 → time dig +trace → 預期從 AWS 拿到 3.3.3.3
# 證明雙活 (Active-Active) / 互為備援，而非單向備援。
# 用法：sudo bash /path/to/dig-trace-failover.sh [域名]
# 選項：--single-test  封鎖後先做單點測試
# ==============================================================================

set -e

# 配置
DOMAIN="${1:-www.clouddeployment168.site}"
AWS_NS=("205.251.197.44" "205.251.199.48" "205.251.192.236" "205.251.195.65")
GCP_NS=("216.239.32.108" "216.239.34.108" "216.239.36.108" "216.239.38.108")
GCP_NS_FIRST="${GCP_NS[0]}"
AWS_NS_FIRST="${AWS_NS[0]}"
EXPECTED_IP_GOOGLE="2.2.2.2"
EXPECTED_IP_AWS="3.3.3.3"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

DO_SINGLE_TEST=false
for arg in "$@"; do
    [ "$arg" = "--single-test" ] && DO_SINGLE_TEST=true
done

# 日誌：時間戳檔名，即時同時輸出到終端與檔案
LOG=/tmp/dig-trace-failover_$(date '+%Y%m%d_%H%M%S').log

# 清理：還原防火牆（中斷或結束時執行）
cleanup_pf() {
    echo ""
    echo -e "${YELLOW}還原防火牆 (pfctl -F all)...${NC}"
    sudo pfctl -F all 2>/dev/null || true
    echo -e "${GREEN}防火牆已重置${NC}"
}

trap cleanup_pf EXIT INT TERM

# 步驟 1：只封鎖 AWS NS（UDP + TCP），放行其餘（含 Google NS）
apply_block_aws_only() {
    echo -e "${CYAN}步驟 1：只封鎖 AWS 的 4 個 NS，Google NS 保持暢通${NC}"
    echo "AWS NS IP: ${AWS_NS[*]}"
    if ! sudo pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        sudo pfctl -e 2>/dev/null || { echo -e "${RED}[FAIL] 無法啟用 pfctl${NC}"; exit 1; }
    fi
    local tmp_rules
    tmp_rules=$(mktemp)
    for ip in "${AWS_NS[@]}"; do
        echo "block drop out quick inet proto udp from any to $ip port 53"
        echo "block drop out quick inet proto tcp from any to $ip port 53"
    done > "$tmp_rules"
    sudo pfctl -nf "$tmp_rules" 2>/dev/null || { echo -e "${RED}[FAIL] 規則語法錯誤${NC}"; rm -f "$tmp_rules"; exit 1; }
    sudo pfctl -f "$tmp_rules"
    rm -f "$tmp_rules"
    for ip in "${AWS_NS[@]}"; do
        sudo pfctl -k "$ip" 2>/dev/null || true
    done
    echo -e "${GREEN}AWS NS 已封鎖，Google NS 保持暢通。${NC}"
    echo ""
}

# 步驟 1 反向：只封鎖 Google NS（UDP + TCP），放行其餘（含 AWS NS）
apply_block_google_only() {
    echo -e "${CYAN}步驟 1（反向）：只封鎖 Google 的 4 個 NS，AWS NS 保持暢通${NC}"
    echo "Google NS IP: ${GCP_NS[*]}"
    if ! sudo pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        sudo pfctl -e 2>/dev/null || { echo -e "${RED}[FAIL] 無法啟用 pfctl${NC}"; exit 1; }
    fi
    local tmp_rules
    tmp_rules=$(mktemp)
    for ip in "${GCP_NS[@]}"; do
        echo "block drop out quick inet proto udp from any to $ip port 53"
        echo "block drop out quick inet proto tcp from any to $ip port 53"
    done > "$tmp_rules"
    sudo pfctl -nf "$tmp_rules" 2>/dev/null || { echo -e "${RED}[FAIL] 規則語法錯誤${NC}"; rm -f "$tmp_rules"; exit 1; }
    sudo pfctl -f "$tmp_rules"
    rm -f "$tmp_rules"
    for ip in "${GCP_NS[@]}"; do
        sudo pfctl -k "$ip" 2>/dev/null || true
    done
    echo -e "${GREEN}Google NS 已封鎖，AWS NS 保持暢通。${NC}"
    echo ""
}

# 清除本機 DNS 快取（確保 dig 真的走網路，測到的是 Failover 時間）
flush_dns_cache() {
    echo -e "${CYAN}清除本機 DNS 快取（確保測到真實查詢時間）...${NC}"
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    echo -e "${GREEN}快取已清除${NC}"
    echo ""
}

# 解析 time 的 real 秒數（real    0m2.053s 或 1m0.500s）
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

# 步驟 2：time + dig +trace（宏觀測量：從 Enter 到結果的總時間）
run_dig_trace() {
    echo -e "${CYAN}步驟 2：time + dig +trace（宏觀測量：發現 AWS 查不到 → 用 Google 查成功 的總時間）${NC}"
    echo "執行: time dig +trace +nodnssec $DOMAIN"
    echo -e "${YELLOW}請看輸出最後「Received ... from x.x.x.x」→ 應來自 Google；real = 實際經過時間。${NC}"
    echo ""
    local time_tmp
    time_tmp=$(mktemp)
    set +e
    { time dig +trace +nodnssec "$DOMAIN" 2>&1 ; } 2> "$time_tmp"
    set -e
    echo ""
    echo -e "${CYAN}---------- 時間統計 (time) ----------${NC}"
    cat "$time_tmp"
    if real_line=$(grep '^real' "$time_tmp" 2>/dev/null); then
        real_sec=$(parse_real_seconds "$real_line")
        echo ""
        echo -e "${CYAN}---------- 解讀 (real = ${real_sec}s) ----------${NC}"
        if awk -v r="$real_sec" 'BEGIN { exit (r < 0.5 ? 0 : 1) }' 2>/dev/null; then
            echo -e "${GREEN}real < 0.5 秒：dig 採用了並行查詢或快速失敗，故障切換幾乎無感。${NC}"
        elif awk -v r="$real_sec" 'BEGIN { exit (r >= 1 && r <= 2.5 ? 0 : 1) }' 2>/dev/null; then
            echo -e "${YELLOW}real 約 1~2.5 秒：標準 Timeout。dig 嘗試連 AWS、等待逾時後才問 Google，這就是故障切換的代價。${NC}"
        elif awk -v r="$real_sec" 'BEGIN { exit (r > 4 ? 0 : 1) }' 2>/dev/null; then
            echo -e "${YELLOW}real > 4 秒：重試了多次才成功。${NC}"
        else
            echo -e "${CYAN}real 約 0.5~1 秒或 2.5~4 秒：介於上述之間。${NC}"
        fi
    fi
    rm -f "$time_tmp"
    echo ""
    echo -e "${CYAN}---------- 對比：同一個域名，再問 Google 與 AWS ----------${NC}"
    echo -e "問 Google ($GCP_NS_FIRST)："
    set +e
    gout=$(dig @"$GCP_NS_FIRST" "$DOMAIN" +short +time=3 2>&1)
    echo "$gout" | sed 's/^/  /'
    echo -e "問 AWS ($AWS_NS_FIRST)（目前被擋，預期逾時或無結果）："
    aout=$(dig @"$AWS_NS_FIRST" "$DOMAIN" +short +time=2 +tries=1 2>&1)
    echo "$aout" | sed 's/^/  /'
    set -e
    echo ""
}

# 步驟 2 反向：time dig +trace（封鎖 Google → 預期從 AWS 拿到 3.3.3.3）
run_dig_trace_reverse() {
    echo -e "${CYAN}步驟 2（反向）：time + dig +trace（封鎖 Google → 預期從 AWS 拿到 $EXPECTED_IP_AWS）${NC}"
    echo "執行: time dig +trace +nodnssec $DOMAIN"
    echo -e "${YELLOW}請看輸出最後「Received ... from x.x.x.x」→ 應來自 AWS (205.251.x.x)；A 記錄應為 $EXPECTED_IP_AWS。${NC}"
    echo ""
    local time_tmp
    time_tmp=$(mktemp)
    set +e
    { time dig +trace +nodnssec "$DOMAIN" 2>&1 ; } 2> "$time_tmp"
    set -e
    echo ""
    echo -e "${CYAN}---------- 時間統計 (time) ----------${NC}"
    cat "$time_tmp"
    if real_line=$(grep '^real' "$time_tmp" 2>/dev/null); then
        real_sec=$(parse_real_seconds "$real_line")
        echo ""
        echo -e "${CYAN}---------- 解讀 (real = ${real_sec}s) ----------${NC}"
        if awk -v r="$real_sec" 'BEGIN { exit (r < 0.5 ? 0 : 1) }' 2>/dev/null; then
            echo -e "${GREEN}real < 0.5 秒：可能 dig 先問 AWS 即成功，或快速失敗後轉彎。${NC}"
        else
            echo -e "${YELLOW}real 較長：可能 dig 先試了被擋的 Google，逾時後才問 AWS。無論快慢，結果為 $EXPECTED_IP_AWS 即成功。${NC}"
        fi
    fi
    rm -f "$time_tmp"
    echo ""
    echo -e "${CYAN}---------- 對比：同一個域名，再問 AWS 與 Google ----------${NC}"
    echo -e "問 AWS ($AWS_NS_FIRST)（目前暢通，預期 $EXPECTED_IP_AWS）："
    set +e
    aout=$(dig @"$AWS_NS_FIRST" "$DOMAIN" +short +time=3 2>&1)
    echo "$aout" | sed 's/^/  /'
    echo -e "問 Google ($GCP_NS_FIRST)（目前被擋，預期逾時或無結果）："
    gout=$(dig @"$GCP_NS_FIRST" "$DOMAIN" +short +time=2 +tries=1 2>&1)
    echo "$gout" | sed 's/^/  /'
    set -e
    echo ""
}

# 步驟 3：time nslookup（真實使用者等待時間 — 走系統解析器）
run_nslookup_time() {
    echo -e "${CYAN}步驟 3：time nslookup（真實使用者等待時間，強迫走 macOS 系統解析器）${NC}"
    echo "執行: time nslookup $DOMAIN"
    echo -e "${YELLOW}nslookup 會走系統 DNS 設定，更能反映真實上網體驗。${NC}"
    echo ""
    flush_dns_cache
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
}

# 步驟 2b（可選）：單點測試 — AWS 應逾時，Google 應成功
run_single_tests() {
    echo -e "${CYAN}步驟 2b：單點測試（驗證 AWS 真的被擋、Google 可達）${NC}"
    echo -e "測試 AWS ($AWS_NS_FIRST)，預期: connection timed out ..."
    if dig @"$AWS_NS_FIRST" "$DOMAIN" +short +time=2 +tries=1 2>&1 | grep -q "timed out\|no servers could be reached"; then
        echo -e "${GREEN}  [OK] AWS 查詢逾時（符合預期）${NC}"
    else
        echo -e "${YELLOW}  [!] AWS 有回應，請確認規則已生效${NC}"
    fi
    echo -e "測試 Google ($GCP_NS_FIRST)，預期: 取得 A 記錄..."
    if dig @"$GCP_NS_FIRST" "$DOMAIN" +short +time=3 2>/dev/null | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
        echo -e "${GREEN}  [OK] Google 解析成功${NC}"
    else
        echo -e "${RED}  [FAIL] Google 無結果${NC}"
    fi
    echo ""
}

# 步驟 2b 反向：單點測試 — Google 應逾時，AWS 應成功 (3.3.3.3)
run_single_tests_reverse() {
    echo -e "${CYAN}步驟 2b（反向）：單點測試（驗證 Google 真的被擋、AWS 可達）${NC}"
    echo -e "測試 Google ($GCP_NS_FIRST)，預期: connection timed out ..."
    if dig @"$GCP_NS_FIRST" "$DOMAIN" +short +time=2 +tries=1 2>&1 | grep -q "timed out\|no servers could be reached"; then
        echo -e "${GREEN}  [OK] Google 查詢逾時（符合預期）${NC}"
    else
        echo -e "${YELLOW}  [!] Google 有回應，請確認規則已生效${NC}"
    fi
    echo -e "測試 AWS ($AWS_NS_FIRST)，預期: 取得 A 記錄 $EXPECTED_IP_AWS ..."
    if dig @"$AWS_NS_FIRST" "$DOMAIN" +short +time=3 2>/dev/null | grep -q "$EXPECTED_IP_AWS"; then
        echo -e "${GREEN}  [OK] AWS 解析成功 ($EXPECTED_IP_AWS)${NC}"
    else
        echo -e "${RED}  [FAIL] AWS 無預期結果${NC}"
    fi
    echo ""
}

# 主流程
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}請使用 sudo 執行本腳本${NC}"
    echo "例: sudo bash $(basename "$0") $DOMAIN"
    exit 1
fi

(
echo "日誌寫入: $LOG"
echo ""
echo -e "${CYAN}======================================================${NC}"
echo -e "${CYAN}   dig +trace 雙向 Failover 驗證（A: 擋 AWS / B: 擋 Google）${NC}"
echo -e "${CYAN}======================================================${NC}"
echo "域名: $DOMAIN"
echo ""

# ========== 階段 A：封鎖 AWS，驗證 Google 接手 (2.2.2.2) ==========
echo -e "${YELLOW}>>>> 階段 A：封鎖 AWS，驗證撞牆後由 Google 解析 (預期 $EXPECTED_IP_GOOGLE) <<<<${NC}"
echo ""

apply_block_aws_only

flush_dns_cache

if [ "$DO_SINGLE_TEST" = true ]; then
    run_single_tests
fi

run_dig_trace

run_nslookup_time

# ========== 階段 B（反向）：封鎖 Google，驗證 AWS 接手 (3.3.3.3) ==========
echo -e "${YELLOW}======================================================${NC}"
echo -e "${YELLOW}   🔄 反向驗證：換為封鎖 Google，驗證 AWS 接手 ($EXPECTED_IP_AWS)${NC}"
echo -e "${YELLOW}======================================================${NC}"
echo ""

apply_block_google_only

flush_dns_cache

if [ "$DO_SINGLE_TEST" = true ]; then
    run_single_tests_reverse
fi

run_dig_trace_reverse

run_nslookup_time

echo -e "${GREEN}雙向驗證結束（A: Google 備援 / B: AWS 備援），防火牆將由 trap 自動還原。${NC}"
) 2>&1 | tee $LOG
