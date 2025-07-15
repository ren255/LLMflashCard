import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from pathlib import Path
from dotenv import load_dotenv

from app.config.logging_config import get_logger

# 環境変数の読み込み
load_dotenv()

# ログ設定
logger = get_logger(__name__)

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

# SQLAlchemy Base
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