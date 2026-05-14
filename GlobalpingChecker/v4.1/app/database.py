"""
GlobalpingChecker V4.1 - Database Connection
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .config import get_settings
from .models import Base

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化資料庫"""
    # 導入所有模型以確保它們被註冊
    from .node_pool import NodePool  # 導入 NodePool 模型
    
    Base.metadata.create_all(bind=engine)
    print("✅ PostgreSQL 資料庫初始化完成")


def get_db():
    """獲取資料庫 Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """獲取資料庫 Session（非生成器版本）"""
    return SessionLocal()
