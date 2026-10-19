"""SQLAlchemy engine + session. DB file lives at backend/aura_ems.db by default."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_ROOT / "aura_ems.db"


def _resolve_database_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    DEFAULT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Absolute SQLite path so cwd (uvicorn vs scripts) cannot create a second empty DB
    return f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"


DATABASE_URL = _resolve_database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """SQLAlchemy 2.0 declarative base used by all ORM models."""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
