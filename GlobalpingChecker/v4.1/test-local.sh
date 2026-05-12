#!/bin/bash

# 本機快速測試腳本
# 使用最少數據驗證所有功能

set -e

echo "🧪 GlobalpingChecker V4.1 - 本機測試"
echo "===================================="
echo ""

# 檢查目錄
if [ ! -f "app/main.py" ]; then
    echo "❌ 請在 v4.1 目錄下執行此腳本"
    exit 1
fi

# 1. 測試數據庫
echo "1️⃣ 測試數據庫連接..."
if python test_db.py > /dev/null 2>&1; then
    echo "   ✅ 數據庫連接正常"
else
    echo "   ❌ 數據庫連接失敗"
    exit 1
fi

# 2. 檢查虛擬環境
echo "2️⃣ 檢查虛擬環境..."
if [ -d "venv" ]; then
    echo "   ✅ 虛擬環境存在"
else
    echo "   ⚠️  虛擬環境不存在，正在創建..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# 3. 檢查配置文件
echo "3️⃣ 檢查配置文件..."
if [ -f ".env" ]; then
    echo "   ✅ .env 文件存在"
else
    echo "   ⚠️  .env 文件不存在，從示例創建..."
    cp .env.example .env
fi

# 4. 檢查域名文件
echo "4️⃣ 檢查域名文件..."
if [ -f "domains.txt" ]; then
    DOMAIN_COUNT=$(wc -l < domains.txt)
    echo "   ✅ domains.txt 存在 ($DOMAIN_COUNT 個域名)"
else
    echo "   ⚠️  domains.txt 不存在"
fi

# 5. 創建測試域名文件
echo "5️⃣ 創建測試域名文件..."
cat > test_5_domains.txt << 'EOF'
google.com
facebook.com
twitter.com
github.com
stackoverflow.com
EOF
echo "   ✅ 已創建 test_5_domains.txt (5 個域名)"

# 6. 檢查數據庫數據
echo "6️⃣ 檢查數據庫數據..."
source venv/bin/activate
python << 'PYEOF'
from app.database import SessionLocal
from app.models import Domain, TestBatch, DomainResult

db = SessionLocal()
domain_count = db.query(Domain).count()
batch_count = db.query(TestBatch).count()
result_count = db.query(DomainResult).count()
db.close()

print(f"   📊 域名: {domain_count} 個")
print(f"   📊 批次: {batch_count} 個")
print(f"   📊 結果: {result_count} 個")

if batch_count == 0:
    print("   ⚠️  沒有批次數據，需要執行檢測")
else:
    print("   ✅ 有歷史數據")
PYEOF

echo ""
echo "===================================="
echo "✅ 本機測試完成！"
echo ""
echo "📝 下一步："
echo "   1. 啟動服務: ./start.sh"
echo "   2. 訪問: http://127.0.0.1:9002"
echo "   3. 測試所有功能"
echo "   4. 確認無誤後部署: ./deploy-to-aws.sh"
echo ""
