#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
股票資訊儀表板 - 後端主程式
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

from api import stocks, prices, indicators, dashboard, futures, options, margin
from scheduler.tasks import setup_scheduler
from database.session import init_db

# 載入環境變數
load_dotenv()

# 應用程式初始化
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動時執行
    print("🚀 啟動股票資訊儀表板後端服務...")
    
    # 初始化資料庫
    init_db()
    print("✅ 資料庫初始化完成")
    
    # 啟動定時任務
    if os.getenv("SCHEDULER_ENABLED", "True").lower() == "true":
        scheduler = setup_scheduler()
        scheduler.start()
        print("✅ 定時任務已啟動")
    
    yield
    
    # 關閉時執行
    print("🛑 關閉服務...")
    if os.getenv("SCHEDULER_ENABLED", "True").lower() == "true":
        scheduler.shutdown()
        print("✅ 定時任務已關閉")

# 建立 FastAPI 應用程式
app = FastAPI(
    title="股票資訊儀表板 API",
    description="自動化股票資訊抓取與顯示系統",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 設定
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(stocks.router, prefix="/api/stocks", tags=["股票"])
app.include_router(prices.router, prefix="/api/stocks", tags=["價格"])
app.include_router(indicators.router, prefix="/api/stocks", tags=["技術指標"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["儀表板"])
app.include_router(futures.router, prefix="/api/futures", tags=["期貨"])
app.include_router(options.router, prefix="/api/futures/options", tags=["選擇權"])
app.include_router(margin.router, prefix="/api/futures", tags=["融資融券"])

# 根路徑
@app.get("/")
async def root():
    return {
        "message": "股票資訊儀表板 API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# 健康檢查
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)

