@echo off
REM BIND DNS Container 停止腳本 (Windows)

echo 🛑 停止 BIND DNS 容器...

docker-compose down

echo ✅ BIND DNS 容器已停止
pause

