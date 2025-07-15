"""
Configuration module for application settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

# SQLAlchemy configuration
SQLALCHEMY_DATABASE_URL = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

# Alembic configuration
ALEMBIC_CONFIG = str(BASE_DIR / "alembic.ini")

# Application configuration
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Export all configuration
__all__ = [
    'BASE_DIR',
    'DATABASE_URL',
    'SQLALCHEMY_DATABASE_URL',
    'SQLALCHEMY_TRACK_MODIFICATIONS',
    'SQLALCHEMY_ECHO',
    'ALEMBIC_CONFIG',
    'DEBUG',
    'SECRET_KEY',
    'LOG_LEVEL'
]