#!/bin/bash

# 查看 EC2 上的檢測腳本配置

echo "🔍 檢查 EC2 上的檢測腳本配置"
echo "========================================"
echo ""

KEY_FILE="$HOME/.ssh/globalping-checker-key.pem"
EC2_IP="54.238.247.106"

# 1. 查看 smart-check.sh 的關鍵配置
echo "1️⃣  smart-check.sh 配置："
echo ""
ssh -i "$KEY_FILE" ec2-user@$EC2_IP 'grep -E "API_TOKEN|QUOTA_THRESHOLD|DOMAINS_FILE" ~/globalping-checker/smart-check.sh | head -5'

echo ""
echo "========================================"
echo ""

# 2. 查看 auto-quota-check.sh 的關鍵配置
echo "2️⃣  auto-quota-check.sh 配置："
echo ""
ssh -i "$KEY_FILE" ec2-user@$EC2_IP 'grep -E "API_TOKEN|QUOTA_THRESHOLD|CHECK_INTERVAL" ~/globalping-checker/auto-quota-check.sh | head -5'

echo ""
echo "========================================"
echo ""

# 3. 查看 Telegram 配置
echo "3️⃣  Telegram 配置："
echo ""
ssh -i "$KEY_FILE" ec2-user@$EC2_IP 'cat ~/globalping-checker/telegram-config.env'

echo ""
echo "========================================"
echo ""

# 4. 查看 Crontab
echo "4️⃣  Crontab 定時任務："
echo ""
ssh -i "$KEY_FILE" ec2-user@$EC2_IP 'crontab -l'

echo ""
echo "========================================"
echo ""

# 5. 查看文件列表
echo "5️⃣  檢測腳本文件列表："
echo ""
ssh -i "$KEY_FILE" ec2-user@$EC2_IP 'ls -lh ~/globalping-checker/'

echo ""
echo "========================================"
echo "✅ 檢查完成"
echo "========================================"
