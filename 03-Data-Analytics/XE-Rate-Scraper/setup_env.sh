#!/bin/bash

# XE.com 登入憑證設定腳本

echo "🔐 XE.com 登入憑證設定"
echo "===================="
echo ""

# 檢查是否已存在 .env 檔案
if [ -f ".env" ]; then
    echo "⚠️  .env 檔案已存在"
    read -p "是否要覆蓋現有的 .env 檔案？(y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 已取消"
        exit 0
    fi
fi

# 讀取 Email
echo "請輸入您的 XE.com Email:"
read -r XE_EMAIL

if [ -z "$XE_EMAIL" ]; then
    echo "❌ Email 不能為空"
    exit 1
fi

# 讀取 Password（隱藏輸入）
echo "請輸入您的 XE.com 密碼:"
read -rs XE_PASSWORD

if [ -z "$XE_PASSWORD" ]; then
    echo "❌ 密碼不能為空"
    exit 1
fi

echo ""

# 確認
echo "📧 Email: ${XE_EMAIL:0:3}***"
echo "🔐 密碼: ****"
read -p "確認以上資訊正確？(y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 0
fi

# 創建 .env 檔案
cat > .env << EOF
# XE.com 登入憑證
# 此檔案包含敏感資訊，請勿提交到版本控制
XE_EMAIL=$XE_EMAIL
XE_PASSWORD=$XE_PASSWORD
EOF

echo ""
echo "✅ .env 檔案已創建！"
echo ""
echo "💡 提示:"
echo "   - .env 檔案已在 .gitignore 中，不會被提交到版本控制"
echo "   - 現在可以執行 ./run.sh 開始抓取匯率數據"
echo ""

