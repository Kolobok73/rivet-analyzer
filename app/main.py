"""Точка входа FastAPI. Запуск из корня: uvicorn app.main:app --reload"""
from fastapi import FastAPI

from app.api.routes import router
from app.db.database import init_db

app = FastAPI(title="Rivet Analyzer", version="0.1.0")
init_db()                    # создать таблицы БД при старте
app.include_router(router)   # подключить все эндпоинты из app/api/routes.py
