"""Генерация графиков на сервере (matplotlib) -> PNG в base64 для <img>."""
import base64
import io

import matplotlib

matplotlib.use("Agg")  # режим без GUI — рисуем в память на сервере
from matplotlib.figure import Figure  # noqa: E402


def _short(name: str, limit: int = 14) -> str:
    return name if len(name) <= limit else name[:limit] + "…"


def defect_bar_chart(items: list[dict]) -> str:
    """Столбчатая диаграмма 'процент брака по файлам' -> data-URL PNG."""
    labels = [_short(i["filename"]) for i in items]
    values = [i["defect_percent"] for i in items]

    fig = Figure(figsize=(7, 3.6))
    ax = fig.subplots()
    bars = ax.bar(range(len(values)), values, color="#ff3b30")
    ax.set_ylabel("Процент брака, %")
    ax.set_ylim(0, 100)
    ax.set_title("Процент брака по файлам", pad=25)
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=8)
    for bar, v in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1, f"{v}%", ha="center", fontsize=8)
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    buf.seek(0)
    return f"data:image/png;base64,{base64.b64encode(buf.read()).decode()}"
