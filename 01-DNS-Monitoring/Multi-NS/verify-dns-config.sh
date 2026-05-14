#!/bin/bash
#
# DNS 架構配置驗證腳本
# 用於驗證 Multi-NS 架構是否正確設定
#

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置（請根據實際情況修改）
DOMAIN="${1:-example.com}"
AWS_NS="${2:-ns-11.awsdns-11.com}"
GOOGLE_NS="${3:-ns-cloud-c1.googledomains.com}"

echo "=========================================="
echo "🔍 DNS 架構配置驗證工具"
echo "=========================================="
echo ""
echo "域名: $DOMAIN"
echo "AWS NS: $AWS_NS"
echo "Google NS: $GOOGLE_NS"
echo ""

# 檢查 dig 是否可用
if ! command -v dig &> /dev/null; then
    echo -e "${RED}❌ 錯誤: 未找到 dig 命令${NC}"
    echo "   請安裝 bind-utils (Linux) 或 bind (macOS)"
    exit 1
fi

ERRORS=0
WARNINGS=0

# 1. 檢查 Registrar 層級 NS 記錄
echo "1️⃣  檢查 Registrar 層級 NS 記錄..."
REGISTRAR_NS=$(dig +short NS "$DOMAIN" 2>/dev/null | sort)

if [ -z "$REGISTRAR_NS" ]; then
    echo -e "${RED}   ❌ 無法查詢 Registrar 層級的 NS 記錄${NC}"
    ERRORS=$((ERRORS + 1))
else
    echo "   Registrar 返回的 NS 記錄:"
    echo "$REGISTRAR_NS" | while read ns; do
        echo "   - $ns"
    done
    
    # 檢查是否包含 AWS 和 Google
    HAS_AWS=$(echo "$REGISTRAR_NS" | grep -i "aws" | wc -l)
    HAS_GOOGLE=$(echo "$REGISTRAR_NS" | grep -i "google\|googledomains" | wc -l)
    
    if [ "$HAS_AWS" -gt 0 ] && [ "$HAS_GOOGLE" -gt 0 ]; then
        echo -e "${GREEN}   ✅ 包含 AWS 和 Google Name Server${NC}"
    else
        echo -e "${YELLOW}   ⚠️  警告: 可能未包含 AWS 和 Google 的混合配置${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi
echo ""

# 2. 檢查 NS 記錄一致性
echo "2️⃣  檢查 NS 記錄一致性..."
AWS_NS_LIST=$(dig @"$AWS_NS" +short NS "$DOMAIN" 2>/dev/null | sort)
GOOGLE_NS_LIST=$(dig @"$GOOGLE_NS" +short NS "$DOMAIN" 2>/dev/null | sort)

if [ -z "$AWS_NS_LIST" ]; then
    echo -e "${RED}   ❌ 無法從 AWS NS 查詢 NS 記錄${NC}"
    ERRORS=$((ERRORS + 1))
elif [ -z "$GOOGLE_NS_LIST" ]; then
    echo -e "${RED}   ❌ 無法從 Google NS 查詢 NS 記錄${NC}"
    ERRORS=$((ERRORS + 1))
elif [ "$AWS_NS_LIST" = "$GOOGLE_NS_LIST" ]; then
    echo -e "${GREEN}   ✅ NS 記錄一致${NC}"
    echo "   所有權威 DNS 返回相同的 NS 列表"
else
    echo -e "${RED}   ❌ NS 記錄不一致！${NC}"
    echo "   AWS 返回:"
    echo "$AWS_NS_LIST" | sed 's/^/      /'
    echo "   Google 返回:"
    echo "$GOOGLE_NS_LIST" | sed 's/^/      /'
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 3. 檢查 A 記錄一致性
echo "3️⃣  檢查 A 記錄一致性..."
AWS_A=$(dig @"$AWS_NS" +short A "$DOMAIN" 2>/dev/null | sort)
GOOGLE_A=$(dig @"$GOOGLE_NS" +short A "$DOMAIN" 2>/dev/null | sort)

if [ -z "$AWS_A" ] && [ -z "$GOOGLE_A" ]; then
    echo -e "${YELLOW}   ⚠️  警告: 域名可能沒有設定 A 記錄${NC}"
    WARNINGS=$((WARNINGS + 1))
elif [ "$AWS_A" = "$GOOGLE_A" ]; then
    echo -e "${GREEN}   ✅ A 記錄一致${NC}"
    if [ -n "$AWS_A" ]; then
        echo "   IP 地址:"
        echo "$AWS_A" | sed 's/^/      /'
    fi
else
    echo -e "${RED}   ❌ A 記錄不一致！${NC}"
    echo "   AWS 返回: $AWS_A"
    echo "   Google 返回: $GOOGLE_A"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# 4. 檢查 Glue Records（如果需要）
echo "4️⃣  檢查 Glue Records..."
ADDITIONAL=$(dig +additional "$DOMAIN" NS 2>/dev/null | grep -A 10 "ADDITIONAL SECTION" | grep "IN A" || true)

if [ -n "$ADDITIONAL" ]; then
    echo "   找到 Glue Records:"
    echo "$ADDITIONAL" | sed 's/^/      /'
    echo -e "${GREEN}   ✅ Glue Records 已設定${NC}"
else
    # 檢查 NS 是否指向同域名
    NS_IN_SAME_DOMAIN=$(echo "$REGISTRAR_NS" | grep -i "$DOMAIN" | wc -l)
    if [ "$NS_IN_SAME_DOMAIN" -gt 0 ]; then
        echo -e "${YELLOW}   ⚠️  警告: NS 指向同域名但未找到 Glue Records${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}   ✅ 不需要 Glue Records（NS 不在同域名）${NC}"
    fi
fi
echo ""

# 總結
echo "=========================================="
echo "📊 驗證結果總結"
echo "=========================================="

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有檢查通過！架構配置正確。${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  有 $WARNINGS 個警告，但沒有嚴重錯誤${NC}"
    exit 0
else
    echo -e "${RED}❌ 發現 $ERRORS 個錯誤，$WARNINGS 個警告${NC}"
    echo ""
    echo "請參考 DNS故障切換驗證方法.md 進行修正"
    exit 1
fi

