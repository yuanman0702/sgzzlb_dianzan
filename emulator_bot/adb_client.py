from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import os
import re
import shutil
import subprocess
import time

from .config import BotConfig


class AdbError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class AdbDevice:
    serial: str
    state: str
    detail: str = ""


def subprocess_startup_kwargs() -> dict[str, object]:
    if os.name != "nt":
        return {}
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = getattr(subprocess, "SW_HIDE", 0)
    return {
        "startupinfo": startupinfo,
        "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0),
    }


def _bundled_adb_paths() -> list[Path]:
    repo_root = Path(__file__).resolve().parents[1]
    candidates: list[Path] = []
    for base_dir in (Path.cwd(), repo_root):
        candidates.extend(
            [
                base_dir / "adb" / "adb.exe",
                base_dir / "platform-tools" / "adb.exe",
                base_dir / "remote_app_control" / "adb" / "adb.exe",
            ]
        )
    return candidates


def _candidate_adb_paths() -> list[Path]:
    candidates: list[Path] = _bundled_adb_paths()

    android_home = os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT")
    if android_home:
        candidates.append(Path(android_home) / "platform-tools" / "adb.exe")
        candidates.append(Path(android_home) / "platform-tools" / "adb")

    drives = ["C", "D", "E", "F"]
    versions = ["14", "9", "4"]
    for drive in drives:
        for version in versions:
            candidates.extend(
                [
                    Path(rf"{drive}:\leidian\LDPlayer{version}\adb.exe"),
                    Path(rf"{drive}:\LDPlayer\LDPlayer{version}\adb.exe"),
                    Path(rf"{drive}:\LDPlayer{version}\adb.exe"),
                    Path(rf"{drive}:\Program Files\LDPlayer\LDPlayer{version}\adb.exe"),
                    Path(
                        rf"{drive}:\Program Files (x86)\LDPlayer\LDPlayer{version}\adb.exe"
                    ),
                ]
            )
        candidates.extend(
            [
                Path(rf"{drive}:\Program Files\dnplayerext2\adb.exe"),
                Path(rf"{drive}:\Program Files (x86)\dnplayerext2\adb.exe"),
            ]
        )

    return candidates


def discover_adb_path(configured_path: str | None = None) -> str:
    if configured_path:
        path = Path(os.path.expandvars(configured_path)).expanduser()
        if path.is_file():
            return str(path)
        raise AdbError(f"Configured adb path does not exist: {path}")

    for path in _bundled_adb_paths():
        if path.is_file():
            return str(path)

    env_path = os.environ.get("ADB_PATH")
    if env_path:
        path = Path(os.path.expandvars(env_path)).expanduser()
        if path.is_file():
            return str(path)

    from_path = shutil.which("adb")
    if from_path:
        return from_path

    for path in _candidate_adb_paths():
        if path.is_file():
            return str(path)

    raise AdbError(
        "ADB was not found. Set adb.path in config.toml to LDPlayer's adb.exe."
    )


class AdbClient:
    def __init__(self, adb_path: str, serial: str | None = None) -> None:
        self.adb_path = adb_path
        self.serial = serial

    @classmethod
    def connect_from_config(cls, config: BotConfig) -> "AdbClient":
        adb_path = discover_adb_path(config.adb_path)
        client = cls(adb_path)
        client.start_server()

        if config.device_serial:
            if ":" in config.device_serial:
                client.connect(config.device_serial, check=False)
            client.serial = config.device_serial
            client.ensure_device()
            return client

        devices = client.list_devices()
        live_devices = [device for device in devices if device.state == "device"]
        if not live_devices:
            client.try_auto_connect(config.auto_connect_hosts, config.auto_connect_ports)
            devices = client.list_devices()
            live_devices = [device for device in devices if device.state == "device"]

        if not live_devices:
            raise AdbError(
                "No online Android device was found. Check that LDPlayer is open and ADB is enabled."
            )

        client.serial = live_devices[0].serial
        return client

    def _base_cmd(self, include_serial: bool = True) -> list[str]:
        cmd = [self.adb_path]
        if include_serial and self.serial:
            cmd.extend(["-s", self.serial])
        return cmd

    def _run_text(
        self,
        args: Sequence[str],
        *,
        include_serial: bool = True,
        timeout: float = 20.0,
        check: bool = True,
    ) -> str:
        proc = subprocess.run(
            self._base_cmd(include_serial) + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            **subprocess_startup_kwargs(),
        )
        stdout = proc.stdout.decode("utf-8", errors="replace")
        stderr = proc.stderr.decode("utf-8", errors="replace")
        if check and proc.returncode != 0:
            raise AdbError(stderr.strip() or stdout.strip() or f"ADB failed: {args}")
        return stdout

    def _run_bytes(
        self,
        args: Sequence[str],
        *,
        include_serial: bool = True,
        timeout: float = 20.0,
        check: bool = True,
    ) -> bytes:
        proc = subprocess.run(
            self._base_cmd(include_serial) + list(args),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            **subprocess_startup_kwargs(),
        )
        if check and proc.returncode != 0:
            stderr = proc.stderr.decode("utf-8", errors="replace").strip()
            raise AdbError(stderr or f"ADB failed: {args}")
        return proc.stdout

    def start_server(self) -> None:
        self._run_text(["start-server"], include_serial=False, timeout=20.0)

    def connect(self, serial: str, *, check: bool = True) -> str:
        return self._run_text(
            ["connect", serial],
            include_serial=False,
            timeout=5.0,
            check=check,
        )

    def try_auto_connect(self, hosts: Sequence[str], ports: Sequence[int]) -> None:
        for host in hosts:
            for port in ports:
                self.connect(f"{host}:{port}", check=False)
                time.sleep(0.1)

    def list_devices(self) -> list[AdbDevice]:
        output = self._run_text(["devices", "-l"], include_serial=False)
        devices: list[AdbDevice] = []
        for line in output.splitlines()[1:]:
            line = line.strip()
            if not line:
                continue
            parts = line.split(maxsplit=2)
            serial = parts[0]
            state = parts[1] if len(parts) > 1 else "unknown"
            detail = parts[2] if len(parts) > 2 else ""
            devices.append(AdbDevice(serial=serial, state=state, detail=detail))
        return devices

    def ensure_device(self) -> None:
        if not self.serial:
            raise AdbError("No device serial selected.")
        matches = [device for device in self.list_devices() if device.serial == self.serial]
        if not matches:
            raise AdbError(f"Device is not listed by adb: {self.serial}")
        if matches[0].state != "device":
            raise AdbError(f"Device is not online: {self.serial} ({matches[0].state})")

    def shell(self, command: Sequence[str] | str, *, timeout: float = 20.0) -> str:
        if isinstance(command, str):
            args = ["shell", command]
        else:
            args = ["shell", *command]
        return self._run_text(args, timeout=timeout)

    def screencap_png(self) -> bytes:
        last_timeout: subprocess.TimeoutExpired | None = None
        for attempt in range(2):
            try:
                data = self._run_bytes(["exec-out", "screencap", "-p"], timeout=20.0)
            except subprocess.TimeoutExpired as exc:
                last_timeout = exc
                if attempt == 0:
                    time.sleep(0.35)
                continue
            if data.startswith(b"\x89PNG"):
                return data

        for attempt in range(2):
            try:
                data = self._run_bytes(["shell", "screencap", "-p"], timeout=20.0)
            except subprocess.TimeoutExpired as exc:
                last_timeout = exc
                if attempt == 0:
                    time.sleep(0.35)
                continue
            data = data.replace(b"\r\r\n", b"\n").replace(b"\r\n", b"\n")
            if data.startswith(b"\x89PNG"):
                return data

        if last_timeout is not None:
            raise last_timeout
        raise AdbError("ADB screenshot did not return PNG data.")

    def save_screenshot(self, path: str | Path) -> Path:
        out_path = Path(path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(self.screencap_png())
        return out_path

    def tap(self, x: int, y: int) -> None:
        self.shell(["input", "tap", str(int(x)), str(int(y))])

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> None:
        self.shell(
            [
                "input",
                "swipe",
                str(int(x1)),
                str(int(y1)),
                str(int(x2)),
                str(int(y2)),
                str(int(duration_ms)),
            ]
        )

    def keyevent(self, keycode: str | int) -> None:
        self.shell(["input", "keyevent", str(keycode)])

    def keyevents(self, keycodes: Sequence[str | int]) -> None:
        values = [str(keycode) for keycode in keycodes]
        if values:
            self.shell(["input", "keyevent", *values], timeout=20.0)

    def input_text(self, text: str) -> None:
        escaped = text.replace(" ", "%s")
        self.shell(["input", "text", escaped], timeout=10.0)

    def get_screen_size(self) -> tuple[int, int]:
        output = self.shell(["wm", "size"])
        match = re.search(r"(\d+)x(\d+)", output)
        if not match:
            raise AdbError(f"Could not parse screen size: {output.strip()}")
        return int(match.group(1)), int(match.group(2))

    def is_package_installed(self, package: str) -> bool:
        output = self._run_text(
            ["shell", "pm", "path", package],
            timeout=10.0,
            check=False,
        )
        return "package:" in output

    def resolve_launcher_activity(self, package: str) -> str | None:
        output = self._run_text(
            ["shell", "cmd", "package", "resolve-activity", "--brief", package],
            timeout=10.0,
            check=False,
        )
        for line in reversed(output.splitlines()):
            line = line.strip()
            if "/" in line and not line.lower().startswith("no activity"):
                return line
        return None

    def launch_package(self, package: str) -> str:
        if not self.is_package_installed(package):
            raise AdbError(f"Package is not installed on the emulator: {package}")
        component = self.resolve_launcher_activity(package)
        if component:
            output = self._run_text(
                [
                    "shell",
                    "am",
                    "start",
                    "-n",
                    component,
                    "-a",
                    "android.intent.action.MAIN",
                    "-c",
                    "android.intent.category.LAUNCHER",
                ],
                timeout=20.0,
                check=False,
            )
            if "Error" not in output and "Exception" not in output:
                return output

        try:
            output = self.shell(
                [
                    "monkey",
                    "-p",
                    package,
                    "-c",
                    "android.intent.category.LAUNCHER",
                    "1",
                ],
                timeout=20.0,
            )
        except AdbError as exc:
            raise AdbError(
                f"Could not launch {package}. Resolved activity: {component}. {exc}"
            ) from exc
        if "No activities found" in output or "Error" in output:
            raise AdbError(output.strip())
        return output

    def force_stop_package(self, package: str) -> str:
        return self.shell(["am", "force-stop", package], timeout=10.0)

    def current_focus(self) -> str:
        output = self.shell(["dumpsys", "window"], timeout=20.0)
        for line in output.splitlines():
            if "mCurrentFocus" in line or "mFocusedApp" in line:
                return line.strip()
        return ""
