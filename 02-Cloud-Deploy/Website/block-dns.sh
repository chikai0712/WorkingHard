#!/bin/bash

# 封鎖/解除封鎖 DNS 的腳本

set -e

# 顏色輸出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DNS_IP="${1:-205.251.197.44}"
ACTION="${2:-block}"
ANCHOR="custom"

if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ 需要 root 權限${NC}"
    echo "請使用 sudo 執行"
    exit 1
fi

# 確保 pfctl 已啟用
if ! pfctl -si 2>/dev/null | grep -q "Status: Enabled"; then
    echo -e "${YELLOW}⚠️  啟用 pfctl...${NC}"
    pfctl -e 2>/dev/null || {
        echo -e "${RED}❌ 無法啟用 pfctl${NC}"
        exit 1
    }
    echo -e "${GREEN}✅ pfctl 已啟用${NC}"
fi

case "$ACTION" in
    block)
        echo -e "${BLUE}🚫 封鎖 DNS: $DNS_IP${NC}"
        
        # 方法 1：使用 anchor
        echo "block drop out quick proto udp from any to $DNS_IP port 53" | \
            pfctl -a $ANCHOR -f - 2>/dev/null
        
        # 驗證
        sleep 1
        if pfctl -a $ANCHOR -sr 2>/dev/null | grep -q "$DNS_IP"; then
            echo -e "${GREEN}✅ 封鎖成功（使用 anchor）${NC}"
            echo ""
            echo "規則："
            pfctl -a $ANCHOR -sr | grep "$DNS_IP"
        else
            echo -e "${YELLOW}⚠️  anchor 方法失敗，嘗試備用方法...${NC}"
            
            # 方法 2：添加到主規則集
            (pfctl -sr 2>/dev/null; \
             echo "block drop out quick proto udp from any to $DNS_IP port 53") | \
                pfctl -f - 2>/dev/null
            
            sleep 1
            if pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
                echo -e "${GREEN}✅ 封鎖成功（使用主規則集）${NC}"
                echo ""
                echo "規則："
                pfctl -sr | grep "$DNS_IP"
            else
                echo -e "${RED}❌ 封鎖失敗${NC}"
                echo ""
                echo "請手動執行："
                echo "  sudo pfctl -a custom -f - <<< 'block drop out quick proto udp from any to $DNS_IP port 53'"
                exit 1
            fi
        fi
        
        echo ""
        echo -e "${CYAN}測試封鎖...${NC}"
        if dig @$DNS_IP www.clouddeployment168.site +time=2 +tries=1 2>&1 | grep -qi "timeout\|connection refused\|no servers could be reached"; then
            echo -e "${GREEN}✅ 封鎖生效：DNS 查詢失敗${NC}"
        else
            echo -e "${YELLOW}⚠️  警告：DNS 查詢仍然成功，可能：${NC}"
            echo "  1. 規則未正確應用"
            echo "  2. DNS 快取影響"
            echo "  3. 需要清除快取：sudo dscacheutil -flushcache"
        fi
        ;;
    
    unblock)
        echo -e "${BLUE}🔓 解除封鎖 DNS: $DNS_IP${NC}"
        
        # 清除 anchor 規則
        pfctl -a $ANCHOR -F all 2>/dev/null || true
        
        # 從主規則集移除
        pfctl -sr 2>/dev/null | grep -v "$DNS_IP" | pfctl -f - 2>/dev/null || {
            # 如果失敗，重新載入原始配置
            if [ -f /etc/pf.conf ]; then
                pfctl -f /etc/pf.conf 2>/dev/null || true
            else
                echo "" | pfctl -f - 2>/dev/null || true
            fi
        }
        
        sleep 1
        
        if pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
            echo -e "${YELLOW}⚠️  仍有規則存在${NC}"
            echo "當前規則："
            pfctl -sr | grep "$DNS_IP"
        else
            echo -e "${GREEN}✅ 已解除封鎖${NC}"
        fi
        ;;
    
    status)
        echo -e "${BLUE}📊 檢查封鎖狀態${NC}"
        echo ""
        
        if pfctl -sr 2>/dev/null | grep -q "$DNS_IP"; then
            echo -e "${RED}🚫 DNS $DNS_IP 已被封鎖${NC}"
            echo ""
            echo "規則："
            pfctl -sr | grep "$DNS_IP"
        else
            echo -e "${GREEN}✅ DNS $DNS_IP 未被封鎖${NC}"
        fi
        ;;
    
    *)
        echo "用法：$0 <DNS_IP> [block|unblock|status]"
        echo ""
        echo "範例："
        echo "  $0 205.251.197.44 block    # 封鎖 DNS"
        echo "  $0 205.251.197.44 unblock  # 解除封鎖"
        echo "  $0 205.251.197.44 status   # 檢查狀態"
        exit 1
        ;;
esac
