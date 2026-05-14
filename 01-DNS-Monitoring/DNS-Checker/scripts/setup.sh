#!/bin/bash
# DNS 檢查工具安裝腳本

set -e

echo "🚀 開始安裝 DNS 檢查工具..."

# 檢查 Python 版本
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 未安裝"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python 版本: $PYTHON_VERSION"

# 創建虛擬環境
if [ ! -d "venv" ]; then
    echo "📦 創建虛擬環境..."
    python3 -m venv venv
fi

# 激活虛擬環境
echo "🔧 激活虛擬環境..."
source venv/bin/activate

# 安裝依賴
echo "📥 安裝依賴..."
pip install --upgrade pip
pip install -r requirements.txt

# 創建默認白名單目錄
DEFAULT_WHITELIST_DIR="/opt/dnsapi"
if [ ! -d "$DEFAULT_WHITELIST_DIR" ]; then
    echo "📁 創建白名單目錄: $DEFAULT_WHITELIST_DIR"
    sudo mkdir -p "$DEFAULT_WHITELIST_DIR"
    sudo chmod 755 "$DEFAULT_WHITELIST_DIR"
fi

# 複製示例白名單
if [ ! -f "$DEFAULT_WHITELIST_DIR/whitelist.txt" ]; then
    echo "📋 複製示例白名單..."
    sudo cp configs/whitelist.txt "$DEFAULT_WHITELIST_DIR/whitelist.txt"
    sudo chmod 644 "$DEFAULT_WHITELIST_DIR/whitelist.txt"
fi

# 設置執行權限
chmod +x src/dns_checker.py
chmod +x src/dns_checker_v2.py

echo "✅ 安裝完成！"
echo ""
echo "使用方式："
echo "  source venv/bin/activate"
echo "  python src/dns_checker_v2.py -R example.com -S 8.8.8.8"

