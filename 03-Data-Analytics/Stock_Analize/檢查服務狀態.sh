#!/bin/bash

echo "🔍 檢查服務狀態..."
echo ""

# 檢查前端
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ 前端服務: http://localhost:5173 (運行中)"
else
    echo "❌ 前端服務: http://localhost:5173 (未運行)"
fi

# 檢查後端
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ 後端服務: http://localhost:8000 (運行中)"
else
    echo "❌ 後端服務: http://localhost:8000 (未運行)"
fi

echo ""
echo "如需啟動服務，請執行："
echo "  後端: cd backend && python main.py"
echo "  前端: cd frontend && npm run dev"

