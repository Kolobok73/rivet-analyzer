"""Таблицы БД (SQLAlchemy-модели)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.db.database import Base


class Analysis(Base):
    """Результат анализа одного файла (одна запись истории)."""

    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # "image" или "video"

    total = Column(Integer, nullable=False)
    ok_count = Column(Integer, nullable=False)
    defect_count = Column(Integer, nullable=False)
    defect_percent = Column(Float, nullable=False)
    avg_confidence = Column(Float, nullable=False)
    edge_ignored = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
