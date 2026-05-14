#!/bin/bash

# 測試哪個密鑰可以連接到 Globalping EC2

IP="54.238.247.106"
KEYS=(
    "dns-test-key.pem"
    "globalping-checker-key.pem"
    "my-ec2-key.pem"
    "pokemon-game-key.pem"
)

echo "🔍 測試 SSH 密鑰連線到 $IP"
echo "========================================"
echo ""

for key in "${KEYS[@]}"; do
    echo "測試: $key"
    
    if ssh -i ~/.ssh/$key -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
        ec2-user@$IP "echo 'Success'" 2>/dev/null; then
        echo "✅ 成功！使用此密鑰: $key"
        echo ""
        echo "上傳命令："
        echo "  scp -i ~/.ssh/$key <文件> ec2-user@$IP:~/"
        echo ""
        echo "SSH 命令："
        echo "  ssh -i ~/.ssh/$key ec2-user@$IP"
        exit 0
    else
        echo "❌ 失敗"
    fi
    echo ""
done

echo "⚠️  沒有找到可用的密鑰"
echo ""
echo "請檢查："
echo "1. 實例是否正在運行"
echo "2. 安全組是否允許 SSH"
echo "3. 是否需要其他密鑰"
