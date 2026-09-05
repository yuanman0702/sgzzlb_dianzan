from __future__ import annotations

import os
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_ROOT = REPO_ROOT / "logs" / "remote_app_control"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from emulator_bot.adb_client import AdbClient, AdbDevice, discover_adb_path  # noqa: E402


def iso_from_timestamp(value: float | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(value).isoformat(timespec="seconds")


def safe_file_id(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in "._-" else "-" for ch in value.strip())
    cleaned = cleaned.strip("-._")
    return cleaned or "android-device"


def auto_connect_ports() -> list[int]:
    raw = os.environ.get("ADB_AUTO_CONNECT_PORTS", "5555,5557,5559,5561,5563,5565")
    ports: list[int] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ports.append(int(part))
        except ValueError:
            continue
    return ports or [5555, 5557, 5559, 5561, 5563, 5565]


@dataclass
class DeviceState:
    device_id: str
    serial: str
    name: str = ""
    adb_state: str = "unknown"
    detail: str = ""
    bound: bool = False
    discovered_at: float = field(default_factory=time.time)
    last_seen_at: float = field(default_factory=time.time)
    last_scan_at: float = 0.0
    latest_frame_at: float | None = None
    latest_frame_path: Path | None = None
    latest_frame_bytes: bytes | None = field(default=None, repr=False)
    frame_count: int = 0
    screen_width: int | None = None
    screen_height: int | None = None
    current_focus: str = ""
    android_id: str = ""
    model: str = ""
    aliases: set[str] = field(default_factory=set)

    def snapshot(self, *, include_commands: bool = False) -> dict[str, Any]:
        now = time.time()
        online = self.adb_state == "device" and now - self.last_seen_at < 30.0
        has_fresh_frame = (
            self.latest_frame_at is not None
            and now - self.latest_frame_at <= 30.0
        )
        status = {
            "adb_state": self.adb_state,
            "bound": self.bound,
            "controllable": self.bound and online,
            "foreground": self.current_focus,
            "model": self.model,
            "android_id": self.android_id,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
        }
        payload = {
            "device_id": self.device_id,
            "serial": self.serial,
            "name": self.name or self.serial,
            "capabilities": {"transport": "adb"},
            "status": status,
            "discovered_at": iso_from_timestamp(self.discovered_at),
            "last_seen_at": iso_from_timestamp(self.last_seen_at),
            "last_scan_at": iso_from_timestamp(self.last_scan_at),
            "latest_frame_at": iso_from_timestamp(self.latest_frame_at),
            "latest_frame_path": str(self.latest_frame_path) if self.latest_frame_path else None,
            "frame_count": self.frame_count,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "online": online,
            "bound": self.bound,
            "has_fresh_frame": has_fresh_frame,
            "detail": self.detail,
            "aliases": sorted(self.aliases),
        }
        if include_commands:
            payload["commands"] = []
        return payload


class DeviceRegistry:
    """ADB-backed device registry used by the server UI and SGZZ workers."""

    def __init__(self, log_root: Path = LOG_ROOT) -> None:
        self.log_root = log_root
        self.log_root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.devices: dict[str, DeviceState] = {}
        self.aliases: dict[str, str] = {}
        self._adb_path: str | None = None
        self._last_scan_at = 0.0
        self._scan_interval_seconds = 2.0

    @property
    def adb_path(self) -> str:
        if self._adb_path is None:
            self._adb_path = discover_adb_path()
        return self._adb_path

    def adb_client(self, serial: str | None = None) -> AdbClient:
        return AdbClient(self.adb_path, serial)

    def scan_devices(self, *, force: bool = False, auto_connect: bool = True) -> list[dict[str, Any]]:
        now = time.time()
        with self.lock:
            if not force and now - self._last_scan_at < self._scan_interval_seconds:
                return self.list_devices()
            self._last_scan_at = now

        client = self.adb_client()
        client.start_server()
        raw_devices = client.list_devices()
        if auto_connect and not any(device.state == "device" for device in raw_devices):
            client.try_auto_connect(["127.0.0.1"], auto_connect_ports())
            raw_devices = client.list_devices()

        seen: set[str] = set()
        with self.lock:
            for adb_device in sorted(raw_devices, key=self._device_sort_key):
                seen.add(adb_device.serial)
                self._update_from_adb_device_locked(adb_device, now)
            for state in self.devices.values():
                if state.serial not in seen and not state.aliases.intersection(seen):
                    state.adb_state = "offline"
                    state.detail = "not listed by adb"
                    state.last_scan_at = now
            self._dedupe_devices_locked()
        return self.list_devices()

    def connect_device(self, serial: str) -> dict[str, Any]:
        serial = serial.strip()
        if not serial:
            raise ValueError("ADB serial is required.")
        client = self.adb_client()
        client.start_server()
        if ":" in serial:
            client.connect(serial, check=False)
        self.scan_devices(force=True, auto_connect=False)
        return self.bind_device(serial)

    def bind_device(self, serial: str) -> dict[str, Any]:
        serial = serial.strip()
        if not serial:
            raise ValueError("ADB serial is required.")
        self.scan_devices(force=True, auto_connect=False)
        with self.lock:
            key = self._canonical_serial_locked(serial)
            state = self.devices.get(key) or self.devices.get(serial)
            if state is None:
                state = DeviceState(device_id=serial, serial=serial, name=serial)
                self.devices[serial] = state
            if state.adb_state != "device":
                raise RuntimeError(f"ADB device is not online: {serial} ({state.adb_state})")
            state.bound = True
            state.last_seen_at = time.time()
            self._refresh_details_locked(state, lightweight=False)
            return state.snapshot(include_commands=True)

    def unbind_device(self, serial: str) -> dict[str, Any]:
        with self.lock:
            state = self._get_device_locked(serial)
            state.bound = False
            return state.snapshot(include_commands=True)

    def list_devices(self, *, include_commands: bool = False) -> list[dict[str, Any]]:
        with self.lock:
            devices = [
                state.snapshot(include_commands=include_commands)
                for state in self.devices.values()
            ]
        return sorted(
            devices,
            key=lambda item: (
                0 if item.get("online") else 1,
                0 if item.get("bound") else 1,
                str(item.get("serial") or item.get("device_id") or ""),
            ),
        )

    def get_device_snapshot(self, device_id: str, *, include_commands: bool = False) -> dict[str, Any]:
        with self.lock:
            state = self._get_device_locked(device_id)
            return state.snapshot(include_commands=include_commands)

    def resolve_device_id(self, device_id: str | None = None) -> str:
        if device_id:
            with self.lock:
                key = device_id.strip()
                canonical = self._canonical_serial_locked(key)
                if canonical in self.devices:
                    return canonical
                if key in self.devices:
                    return key
                return canonical
        with self.lock:
            bound_online = [
                state
                for state in self.devices.values()
                if state.bound and state.adb_state == "device"
            ]
            if not bound_online:
                raise RuntimeError("No bound ADB emulator is available.")
            if len(bound_online) > 1:
                raise RuntimeError("Multiple bound ADB emulators are available; select one first.")
            return bound_online[0].serial

    def ensure_bound(self, device_id: str) -> DeviceState:
        with self.lock:
            state = self._get_device_locked(device_id)
            if state.adb_state != "device":
                raise RuntimeError(f"ADB device is not online: {state.serial} ({state.adb_state})")
            if not state.bound:
                raise RuntimeError(f"ADB device is not bound: {state.serial}")
            return state

    def capture_screenshot(self, device_id: str) -> Path:
        serial = self.resolve_device_id(device_id)
        self.ensure_bound(serial)
        raw = self.adb_client(serial).screencap_png()
        payload = self.update_frame(serial, raw, content_type="image/png")
        return Path(str(payload["latest_frame_path"]))

    def update_frame(
        self,
        device_id: str,
        raw: bytes,
        *,
        content_type: str = "image/png",
        status: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not raw:
            raise ValueError("empty screenshot")
        serial = self.resolve_device_id(device_id)
        device_dir = self.log_root / "devices" / safe_file_id(serial)
        device_dir.mkdir(parents=True, exist_ok=True)
        ext = ".png" if content_type.lower().endswith("png") else ".jpg"
        latest_path = device_dir / f"latest{ext}"
        latest_path.write_bytes(raw)

        width: int | None = None
        height: int | None = None
        image = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is not None:
            height, width = image.shape[:2]

        with self.lock:
            state = self.devices.get(serial)
            if state is None:
                state = DeviceState(device_id=serial, serial=serial, name=serial, bound=True)
                self.devices[serial] = state
            state.latest_frame_bytes = raw
            state.latest_frame_path = latest_path
            state.latest_frame_at = time.time()
            state.frame_count += 1
            state.last_seen_at = time.time()
            state.adb_state = "device"
            if width is not None and height is not None:
                state.screen_width = int(width)
                state.screen_height = int(height)
            if status:
                self._apply_status_locked(state, status)
            return state.snapshot(include_commands=True)

    def get_latest_frame_path(self, device_id: str) -> Path:
        serial = self.resolve_device_id(device_id)
        with self.lock:
            state = self._get_device_locked(serial)
            path = state.latest_frame_path
            latest_at = state.latest_frame_at or 0.0
        if path is not None and time.time() - latest_at <= 30.0 and path.exists():
            return path
        return self.capture_screenshot(serial)

    def wait_for_frame(
        self,
        device_id: str,
        *,
        after: float | None = None,
        max_age_seconds: float = 2.5,
        timeout: float = 12.0,
    ) -> bytes:
        del after, max_age_seconds, timeout
        serial = self.resolve_device_id(device_id)
        self.ensure_bound(serial)
        raw = self.adb_client(serial).screencap_png()
        self.update_frame(serial, raw, content_type="image/png")
        return raw

    def send_command_and_wait(
        self,
        device_id: str,
        command_type: str,
        *,
        timeout: float = 10.0,
        **payload: Any,
    ) -> str:
        del timeout
        serial = self.resolve_device_id(device_id)
        self.ensure_bound(serial)
        client = self.adb_client(serial)
        if command_type == "tap":
            client.tap(int(payload["x"]), int(payload["y"]))
            return "tap sent"
        if command_type == "swipe":
            client.swipe(
                int(payload["x1"]),
                int(payload["y1"]),
                int(payload["x2"]),
                int(payload["y2"]),
                int(payload.get("duration_ms", 300)),
            )
            return "swipe sent"
        if command_type == "keyevent":
            client.keyevent(str(payload["keycode"]))
            return "keyevent sent"
        if command_type == "input_text":
            client.input_text(str(payload.get("text") or ""))
            return "input text sent"
        if command_type == "launch":
            return client.launch_package(str(payload["package"]))
        if command_type == "force_stop":
            return client.force_stop_package(str(payload["package"]))
        raise ValueError(f"Unsupported ADB command: {command_type}")

    def _update_from_adb_device_locked(self, adb_device: AdbDevice, now: float) -> None:
        state = self.devices.get(adb_device.serial)
        if state is None:
            state = DeviceState(
                device_id=adb_device.serial,
                serial=adb_device.serial,
                name=adb_device.serial,
            )
            self.devices[adb_device.serial] = state
        state.adb_state = adb_device.state
        state.detail = adb_device.detail
        state.last_scan_at = now
        if adb_device.state == "device":
            state.last_seen_at = now
            self._refresh_details_locked(state, lightweight=True)

    def _dedupe_devices_locked(self) -> None:
        groups: dict[str, list[DeviceState]] = {}
        for state in list(self.devices.values()):
            groups.setdefault(self._physical_device_key(state), []).append(state)

        devices: dict[str, DeviceState] = {}
        aliases: dict[str, str] = {}
        for states in groups.values():
            primary = min(states, key=self._device_state_preference_key)
            merged_aliases = set(primary.aliases)
            for state in states:
                if state is primary:
                    continue
                self._merge_device_state_locked(primary, state)
                merged_aliases.add(state.serial)
                merged_aliases.update(state.aliases)

            primary.device_id = primary.serial
            merged_aliases.discard(primary.serial)
            primary.aliases = merged_aliases
            devices[primary.serial] = primary
            for alias in merged_aliases:
                aliases[alias] = primary.serial

        self.devices = devices
        self.aliases = {
            alias: target
            for alias, target in aliases.items()
            if alias and target and alias != target
        }

    def _merge_device_state_locked(self, primary: DeviceState, other: DeviceState) -> None:
        primary.bound = primary.bound or other.bound
        primary.discovered_at = min(primary.discovered_at, other.discovered_at)
        primary.last_seen_at = max(primary.last_seen_at, other.last_seen_at)
        primary.last_scan_at = max(primary.last_scan_at, other.last_scan_at)
        if primary.adb_state != "device" and other.adb_state == "device":
            primary.adb_state = other.adb_state
        if not primary.detail and other.detail:
            primary.detail = other.detail
        if not primary.android_id and other.android_id:
            primary.android_id = other.android_id
        if not primary.model and other.model:
            primary.model = other.model
        if not primary.current_focus and other.current_focus:
            primary.current_focus = other.current_focus
        if primary.screen_width is None and other.screen_width is not None:
            primary.screen_width = other.screen_width
        if primary.screen_height is None and other.screen_height is not None:
            primary.screen_height = other.screen_height
        primary.frame_count = max(primary.frame_count, other.frame_count)
        if (
            other.latest_frame_at is not None
            and (
                primary.latest_frame_at is None
                or other.latest_frame_at > primary.latest_frame_at
            )
        ):
            primary.latest_frame_at = other.latest_frame_at
            primary.latest_frame_path = other.latest_frame_path
            primary.latest_frame_bytes = other.latest_frame_bytes
        primary.name = f"{primary.serial} ({primary.model})" if primary.model else primary.serial

    def _refresh_details_locked(self, state: DeviceState, *, lightweight: bool) -> None:
        if state.adb_state != "device":
            return
        client = self.adb_client(state.serial)
        try:
            width, height = client.get_screen_size()
            state.screen_width = width
            state.screen_height = height
        except Exception:
            pass
        if lightweight and state.model and state.android_id:
            return
        try:
            state.model = client.shell(["getprop", "ro.product.model"], timeout=4.0).strip()
        except Exception:
            pass
        try:
            android_id = client.shell(
                ["settings", "get", "secure", "android_id"],
                timeout=4.0,
            ).strip()
            if android_id and android_id.lower() not in {"null", "unknown"}:
                state.android_id = android_id
        except Exception:
            pass
        try:
            state.current_focus = client.current_focus()
        except Exception:
            pass
        state.name = f"{state.serial} ({state.model})" if state.model else state.serial

    def _get_device_locked(self, device_id: str) -> DeviceState:
        key = device_id.strip()
        state = self.devices.get(self._canonical_serial_locked(key)) or self.devices.get(key)
        if state is None:
            raise KeyError(f"Unknown ADB device: {key}")
        return state

    def _canonical_serial_locked(self, serial: str) -> str:
        key = serial.strip()
        seen: set[str] = set()
        while key in self.aliases and key not in seen:
            seen.add(key)
            key = self.aliases[key]
        return key

    @classmethod
    def _physical_device_key(cls, state: DeviceState) -> str:
        emulator_adb_port = cls._local_emulator_adb_port(state.serial)
        if emulator_adb_port is not None:
            return f"local-emulator-adb-port:{emulator_adb_port}"
        return f"serial:{state.serial}"

    @staticmethod
    def _local_emulator_adb_port(serial: str) -> int | None:
        serial = serial.strip()
        if serial.startswith("emulator-"):
            try:
                console_port = int(serial.split("-", 1)[1])
            except ValueError:
                return None
            return console_port + 1
        for prefix in ("127.0.0.1:", "localhost:"):
            if serial.startswith(prefix):
                try:
                    return int(serial.removeprefix(prefix))
                except ValueError:
                    return None
        return None

    @classmethod
    def _device_state_preference_key(cls, state: DeviceState) -> tuple[int, float, int, str]:
        return (
            0 if state.adb_state == "device" else 1,
            -state.last_scan_at,
            cls._serial_preference_rank(state.serial),
            state.serial,
        )

    @staticmethod
    def _serial_preference_rank(serial: str) -> int:
        if serial.startswith("emulator-"):
            return 0
        if ":" not in serial:
            return 1
        if serial.startswith("127.0.0.1:") or serial.startswith("localhost:"):
            return 2
        return 3

    @staticmethod
    def _device_sort_key(device: AdbDevice) -> tuple[int, str]:
        return (0 if device.serial.startswith("emulator-") else 1, device.serial)

    @staticmethod
    def _apply_status_locked(state: DeviceState, status: dict[str, Any]) -> None:
        width = status.get("screen_width")
        height = status.get("screen_height")
        try:
            if width is not None:
                state.screen_width = int(width)
            if height is not None:
                state.screen_height = int(height)
        except (TypeError, ValueError):
            return


def build_adb_bot(registry: DeviceRegistry, device_id: str | None):
    from emulator_bot.bot import EmulatorBot
    from emulator_bot.config import BotConfig

    serial = registry.resolve_device_id(device_id)
    registry.ensure_bound(serial)
    base_dir = LOG_ROOT / "devices" / safe_file_id(serial)
    config = BotConfig(
        adb_path=registry.adb_path,
        device_serial=serial,
        screenshot_dir=base_dir / "screenshots",
        debug_dir=base_dir / "debug",
        template_dir=REPO_ROOT / "assets" / "templates",
        click_jitter_pixels=0,
    )
    config.ensure_dirs()
    return EmulatorBot(AdbClient(registry.adb_path, serial), config)
