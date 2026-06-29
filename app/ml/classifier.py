"""Слой ML: классификатор одной заклёпки + сведение нескольких ракурсов в вердикт."""
from ultralytics import YOLO

from app import config

# Классификатор грузится один раз при импорте (как и детектор).
_model = YOLO(str(config.CLASSIFIER_WEIGHTS_PATH))


def get_model():
    return _model


def classify(image):
    """Одна картинка одной заклёпки -> вероятности классов в процентах.

    Пример: {"rivet_defect": 85.0, "rivet_ok": 15.0}.
    """
    result = get_model().predict(image, device=config.DEVICE, verbose=False)[0]
    probs = result.probs.data.tolist()   # [p_class0, p_class1] в долях 0..1
    names = result.names                 # {0: rivet_defect, 1: rivet_ok}
    return {names[i]: round(probs[i] * 100, 1) for i in range(len(probs))}


def verdict_from_views(views):
    """Свести список % брака по ракурсам в один вердикт (по ХУДШЕМУ ракурсу).

    Дефект часто виден лишь с одного угла, поэтому берём максимум вероятности
    брака: достаточно одной камеры/кадра, увидевшего дефект.
    """
    worst = max(views) if views else 0.0
    is_defect = worst >= config.DEFECT_VERDICT_THRESHOLD
    return {
        "verdict": config.DEFECT_CLASS_NAME if is_defect else "rivet_ok",
        "defect_percent": worst,                          # вероятность брака (по худшему)
        "confidence": worst if is_defect else round(100 - worst, 1),  # уверенность в вердикте
        "views": views,                                   # % брака по каждому ракурсу
    }


def analyze_rivet(images):
    """N ракурсов ОДНОЙ заклёпки -> один вердикт."""
    views = [classify(img)[config.DEFECT_CLASS_NAME] for img in images]
    return verdict_from_views(views)
