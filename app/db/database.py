"""Подключение к БД, сессии и создание таблиц (SQLAlchemy)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app import config

engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


def init_db():
    """Создать таблицы, если их ещё нет (вызывается при старте)."""
    from app.db import models  # noqa: F401 — чтобы модели зарегистрировались в Base
    Base.metadata.create_all(bind=engine)
