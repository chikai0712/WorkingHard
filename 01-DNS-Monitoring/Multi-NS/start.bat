@echo off
REM BIND DNS Container 啟動腳本 (Windows)

echo 🚀 啟動 BIND DNS 容器...

REM 檢查 Docker 是否運行
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ 錯誤: Docker 未運行，請先啟動 Docker Desktop
    pause
    exit /b 1
)

REM 檢查必要目錄
echo 📁 檢查必要目錄...
if not exist bind\cache mkdir bind\cache
if not exist bind\logs mkdir bind\logs
if not exist bind\zones mkdir bind\zones
if not exist bind\config mkdir bind\config

REM 啟動容器
echo 🐳 啟動 Docker 容器...
docker-compose up -d

REM 等待服務啟動
echo ⏳ 等待 BIND DNS 服務啟動...
timeout /t 3 /nobreak >nul

REM 檢查容器狀態
docker ps | findstr bind9-dns >nul
if errorlevel 1 (
    echo ❌ 容器啟動失敗，請檢查日誌:
    docker-compose logs bind9
    pause
    exit /b 1
) else (
    echo ✅ BIND DNS 容器已啟動
    echo.
    echo 📊 容器狀態:
    docker ps | findstr bind9-dns
    echo.
    echo 📝 查看日誌: docker-compose logs -f bind9
    echo 🛑 停止服務: docker-compose down
    echo 🔄 重啟服務: docker-compose restart bind9
    echo.
    echo 🧪 測試 DNS:
    echo    nslookup example.com 127.0.0.1
)

pause






 
