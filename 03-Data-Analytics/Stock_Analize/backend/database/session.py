"""
資料庫連線管理
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stock_data.db")

# 建立資料庫引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=os.getenv("DEBUG", "False").lower() == "true"
)

# 建立 Session 類別
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """取得資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化資料庫（建立所有表）"""
    from database.models import Base
    from database.models_futures import Base as FuturesBase
    
    # 建立所有表
    Base.metadata.create_all(bind=engine)
    FuturesBase.metadata.create_all(bind=engine)

