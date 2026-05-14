#!/bin/bash

# XE.com 匯率抓取工具 - 快速啟動腳本

echo "🌐 XE.com 匯率抓取工具"
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

# 檢查登入憑證
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  未找到 .env 檔案"
    echo "💡 提示: 您可以："
    echo "   1. 創建 .env 檔案（從 .env.example 複製）"
    echo "   2. 使用環境變數: export XE_EMAIL=xxx && export XE_PASSWORD=xxx"
    echo "   3. 使用命令列參數: ./run.sh --email xxx --password xxx"
    echo ""
    read -p "是否要現在創建 .env 檔案？(y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "✅ 已創建 .env 檔案，請編輯並填入您的帳號資訊"
            echo "   使用編輯器打開: open -e .env 或 nano .env"
            exit 0
        else
            echo "📝 創建 .env 檔案..."
            cat > .env << 'EOF'
# XE.com 登入憑證
XE_EMAIL=your-email@example.com
XE_PASSWORD=your-password
EOF
            echo "✅ 已創建 .env 檔案，請編輯並填入您的帳號資訊"
            echo "   使用編輯器打開: open -e .env 或 nano .env"
            exit 0
        fi
    fi
fi

# 檢查環境變數或命令列參數是否提供憑證
if [ -z "$XE_EMAIL" ] && [ -z "$XE_PASSWORD" ] && [[ ! "$*" =~ --email ]] && [[ ! "$*" =~ --password ]]; then
    # 載入 .env 檔案（如果存在）
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
    fi
fi

echo ""
echo "🚀 開始抓取匯率數據..."
echo ""

# 執行抓取腳本
python3 xe_scraper.py "$@"

echo ""
echo "✅ 完成！"

