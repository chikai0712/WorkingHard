#!/bin/bash
# -------------------------------------------------------------------------------
# macOS DNS 設定腳本 - 將系統 DNS 指向本機 Docker BIND
# 功能：自動設定 macOS 網路介面的 DNS 伺服器為 127.0.0.1
# 
# 用法：
#   sudo bash ./setup-macos-dns.sh [網路介面名稱]
#   例如：sudo bash ./setup-macos-dns.sh Wi-Fi
#
# 如果不指定介面，腳本會自動偵測主要網路介面
# -------------------------------------------------------------------------------

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m'

# 檢查權限
if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}❌ 需要 sudo 權限${NC}"
    echo "請使用: sudo bash $0"
    exit 1
fi

# 檢查 Docker BIND 是否運行
check_bind_running() {
    if docker ps | grep -q "bind-dns-local"; then
        echo -e "${GREEN}✅ BIND DNS 容器正在運行${NC}"
        return 0
    else
        echo -e "${RED}❌ BIND DNS 容器未運行${NC}"
        echo -e "${YELLOW}請先啟動 BIND: cd bind-dns-local && ./scripts/start.sh${NC}"
        return 1
    fi
}

# 取得主要網路介面
get_primary_interface() {
    # 取得預設路由的介面
    local interface
    interface=$(route get default 2>/dev/null | grep "interface:" | awk '{print $2}')
    
    if [ -z "$interface" ]; then
        # 備用方法：取得第一個活躍的網路介面
        interface=$(networksetup -listallnetworkservices | grep -v "^An asterisk" | grep -v "^The following" | head -1)
    fi
    
    echo "$interface"
}

# 列出所有網路介面
list_interfaces() {
    echo -e "${CYAN}可用的網路介面：${NC}"
    networksetup -listallnetworkservices | grep -v "^An asterisk" | grep -v "^The following" | nl
}

# 顯示當前 DNS 設定
show_current_dns() {
    local interface=$1
    echo -e "${CYAN}當前 DNS 設定 ($interface)：${NC}"
    networksetup -getdnsservers "$interface" 2>/dev/null || echo "無法取得 DNS 設定"
}

# 設定 DNS
set_dns() {
    local interface=$1
    local dns_server="${2:-127.0.0.1}"
    
    echo -e "${YELLOW}正在設定 DNS...${NC}"
    echo -e "介面: ${CYAN}$interface${NC}"
    echo -e "DNS 伺服器: ${CYAN}$dns_server${NC}"
    
    # 設定 DNS
    if networksetup -setdnsservers "$interface" "$dns_server"; then
        echo -e "${GREEN}✅ DNS 設定成功${NC}"
        
        # 驗證設定
        echo ""
        echo -e "${CYAN}驗證 DNS 設定：${NC}"
        networksetup -getdnsservers "$interface"
        
        # 清除 DNS 快取
        echo ""
        echo -e "${YELLOW}清除 DNS 快取...${NC}"
        dscacheutil -flushcache 2>/dev/null || true
        killall -HUP mDNSResponder 2>/dev/null || true
        echo -e "${GREEN}✅ DNS 快取已清除${NC}"
        
        return 0
    else
        echo -e "${RED}❌ DNS 設定失敗${NC}"
        return 1
    fi
}

# 還原 DNS 設定（使用 DHCP 或系統預設）
restore_dns() {
    local interface=$1
    
    echo -e "${YELLOW}正在還原 DNS 設定...${NC}"
    echo -e "介面: ${CYAN}$interface${NC}"
    
    # 還原為 DHCP 提供的 DNS
    if networksetup -setdnsservers "$interface" "Empty"; then
        echo -e "${GREEN}✅ DNS 已還原為 DHCP 設定${NC}"
        
        # 清除 DNS 快取
        dscacheutil -flushcache 2>/dev/null || true
        killall -HUP mDNSResponder 2>/dev/null || true
        
        return 0
    else
        echo -e "${RED}❌ DNS 還原失敗${NC}"
        return 1
    fi
}

# 測試 DNS 解析
test_dns() {
    local test_domain="${1:-example.com}"
    
    echo ""
    echo -e "${CYAN}測試 DNS 解析...${NC}"
    echo -e "測試域名: ${CYAN}$test_domain${NC}"
    
    # 使用 dig 測試
    local result
    result=$(dig +short "$test_domain" @127.0.0.1 2>/dev/null | head -1)
    
    if [ -n "$result" ]; then
        echo -e "${GREEN}✅ DNS 解析成功: $test_domain -> $result${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  DNS 解析失敗或無回應${NC}"
        echo -e "${CYAN}提示: 請確認 BIND 容器正在運行${NC}"
        return 1
    fi
}

# 主流程
main() {
    local action="${1:-set}"
    local interface="${2:-}"
    local dns_server="${3:-127.0.0.1}"
    
    clear
    echo -e "${GREEN}=== macOS DNS 設定工具 ===${NC}\n"
    
    # 檢查 BIND 是否運行（僅在設定時檢查）
    if [ "$action" = "set" ]; then
        if ! check_bind_running; then
            exit 1
        fi
        echo ""
    fi
    
    # 取得網路介面
    if [ -z "$interface" ]; then
        interface=$(get_primary_interface)
        if [ -z "$interface" ]; then
            echo -e "${RED}❌ 無法自動偵測網路介面${NC}"
            echo ""
            list_interfaces
            echo ""
            read -p "請輸入網路介面名稱: " interface
            if [ -z "$interface" ]; then
                echo -e "${RED}❌ 未指定網路介面${NC}"
                exit 1
            fi
        fi
    fi
    
    # 驗證介面是否存在
    if ! networksetup -listallnetworkservices | grep -q "^$interface$"; then
        echo -e "${RED}❌ 找不到網路介面: $interface${NC}"
        echo ""
        list_interfaces
        exit 1
    fi
    
    echo -e "${CYAN}使用網路介面: $interface${NC}\n"
    
    # 顯示當前設定
    show_current_dns "$interface"
    echo ""
    
    # 執行操作
    case "$action" in
        set)
            if set_dns "$interface" "$dns_server"; then
                test_dns "example.com"
                echo ""
                echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
                echo -e "${GREEN}✅ DNS 設定完成${NC}"
                echo ""
                echo -e "${CYAN}📝 提示：${NC}"
                echo "  - 系統 DNS 已設定為: 127.0.0.1 (本機 BIND)"
                echo "  - 測試 DNS: dig example.com"
                echo "  - 還原 DNS: sudo bash $0 restore $interface"
                echo ""
            fi
            ;;
        restore)
            restore_dns "$interface"
            ;;
        show)
            show_current_dns "$interface"
            ;;
        list)
            list_interfaces
            ;;
        test)
            test_dns "${2:-example.com}"
            ;;
        *)
            echo -e "${RED}❌ 未知的操作: $action${NC}"
            echo ""
            echo "用法:"
            echo "  sudo bash $0 [set|restore|show|list|test] [介面名稱] [DNS伺服器]"
            echo ""
            echo "範例:"
            echo "  sudo bash $0 set Wi-Fi              # 設定 Wi-Fi 使用本機 BIND"
            echo "  sudo bash $0 restore Wi-Fi          # 還原 Wi-Fi DNS 設定"
            echo "  sudo bash $0 show Wi-Fi             # 顯示當前 DNS 設定"
            echo "  sudo bash $0 list                   # 列出所有網路介面"
            echo "  sudo bash $0 test example.com       # 測試 DNS 解析"
            exit 1
            ;;
    esac
}

main "$@"
