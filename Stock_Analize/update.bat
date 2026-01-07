@echo off
REM 手動更新資料腳本 (Windows)

echo 🚀 開始手動更新資料...
echo.

cd backend

REM 檢查虛擬環境
if not exist venv (
    echo ❌ 錯誤: 未找到虛擬環境，請先執行 start.bat
    pause
    exit /b 1
)

REM 啟動虛擬環境並執行更新
call venv\Scripts\activate.bat

echo 📊 更新股票和期貨資料...
python scripts\update_all.py

deactivate

cd ..

echo.
echo ✅ 更新完成！
pause

