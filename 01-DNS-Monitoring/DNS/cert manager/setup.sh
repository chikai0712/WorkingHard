#!/bin/bash

# SSL 憑證管理器快速設定腳本

set -e

echo "=========================================="
echo "SSL 憑證管理器 - 快速設定"
echo "=========================================="
echo ""

# 檢查 Python 版本
echo "檢查 Python 版本..."
if ! command -v python3 &> /dev/null; then
    echo "錯誤: 未找到 python3，請先安裝 Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Python 版本: $(python3 --version)"
echo ""

# 檢查並安裝依賴
echo "檢查依賴套件..."
if [ ! -f "requirements.txt" ]; then
    echo "錯誤: 找不到 requirements.txt"
    exit 1
fi

echo "安裝 Python 依賴套件..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
echo "✓ 依賴套件安裝完成"
echo ""

# 檢查 Certbot
echo "檢查 Certbot..."
if ! command -v certbot &> /dev/null; then
    echo "警告: 未找到 certbot"
    echo "請安裝 certbot:"
    echo "  Ubuntu/Debian: sudo apt-get install certbot"
    echo "  macOS: brew install certbot"
    echo "  或使用 pip: pip install certbot"
    echo ""
else
    echo "✓ Certbot 已安裝: $(certbot --version)"
    echo ""
fi

# 建立配置檔案
if [ ! -f "config.json" ]; then
    if [ -f "config.example.json" ]; then
        echo "建立配置檔案..."
        cp config.example.json config.json
        echo "✓ 已建立 config.json（從 config.example.json）"
        echo "請編輯 config.json 並填入你的憑證資訊"
        echo ""
    else
        echo "警告: 找不到 config.example.json"
    fi
else
    echo "✓ config.json 已存在"
    echo ""
fi

# 建立日誌目錄
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo "✓ 已建立 logs 目錄"
    echo ""
fi

echo "=========================================="
echo "設定完成！"
echo "=========================================="
echo ""
echo "下一步："
echo "1. 編輯 config.json 並填入你的憑證資訊"
echo "2. 執行測試: python3 test_cert_manager.py"
echo "3. 執行檢查: python3 cert_manager.py --config config.json"
echo "4. 設定 Cron 定期執行（建議每天執行一次）"
echo ""
echo "Cron 範例（每天凌晨 2 點執行）："
echo "  0 2 * * * cd $(pwd) && python3 cert_manager.py --config config.json >> logs/cert_manager.log 2>&1"
echo ""

