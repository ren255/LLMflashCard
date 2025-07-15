# not using?
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL","NONE")

# SQLAlchemy configuration
SQLALCHEMY_DATABASE_URL = DATABASE_URL
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"

# Alembic configuration
ALEMBIC_CONFIG = str(BASE_DIR / "alembic.ini")