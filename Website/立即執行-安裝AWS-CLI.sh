#!/bin/bash

# AWS CLI 安裝指令（請在終端機中執行）

echo "🔧 AWS CLI 安裝步驟"
echo ""
echo "請在終端機中依序執行以下命令："
echo ""

echo "=== 步驟 1：修復 Homebrew 權限 ==="
echo "sudo chown -R \$(whoami) /opt/homebrew /Users/\$(whoami)/Library/Logs/Homebrew"
echo ""

echo "=== 步驟 2：安裝 AWS CLI ==="
echo "brew install awscli"
echo ""

echo "=== 步驟 3：驗證安裝 ==="
echo "aws --version"
echo ""

echo "=== 步驟 4：配置 AWS 憑證 ==="
echo "aws configure"
echo ""

echo "=== 步驟 5：執行設定腳本 ==="
echo "cd $(pwd)"
echo "./setup-aws-key.sh"
echo ""

echo "---"
echo "或直接複製以下命令一次執行："
echo "---"
echo ""
echo "sudo chown -R \$(whoami) /opt/homebrew /Users/\$(whoami)/Library/Logs/Homebrew && \\"
echo "brew install awscli && \\"
echo "aws --version && \\"
echo "echo '✅ 安裝完成！請執行：aws configure'"
