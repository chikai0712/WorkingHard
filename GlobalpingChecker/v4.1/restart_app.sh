#!/bin/bash
# 重启应用脚本

echo "🔄 重启 GlobalpingChecker 应用..."
echo

# 杀死现有进程
echo "1️⃣  杀死现有进程..."
pkill -f "uvicorn app.main" 2>/dev/null
sleep 2

# 进入项目目录
cd /Users/ckchiu/Desktop/Project/GlobalpingChecker/v4.1

# 启动应用
echo "2️⃣  启动应用..."
source venv/bin/activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8766 --reload &

sleep 3

echo "✅ 应用已启动"
echo "🌐 访问地址: http://127.0.0.1:8766"
