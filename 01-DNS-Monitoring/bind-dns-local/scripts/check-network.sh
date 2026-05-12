#!/usr/bin/env bash
# 確認 BIND 容器能否上網：ping 外網 IP、dig 查外部網域

set -e
CONTAINER="${1:-bind-dns-local}"

echo "容器名稱: $CONTAINER"
echo ""

echo "1. 測試網路（ping 8.8.8.8）..."
if docker exec "$CONTAINER" ping -c 4 8.8.8.8 2>/dev/null; then
    echo "[OK] ping 8.8.8.8 成功"
else
    echo "[!] ping 可能未安裝或失敗，改以 dig 測試連線..."
    if docker exec "$CONTAINER" dig @8.8.8.8 google.com +short +time=3 2>/dev/null | grep -q .; then
        echo "[OK] dig @8.8.8.8 google.com 有回應，網路通"
    else
        echo "[FAIL] 無法連線 8.8.8.8"
        exit 1
    fi
fi
echo ""

echo "2. 測試解析（dig @8.8.8.8 google.com）..."
docker exec "$CONTAINER" dig @8.8.8.8 google.com +short
echo "[OK] 外部解析正常"
echo ""
echo "容器可上網、可對外解析。"
