@echo off
REM DNS 測試腳本 (Windows)

echo 🧪 測試 BIND DNS 服務...
echo.

REM 檢查容器是否運行
docker ps | findstr bind9-dns >nul
if errorlevel 1 (
    echo ❌ 錯誤: BIND DNS 容器未運行
    echo    請先執行: start.bat
    pause
    exit /b 1
)

echo ✅ 容器運行中
echo.

REM 測試 DNS 查詢
echo 📡 測試 DNS 查詢...
nslookup example.com 127.0.0.1

echo.
echo 📝 最近的日誌（最後 10 行）:
docker-compose logs --tail=10 bind9

echo.
echo ✅ 測試完成
pause

