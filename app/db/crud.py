"""Операции с БД: сохранить результат анализа и прочитать историю."""
from app.db.database import SessionLocal
from app.db.models import Analysis


def save_analysis(filename: str, file_type: str, summary: dict) -> None:
    db = SessionLocal()
    try:
        record = Analysis(
            filename=filename,
            file_type=file_type,
            total=summary["total"],
            ok_count=summary["ok"],
            defect_count=summary["defect"],
            defect_percent=summary["defect_percent"],
            avg_confidence=summary["avg_confidence"],
            edge_ignored=summary.get("edge_ignored", 0),
        )
        db.add(record)
        db.commit()
    finally:
        db.close()


def get_recent(limit: int = 50) -> list[Analysis]:
    db = SessionLocal()
    try:
        return (
            db.query(Analysis)
            .order_by(Analysis.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()
