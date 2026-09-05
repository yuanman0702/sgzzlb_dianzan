from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True, slots=True)
class Match:
    x: int
    y: int
    width: int
    height: int
    score: float
    kind: str

    @property
    def center(self) -> tuple[int, int]:
        return self.x + self.width // 2, self.y + self.height // 2


def _cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "OpenCV is required for vision features. Run: python -m pip install -r requirements.txt"
        ) from exc
    return cv2


def _np():
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "Numpy is required for vision features. Run: python -m pip install -r requirements.txt"
        ) from exc
    return np


def decode_png_to_bgr(png_bytes: bytes):
    cv2 = _cv2()
    np = _np()
    arr = np.frombuffer(png_bytes, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError("Could not decode screenshot PNG.")
    return image


def _crop(image, region: Sequence[int] | None):
    if not region:
        return image, 0, 0
    x, y, width, height = [int(v) for v in region]
    img_h, img_w = image.shape[:2]
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    width = max(1, min(width, img_w - x))
    height = max(1, min(height, img_h - y))
    return image[y : y + height, x : x + width], x, y


def match_template(
    screenshot,
    template_path: str | Path,
    *,
    threshold: float = 0.86,
    region: Sequence[int] | None = None,
) -> Match | None:
    cv2 = _cv2()
    template = cv2.imread(str(template_path), cv2.IMREAD_COLOR)
    if template is None:
        raise FileNotFoundError(f"Template image could not be read: {template_path}")

    haystack, offset_x, offset_y = _crop(screenshot, region)
    h, w = template.shape[:2]
    if haystack.shape[0] < h or haystack.shape[1] < w:
        return None

    result = cv2.matchTemplate(haystack, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    if max_val < threshold:
        return None

    x = int(max_loc[0] + offset_x)
    y = int(max_loc[1] + offset_y)
    return Match(x=x, y=y, width=w, height=h, score=float(max_val), kind="image")


def find_color(
    screenshot,
    *,
    rgb: Sequence[int],
    tolerance: int = 20,
    region: Sequence[int] | None = None,
    min_area: int = 20,
) -> Match | None:
    cv2 = _cv2()
    np = _np()
    crop, offset_x, offset_y = _crop(screenshot, region)
    r, g, b = [int(v) for v in rgb]
    bgr = np.array([b, g, r], dtype=np.int16)
    lower = np.clip(bgr - int(tolerance), 0, 255).astype(np.uint8)
    upper = np.clip(bgr + int(tolerance), 0, 255).astype(np.uint8)
    mask = cv2.inRange(crop, lower, upper)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    contour = max(contours, key=cv2.contourArea)
    area = float(cv2.contourArea(contour))
    if area < min_area:
        return None

    x, y, width, height = cv2.boundingRect(contour)
    return Match(
        x=int(x + offset_x),
        y=int(y + offset_y),
        width=int(width),
        height=int(height),
        score=area,
        kind="color",
    )


def save_debug_image(path: str | Path, screenshot, match: Match | None = None) -> Path:
    cv2 = _cv2()
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image = screenshot.copy()
    if match:
        cv2.rectangle(
            image,
            (match.x, match.y),
            (match.x + match.width, match.y + match.height),
            (0, 255, 0),
            2,
        )
        cx, cy = match.center
        cv2.drawMarker(image, (cx, cy), (0, 0, 255), markerSize=16, thickness=2)
        cv2.putText(
            image,
            f"{match.kind}:{match.score:.3f}",
            (match.x, max(20, match.y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
    cv2.imwrite(str(out_path), image)
    return out_path
