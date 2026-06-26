"""Единое место для всех настроек проекта: пути, лимиты, параметры модели, БД."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Пути проекта
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
STORAGE_DIR = BASE_DIR / "storage"

# Лимиты загрузки (до 4 фото и до 4 видео за раз)
MAX_IMAGES = 4
MAX_VIDEOS = 4

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

# Модель YOLO
MODEL_WEIGHTS_PATH = MODELS_DIR / "best.pt"

# Авторитетный источник имён классов — сама модель (model.names).
# Здесь зеркало для справки; порядок сверен с best.pt.
CLASS_NAMES = {
    0: "rivet_defect",
    1: "rivet_ok",
}

# Какой класс считается браком (сравниваем по имени, не по id).
DEFECT_CLASS_NAME = "rivet_defect"

# Заклёпки, чья рамка ближе этой доли к краю кадра, считаем обрезанными
# и не учитываем в проценте брака.
EDGE_MARGIN_RATIO = 0.005

# Порог уверенности: детекции слабее отбрасываем (баланс precision/recall).
CONFIDENCE_THRESHOLD = 0.55

# Порог склейки рамок (NMS IoU): ниже -> агрессивнее убирает дубли.
NMS_IOU_THRESHOLD = 0.5

# Видео: берём один кадр раз в N секунд, анализируем не дольше N секунд.
VIDEO_SAMPLE_SECONDS = 0.5
MAX_VIDEO_SECONDS = 10

# База данных (PostgreSQL). Секреты — из .env (не коммитится).
load_dotenv(BASE_DIR / ".env")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "rivet_analyzer")

DATABASE_URL = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
