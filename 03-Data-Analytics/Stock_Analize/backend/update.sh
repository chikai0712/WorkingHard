#!/bin/bash

# 手動更新資料腳本（後端目錄版本）

echo "🚀 開始手動更新資料..."
echo ""

# 檢查是否在 backend 目錄
if [ ! -f "main.py" ] || [ ! -d "scripts" ]; then
    echo "❌ 錯誤: 請在 backend 目錄中執行此腳本"
    echo "   執行: cd backend && ./update.sh"
    exit 1
fi

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "❌ 錯誤: 未找到虛擬環境"
    echo "   請先執行以下命令建立虛擬環境:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# 啟動虛擬環境
echo "🔧 啟動虛擬環境..."
source venv/bin/activate

# 檢查虛擬環境是否成功啟動
if [ $? -ne 0 ]; then
    echo "❌ 錯誤: 無法啟動虛擬環境"
    exit 1
fi

# 確認 Python 可用（虛擬環境中的 python 應該在 PATH 最前面）
if ! command -v python &> /dev/null; then
    echo "⚠️  警告: 找不到 python 命令，嘗試使用 python3..."
    if ! command -v python3 &> /dev/null; then
        echo "❌ 錯誤: 找不到 python 或 python3 命令"
        deactivate
        exit 1
    else
        PYTHON_CMD=python3
    fi
else
    PYTHON_CMD=python
fi

# 確認 Python 版本和路徑
echo "🐍 Python 版本: $($PYTHON_CMD --version)"
echo "📁 Python 路徑: $(which $PYTHON_CMD)"
echo ""

# 執行更新腳本
echo "📊 更新股票和期貨資料..."
$PYTHON_CMD scripts/update_all.py

# 保存退出碼
UPDATE_EXIT_CODE=$?

# 退出虛擬環境
deactivate

echo ""

# 根據退出碼顯示結果
if [ $UPDATE_EXIT_CODE -eq 0 ]; then
    echo "✅ 更新完成！"
else
    echo "⚠️  更新過程中有錯誤，請檢查上方訊息"
fi

exit $UPDATE_EXIT_CODE

