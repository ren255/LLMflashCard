"""Base model configuration."""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Optional
import os

# Base class for all models
Base = declarative_base()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./app.db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv('SQL_ECHO', 'false').lower() == 'true'
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """Drop all tables."""
    Base.metadata.drop_all(bind=engine)