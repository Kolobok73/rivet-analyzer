"""Эндпоинты приложения (маршруты FastAPI)."""
import logging
from io import BytesIO

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from pydantic import BaseModel

from app import charts
from app import config
from app.db import crud
from app.ml import classifier
from app.ml import detector
from app.media import video

router = APIRouter()
logger = logging.getLogger("rivet")


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
    logger.info("Детекция фото %s: брак %s%%, заклёпок %s",
                file.filename, summary["defect_percent"], summary["total"])
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


# Сохранить вердикт по заклёпке в историю (под формат таблицы analyses).
def _save_rivet(result: dict, label: str) -> None:
    is_defect = result["verdict"] == config.DEFECT_CLASS_NAME
    crud.save_analysis(label, "rivet", {
        "total": 1,
        "ok": 0 if is_defect else 1,
        "defect": 1 if is_defect else 0,
        "defect_percent": result["defect_percent"],
        "avg_confidence": result["confidence"],
        "edge_ignored": 0,
    })


# Анализ ОДНОЙ заклёпки с N ракурсов-фото -> один вердикт (по худшему ракурсу).
@router.post("/analyze/rivet")
async def analyze_rivet(files: list[UploadFile] = File(...)):
    images = []
    for file in files:
        content = await file.read()
        images.append(Image.open(BytesIO(content)).convert("RGB"))
    result = classifier.analyze_rivet(images)
    _save_rivet(result, "заклёпка (ракурсы)")
    logger.info("Заклёпка (фото, %d ракурсов): %s, брак %s%%",
                len(images), result["verdict"], result["defect_percent"])
    return result


# Анализ ОДНОЙ заклёпки по ВИДЕО: каждый кадр = отдельный ракурс.
@router.post("/analyze/rivet/video")
async def analyze_rivet_video(file: UploadFile = File(...)):
    content = await file.read()
    save_path = config.STORAGE_DIR / file.filename
    save_path.write_bytes(content)
    frames = video.extract_frames(str(save_path))
    save_path.unlink()
    if not frames:
        raise HTTPException(status_code=400, detail="Не удалось прочитать кадры из видео")
    result = classifier.analyze_rivet(frames)
    _save_rivet(result, "заклёпка (видео)")
    logger.info("Заклёпка (видео, %d кадров): %s, брак %s%%",
                len(frames), result["verdict"], result["defect_percent"])
    return result


# Классификация ОДНОГО ракурса-фото -> % брака. Для пошагового прогресса на фронте.
@router.post("/classify/view")
async def classify_view(file: UploadFile = File(...)):
    content = await file.read()
    image = Image.open(BytesIO(content)).convert("RGB")
    probs = classifier.classify(image)
    return {"defect_percent": probs[config.DEFECT_CLASS_NAME]}


class ViewsIn(BaseModel):
    views: list[float]
    label: str = "заклёпка"


# Свести % ракурсов (отдельно для фото) в вердикт и сохранить в историю.
@router.post("/rivet/finalize")
def rivet_finalize(data: ViewsIn):
    result = classifier.verdict_from_views(data.views)
    _save_rivet(result, data.label)
    logger.info("Заклёпка (%s, %d ракурсов): %s, брак %s%%",
                data.label, len(data.views), result["verdict"], result["defect_percent"])
    return result


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
