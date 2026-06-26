"""Слой ML: загрузка модели YOLO, инференс и расчёт процента брака."""

from ultralytics import YOLO

from app import config

# Модель грузится один раз при импорте модуля (= при старте сервера).
_model = YOLO(str(config.MODEL_WEIGHTS_PATH))


def get_model():
    return _model


def detect(source):
    """
    Прогнать одну картинку через модель.
    source — путь к файлу, numpy-массив (кадр) или PIL.Image.
    Возвращает список {"class_name", "confidence", "box", "at_edge"}.
    """
    model = get_model()
    results = model.predict(
        source,
        conf=config.CONFIDENCE_THRESHOLD,
        iou=config.NMS_IOU_THRESHOLD,
        agnostic_nms=True,  # сливать налезающие рамки независимо от класса
        verbose=False,
    )
    result = results[0]

    # Размер оригинала — нужен, чтобы понять, касается ли рамка края.
    h, w = result.orig_shape
    margin_x = w * config.EDGE_MARGIN_RATIO
    margin_y = h * config.EDGE_MARGIN_RATIO

    detections = []
    for box in result.boxes:
        class_id = int(box.cls[0])
        confidence = float(box.conf[0])
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = xyxy

        at_edge = (
            x1 <= margin_x or y1 <= margin_y
            or x2 >= w - margin_x or y2 >= h - margin_y
        )

        detections.append({
            "class_name": model.names[class_id],  # имя из модели — авторитетный источник
            "confidence": confidence,
            "box": xyxy,
            "at_edge": at_edge,
        })
    return detections


def defect_percentage(detections):
    """
    Процент брака = доля бракованных среди целых (краевые не учитываем).
    Возвращает {"total", "ok", "defect", "defect_percent", "avg_confidence", "edge_ignored"}.
    """
    counted = [d for d in detections if not d.get("at_edge")]
    edge_ignored = len(detections) - len(counted)

    total = len(counted)
    if total == 0:
        return {
            "total": 0, "ok": 0, "defect": 0,
            "defect_percent": 0.0, "avg_confidence": 0.0, "edge_ignored": edge_ignored,
        }

    defect = sum(1 for d in counted if d["class_name"] == config.DEFECT_CLASS_NAME)
    ok = total - defect
    defect_percent = round(defect / total * 100, 1)
    # Средняя уверенность модели (это не вероятность правильности).
    avg_confidence = round(sum(d["confidence"] for d in counted) / total * 100, 1)

    return {
        "total": total,
        "ok": ok,
        "defect": defect,
        "defect_percent": defect_percent,
        "avg_confidence": avg_confidence,
        "edge_ignored": edge_ignored,
    }
