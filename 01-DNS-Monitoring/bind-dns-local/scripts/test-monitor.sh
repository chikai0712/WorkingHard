#!/bin/bash
# 測試 dns-query-monitor.sh 的功能

echo "=== DNS 查詢監控腳本測試 ==="
echo ""

# 測試 1: 語法檢查
echo "測試 1: 語法檢查"
if bash -n dns-query-monitor.sh; then
    echo "✅ 語法正確"
else
    echo "❌ 語法錯誤"
    exit 1
fi
echo ""

# 測試 2: 幫助功能
echo "測試 2: 幫助功能"
if bash dns-query-monitor.sh --help | grep -q "用法"; then
    echo "✅ 幫助功能正常"
else
    echo "❌ 幫助功能異常"
    exit 1
fi
echo ""

# 測試 3: 檢查必要命令
echo "測試 3: 檢查必要命令"
commands=("dig" "bc" "date")
all_ok=true
for cmd in "${commands[@]}"; do
    if command -v "$cmd" &> /dev/null; then
        echo "  ✅ $cmd 已安裝"
    else
        echo "  ❌ $cmd 未安裝"
        all_ok=false
    fi
done

if [ "$all_ok" = false ]; then
    echo ""
    echo "⚠️  部分命令未安裝，腳本可能無法正常運行"
    echo "請安裝: brew install bind coreutils"
fi
echo ""

# 測試 4: 檢查腳本結構
echo "測試 4: 檢查腳本結構"
required_functions=("query_dns_direct" "query_dns_trace" "monitor_direct" "monitor_trace" "cleanup")
for func in "${required_functions[@]}"; do
    if grep -q "^${func}()" dns-query-monitor.sh || grep -q "^${func} ()" dns-query-monitor.sh; then
        echo "  ✅ 函數 $func 存在"
    else
        echo "  ❌ 函數 $func 不存在"
    fi
done
echo ""

# 測試 5: 檢查配置
echo "測試 5: 檢查配置"
if grep -q "AWS_NS=" dns-query-monitor.sh; then
    echo "  ✅ AWS NS 配置存在"
fi
if grep -q "GOOGLE_NS=" dns-query-monitor.sh; then
    echo "  ✅ Google NS 配置存在"
fi
echo ""

echo "=== 測試完成 ==="
echo ""
echo "📝 使用說明："
echo "  直接查詢模式: bash dns-query-monitor.sh 1 www.clouddeployment168.site"
echo "  追蹤模式:     bash dns-query-monitor.sh --trace 5 www.clouddeployment168.site"
echo ""
echo "⚠️  注意: 如果遇到 dig 權限問題，請嘗試："
echo "  1. 使用 nslookup 替代（腳本會自動降級）"
echo "  2. 或執行: sudo bash dns-query-monitor.sh ..."

