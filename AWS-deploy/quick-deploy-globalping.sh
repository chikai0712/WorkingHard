#!/bin/bash

# 快速部署腳本 - 自動處理代理問題

# 禁用所有代理
export http_proxy=""
export https_proxy=""
export HTTP_PROXY=""
export HTTPS_PROXY=""
export all_proxy=""
export ALL_PROXY=""
export no_proxy="*"
export NO_PROXY="*"

echo "🚀 快速部署 Globalping Checker"
echo ""
echo "⚠️  注意：此腳本會自動禁用代理"
echo ""

# 檢查 AWS CLI
echo "檢查 AWS CLI..."
if ! aws sts get-caller-identity --no-cli-pager >/dev/null 2>&1; then
    echo "❌ AWS CLI 無法連線"
    echo ""
    echo "請在新的終端視窗執行以下命令："
    echo ""
    echo "  export http_proxy=\"\""
    echo "  export https_proxy=\"\""
    echo "  export all_proxy=\"\""
    echo "  aws sts get-caller-identity"
    echo ""
    exit 1
fi

echo "✅ AWS CLI 正常"
echo ""

# 執行部署
cd "$(dirname "$0")"
./deploy-globalping-checker.sh
