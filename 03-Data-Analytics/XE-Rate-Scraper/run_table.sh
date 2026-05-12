#!/bin/bash

# XE.com 匯率表格爬蟲 - 快速啟動腳本（無需登入）

echo "🌐 XE.com 匯率表格爬蟲"
echo "===================="
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 錯誤: 未找到 Python3"
    exit 1
fi

# 檢查依賴
if [ ! -d "venv" ]; then
    echo "📦 創建虛擬環境..."
    python3 -m venv venv
fi

echo "📦 啟動虛擬環境並安裝依賴..."
source venv/bin/activate
pip install -q -r requirements.txt

echo ""
echo "🚀 開始爬取匯率數據..."
echo ""
echo "💡 提示:"
echo "   - 單日爬取: ./run_table.sh --date 2025-12-28"
echo "   - 30天平均: ./run_table.sh --days 30"
echo ""

# 執行爬蟲腳本
python3 xe_table_scraper.py "$@"

echo ""
echo "✅ 完成！"

