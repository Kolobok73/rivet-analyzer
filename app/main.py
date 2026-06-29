"""Точка входа FastAPI. Запуск из корня: uvicorn app.main:app --reload"""
import logging
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI

from app import config
from app.api.routes import router
from app.db.database import init_db

# Логи: в файл logs/app.log (с ротацией) и дублируем в консоль.
LOG_DIR = config.BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
_fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# RotatingFileHandler: при 1 МБ заводит новый файл, хранит до 3 старых
# (app.log, app.log.1 ... .3). encoding utf-8 — чтобы кириллица читалась.
_file_handler = RotatingFileHandler(
    LOG_DIR / "app.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
)
_file_handler.setFormatter(_fmt)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(_fmt)

logging.basicConfig(level=logging.INFO, handlers=[_file_handler, _console_handler])
logger = logging.getLogger("rivet")

app = FastAPI(title="Rivet Analyzer", version="0.1.0")
init_db()                    # создать таблицы БД при старте
app.include_router(router)   # подключить эндпоинты из app/api/routes.py

logger.info("Приложение запущено. Устройство вычислений: %s", config.DEVICE)
