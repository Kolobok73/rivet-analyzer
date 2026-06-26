"""Эндпоинты приложения (маршруты FastAPI)."""
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

from app import charts
from app import config
from app.db import crud
from app.ml import detector
from app.media import video

router = APIRouter()


class ChartItem(BaseModel):
    filename: str
    defect_percent: float


# Анализ одного фото — общий помощник для обоих фото-эндпоинтов.
async def analyze_one_image(file: UploadFile) -> dict:
    content = await file.read()
    image = Image.open(BytesIO(content)).convert("RGB")
    detections = detector.detect(image)
    summary = detector.defect_percentage(detections)
    crud.save_analysis(file.filename, "image", summary)
    return {
        "filename": file.filename,
        "summary": summary,
        "detections": detections,
    }


# Анализ одного видео: сохраняем в storage/, затем разбираем по кадрам, потом удаляем.
async def analyze_one_video(file: UploadFile) -> dict:
    content = await file.read()
    save_path = config.STORAGE_DIR / file.filename
    save_path.write_bytes(content)
    result = video.analyze_video(str(save_path))
    save_path.unlink()
    crud.save_analysis(file.filename, "video", result["summary"])
    return {"filename": file.filename, **result}


@router.get("/")
def read_root():
    return FileResponse(config.BASE_DIR / "app" / "static" / "index.html")


@router.get("/health")
def health():
    return {
        "status": "ok",
        "max_images": config.MAX_IMAGES,
        "max_videos": config.MAX_VIDEOS,
        "classes": config.CLASS_NAMES,
    }


@router.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    return await analyze_one_image(file)


@router.post("/analyze/images")
async def analyze_images(files: list[UploadFile] = File(...)):
    if len(files) > config.MAX_IMAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много файлов: максимум {config.MAX_IMAGES}, прислано {len(files)}",
        )
    results = []
    for file in files:
        results.append(await analyze_one_image(file))
    return {"results": results}


@router.post("/analyze/videos")
async def analyze_videos(files: list[UploadFile] = File(...)):
    if len(files) > config.MAX_VIDEOS:
        raise HTTPException(
            status_code=400,
            detail=f"Слишком много видео: максимум {config.MAX_VIDEOS}, прислано {len(files)}",
        )
    results = []
    for file in files:
        results.append(await analyze_one_video(file))
    return {"results": results}


@router.post("/chart/defects")
def chart_defects(items: list[ChartItem]):
    data = [item.model_dump() for item in items]
    return {"image": charts.defect_bar_chart(data)}


@router.get("/history")
def history(limit: int = 50):
    rows = crud.get_recent(limit)
    return {
        "history": [
            {
                "id": r.id,
                "filename": r.filename,
                "file_type": r.file_type,
                "total": r.total,
                "ok": r.ok_count,
                "defect": r.defect_count,
                "defect_percent": r.defect_percent,
                "avg_confidence": r.avg_confidence,
                "edge_ignored": r.edge_ignored,
                "created_at": r.created_at.isoformat(timespec="seconds"),
            }
            for r in rows
        ]
    }
