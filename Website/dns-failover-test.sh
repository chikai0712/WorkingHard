#!/bin/bash

# DNS 故障切換測試腳本
# 用於測試多供應商 DNS 的故障切換行為

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
DEFAULT_DNS="8.8.8.8"  # 系統預設 DNS

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
# 代表用（階段 1 與部分測試仍用第一組）
AWS_DNS="${AWS_DNS_IPS[0]}"
GOOGLE_DNS="${GOOGLE_DNS_IPS[0]}"

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
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔍 DNS 故障切換測試工具${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "測試域名：$DOMAIN"
echo "AWS Route 53 DNS（${#AWS_DNS_IPS[@]} 組）：${AWS_DNS_IPS[*]}"
echo "Google Domains DNS（${#GOOGLE_DNS_IPS[@]} 組）：${GOOGLE_DNS_IPS[*]}"
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

# 函數：驗證封鎖是否生效（修正版）
verify_block() {
    local dns_ip=$1
    local description=$2
    
    echo -e "${CYAN}🔍 驗證 $description ($dns_ip) 是否被封鎖...${NC}"
    
    # 檢查 pfctl 規則（放寬 grep 條件，匹配 'port 53' 或 'port = 53'）
    local has_rule=false
    
    # 直接檢查全域規則
    if pfctl -sr 2>/dev/null | grep -q "$dns_ip.*port.*53"; then
        has_rule=true
        echo -e "${GREEN}✅ pfctl 規則存在${NC}"
        pfctl -sr 2>/dev/null | grep "$dns_ip.*port.*53"
    fi
    
    if [ "$has_rule" != true ]; then
        echo -e "${RED}❌ pfctl 規則不存在${NC}"
        echo "當前規則前 10 行："
        pfctl -sr 2>/dev/null | head -10
        return 1
    fi
    
    # 實際測試：嘗試 DNS 查詢（應該失敗）
    echo ""
    echo -e "${CYAN}測試：嘗試查詢被封鎖的 DNS...${NC}"
    
    # 使用短超時測試
    local test_result=$(run_with_timeout 3 nslookup -timeout=2 $DOMAIN $dns_ip 2>&1)
    local test_exit=$?
    
    # 判斷結果：如果是 timeout (124) 或連線被拒，則代表封鎖成功
    if [ $test_exit -ne 0 ] || echo "$test_result" | grep -qi "timeout\|timed out\|can't find\|connection refused\|SERVFAIL"; then
        echo -e "${GREEN}✅ 封鎖生效：DNS 查詢失敗（預期行為）${NC}"
        return 0
    else
        echo -e "${RED}❌ 警告：DNS 查詢仍然成功，封鎖可能未生效${NC}"
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

# 函數：封鎖 DNS 伺服器（修正版：直接寫入全域規則並清除狀態）
block_dns() {
    local dns_ip=$1
    local description=$2
    
    echo -e "${YELLOW}🚫 封鎖 $description ($dns_ip)...${NC}"
    
    # 檢查是否已經封鎖
    if pfctl -sr 2>/dev/null | grep -q "$dns_ip.*port.*53"; then
        echo -e "${YELLOW}⚠️  已經封鎖 $dns_ip${NC}"
        return 0
    fi
    
    # 確保 pfctl 已啟用
    if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        pfctl -e 2>/dev/null || {
            echo -e "${RED}❌ 無法啟用 pfctl${NC}"
            return 1
        }
    fi
    
    # 方法：讀取現有規則 -> 添加封鎖規則 -> 重新載入
    local current_rules
    current_rules=$(pfctl -sr 2>/dev/null)
    
    # 封鎖「本機 → DNS」：阻擋查詢發出（可選，部分環境 out 未必生效）
    local rule_out="block drop out quick proto { udp, tcp } from any to $dns_ip port 53"
    # 封鎖「DNS → 本機」：阻擋 DNS 回傳的資料，模擬 DNS 沒有回應（查詢可發出但收不到答案）
    local rule_in="block drop in quick proto { udp, tcp } from $dns_ip port 53 to any"
    
    {
        echo "$current_rules"
        echo "$rule_out"
        echo "$rule_in"
    } | pfctl -f - 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 已加入封鎖規則：$dns_ip${NC}"
        
        # 關鍵：清除與該 IP 相關的所有既有狀態，避免舊連線繼續被放行
        echo -e "${YELLOW}⚡ 清除防火牆狀態表 (pfctl -k $dns_ip)...${NC}"
        pfctl -k "$dns_ip" 2>/dev/null || true
        
        sleep 0.5
        if pfctl -sr 2>/dev/null | grep -q "$dns_ip.*port.*53"; then
            return 0
        else
            echo -e "${RED}❌ 規則寫入失敗，請檢查權限${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ 無法載入 pfctl 規則${NC}"
        return 1
    fi
}

# 函數：解除封鎖 DNS
unblock_dns() {
    local dns_ip=$1
    
    echo -e "${YELLOW}🔓 解除封鎖 $dns_ip...${NC}"
    
    # 方法 1：移除 anchor
    local anchor_name="dns_block_$(echo $dns_ip | tr '.' '_')"
    pfctl -a "$anchor_name" -F all 2>/dev/null
    
    # 方法 2：移除 custom anchor 中的規則
    pfctl -a custom -F all 2>/dev/null
    
    # 方法 3：重新載入原始配置（如果有的話）
    if [ -f /etc/pf.conf ]; then
        pfctl -f /etc/pf.conf 2>/dev/null || true
    else
        # 如果沒有原始配置，清除所有規則
        echo "" | pfctl -f - 2>/dev/null || true
    fi
    
    # 驗證是否已解除
    sleep 1
    if pfctl -sr 2>/dev/null | grep -q "$dns_ip.*port.*53"; then
        echo -e "${YELLOW}⚠️  仍有規則存在，嘗試強制清除...${NC}"
        # 強制清除所有規則
        pfctl -F all 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ 已解除封鎖 $dns_ip${NC}"
}

# 函數：一次寫入並載入「全部 DNS IP」的封鎖規則（避免多次 pfctl -f 觸發規則數量限制）
block_all_dns_ips() {
    local desc="$1"
    echo -e "${YELLOW}🚫 $desc：封鎖 AWS ${#AWS_DNS_IPS[@]} 組 + Google ${#GOOGLE_DNS_IPS[@]} 組（共 $(( ${#AWS_DNS_IPS[@]} + ${#GOOGLE_DNS_IPS[@]} )) 個 IP）...${NC}"
    
    if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
        pfctl -e 2>/dev/null || { echo -e "${RED}❌ 無法啟用 pfctl${NC}"; return 1; }
    fi
    
    # 一次讀取現有規則，再追加「所有 IP」的 block 規則，只做一次 pfctl -f -
    local current_rules
    current_rules=$(pfctl -sr 2>/dev/null)
    local all_rules="$current_rules"
    
    for ip in "${AWS_DNS_IPS[@]}" "${GOOGLE_DNS_IPS[@]}"; do
        all_rules="$all_rules"$'\n'"block drop out quick proto { udp, tcp } from any to $ip port 53"
        all_rules="$all_rules"$'\n'"block drop in quick proto { udp, tcp } from $ip port 53 to any"
    done
    
    echo "$all_rules" | pfctl -f - 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 無法載入 pf 規則（一次寫入 $(( (${#AWS_DNS_IPS[@]} + ${#GOOGLE_DNS_IPS[@]}) * 2 )) 條）${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ 已一次加入全部封鎖規則${NC}"
    echo -e "${YELLOW}⚡ 清除防火牆狀態表 (pfctl -k)...${NC}"
    for ip in "${AWS_DNS_IPS[@]}" "${GOOGLE_DNS_IPS[@]}"; do
        pfctl -k "$ip" 2>/dev/null || true
    done
    sleep 0.5
}

# 函數：解除封鎖清單內所有 DNS IP
unblock_all_dns_ips() {
    echo -e "${YELLOW}🔓 解除封鎖所有 DNS（AWS + Google 共 $(( ${#AWS_DNS_IPS[@]} + ${#GOOGLE_DNS_IPS[@]} )) 個 IP）...${NC}"
    for ip in "${AWS_DNS_IPS[@]}"; do
        unblock_dns "$ip"
    done
    for ip in "${GOOGLE_DNS_IPS[@]}"; do
        unblock_dns "$ip"
    done
}

# 函數：清理（確保解除所有封鎖）
cleanup() {
    echo ""
    echo -e "${YELLOW}🧹 清理中...${NC}"
    unblock_all_dns_ips
    echo -e "${GREEN}✅ 清理完成${NC}"
}

# 註冊清理函數
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
echo -e "${YELLOW}💡 建議同時開啟 Wireshark 觀察 DNS 封包${NC}"
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
    
    # 封鎖「全部 8 個 DNS」（兩組都阻擋），若未生效就持續嘗試
    MAX_RETRIES=3
    RETRY_INTERVAL=2
    BLOCK_OK=false
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        echo -e "${CYAN}🔁 嘗試第 $attempt 次封鎖兩組 DNS（共 8 個 IP）...${NC}"
        block_all_dns_ips "封鎖中"
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
            test_dns_query "" "系統自動選擇（兩組皆封鎖）" 10
            echo ""
            
            # 每隔 60 秒測試一次系統自動切換
            for i in {60..300..60}; do
                ELAPSED=$(($(date +%s) - BLOCK_START))
                REMAINING=$((BLOCK_DURATION - ELAPSED))
                
                if [ $REMAINING -le 0 ]; then
                    break
                fi
                
                echo -e "${CYAN}[$ELAPSED 秒] 測試：系統自動選擇 DNS（剩餘 $REMAINING 秒）${NC}"
                echo -e "${YELLOW}💡 觀察：系統是否會自動嘗試其他 DNS 伺服器${NC}"
                test_dns_query "" "系統自動選擇" 10
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
                test_dns_query "" "系統自動選擇" 10
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
            exit 1
        fi
    else
        echo -e "${RED}❌ 無法封鎖兩組 DNS（多次嘗試失敗），停止此測試${NC}"
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

# 測試 2.2：封鎖 Google DNS（4 組），測試系統是否切換
if [ "$GOOGLE_OK" = true ]; then
    echo ""
    echo -e "${CYAN}2.2 測試：封鎖 Google Domains DNS（4 組），觀察系統行為（封鎖持續 60 秒）${NC}"
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
        echo -e "${CYAN}🔁 嘗試第 $attempt 次封鎖 Google DNS（4 組）...${NC}"
        for ip in "${GOOGLE_DNS_IPS[@]}"; do
            block_dns "$ip" "Google"
        done
        sleep $RETRY_INTERVAL
        echo ""
        echo -e "${CYAN}🔍 第 $attempt 次驗證封鎖規則...${NC}"
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
                echo -e "${YELLOW}💡 觀察：系統是否會自動嘗試其他 DNS 伺服器${NC}"
                test_dns_query "" "系統自動選擇" 10
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
                test_dns_query "" "系統自動選擇" 10
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
            exit 1
        fi
    else
        echo -e "${RED}❌ 無法封鎖 Google DNS（多次嘗試失敗），停止此測試${NC}"
        exit 1
    fi
    
    # 解除封鎖（Google 4 組）
    echo -e "${CYAN}🔓 解除封鎖 Google DNS（4 組）...${NC}"
    for ip in "${GOOGLE_DNS_IPS[@]}"; do
        unblock_dns "$ip"
    done
    sleep 2
    
    # 驗證解除封鎖後是否恢復正常
    echo ""
    echo -e "${CYAN}驗證：解除封鎖後的查詢（應該恢復正常）${NC}"
    test_dns_query "$GOOGLE_DNS" "Google DNS（解除封鎖後）" 5
    echo ""
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
echo -e "${YELLOW}💡 若在此階段仍能成功解析，代表系統可能使用了其他未預期的 DNS（例如 ISP 或 8.8.8.8）${NC}"
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
echo -e "${CYAN}🚫 同時封鎖兩組 DNS（共 8 個 IP）...${NC}"
block_all_dns_ips "全面封鎖"
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

# 最終檢查：確認所有封鎖已解除
echo -e "${CYAN}🔍 最終檢查：確認所有 DNS 封鎖已解除...${NC}"
if pfctl -sr 2>/dev/null | grep -qE "($AWS_DNS|$GOOGLE_DNS).*port.*53"; then
    echo -e "${YELLOW}⚠️  警告：仍有 DNS 封鎖規則存在${NC}"
    pfctl -sr 2>/dev/null | grep -E "($AWS_DNS|$GOOGLE_DNS).*port.*53"
    echo ""
    echo "正在清理..."
    cleanup
else
    echo -e "${GREEN}✅ 確認：所有 DNS 封鎖已解除${NC}"
fi
echo ""

echo -e "${GREEN}✅ 測試完成${NC}"
echo ""
