#!/bin/bash

# =====================================================
# 第三方監控服務檢測腳本
# 支援：ThousandEyes, Catchpoint
# =====================================================

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 載入環境變數
if [ -f .env.monitoring ]; then
    source .env.monitoring
    echo -e "${GREEN}✓ 已載入環境變數${NC}"
else
    echo -e "${RED}✗ 找不到 .env.monitoring 文件${NC}"
    echo -e "${YELLOW}請先複製 .env.monitoring.example 並填入你的 API 資訊${NC}"
    exit 1
fi

# =====================================================
# ThousandEyes API 檢測
# =====================================================

check_thousandeyes() {
    echo -e "\n${BLUE}=== ThousandEyes 檢測 ===${NC}\n"
    
    if [ -z "$THOUSANDEYES_API_TOKEN" ]; then
        echo -e "${YELLOW}⚠ ThousandEyes API Token 未設定，跳過${NC}"
        return
    fi
    
    # 1. 獲取可用的 Agent 列表
    echo -e "${BLUE}1. 獲取可用的監控節點...${NC}"
    
    AGENTS_RESPONSE=$(curl -s -u "${THOUSANDEYES_API_TOKEN}:" \
        "https://api.thousandeyes.com/v6/agents.json")
    
    if [ $? -eq 0 ]; then
        echo "$AGENTS_RESPONSE" > thousandeyes_agents.json
        echo -e "${GREEN}✓ 節點列表已保存到 thousandeyes_agents.json${NC}"
        
        # 解析並顯示東南亞節點
        echo -e "\n${BLUE}東南亞節點：${NC}"
        echo "$AGENTS_RESPONSE" | jq -r '.agents[] | select(.countryId == "SG" or .countryId == "VN" or .countryId == "ID" or .countryId == "TH" or .countryId == "PH") | "\(.agentName) - \(.location) (\(.countryId))"' 2>/dev/null || echo "需要安裝 jq 來解析 JSON"
    else
        echo -e "${RED}✗ 無法連接到 ThousandEyes API${NC}"
    fi
    
    # 2. 獲取測試列表
    echo -e "\n${BLUE}2. 獲取現有測試...${NC}"
    
    TESTS_RESPONSE=$(curl -s -u "${THOUSANDEYES_API_TOKEN}:" \
        "https://api.thousandeyes.com/v6/tests.json")
    
    if [ $? -eq 0 ]; then
        echo "$TESTS_RESPONSE" > thousandeyes_tests.json
        echo -e "${GREEN}✓ 測試列表已保存到 thousandeyes_tests.json${NC}"
    fi
    
    # 3. 創建測試（如果提供了域名）
    if [ -n "$TEST_DOMAIN" ]; then
        echo -e "\n${BLUE}3. 為域名 ${TEST_DOMAIN} 創建測試...${NC}"
        
        # HTTP Server 測試
        CREATE_RESPONSE=$(curl -s -u "${THOUSANDEYES_API_TOKEN}:" \
            -H "Content-Type: application/json" \
            -X POST \
            -d "{
                \"testName\": \"${TEST_DOMAIN} - HTTP Test\",
                \"url\": \"https://${TEST_DOMAIN}\",
                \"interval\": 300,
                \"agents\": []
            }" \
            "https://api.thousandeyes.com/v6/tests/http-server/new.json")
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 測試已創建${NC}"
            echo "$CREATE_RESPONSE" | jq '.' 2>/dev/null || echo "$CREATE_RESPONSE"
        else
            echo -e "${RED}✗ 創建測試失敗${NC}"
        fi
    fi
}

# =====================================================
# Catchpoint API 檢測
# =====================================================

check_catchpoint() {
    echo -e "\n${BLUE}=== Catchpoint 檢測 ===${NC}\n"
    
    if [ -z "$CATCHPOINT_API_KEY" ] || [ -z "$CATCHPOINT_API_SECRET" ]; then
        echo -e "${YELLOW}⚠ Catchpoint API 憑證未設定，跳過${NC}"
        return
    fi
    
    # 1. 獲取 Access Token
    echo -e "${BLUE}1. 獲取 Access Token...${NC}"
    
    TOKEN_RESPONSE=$(curl -s -X POST \
        "https://io.catchpoint.com/ui/api/token" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "grant_type=client_credentials&client_id=${CATCHPOINT_API_KEY}&client_secret=${CATCHPOINT_API_SECRET}")
    
    if [ $? -eq 0 ]; then
        ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token' 2>/dev/null)
        
        if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
            echo -e "${GREEN}✓ Access Token 已獲取${NC}"
            
            # 2. 獲取節點列表
            echo -e "\n${BLUE}2. 獲取監控節點列表...${NC}"
            
            NODES_RESPONSE=$(curl -s -X GET \
                "https://io.catchpoint.com/ui/api/v1/nodes" \
                -H "Authorization: Bearer ${ACCESS_TOKEN}")
            
            if [ $? -eq 0 ]; then
                echo "$NODES_RESPONSE" > catchpoint_nodes.json
                echo -e "${GREEN}✓ 節點列表已保存到 catchpoint_nodes.json${NC}"
                
                # 顯示東南亞節點
                echo -e "\n${BLUE}東南亞節點：${NC}"
                echo "$NODES_RESPONSE" | jq -r '.[] | select(.country == "Singapore" or .country == "Vietnam" or .country == "Indonesia" or .country == "Thailand") | "\(.name) - \(.city), \(.country)"' 2>/dev/null || echo "需要安裝 jq 來解析 JSON"
            fi
            
            # 3. 獲取測試列表
            echo -e "\n${BLUE}3. 獲取現有測試...${NC}"
            
            TESTS_RESPONSE=$(curl -s -X GET \
                "https://io.catchpoint.com/ui/api/v1/tests" \
                -H "Authorization: Bearer ${ACCESS_TOKEN}")
            
            if [ $? -eq 0 ]; then
                echo "$TESTS_RESPONSE" > catchpoint_tests.json
                echo -e "${GREEN}✓ 測試列表已保存到 catchpoint_tests.json${NC}"
            fi
        else
            echo -e "${RED}✗ 無法獲取 Access Token${NC}"
        fi
    else
        echo -e "${RED}✗ 無法連接到 Catchpoint API${NC}"
    fi
}

# =====================================================
# Pingdom API 檢測
# =====================================================

check_pingdom() {
    echo -e "\n${BLUE}=== Pingdom 檢測 ===${NC}\n"
    
    if [ -z "$PINGDOM_API_TOKEN" ]; then
        echo -e "${YELLOW}⚠ Pingdom API Token 未設定，跳過${NC}"
        return
    fi
    
    # 1. 獲取探測點列表
    echo -e "${BLUE}1. 獲取探測點列表...${NC}"
    
    PROBES_RESPONSE=$(curl -s -X GET \
        "https://api.pingdom.com/api/3.1/probes" \
        -H "Authorization: Bearer ${PINGDOM_API_TOKEN}")
    
    if [ $? -eq 0 ]; then
        echo "$PROBES_RESPONSE" > pingdom_probes.json
        echo -e "${GREEN}✓ 探測點列表已保存到 pingdom_probes.json${NC}"
        
        # 顯示亞太探測點
        echo -e "\n${BLUE}亞太探測點：${NC}"
        echo "$PROBES_RESPONSE" | jq -r '.probes[] | select(.region == "APAC") | "\(.name) - \(.city), \(.country)"' 2>/dev/null || echo "需要安裝 jq 來解析 JSON"
    else
        echo -e "${RED}✗ 無法連接到 Pingdom API${NC}"
    fi
    
    # 2. 獲取現有檢查
    echo -e "\n${BLUE}2. 獲取現有檢查...${NC}"
    
    CHECKS_RESPONSE=$(curl -s -X GET \
        "https://api.pingdom.com/api/3.1/checks" \
        -H "Authorization: Bearer ${PINGDOM_API_TOKEN}")
    
    if [ $? -eq 0 ]; then
        echo "$CHECKS_RESPONSE" > pingdom_checks.json
        echo -e "${GREEN}✓ 檢查列表已保存到 pingdom_checks.json${NC}"
    fi
}

# =====================================================
# 生成報告
# =====================================================

generate_report() {
    echo -e "\n${BLUE}=== 生成檢測報告 ===${NC}\n"
    
    REPORT_FILE="monitoring_services_report_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$REPORT_FILE" << EOF
# 第三方監控服務檢測報告

生成時間：$(date '+%Y-%m-%d %H:%M:%S')

---

## ThousandEyes

EOF
    
    if [ -f "thousandeyes_agents.json" ]; then
        echo "### 可用節點" >> "$REPORT_FILE"
        echo '```json' >> "$REPORT_FILE"
        cat thousandeyes_agents.json | jq '.' 2>/dev/null >> "$REPORT_FILE" || cat thousandeyes_agents.json >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
    else
        echo "未檢測" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF

---

## Catchpoint

EOF
    
    if [ -f "catchpoint_nodes.json" ]; then
        echo "### 可用節點" >> "$REPORT_FILE"
        echo '```json' >> "$REPORT_FILE"
        cat catchpoint_nodes.json | jq '.' 2>/dev/null >> "$REPORT_FILE" || cat catchpoint_nodes.json >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
    else
        echo "未檢測" >> "$REPORT_FILE"
    fi
    
    cat >> "$REPORT_FILE" << EOF

---

## Pingdom

EOF
    
    if [ -f "pingdom_probes.json" ]; then
        echo "### 可用探測點" >> "$REPORT_FILE"
        echo '```json' >> "$REPORT_FILE"
        cat pingdom_probes.json | jq '.' 2>/dev/null >> "$REPORT_FILE" || cat pingdom_probes.json >> "$REPORT_FILE"
        echo '```' >> "$REPORT_FILE"
    else
        echo "未檢測" >> "$REPORT_FILE"
    fi
    
    echo -e "${GREEN}✓ 報告已生成：${REPORT_FILE}${NC}"
}

# =====================================================
# 主程序
# =====================================================

main() {
    echo -e "${GREEN}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║     第三方監控服務檢測工具                        ║"
    echo "║     支援：ThousandEyes, Catchpoint, Pingdom      ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # 檢查依賴
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}⚠ 建議安裝 jq 以獲得更好的 JSON 解析體驗${NC}"
        echo -e "${YELLOW}  macOS: brew install jq${NC}"
        echo -e "${YELLOW}  Ubuntu: sudo apt-get install jq${NC}"
    fi
    
    # 執行檢測
    check_thousandeyes
    check_catchpoint
    check_pingdom
    
    # 生成報告
    generate_report
    
    echo -e "\n${GREEN}✓ 所有檢測完成！${NC}\n"
    echo -e "${BLUE}下一步：${NC}"
    echo -e "1. 查看生成的 JSON 文件，確認可用的節點"
    echo -e "2. 查看報告文件，了解詳細信息"
    echo -e "3. 在監控服務的 Web 界面中配置測試"
    echo ""
}

# 執行主程序
main

