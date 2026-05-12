#!/bin/bash

# BIND DNS Web UI 启动脚本

echo "🚀 启动 BIND DNS Web UI..."

# 检查是否已安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
fi

# 启动服务
echo "🌐 启动 Web 服务器..."
npm start

