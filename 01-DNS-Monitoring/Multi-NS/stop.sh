#!/bin/bash

# BIND DNS Container 停止腳本
# 支持 macOS/Linux

set -e

echo "🛑 停止 BIND DNS 容器..."

# 停止並移除容器
docker-compose down

echo "✅ BIND DNS 容器已停止"

