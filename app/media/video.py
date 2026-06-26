"""Слой обработки видео: разбор на кадры (по времени) и анализ."""
import cv2

from app import config
from app.ml import detector


def analyze_video(path: str) -> dict:
    """Взять кадр раз в VIDEO_SAMPLE_SECONDS секунд, проанализировать и собрать % брака."""
    cap = cv2.VideoCapture(path)

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    step = max(1, round(fps * config.VIDEO_SAMPLE_SECONDS))  # шаг по времени -> в кадрах
    max_frames = int(fps * config.MAX_VIDEO_SECONDS)         # лимит длины анализа

    all_detections = []
    frames_analyzed = 0
    frame_index = 0

    while True:
        ok, frame = cap.read()
        if not ok or frame_index >= max_frames:
            break
        if frame_index % step == 0:
            all_detections.extend(detector.detect(frame))
            frames_analyzed += 1
        frame_index += 1

    cap.release()

    summary = detector.defect_percentage(all_detections)
    return {
        "fps": round(fps, 1),
        "frame_step": step,
        "frames_read": frame_index,
        "frames_analyzed": frames_analyzed,
        "summary": summary,
    }
