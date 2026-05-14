#!/bin/bash

# 腳本版本驗證工具

echo "========================================"
echo "腳本版本驗證報告"
echo "========================================"
echo "時間: $(date)"
echo ""

# 定義所有腳本
scripts=(
    "/Users/ckchiu/id_check_api_v3.sh"
    "/Users/ckchiu/id_check_expert.sh"
    "/Users/ckchiu/id_check_final.sh"
    "/Users/ckchiu/id_check_v2.sh"
    "/Users/ckchiu/id_dns_check.sh"
    "/Users/ckchiu/id_globalping_multi_v2.1.sh"
    "/Users/ckchiu/id_globalping_multi_v2.sh"
    "/Users/ckchiu/id_globalping_multi.sh"
    "/Users/ckchiu/id_globalping_v2.sh"
    "/Users/ckchiu/id_globalping.sh"
    "/Users/ckchiu/id_verify_api.sh"
    "/Users/ckchiu/Desktop/Project/id_globalping_auto_retry.sh"
    "/Users/ckchiu/Desktop/Project/id_globalping_v1.1.sh"
    "/Users/ckchiu/Desktop/Project/id_globalping_cli.sh"
)

echo "檢查腳本存在性和版本信息："
echo "========================================"

for script in "${scripts[@]}"; do
    name=$(basename "$script")
    
    if [ -f "$script" ]; then
        # 檢查版本信息
        version=$(head -20 "$script" 2>/dev/null | grep -E "^#.*v[0-9]|版本|version" | head -1 | sed 's/^# *//')
        
        # 檢查是否使用 CLI
        uses_cli=$(grep -q "globalping http" "$script" 2>/dev/null && echo "CLI" || echo "API")
        
        # 檢查延遲配置
        delay=$(grep -E "^DELAY=|DELAY_BETWEEN" "$script" 2>/dev/null | head -1 | cut -d'=' -f2 | tr -d ' ')
        
        # 檢查是否有自動重試
        has_retry=$(grep -q "MAX_RETRY\|重試" "$script" 2>/dev/null && echo "✅" || echo "❌")
        
        # 檢查是否禁用代理
        has_unset_proxy=$(grep -q "unset.*proxy" "$script" 2>/dev/null && echo "✅" || echo "❌")
        
        echo "📄 $name"
        echo "   路徑: $script"
        [ -n "$version" ] && echo "   版本: $version"
        echo "   類型: $uses_cli"
        [ -n "$delay" ] && echo "   延遲: ${delay}秒"
        echo "   自動重試: $has_retry"
        echo "   禁用代理: $has_unset_proxy"
        echo ""
    else
        echo "❌ $name - 不存在"
        echo ""
    fi
done

echo "========================================"
echo "推薦使用的腳本："
echo "========================================"
echo ""
echo "1. 【推薦】v3.0 - 穩定版（API 直接調用）"
echo "   文件: /Users/ckchiu/Desktop/Project/id_globalping_auto_retry.sh"
echo "   特點: 自動重試、PARTIAL 二次檢測、節點詳細信息"
echo "   用法: ~/Desktop/Project/id_globalping_auto_retry.sh ~/Documents/domains.txt"
echo ""
echo "2. v4.0 - CLI 版本（需要配額）"
echo "   文件: /Users/ckchiu/Desktop/Project/id_globalping_cli.sh"
echo "   特點: 使用官方 CLI、更穩定"
echo "   限制: 需要 API 配額或註冊帳號"
echo "   用法: ~/Desktop/Project/id_globalping_cli.sh ~/Documents/domains.txt"
echo ""
echo "3. v2.0 - 改進版（已驗證可用）"
echo "   文件: /Users/ckchiu/id_globalping_multi_v2.sh"
echo "   特點: 完整狀態分類、CSV 導出"
echo "   用法: ~/id_globalping_multi_v2.sh ~/Documents/domains.txt"
echo ""
echo "========================================"
echo "當前 API 狀態："
echo "========================================"

# 檢查 API 配額
echo "正在檢查 Globalping API 配額..."
globalping limits 2>&1 || echo "⚠️  API 配額已用完或無法訪問"

echo ""
echo "========================================"
echo "建議："
echo "========================================"
echo "1. 如果 API 配額用完，等待 15-20 分鐘後重試"
echo "2. 或註冊免費帳號獲得更高配額："
echo "   https://dash.globalping.io?view=add-credits"
echo "3. 使用 v3.0 版本（最穩定、功能最完整）"
echo "========================================"
