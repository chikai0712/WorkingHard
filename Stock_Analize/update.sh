#!/bin/bash

# 手動更新資料腳本

echo "🚀 開始手動更新資料..."
echo ""

# 獲取腳本所在目錄
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

cd backend

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "❌ 錯誤: 未找到虛擬環境，請先執行 ./start.sh"
    exit 1
fi

# 啟動虛擬環境
echo "🔧 啟動虛擬環境..."
source venv/bin/activate

# 確認 Python 版本
echo "🐍 Python 版本: $(python --version)"
echo ""

# 執行更新腳本
echo "📊 更新股票和期貨資料..."
python scripts/update_all.py

# 退出虛擬環境
deactivate

cd ..

echo ""
echo "✅ 更新完成！"

