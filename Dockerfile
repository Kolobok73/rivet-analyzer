# Базовый образ: лёгкий Python 3.10
FROM python:3.10-slim

# Системные библиотеки, нужные OpenCV (иначе import cv2 падает)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Зависимости (слой кэшируется, пока requirements.txt не меняется).
COPY requirements.txt .
# CPU-сборка torch с отдельного индекса (без тяжёлых CUDA-зависимостей),
# затем остальное БЕЗ строки torch (grep -v убирает её, чтобы не перетёрлась).
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu \
    && grep -v "^torch" requirements.txt > /tmp/req.txt \
    && pip install --no-cache-dir -r /tmp/req.txt

# Затем весь код (включая веса models/*.pt)
COPY . .

EXPOSE 8000

# Запуск сервера. host 0.0.0.0 — чтобы был доступен снаружи контейнера.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
