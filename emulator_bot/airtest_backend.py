from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os

from .bot import EmulatorBot
from .vision import Match


class AirtestUnavailableError(RuntimeError):
    pass


def check_airtest_available() -> tuple[bool, str]:
    try:
        import airtest  # type: ignore
    except ImportError:
        return False, "Airtest is not installed. Run: python -m pip install -r requirements-airtest.txt"
    version = getattr(airtest, "__version__", "unknown")
    return True, str(version)


@dataclass(slots=True)
class AirtestBackend:
    bot: EmulatorBot
    device_uri: str
    connected: bool = False

    @classmethod
    def from_bot(cls, bot: EmulatorBot) -> "AirtestBackend":
        serial = bot.client.serial
        if not serial:
            raise AirtestUnavailableError("No ADB device serial is selected.")
        uri = bot.config.airtest_device_uri or (
            "Android://127.0.0.1:5037/"
            f"{serial}?cap_method={bot.config.airtest_cap_method}"
            f"&touch_method={bot.config.airtest_touch_method}"
        )
        return cls(bot=bot, device_uri=uri)

    def connect(self) -> None:
        if self.connected:
            return
        available, message = check_airtest_available()
        if not available:
            raise AirtestUnavailableError(message)

        adb_dir = str(Path(self.bot.client.adb_path).resolve().parent)
        path_parts = os.environ.get("PATH", "").split(os.pathsep)
        if adb_dir not in path_parts:
            os.environ["PATH"] = adb_dir + os.pathsep + os.environ.get("PATH", "")
        os.environ.setdefault("ADB_PATH", self.bot.client.adb_path)

        from airtest.core.api import auto_setup, connect_device  # type: ignore

        self.bot.config.airtest_log_dir.mkdir(parents=True, exist_ok=True)
        auto_setup(
            basedir=str(Path.cwd()),
            logdir=str(self.bot.config.airtest_log_dir),
            project_root=str(Path.cwd()),
        )
        connect_device(self.device_uri)
        self.connected = True

    def exists_template(self, template_path: str | Path, threshold: float = 0.86) -> Match | None:
        self.connect()
        from airtest.core.api import Template, exists  # type: ignore

        pos: Any = exists(Template(str(template_path), threshold=threshold))
        if not pos:
            return None
        x, y = int(pos[0]), int(pos[1])
        return Match(x=x, y=y, width=1, height=1, score=1.0, kind="airtest_image")

    def touch(self, x: int, y: int) -> None:
        self.connect()
        from airtest.core.api import touch  # type: ignore

        touch((int(x), int(y)))

    def touch_template(self, template_path: str | Path, threshold: float = 0.86) -> Match | None:
        match = self.exists_template(template_path, threshold=threshold)
        if not match:
            return None
        self.touch(*match.center)
        return match

    def snapshot(self, filename: str | Path | None = None) -> Path | None:
        self.connect()
        from airtest.core.api import snapshot  # type: ignore

        if filename is None:
            snapshot()
            return None
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        snapshot(filename=str(path))
        return path
