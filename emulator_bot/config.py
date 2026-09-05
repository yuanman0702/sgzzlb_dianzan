from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


@dataclass(slots=True)
class BotConfig:
    adb_path: str | None = None
    device_serial: str | None = None
    auto_connect_hosts: list[str] = field(default_factory=lambda: ["127.0.0.1"])
    auto_connect_ports: list[int] = field(
        default_factory=lambda: [5555, 5557, 5559, 5561, 5563, 5565]
    )
    screenshot_dir: Path = Path("logs/screenshots")
    debug_dir: Path = Path("logs/debug")
    template_dir: Path = Path("assets/templates")
    airtest_device_uri: str | None = None
    airtest_log_dir: Path = Path("logs/airtest")
    airtest_cap_method: str = "javacap"
    airtest_touch_method: str = "adb"
    default_timeout_seconds: float = 8.0
    poll_interval_seconds: float = 0.35
    click_jitter_pixels: int = 3
    weibo_package: str = "com.sina.weibo"
    weibo_launch_wait_seconds: float = 2.0

    def ensure_dirs(self) -> None:
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.template_dir.mkdir(parents=True, exist_ok=True)


def _blank_to_none(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _resolve_path(base_dir: Path, value: object, default: str) -> Path:
    text = str(value or default).strip()
    path = Path(text)
    if not path.is_absolute():
        path = base_dir / path
    return path


def load_config(path: str | Path = "config.toml") -> BotConfig:
    config_path = Path(path)
    base_dir = config_path.resolve().parent

    raw: dict[str, object] = {}
    if config_path.exists():
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)

    adb = raw.get("adb", {})
    connect = raw.get("connect", {})
    paths = raw.get("paths", {})
    vision = raw.get("vision", {})
    airtest = raw.get("airtest", {})
    demo = raw.get("demo", {})
    weibo = demo.get("weibo", {}) if isinstance(demo, dict) else {}

    if not isinstance(adb, dict):
        adb = {}
    if not isinstance(connect, dict):
        connect = {}
    if not isinstance(paths, dict):
        paths = {}
    if not isinstance(vision, dict):
        vision = {}
    if not isinstance(airtest, dict):
        airtest = {}
    if not isinstance(weibo, dict):
        weibo = {}

    cfg = BotConfig(
        adb_path=_blank_to_none(adb.get("path")),
        device_serial=_blank_to_none(adb.get("device_serial")),
        auto_connect_hosts=list(connect.get("auto_connect_hosts", ["127.0.0.1"])),
        auto_connect_ports=[int(port) for port in connect.get("auto_connect_ports", [])]
        or [5555, 5557, 5559, 5561, 5563, 5565],
        screenshot_dir=_resolve_path(
            base_dir, paths.get("screenshot_dir"), "logs/screenshots"
        ),
        debug_dir=_resolve_path(base_dir, paths.get("debug_dir"), "logs/debug"),
        template_dir=_resolve_path(
            base_dir, paths.get("template_dir"), "assets/templates"
        ),
        airtest_device_uri=_blank_to_none(airtest.get("device_uri")),
        airtest_log_dir=_resolve_path(
            base_dir, airtest.get("log_dir"), "logs/airtest"
        ),
        airtest_cap_method=str(airtest.get("cap_method", "javacap")).strip()
        or "javacap",
        airtest_touch_method=str(airtest.get("touch_method", "adb")).strip()
        or "adb",
        default_timeout_seconds=float(vision.get("default_timeout_seconds", 8.0)),
        poll_interval_seconds=float(vision.get("poll_interval_seconds", 0.35)),
        click_jitter_pixels=int(vision.get("click_jitter_pixels", 3)),
        weibo_package=str(weibo.get("package", "com.sina.weibo")).strip()
        or "com.sina.weibo",
        weibo_launch_wait_seconds=float(weibo.get("launch_wait_seconds", 2.0)),
    )
    cfg.ensure_dirs()
    return cfg
