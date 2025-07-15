from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_logger, DATABASE_URL, SQLALCHEMY_ECHO

logger = get_logger(__name__)

Base = declarative_base()

# Database engine
engine = create_engine(
    DATABASE_URL,
    echo=SQLALCHEMY_ECHO,
    # SQLiteの場合のconnection pool設定
    pool_pre_ping=True,
    pool_recycle=300,
)

# Session factory
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False
)


def get_db():
    """
    データベースセッションの取得
    依存性注入で使用
    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_engine():
    """
    データベースエンジンの取得
    """
    return engine


def get_session():
    """
    データベースセッションの取得（直接使用）
    """
    return SessionLocal()


# 初期化時にログ出力
logger.info(f"Database configured with URL: {DATABASE_URL}")
logger.info(f"SQLAlchemy echo: {SQLALCHEMY_ECHO}")
