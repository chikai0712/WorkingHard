#!/bin/bash

# BIND DNS Container 啟動腳本
# 支持 macOS/Linux

set -e

echo "🚀 啟動 BIND DNS 容器..."

# 檢查 Docker 是否運行
if ! docker info > /dev/null 2>&1; then
    echo "❌ 錯誤: Docker 未運行，請先啟動 Docker"
    exit 1
fi

# 檢查必要目錄
echo "📁 檢查必要目錄..."
mkdir -p bind/cache bind/logs bind/zones bind/config

# 設置目錄權限（Linux 需要）
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "🔐 設置目錄權限（Linux）..."
    sudo chown -R 101:101 bind/cache bind/logs bind/zones 2>/dev/null || true
fi

# 啟動容器
echo "🐳 啟動 Docker 容器..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待 BIND DNS 服務啟動..."
sleep 3

# 檢查容器狀態
if docker ps | grep -q bind9-dns; then
    echo "✅ BIND DNS 容器已啟動"
    echo ""
    echo "📊 容器狀態:"
    docker ps | grep bind9-dns
    echo ""
    echo "📝 查看日誌: docker-compose logs -f bind9"
    echo "🛑 停止服務: docker-compose down"
    echo "🔄 重啟服務: docker-compose restart bind9"
    echo ""
    echo "🧪 測試 DNS:"
    echo "   dig @127.0.0.1 example.com"
    echo "   dig @127.0.0.1 -x 192.0.2.1"
else
    echo "❌ 容器啟動失敗，請檢查日誌:"
    docker-compose logs bind9
    exit 1
fi

