#!/bin/bash

# 快速安裝 boto3 並檢查 AWS 狀態

echo "🔧 安裝 boto3..."
echo ""

# 嘗試使用用戶安裝
if /usr/bin/python3 -m pip install --user boto3 --quiet 2>/dev/null; then
    echo "✅ boto3 安裝成功"
else
    echo "⚠️  使用 pip3 安裝..."
    pip3 install --user boto3 --quiet 2>/dev/null || {
        echo "❌ 安裝失敗"
        echo ""
        echo "請手動安裝："
        echo "  pip3 install --user boto3"
        echo ""
        echo "或使用系統終端執行此腳本"
        exit 1
    }
fi

echo ""
echo "🔍 執行 AWS 狀態檢查..."
echo ""

# 執行檢查
python3 "$(dirname "$0")/check-aws-boto3.py"
