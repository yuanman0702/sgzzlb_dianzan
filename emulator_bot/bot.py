from __future__ import annotations

from pathlib import Path
from random import randint
from time import sleep, time
from typing import Sequence

from .adb_client import AdbClient
from .config import BotConfig


class EmulatorBot:
    def __init__(self, client: AdbClient, config: BotConfig) -> None:
        self.client = client
        self.config = config

    @classmethod
    def connect(cls, config: BotConfig) -> "EmulatorBot":
        return cls(AdbClient.connect_from_config(config), config)

    def screenshot_png(self) -> bytes:
        return self.client.screencap_png()

    def screenshot_image(self):
        from .vision import decode_png_to_bgr

        return decode_png_to_bgr(self.screenshot_png())

    def save_screenshot(self, name: str | None = None) -> Path:
        if not name:
            name = f"screenshot_{int(time())}.png"
        return self.client.save_screenshot(self.config.screenshot_dir / name)

    def tap(self, x: int, y: int, *, jitter: int | None = None) -> tuple[int, int]:
        if jitter is None:
            jitter = self.config.click_jitter_pixels
        if jitter > 0:
            x += randint(-jitter, jitter)
            y += randint(-jitter, jitter)
        self.client.tap(x, y)
        return x, y

    def swipe(
        self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300
    ) -> None:
        self.client.swipe(x1, y1, x2, y2, duration_ms)

    def find_image(
        self,
        template: str | Path,
        *,
        threshold: float = 0.86,
        region: Sequence[int] | None = None,
        debug_name: str | None = None,
    ):
        from .vision import match_template, save_debug_image

        template_path = Path(template)
        if not template_path.is_absolute():
            template_path = self.config.template_dir / template_path

        screenshot = self.screenshot_image()
        match = match_template(
            screenshot,
            template_path,
            threshold=threshold,
            region=region,
        )
        if debug_name:
            save_debug_image(self.config.debug_dir / debug_name, screenshot, match)
        return match

    def find_color(
        self,
        rgb: Sequence[int],
        *,
        tolerance: int = 20,
        region: Sequence[int] | None = None,
        min_area: int = 20,
        debug_name: str | None = None,
    ):
        from .vision import find_color, save_debug_image

        screenshot = self.screenshot_image()
        match = find_color(
            screenshot,
            rgb=rgb,
            tolerance=tolerance,
            region=region,
            min_area=min_area,
        )
        if debug_name:
            save_debug_image(self.config.debug_dir / debug_name, screenshot, match)
        return match

    def wait_for_image(
        self,
        template: str | Path,
        *,
        timeout: float | None = None,
        threshold: float = 0.86,
        region: Sequence[int] | None = None,
    ):
        end_at = time() + (timeout or self.config.default_timeout_seconds)
        while time() < end_at:
            match = self.find_image(template, threshold=threshold, region=region)
            if match:
                return match
            sleep(self.config.poll_interval_seconds)
        return None

    def wait_for_color(
        self,
        rgb: Sequence[int],
        *,
        timeout: float | None = None,
        tolerance: int = 20,
        region: Sequence[int] | None = None,
        min_area: int = 20,
    ):
        end_at = time() + (timeout or self.config.default_timeout_seconds)
        while time() < end_at:
            match = self.find_color(
                rgb,
                tolerance=tolerance,
                region=region,
                min_area=min_area,
            )
            if match:
                return match
            sleep(self.config.poll_interval_seconds)
        return None

    def click_image(
        self,
        template: str | Path,
        *,
        timeout: float | None = None,
        threshold: float = 0.86,
        region: Sequence[int] | None = None,
    ) -> tuple[int, int] | None:
        match = self.wait_for_image(
            template,
            timeout=timeout,
            threshold=threshold,
            region=region,
        )
        if not match:
            return None
        return self.tap(*match.center)

    def click_color(
        self,
        rgb: Sequence[int],
        *,
        timeout: float | None = None,
        tolerance: int = 20,
        region: Sequence[int] | None = None,
        min_area: int = 20,
    ) -> tuple[int, int] | None:
        match = self.wait_for_color(
            rgb,
            timeout=timeout,
            tolerance=tolerance,
            region=region,
            min_area=min_area,
        )
        if not match:
            return None
        return self.tap(*match.center)
