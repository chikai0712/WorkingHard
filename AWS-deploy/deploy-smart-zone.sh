#!/bin/bash

# 智能分區檢測系統 - 快速部署腳本

set -e

echo "🚀 部署智能分區檢測系統到 EC2"
echo "========================================"
echo ""

# 配置
KEY_FILE="$HOME/.ssh/globalping-checker-key.pem"
EC2_IP="54.238.247.106"
EC2_USER="ec2-user"
LOCAL_DIR="$HOME/Desktop/Project/GlobalpingChecker"

# 檢查密鑰文件
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ 找不到 SSH 密鑰: $KEY_FILE"
    exit 1
fi

echo "步驟 1：上傳智能分區檢測腳本..."
scp -i "$KEY_FILE" "$LOCAL_DIR/smart-zone-check.sh" "$EC2_USER@$EC2_IP:~/globalping-checker/"
echo "✅ smart-zone-check.sh 已上傳"
echo ""

echo "步驟 2：上傳狀態管理工具..."
scp -i "$KEY_FILE" "$LOCAL_DIR/domain-status-manager.sh" "$EC2_USER@$EC2_IP:~/globalping-checker/"
echo "✅ domain-status-manager.sh 已上傳"
echo ""

echo "步驟 3：設置執行權限..."
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" 'chmod +x ~/globalping-checker/*.sh'
echo "✅ 權限已設置"
echo ""

echo "步驟 4：檢查文件..."
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP" 'ls -lh ~/globalping-checker/*.sh'
echo ""

echo "========================================"
echo "🎉 部署完成！"
echo "========================================"
echo ""
echo "📋 下一步操作："
echo ""
echo "1. SSH 到 EC2："
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_IP"
echo ""
echo "2. 初始化系統（首次運行）："
echo "   cd ~/globalping-checker"
echo "   bash smart-zone-check.sh domains.txt"
echo ""
echo "3. 查看統計信息："
echo "   bash domain-status-manager.sh stats"
echo ""
echo "4. 更新 Crontab："
echo "   crontab -e"
echo "   # 替換為："
echo "   */10 * * * * cd ~/globalping-checker && bash smart-zone-check.sh domains.txt >> ~/smart-check.log 2>&1"
echo ""
echo "5. 監控運行："
echo "   tail -f ~/smart-check.log"
echo ""

read -p "是否要立即 SSH 到 EC2 進行初始化? (y/N): " answer
if [[ "$answer" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔗 連接到 EC2..."
    ssh -i "$KEY_FILE" "$EC2_USER@$EC2_IP"
fi
