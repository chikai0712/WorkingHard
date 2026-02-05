#!/bin/bash
# -------------------------------------------------------------------------------
# DNS Failover Simulation Tool for macOS (PF-based)
# 功能：精確模擬特定 DNS 服務商失效，驗證系統高可用行為（單純監控／故障模擬）。
# 用法：
#   因 sudo 會改變工作目錄，請用「絕對路徑」或「bash 指定腳本」執行，例如：
#     sudo bash /path/to/Website/dns_test_pro.sh [域名]
#     sudo /path/to/Website/dns_test_pro.sh [域名]
#   或在 Website 目錄下：  sudo bash ./dns_test_pro.sh [域名]
# 預設域名：www.clouddeployment168.site
# 流程：步驟1 全黑 → 步驟2A 僅 AWS → 步驟2B 僅 Google → 步驟3 切換 loop → 步驟4 dig +trace
# 可覆寫：FAILOVER_LOOP_RUNS=3 sudo bash ./dns_test_pro.sh
# 選項：--unbound 啟用本地 Unbound Docker 白箱測試
# 量測結果會同時顯示於終端並寫入 LOG（預設 /tmp/dns_test_YYYYMMDD_HHMMSS.log）
# PF 規則邏輯完全參照 dns-failover-test.sh 的 apply_dns_whitelist（可成功阻擋）。
# 失敗時可查 Debug：/tmp/dns_test_pro_debug.log
# -------------------------------------------------------------------------------

set -e

# LOG 路徑（main 內會依時間建立檔名）
LOG=""

# 配置區域
DOMAIN="www.clouddeployment168.site"
AWS_NS=("205.251.197.44" "205.251.199.48" "205.251.192.236" "205.251.195.65")
GCP_NS=("216.239.32.108" "216.239.34.108" "216.239.36.108" "216.239.38.108")
PUBLIC_DNS=("8.8.8.8" "8.8.4.4" "1.1.1.1")

# 步驟 1 全黑驗證：curl 逾時（秒）
BASELINE_CURL_TIMEOUT="${BASELINE_CURL_TIMEOUT:-5}"
# 步驟 2 單一供應商驗證：curl 逾時（秒）
ISOLATION_CURL_TIMEOUT="${ISOLATION_CURL_TIMEOUT:-10}"
# 步驟 3 切換耗時：每輪 curl 逾時（秒）
FAILOVER_CURL_TIMEOUT="${FAILOVER_CURL_TIMEOUT:-15}"
# 步驟 3 重試 loop：共幾輪（每輪先清快取再重試直到成功）
FAILOVER_LOOP_RUNS="${FAILOVER_LOOP_RUNS:-5}"
# 步驟 3 每輪最多嘗試幾次（避免無限迴圈）
FAILOVER_MAX_ATTEMPTS="${FAILOVER_MAX_ATTEMPTS:-10}"

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# 解析參數：--unbound 啟用 Unbound Docker 測試，其餘非 -- 開頭視為域名
USE_UNBOUND=false
for arg in "$@"; do
    case "$arg" in
        --unbound) USE_UNBOUND=true ;;
        *) [ -n "$arg" ] && [[ "$arg" != --* ]] && DOMAIN="$arg" ;;
    esac
done

# 白名單具名表格（與 dns-failover-test.sh 一致）
ALLOWED_TABLE_NAME="allowed_dns_table"
# Debug 日誌（與 dns-failover-test.sh 相同用途，失敗時可查）
DNS_TEST_DEBUG_LOG="/tmp/dns_test_pro_debug.log"
# 錯誤日誌：放行供應商時仍無法解析／連線失敗時寫入，供後續排查
DNS_TEST_ERROR_LOG="/tmp/dns_test_pro_errors.log"

# -------------------------------------------------------------------------------
# 套用防火牆規則（完全參照 dns-failover-test.sh apply_dns_whitelist）
# 含：pf 啟用檢查、語法檢查、載入失敗處理、清除狀態表、快取清除、規則驗證
# -------------------------------------------------------------------------------
apply_rules() {
    local desc=$1
    shift
    local allowed=("$@")
    local temp_rules
    temp_rules=$(mktemp)
    local final_conf
    final_conf=$(mktemp)
    local LOG_FILE="${DNS_TEST_DEBUG_LOG}"

    {
        echo "===== 執行測試: $desc [$(date)] ====="
        echo "嘗試套用白名單: 放行 ${#allowed[@]} 個 IP (其餘 DNS 全擋)"
    } >> "$LOG_FILE"

    if [ ${#allowed[@]} -eq 0 ]; then
        echo -e "${YELLOW}[白名單] $desc: 全部 DNS 都擋（port 53）${NC}"
    else
        echo -e "${YELLOW}[白名單] $desc: 只放行 ${#allowed[@]} 個 IP，其餘 DNS 全擋${NC}"
        echo -e "${CYAN}   放行: ${allowed[*]}${NC}"
    fi

    # 1. 確保 pf 已啟用（與 dns-failover-test.sh 一致）
    if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        pfctl -e 2>/dev/null || { echo -e "${RED}[FAIL] 無法啟用 pfctl${NC}"; rm -f "$temp_rules" "$final_conf"; return 1; }
    fi

    # 2. 準備規則（與 dns-failover-test.sh 完全一致）
    if [ ${#allowed[@]} -gt 0 ]; then
        local ip_list=""
        for ip in "${allowed[@]}"; do ip_list="$ip_list $ip"; done
        {
            echo "table <$ALLOWED_TABLE_NAME> { $ip_list }"
            echo "pass in quick inet proto { udp, tcp } from <$ALLOWED_TABLE_NAME> port 53 to any"
            echo "pass out quick inet proto { udp, tcp } to <$ALLOWED_TABLE_NAME> port 53"
            echo "block in quick inet proto { udp, tcp } from any to any port 53"
            echo "block out quick inet proto { udp, tcp } to any port 53"
        } > "$temp_rules"
    else
        {
            echo "block in quick inet proto { udp, tcp } from any to any port 53"
            echo "block out quick inet proto { udp, tcp } to any port 53"
        } > "$temp_rules"
    fi

    # 3. 聰明合併：最後一個 anchor/scrub 之後插入（與 dns-failover-test.sh 相同）
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

    # 4. 語法檢查（-n）：只依 exit code；macOS flush 警告不視為失敗
    local nf_out
    nf_out=$(pfctl -nf "$final_conf" 2>&1)
    echo "$nf_out" >> "$LOG_FILE"
    if [ $? -ne 0 ]; then
        if echo "$nf_out" | grep -qi "flushing"; then
            echo -e "${CYAN}   （偵測到 macOS flush 警告，仍嘗試載入規則）${NC}"
        else
            echo -e "${RED}[FAIL] 規則語法/順序錯誤:${NC}"
            echo "$nf_out" | head -5 | sed 's/^/   /'
            echo -e "${CYAN}詳情請見 $LOG_FILE${NC}"
            rm -f "$temp_rules" "$final_conf"
            return 1
        fi
    fi
    if ! pfctl -f "$final_conf" 2>> "$LOG_FILE"; then
        echo -e "${RED}[FAIL] 規則載入失敗，詳情請見 $LOG_FILE${NC}"
        tail -20 "$LOG_FILE" 2>/dev/null | sed 's/^/   /'
        rm -f "$temp_rules" "$final_conf"
        return 1
    fi

    # 5. 強制斷開狀態表，避免舊連線讓封包溜過
    echo -e "${YELLOW}清除防火牆狀態表 (pfctl -k 0.0.0.0/0)...${NC}"
    pfctl -k 0.0.0.0/0 2>/dev/null || true
    sleep 0.5

    # 6. 驗證與日誌（與 dns-failover-test.sh 一致）
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
    echo -e "${GREEN}[OK] 規則已載入（插入 anchor 之後）。${NC}"
    echo -e "${CYAN}   block 規則 Packets: ${block_packets:-0}（若 >0 代表有擋到）| Debug: $LOG_FILE${NC}"

    local main_rules
    main_rules=$(pfctl -sr 2>/dev/null)
    if ! echo "$main_rules" | grep -qE "block.*(port|53)|pass.*(port|53)"; then
        echo -e "${RED}[FAIL] 主規則集中未見 port 53 規則${NC}"
        echo "$main_rules" | head -20
        rm -f "$temp_rules" "$final_conf"
        return 1
    fi
    echo -e "${GREEN}[OK] 防火牆已更新: 白名單已套用${NC}"

    echo -e "${CYAN}清除系統 DNS 快取...${NC}"
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    echo -e "${GREEN}[OK] 快取已清除${NC}"
    rm -f "$temp_rules" "$final_conf"
}

# -------------------------------------------------------------------------------
# 清除快取與規則（trap 時自動呼叫）
# -------------------------------------------------------------------------------
cleanup() {
    echo -e "\n${YELLOW}正在還原網路環境...${NC}"
    pfctl -f /etc/pf.conf 2>/dev/null || true
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    docker stop my-dns 2>/dev/null || true
    docker rm my-dns 2>/dev/null || true
    echo -e "${GREEN}[OK] 環境已恢復。${NC}"
}

trap cleanup EXIT

# -------------------------------------------------------------------------------
# 輸出 Wireshark 過濾器與並行觀察說明（方法二：封包時序分析）
# -------------------------------------------------------------------------------
print_wireshark_hint() {
    local phase_desc=$1
    local ips=("${AWS_NS[@]}" "${GCP_NS[@]}")
    local filter_parts=""
    for ip in "${ips[@]}"; do filter_parts="${filter_parts}ip.dst == $ip or "; done
    filter_parts="${filter_parts% or }"
    echo -e "${CYAN}[Wireshark 方法二] $phase_desc 可並行抓包:${NC}"
    echo -e "  過濾器: dns and ($filter_parts)"
    echo -e "  觀察: 封包發送順序（並行/序列）、重試間隔、Delta Time${NC}\n"
}

# -------------------------------------------------------------------------------
# 放行供應商時仍無法解析／連線失敗：將錯誤寫入 ERROR_LOG 供後續排查
# 參數: phase url timeout curl_stderr curl_w_line curl_exit_code
# -------------------------------------------------------------------------------
write_curl_error_log() {
    local phase=$1
    local url=$2
    local timeout=$3
    local curl_stderr=$4
    local curl_w_line=$5
    local curl_exit_code=$6
    local err_log="${DNS_TEST_ERROR_LOG}"
    {
        echo "--- [$(date '+%Y-%m-%d %H:%M:%S')] phase=$phase ---"
        echo "url=$url"
        echo "connect_timeout=$timeout"
        echo "curl -w line: $curl_w_line"
        echo "curl exit code: ${curl_exit_code}"
        echo "curl stderr:"
        echo "$curl_stderr"
        echo ""
    } >> "$err_log"
}

# -------------------------------------------------------------------------------
# 強制清除系統 DNS 快取（步驟間／loop 前使用）
# -------------------------------------------------------------------------------
flush_dns_cache() {
    echo -e "${CYAN}清除系統 DNS 快取...${NC}"
    dscacheutil -flushcache 2>/dev/null || true
    killall -HUP mDNSResponder 2>/dev/null || true
    sleep 1
    echo -e "${GREEN}[OK] 快取已清除${NC}"
}

# -------------------------------------------------------------------------------
# curl 驗證並回傳時序（-w：time_namelookup, time_connect, time_total, http_code）
# 用法：curl_verify_with_timing URL [connect_timeout]
# 輸出到 stdout 一行：namelookup connect total http_code（空白分隔）
# 回傳：0=成功(HTTP 200)，1=失敗
# -------------------------------------------------------------------------------
curl_verify_with_timing() {
    local url=$1
    local timeout=${2:-10}
    local line
    line=$(curl -o /dev/null -s -w "%{time_namelookup} %{time_connect} %{time_total} %{http_code}" \
        --connect-timeout "$timeout" --max-time "$((timeout + 5))" "$url" 2>/dev/null) || true
    echo "$line"
    local code
    code=$(echo "$line" | awk '{print $4}')
    [ "$code" = "200" ] && return 0 || return 1
}

# -------------------------------------------------------------------------------
# 量測「系統解析」耗時（使用系統遞迴，不指定 @server）
# -------------------------------------------------------------------------------
measure_system_resolve() {
    local domain=$1
    local elapsed=$2
    local timeout=${3:-15}
    local t0 t1 duration result
    t0=$(date +%s.%N 2>/dev/null || date +%s)
    result=$(dig +short "$domain" +time="$timeout" 2>&1) || true
    t1=$(date +%s.%N 2>/dev/null || date +%s)
    duration=$(echo "$t1 - $t0" 2>/dev/null | bc 2>/dev/null || echo "?")
    if echo "$result" | grep -qE '^[0-9.]+'; then
        echo -e "  T+${elapsed}s  DNS: ${duration}s  ${GREEN}成功${NC}  ($(echo "$result" | head -1))"
    elif [ -z "$result" ]; then
        echo -e "  T+${elapsed}s  DNS: ${duration}s  ${YELLOW}逾時/無回應${NC}"
    else
        echo -e "  T+${elapsed}s  DNS: ${duration}s  ${RED}失敗${NC}"
    fi
}

# -------------------------------------------------------------------------------
# 用 curl 解析並請求目標 URL（含 DNS + 連線 + HTTP），觀察實際「開啟」耗時
# -------------------------------------------------------------------------------
measure_curl_fetch() {
    local url=$1
    local elapsed=$2
    local timeout=${3:-20}
    local out
    out=$(curl -s -o /dev/null -w "%{http_code} %{time_total}" --connect-timeout "$timeout" --max-time "$timeout" "$url" 2>/dev/null) || true
    local code="${out%% *}"
    local time="${out##* }"
    if [ -z "$time" ]; then time="?"; fi
    if [ -n "$code" ] && [ "$code" != "000" ]; then
        echo -e "         curl: HTTP $code  ${time}s  ${GREEN}成功${NC}"
    else
        echo -e "         curl: 逾時/連線失敗  ${RED}失敗${NC}"
    fi
}

# -------------------------------------------------------------------------------
# 主流程：三階段負向驗證 + 切換耗時 loop
# -------------------------------------------------------------------------------
main() {
    [ "$(id -u)" -ne 0 ] && echo -e "${RED}請使用 sudo 執行${NC}" && exit 1

    LOG="/tmp/dns_test_$(date +%Y%m%d_%H%M%S).log"
    exec 1> >(tee -a "$LOG") 2>&1

    echo "=== DNS Test Pro Run @ $(date '+%Y-%m-%d %H:%M:%S') domain=$DOMAIN ===" >> "${DNS_TEST_ERROR_LOG}"

    local PHASE_URL="https://$DOMAIN"
    local AWS_ONLY=("${AWS_NS[@]}")
    local GCP_ONLY=("${GCP_NS[@]}")

    clear
    echo -e "${GREEN}=== DNS Failover Test（三種驗證方法整合）===${NC}"
    echo -e "域名: ${CYAN}$DOMAIN${NC}"
    [ "$USE_UNBOUND" = true ] && echo -e "模式: ${CYAN}--unbound（含 Unbound 白箱測試）${NC}"
    echo -e "LOG: ${CYAN}$LOG${NC}"
    echo -e "Debug: ${CYAN}$DNS_TEST_DEBUG_LOG${NC}"
    echo -e "錯誤 LOG (無法解析時): ${CYAN}$DNS_TEST_ERROR_LOG${NC}\n"

    # -------------------------------------------------------------------------
    # 步驟 1：全黑環境驗證 (Baseline)
    # 目標：確認防火牆規則生效，無任何 DNS 可解析
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 1: 全黑環境驗證 (Baseline) ━━━${NC}"
    echo -e "目標：block all port 53，預期 dig 無法解析出 IP\n"
    apply_rules "步驟1 全黑驗證"
    flush_dns_cache
    echo -e "驗證: dig +short $DOMAIN（只測 DNS 解析，不連 443）"
    set +e
    local ip_baseline
    ip_baseline=$(dig +short "$DOMAIN" A +time=3 2>/dev/null | grep -E '^[0-9.]+$' | head -1) || true
    set -e
    if [ -z "$ip_baseline" ]; then
        echo -e "${GREEN}[OK] 預期結果: 無法解析（防火牆生效）${NC}\n"
    else
        echo -e "${RED}[!] 非預期: 仍解析出 $ip_baseline，請檢查規則${NC}\n"
    fi

    # -------------------------------------------------------------------------
    # 步驟 2A：單一供應商驗證 — 僅放行 AWS（只驗證 DNS 解析出 IP）
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 2A: 單一供應商驗證（僅放行 AWS）━━━${NC}"
    print_wireshark_hint "此階段"
    apply_rules "步驟2A 僅放行 AWS" "${AWS_ONLY[@]}"
    flush_dns_cache
    echo -e "正在透過 dig 驗證 DNS 解析 $DOMAIN（只測解析，不連 443）..."
    set +e
    local t0_a t1_a ip_a
    t0_a=$(date +%s.%N 2>/dev/null || date +%s)
    ip_a=$(dig +short "$DOMAIN" A 2>/dev/null | grep -E '^[0-9.]+$' | head -1) || true
    t1_a=$(date +%s.%N 2>/dev/null || date +%s)
    set -e
    local dur_a
    dur_a=$(echo "$t1_a - $t0_a" 2>/dev/null | bc) || dur_a="?"
    if [ -n "$ip_a" ]; then
        echo -e "  解析耗時: ${dur_a}s  結果: ${GREEN}$ip_a [OK]${NC}"
        echo -e "${GREEN}[OK] 確認僅靠 AWS 權威即可解析出 IP。${NC}\n"
    else
        {
            echo "--- [$(date '+%Y-%m-%d %H:%M:%S')] phase=2A-僅放行AWS ---"
            echo "domain=$DOMAIN"
            echo "dig +short 結果: 空"
            dig "$DOMAIN" A 2>&1 || true
            echo ""
        } >> "${DNS_TEST_ERROR_LOG}"
        echo -e "  解析耗時: ${dur_a}s  結果: ${RED}無 IP [FAIL]${NC}"
        echo -e "${RED}[FAIL] 無法解析，錯誤已寫入: $DNS_TEST_ERROR_LOG${NC}\n"
    fi

    # -------------------------------------------------------------------------
    # 步驟 2B：單一供應商驗證 — 僅放行 Google（只驗證 DNS 解析出 IP）
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 2B: 單一供應商驗證（僅放行 Google）━━━${NC}"
    print_wireshark_hint "此階段"
    apply_rules "步驟2B 僅放行 Google" "${GCP_ONLY[@]}"
    flush_dns_cache
    echo -e "正在透過 dig 驗證 DNS 解析 $DOMAIN（只測解析，不連 443）..."
    set +e
    local t0_b t1_b ip_b
    t0_b=$(date +%s.%N 2>/dev/null || date +%s)
    ip_b=$(dig +short "$DOMAIN" A 2>/dev/null | grep -E '^[0-9.]+$' | head -1) || true
    t1_b=$(date +%s.%N 2>/dev/null || date +%s)
    set -e
    local dur_b
    dur_b=$(echo "$t1_b - $t0_b" 2>/dev/null | bc) || dur_b="?"
    if [ -n "$ip_b" ]; then
        echo -e "  解析耗時: ${dur_b}s  結果: ${GREEN}$ip_b [OK]${NC}"
        echo -e "${GREEN}[OK] 確認僅靠 Google 權威即可解析出 IP。${NC}\n"
    else
        {
            echo "--- [$(date '+%Y-%m-%d %H:%M:%S')] phase=2B-僅放行Google ---"
            echo "domain=$DOMAIN"
            echo "dig +short 結果: 空"
            dig "$DOMAIN" A 2>&1 || true
            echo ""
        } >> "${DNS_TEST_ERROR_LOG}"
        echo -e "  解析耗時: ${dur_b}s  結果: ${RED}無 IP [FAIL]${NC}"
        echo -e "${RED}[FAIL] 無法解析，錯誤已寫入: $DNS_TEST_ERROR_LOG${NC}\n"
    fi

    # -------------------------------------------------------------------------
    # 步驟 3：切換耗時測試 (Failover Timing) + 重試 loop
    # -------------------------------------------------------------------------
    echo -e "${YELLOW}━━━ 步驟 3: 切換耗時測試 + 重試 loop ━━━${NC}"
    echo -e "情境: 僅放行 AWS（擋 Google），觀察系統需幾次重試才能解析出 IP\n"
    print_wireshark_hint "此階段（最具說服力：觀察 AWS 失敗後是否切到其他路徑）"
    apply_rules "步驟3 僅放行 AWS（擋 Google）" "${AWS_ONLY[@]}"
    echo -e "錯誤日誌 (無法解析時): ${CYAN}$DNS_TEST_ERROR_LOG${NC}\n"

    local run=1 attempts_sum=0 success_count=0
    local duration_sum=0 consecutive_fail=0
    local stop_early=0
    while [ "$run" -le "$FAILOVER_LOOP_RUNS" ] && [ "$stop_early" -eq 0 ]; do
        echo -e "${CYAN}--- 第 $run 輪（共 $FAILOVER_LOOP_RUNS 輪）---${NC}"
        flush_dns_cache
        local attempt=0 got=0
        while [ "$attempt" -lt "$FAILOVER_MAX_ATTEMPTS" ] && [ "$stop_early" -eq 0 ]; do
            attempt=$((attempt + 1))
            set +e
            local t0_r t1_r ip_r
            t0_r=$(date +%s.%N 2>/dev/null || date +%s)
            ip_r=$(dig +short "$DOMAIN" A +time=5 2>/dev/null | grep -E '^[0-9.]+$' | head -1) || true
            t1_r=$(date +%s.%N 2>/dev/null || date +%s)
            set -e
            local dur_r
            dur_r=$(echo "$t1_r - $t0_r" 2>/dev/null | bc) || dur_r="?"
            if [ -n "$ip_r" ]; then
                echo -e "  嘗試 $attempt: ${GREEN}成功${NC}  解析耗時: ${dur_r}s  IP: $ip_r"
                attempts_sum=$((attempts_sum + attempt))
                success_count=$((success_count + 1))
                consecutive_fail=0
                local dsum
                dsum=$(echo "$duration_sum + $dur_r" 2>/dev/null | bc); [ -n "$dsum" ] && duration_sum=$dsum
                got=1
                break
            fi
            consecutive_fail=$((consecutive_fail + 1))
            {
                echo "--- [$(date '+%Y-%m-%d %H:%M:%S')] phase=3-run${run}-attempt${attempt} ---"
                echo "domain=$DOMAIN"
                echo "dig +short 結果: 空"
                dig "$DOMAIN" A +time=2 2>&1 || true
                echo ""
            } >> "${DNS_TEST_ERROR_LOG}"
            echo -e "  嘗試 $attempt: ${RED}失敗${NC}（無 IP）連續 $consecutive_fail 次"
            if [ "$consecutive_fail" -ge 3 ]; then
                echo -e "  ${YELLOW}連續 3 次無法解析，步驟 3 提前結束${NC}"
                stop_early=1
                break
            fi
        done
        if [ "$got" -eq 0 ] && [ "$stop_early" -eq 0 ]; then
            echo -e "  ${RED}本輪達最大嘗試次數 ($FAILOVER_MAX_ATTEMPTS) 未成功，錯誤詳情: $DNS_TEST_ERROR_LOG${NC}"
        fi
        echo ""
        run=$((run + 1))
    done

    # 步驟 3 摘要（run 在每輪結束 +1，故實際執行輪數 = run - 1）
    local runs_done=$((run - 1))
    echo -e "${CYAN}--- 步驟 3 摘要 ---${NC}"
    [ "$stop_early" -eq 1 ] && echo -e "  ${YELLOW}（已提前結束：連續 3 次無法解析）${NC}"
    if [ "$success_count" -gt 0 ]; then
        local avg_attempts
        avg_attempts=$(echo "scale=2; $attempts_sum / $success_count" 2>/dev/null | bc) || avg_attempts="?"
        local avg_dur
        avg_dur=$(echo "scale=3; $duration_sum / $success_count" 2>/dev/null | bc) || avg_dur="?"
        echo -e "  成功輪數: $success_count / $runs_done"
        echo -e "  平均嘗試次數（直到解析成功）: ${avg_attempts}"
        echo -e "  成功時平均 DNS 解析耗時: ${avg_dur}s"
    else
        echo -e "  成功輪數: 0 / $runs_done"
        echo -e "  ${RED}無法計算平均。錯誤詳情: $DNS_TEST_ERROR_LOG${NC}"
    fi

    # -------------------------------------------------------------------------
    # 步驟 4：dig +trace 驗證（方法一：模擬遞回解析器，觀察撞牆後轉彎）
    # 只放行 1 個 AWS IP，其餘全擋 → dig +trace 會先撞牆再轉向唯一活口
    # -------------------------------------------------------------------------
    echo -e "\n${YELLOW}━━━ 步驟 4: dig +trace 遞回模擬（半故障：僅 1 個 AWS 活口）━━━${NC}"
    echo -e "目標: 觀察 dig 從根開始遞回，撞到被封鎖的 NS 後是否轉向唯一活口\n"
    local AWS_ONE=("${AWS_NS[0]}")
    apply_rules "步驟4 僅放行 1 個 AWS" "${AWS_ONE[@]}"
    flush_dns_cache
    echo -e "執行: dig +trace +stats $DOMAIN"
    echo -e "${CYAN}（觀察輸出: connection timed out 後是否最終取得 IP）${NC}\n"
    set +e
    dig +trace +stats "$DOMAIN" 2>&1 | tee -a "$LOG"
    local trace_exit=$?
    set -e
    echo ""
    if [ $trace_exit -eq 0 ]; then
        echo -e "${GREEN}[OK] dig +trace 完成，遞回流程可從唯一活口取得結果${NC}"
    else
        echo -e "${YELLOW}[!] dig +trace 傳回 $trace_exit，請檢查上述輸出${NC}"
    fi

    # -------------------------------------------------------------------------
    # 步驟 5（選用）：本地 Unbound 白箱測試（方法三，需 --unbound）
    # 透過 Log 觀察解析器內部 Failover 決策
    # -------------------------------------------------------------------------
    if [ "$USE_UNBOUND" = true ]; then
        echo -e "\n${YELLOW}━━━ 步驟 5: 本地 Unbound 白箱測試 (--unbound) ━━━${NC}"
        if ! command -v docker &>/dev/null; then
            echo -e "${RED}[FAIL] 需要 Docker，請先安裝${NC}"
        else
            echo -e "啟動 Unbound 容器 (port 5353)..."
            docker rm -f my-dns 2>/dev/null || true
            docker run -d --name my-dns -p 5353:53/udp mvance/unbound &>/dev/null || {
                echo -e "${RED}[FAIL] 無法啟動 Unbound 容器${NC}"
            }
            if docker ps | grep -q my-dns; then
                sleep 2
                apply_rules "步驟5 擋 AWS（Unbound 需經 Google）" "${GCP_ONLY[@]}"
                flush_dns_cache
                echo -e "查詢: dig @127.0.0.1 -p 5353 $DOMAIN"
                set +e
                dig @127.0.0.1 -p 5353 "$DOMAIN" +short 2>&1 | tee -a "$LOG"
                set -e
                echo -e "\n${CYAN}Unbound 內部 Log（觀察 Failover 決策）:${NC}"
                docker logs my-dns 2>&1 | tail -30
            fi
        fi
    fi

    echo -e "\n${GREEN}測試順利結束${NC}"
}

main "$@"
