"""
GlobalpingChecker V5 - Database
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from .config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """建立所有資料表"""
    Base.metadata.create_all(bind=engine)
    # 若 node_pool.asn 為舊版 INTEGER 型別，自動遷移為 VARCHAR(50)
    try:
        with engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text(
                "SELECT data_type FROM information_schema.columns "
                "WHERE table_name='node_pool' AND column_name='asn'"
            )).fetchone()
            if result and result[0].lower() in ("integer", "int4", "bigint"):
                conn.execute(text(
                    "ALTER TABLE node_pool ALTER COLUMN asn TYPE VARCHAR(50) USING asn::text"
                ))
                conn.commit()
                print("✅ node_pool.asn 已從 INTEGER 遷移為 VARCHAR(50)")
    except Exception:
        pass
    print("✅ V5 資料庫初始化完成")


def get_db():
    """FastAPI dependency: 取得 DB Session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """非 dependency 用法，手動管理 session"""
    return SessionLocal()
