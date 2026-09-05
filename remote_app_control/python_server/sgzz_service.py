from __future__ import annotations

import json
import os
import shutil
import sys
import threading
import traceback
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from time import sleep, time
from typing import Any

import cv2
import numpy as np

from remote_bot import DeviceRegistry, LOG_ROOT, build_adb_bot


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from emulator_bot.sgzz import (  # noqa: E402
    SGZZ_FLOW_NODES,
    SGZZ_PACKAGE,
    SGZZStartAccountRunner,
    SGZZStopRequested,
    load_sgzz_account_credentials,
    mask_sgzz_account,
    resolve_sgzz_accounts_file,
    sgzz_account_key,
)
from emulator_bot.vision import match_template  # noqa: E402


ASSETS_DIR = REPO_ROOT / "assets" / "templates"
SGZZ_TEMPLATE_DIR = ASSETS_DIR / "sgzz"
SGZZ_PROGRESS_LINE_LIMIT = 300
SGZZ_JOB_HEARTBEAT_SECONDS = 8.0
SGZZ_ACCOUNT_LIKE_STATUS_PATH = LOG_ROOT / "sgzz_account_like_status.json"
SGZZ_SELECTED_ACCOUNTS_DIR = LOG_ROOT / "selected_accounts"
PROJECT_LOG_ROOT = REPO_ROOT / "logs"
SGZZ_LOG_CLEANUP_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "off", "no"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def _path_is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _safe_remove_log_path(path: Path) -> int:
    if not path.exists() or not _path_is_under(path, PROJECT_LOG_ROOT):
        return 0
    if path.resolve() == PROJECT_LOG_ROOT.resolve():
        return 0
    size = _path_size_bytes(path)
    try:
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
    except OSError:
        return 0
    return size


def _path_size_bytes(path: Path) -> int:
    try:
        if path.is_file():
            return int(path.stat().st_size)
        total = 0
        for child in path.rglob("*"):
            if child.is_file():
                try:
                    total += int(child.stat().st_size)
                except OSError:
                    continue
        return total
    except OSError:
        return 0


def _is_active_path(path: Path, active_run_dirs: set[Path]) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for active in active_run_dirs:
        try:
            active_resolved = active.resolve()
            if resolved == active_resolved:
                return True
            resolved.relative_to(active_resolved)
            return True
        except OSError:
            continue
        except ValueError:
            continue
    return False


def _run_dir_candidates(active_run_dirs: set[Path]) -> list[Path]:
    runs: list[Path] = []
    devices_root = LOG_ROOT / "devices"
    if not devices_root.exists():
        return runs
    for path in devices_root.glob("*/sgzz_runs/*"):
        if (
            path.is_dir()
            and path.name
            and len(path.name) == 15
            and path.name[8] == "_"
            and path.name.replace("_", "").isdigit()
            and not _is_active_path(path, active_run_dirs)
        ):
            runs.append(path)
    return runs


def prune_project_logs(active_run_dirs: set[Path] | None = None) -> dict[str, object]:
    if not _env_bool("SGZZ_LOG_ROLLING_CLEANUP", True):
        return {"enabled": False, "deleted_count": 0, "deleted_bytes": 0}
    if not PROJECT_LOG_ROOT.exists():
        return {"enabled": True, "deleted_count": 0, "deleted_bytes": 0, "remaining_bytes": 0}

    active_run_dirs = active_run_dirs or set()
    max_total_bytes = int(max(200.0, _env_float("SGZZ_LOG_MAX_TOTAL_MB", 1200.0)) * 1024 * 1024)
    keep_runs_per_device = max(0, _env_int("SGZZ_LOG_KEEP_COMPLETED_RUNS_PER_DEVICE", 1))

    delete_targets: list[Path] = []
    for path in (
        PROJECT_LOG_ROOT / "sgzz_runs",
        PROJECT_LOG_ROOT / "screenshots",
    ):
        if path.exists() and not _is_active_path(path, active_run_dirs):
            delete_targets.append(path)

    for path in PROJECT_LOG_ROOT.iterdir():
        if path.is_file() and path.suffix.lower() in SGZZ_LOG_CLEANUP_IMAGE_SUFFIXES:
            delete_targets.append(path)

    runs_by_parent: dict[Path, list[Path]] = {}
    for run_dir in _run_dir_candidates(active_run_dirs):
        runs_by_parent.setdefault(run_dir.parent, []).append(run_dir)
    for run_dirs in runs_by_parent.values():
        run_dirs.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0.0, reverse=True)
        delete_targets.extend(run_dirs[keep_runs_per_device:])

    remaining_bytes = _path_size_bytes(PROJECT_LOG_ROOT)
    if remaining_bytes > max_total_bytes:
        protected = {path.resolve() for path in delete_targets}
        extra_targets = [
            run_dir
            for run_dir in _run_dir_candidates(active_run_dirs)
            if run_dir.resolve() not in protected
        ]
        extra_targets.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0.0)
        for path in extra_targets:
            if remaining_bytes <= max_total_bytes:
                break
            delete_targets.append(path)
            remaining_bytes -= _path_size_bytes(path)

    deleted_count = 0
    deleted_bytes = 0
    for path in dict.fromkeys(delete_targets):
        removed = _safe_remove_log_path(path)
        if removed > 0:
            deleted_count += 1
            deleted_bytes += removed

    return {
        "enabled": True,
        "deleted_count": deleted_count,
        "deleted_bytes": deleted_bytes,
        "deleted_mb": round(deleted_bytes / 1024 / 1024, 2),
        "remaining_bytes": _path_size_bytes(PROJECT_LOG_ROOT),
        "max_total_mb": round(max_total_bytes / 1024 / 1024, 2),
    }


@dataclass(frozen=True)
class SGZZTemplateRule:
    key: str
    template: str
    stage: str
    title: str
    next_action: str
    threshold: float = 0.78


SGZZ_TEMPLATE_RULES: tuple[SGZZTemplateRule, ...] = (
    SGZZTemplateRule(
        key="restore_cancel",
        template="restore_cancel_button.png",
        stage="restore_prompt",
        title="恢复角色弹窗",
        next_action="点取消，回到标题页",
    ),
    SGZZTemplateRule(
        key="title_select_server",
        template="title_select_server.png",
        stage="title_select_server",
        title="标题页-选服",
        next_action="打开选服，选择普通赛季1最新服",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="title_enter",
        template="title_enter_button.png",
        stage="title_enter",
        title="标题页-前往征战",
        next_action="进入已选服务器",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="server_selector",
        template="server_selector_title.png",
        stage="server_selector",
        title="选服弹窗",
        next_action="点赛季1，再点左上第一服并确认",
    ),
    SGZZTemplateRule(
        key="season1_tab",
        template="season1_tab.png",
        stage="season1_tab",
        title="赛季1选择",
        next_action="快速点最新普通 S1 服务器",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="queue",
        template="queue_title.png",
        stage="queue",
        title="服务器排队",
        next_action="等待自动进入",
    ),
    SGZZTemplateRule(
        key="old_man",
        template="old_man_marker.png",
        stage="old_man_intro",
        title="老者剧情",
        next_action="连续点继续；问答默认点顶部选项",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="avatar_confirm",
        template="avatar_confirm_button.png",
        stage="avatar_confirm",
        title="头像确认",
        next_action="确认头像",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="name_enter",
        template="name_enter_button.png",
        stage="name_enter",
        title="起名页",
        next_action="提交随机名，进入乱世",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="region_select",
        template="region_select_title.png",
        stage="region_select",
        title="落州选择",
        next_action="选择西凉并确认",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="xiliang_enter",
        template="xiliang_enter_button.png",
        stage="xiliang_enter",
        title="西凉确认",
        next_action="点入驻西凉",
        threshold=0.76,
    ),
    SGZZTemplateRule(
        key="chapter_next",
        template="chapter_next_button.png",
        stage="chapter_next",
        title="章节页",
        next_action="点下一步",
        threshold=0.74,
    ),
    SGZZTemplateRule(
        key="recruit",
        template="recruit_button.png",
        stage="map_recruit",
        title="地图招募入口",
        next_action="进入招募并完成免费招募",
        threshold=0.76,
    ),
)


@dataclass(frozen=True)
class SGZZStageMatch:
    key: str
    stage: str
    title: str
    next_action: str
    score: float
    x: int
    y: int
    width: int
    height: int


@dataclass
class SGZZJobState:
    device_id: str
    state: str = "idle"
    command: str | None = None
    mode: str | None = None
    accounts_file: str | None = None
    max_cycles_per_account: int | None = None
    include_gacha: bool | None = None
    include_gamecircle_signin: bool | None = None
    selected_account_count: int | None = None
    selected_account_keys: list[str] | None = None
    stop_requested: bool = False
    started_at: str | None = None
    finished_at: str | None = None
    record_path: str | None = None
    error: str | None = None
    traceback: str | None = None
    progress_lines: list[str] = field(default_factory=list)
    progress_first_seq: int = 1
    progress_next_seq: int = 1


def _short_text(value: object, *, max_length: int = 90) -> str:
    text = str(value)
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _event_details(event: dict[str, object], keys: tuple[str, ...]) -> str:
    parts: list[str] = []
    for key in keys:
        if key not in event:
            continue
        value = event[key]
        if value is None:
            continue
        parts.append(f"{key}={_short_text(value)}")
    return f" ({', '.join(parts)})" if parts else ""


def format_sgzz_progress_event(event: dict[str, object]) -> str | None:
    event_type = str(event.get("type") or "")

    if event_type == "state":
        state = str(event.get("state") or "")
        if not state:
            return None
        details = _event_details(
            event,
            (
                "node",
                "source",
                "package",
                "path",
                "include_gacha",
                "include_gamecircle_signin",
                "iteration",
                "processed_cycles",
                "processed_offset",
                "processed_this_run",
                "index",
                "account",
                "account_count",
                "pending_count",
                "skipped_liked_count",
                "total_count",
                "line_number",
                "max_cycles",
                "max_steps",
                "reason",
                "selected_count",
                "recovered",
                "daily_like_done_count",
                "account_like_completed",
                "completion_reason",
                "process_bootstrap_current_role",
                "process_current_role_before_switch",
                "elapsed_seconds",
                "timeout_seconds",
                "remaining_seconds",
                "like_limit_reached",
                "like_limit_stop_reached",
                "like_limit_consecutive_count",
                "like_limit_stop_threshold",
                "dark_ratio",
                "mean",
                "edge_ratio",
                "restart_count",
                "restart_limit",
                "deleted_count",
                "deleted_files",
                "deleted_mb",
                "keep_images",
                "max_mb",
                "error",
            ),
        )
        return f"脚本状态: {state}{details}"

    if event_type == "flow_node":
        node = str(event.get("node") or "")
        details = _event_details(event, ("step_count", "error"))
        return f"节点流程: {node}{details}" if node else f"节点流程{details}"

    if event_type == "screenshot":
        label = str(event.get("label") or "")
        path = Path(str(event.get("path") or "")).name if event.get("path") else ""
        suffix = f" -> {path}" if path else ""
        return f"截图: {label}{suffix}" if label else None

    if event_type == "screenshot_crop":
        label = str(event.get("label") or "")
        details = _event_details(event, ("x", "y", "width", "height"))
        return f"截图裁剪: {label}{details}" if label else None

    if event_type == "tap":
        label = str(event.get("label") or "")
        details = _event_details(event, ("x", "y", "step"))
        return f"点击: {label}{details}" if label else f"点击{details}"

    if event_type == "swipe":
        label = str(event.get("label") or "")
        details = _event_details(
            event,
            ("x1", "y1", "x2", "y2", "start_x", "start_y", "end_x", "end_y", "duration_ms", "attempt"),
        )
        return f"滑动: {label}{details}" if label else f"滑动{details}"

    if event_type == "keyevent":
        label = str(event.get("label") or "")
        details = _event_details(event, ("keycode", "source"))
        return f"按键: {label}{details}" if label else f"按键{details}"

    if event_type == "match":
        label = str(event.get("label") or event.get("template") or "")
        details = _event_details(event, ("score", "x", "y", "width", "height"))
        return f"识别命中: {label}{details}" if label else f"识别命中{details}"

    if event_type == "match_miss":
        timeout = event.get("timeout_seconds")
        try:
            if timeout is not None and float(timeout) < 0.5:
                return None
        except (TypeError, ValueError):
            pass
        label = str(event.get("label") or event.get("template") or "")
        details = _event_details(event, ("timeout_seconds",))
        return f"识别未命中: {label}{details}" if label else f"识别未命中{details}"

    if event_type == "vision_feature":
        feature = str(event.get("feature") or "")
        details = _event_details(
            event,
            (
                "present",
                "branch",
                "classification",
                "reason",
                "orange_present",
                "orange_arrow_present",
                "source",
                "handled",
                "closed",
                "done",
                "claimed",
                "confirmed",
                "already_signed",
                "clicked",
                "found",
                "loaded",
                "selected",
                "success",
                "skipped",
                "detail_closed",
                "limit_reached",
                "like_limit_reached",
                "like_limit_consecutive_count",
                "like_limit_stop_threshold",
                "score",
                "free_score",
                "half_score",
                "half_badge_score",
                "x",
                "y",
                "width",
                "height",
                "badge_x",
                "badge_y",
                "tap_x",
                "tap_y",
                "error",
            ),
        )
        return f"辅助识别: {feature}{details}" if feature else f"辅助识别{details}"

    return None


def attach_progress_logger(
    runner: SGZZStartAccountRunner,
    progress_logger: Callable[[dict[str, object]], None] | None,
) -> None:
    if progress_logger is None:
        return

    original_record = runner._record

    def record_with_progress(event: dict[str, object]) -> None:
        original_record(event)
        try:
            progress_logger(event)
        except Exception:
            return

    runner._record = record_with_progress  # type: ignore[method-assign]


def build_sgzz_runner(
    registry: DeviceRegistry,
    device_id: str | None,
    *,
    stop_requested: Callable[[], bool] | None = None,
    progress_logger: Callable[[dict[str, object]], None] | None = None,
):
    bot = build_adb_bot(registry, registry.resolve_device_id(device_id))
    runner = SGZZStartAccountRunner(bot, package=SGZZ_PACKAGE, stop_requested=stop_requested)
    attach_progress_logger(runner, progress_logger)
    if progress_logger is not None:
        progress_logger(
            {
                "type": "state",
                "state": "record_file",
                "path": str(runner.record_path),
            }
        )
    return bot, runner


def parse_sgzz_accounts_text(text: str) -> list[dict[str, Any]]:
    accounts: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "#" not in line:
            raise ValueError(
                f"Invalid SGZZ account config at line {line_number}: expected account#password."
            )
        account, password = [part.strip() for part in line.split("#", 1)]
        if not account or not password:
            raise ValueError(
                f"Invalid SGZZ account config at line {line_number}: account and password are required."
            )
        accounts.append(
            {
                "line_number": line_number,
                "account": account,
                "account_key": sgzz_account_key(account),
                "masked_account": mask_sgzz_account(account),
                "password_length": len(password),
            }
        )
    if not accounts:
        raise ValueError("SGZZ account config has no usable accounts.")
    return accounts


def today_key() -> str:
    return datetime.now().date().isoformat()


def _empty_account_like_state() -> dict[str, Any]:
    return {"date": today_key(), "liked": {}}


def _read_account_like_state() -> dict[str, Any]:
    if not SGZZ_ACCOUNT_LIKE_STATUS_PATH.exists():
        return _empty_account_like_state()
    try:
        payload = json.loads(SGZZ_ACCOUNT_LIKE_STATUS_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return _empty_account_like_state()
    if not isinstance(payload, dict):
        return _empty_account_like_state()
    if payload.get("date") != today_key():
        state = _empty_account_like_state()
        _write_account_like_state(state)
        return state
    liked = payload.get("liked")
    if not isinstance(liked, dict):
        payload["liked"] = {}
    return payload


def _write_account_like_state(payload: dict[str, Any]) -> None:
    SGZZ_ACCOUNT_LIKE_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SGZZ_ACCOUNT_LIKE_STATUS_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def read_account_like_status() -> dict[str, Any]:
    payload = _read_account_like_state()
    liked = payload.get("liked") if isinstance(payload.get("liked"), dict) else {}
    return {
        "date": payload.get("date") or today_key(),
        "liked": liked,
        "status_path": str(SGZZ_ACCOUNT_LIKE_STATUS_PATH),
    }


def clear_account_like_status() -> dict[str, Any]:
    payload = _empty_account_like_state()
    _write_account_like_state(payload)
    return read_account_like_status()


def mark_account_liked_today(account_key: str, masked_account: str = "") -> dict[str, Any]:
    key = str(account_key or "").strip()
    if not key:
        return read_account_like_status()
    payload = _read_account_like_state()
    liked = payload.setdefault("liked", {})
    if not isinstance(liked, dict):
        liked = {}
        payload["liked"] = liked
    liked[key] = {
        "account": str(masked_account or "").strip(),
        "completed_at": datetime.now().isoformat(timespec="seconds"),
    }
    _write_account_like_state(payload)
    return read_account_like_status()


def set_account_liked_today(
    account_key: str,
    liked: bool,
    masked_account: str = "",
) -> dict[str, Any]:
    key = str(account_key or "").strip()
    if not key:
        raise ValueError("account_key is required")
    if liked:
        return mark_account_liked_today(key, masked_account)

    payload = _read_account_like_state()
    liked_map = payload.setdefault("liked", {})
    if not isinstance(liked_map, dict):
        liked_map = {}
        payload["liked"] = liked_map
    liked_map.pop(key, None)
    _write_account_like_state(payload)
    return read_account_like_status()


def write_selected_accounts_file(
    accounts_file: str | None,
    selected_account_keys: list[str] | None,
) -> dict[str, Any]:
    if selected_account_keys is None:
        return {
            "path": str(resolve_sgzz_accounts_file(accounts_file)),
            "account_count": None,
            "accounts": [],
        }

    selected = {str(key).strip() for key in selected_account_keys if str(key).strip()}
    if not selected:
        raise ValueError("No SGZZ accounts are selected.")

    credentials = load_sgzz_account_credentials(accounts_file)
    picked = [credential for credential in credentials if credential.account_key in selected]
    if not picked:
        raise ValueError("Selected SGZZ accounts were not found in the account file.")

    SGZZ_SELECTED_ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    path = SGZZ_SELECTED_ACCOUNTS_DIR / (
        f"sgzz_selected_accounts_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time() * 1000)}.txt"
    )
    text = "".join(f"{credential.account}#{credential.password}\n" for credential in picked)
    path.write_text(text, encoding="utf-8")
    return {
        "path": str(path),
        "account_count": len(picked),
        "accounts": [
            {
                "line_number": credential.line_number,
                "account_key": credential.account_key,
                "masked_account": credential.masked_account,
            }
            for credential in picked
        ],
    }


def read_accounts_config(accounts_file: str | None = None) -> dict[str, Any]:
    account_path = resolve_sgzz_accounts_file(accounts_file)
    text = account_path.read_text(encoding="utf-8") if account_path.exists() else ""
    accounts = parse_sgzz_accounts_text(text) if text.strip() else []
    like_status = read_account_like_status()
    liked = like_status["liked"]
    for account in accounts:
        liked_payload = liked.get(account["account_key"]) if isinstance(liked, dict) else None
        account["liked_today"] = bool(liked_payload)
        account["liked_at"] = (
            liked_payload.get("completed_at")
            if isinstance(liked_payload, dict)
            else None
        )
    return {
        "path": str(account_path),
        "accounts_text": text,
        "account_count": len(accounts),
        "accounts": accounts,
        "like_date": like_status["date"],
        "like_status_path": like_status["status_path"],
    }


def pending_account_keys_for_today(accounts_file: str | None = None) -> dict[str, Any]:
    config = read_accounts_config(accounts_file)
    accounts = list(config["accounts"])
    pending = [account for account in accounts if not bool(account.get("liked_today"))]
    return {
        "account_count": len(accounts),
        "pending_count": len(pending),
        "skipped_liked_count": len(accounts) - len(pending),
        "account_keys": [str(account["account_key"]) for account in pending],
        "accounts": pending,
    }


def write_accounts_config(accounts_text: str, accounts_file: str | None = None) -> dict[str, Any]:
    accounts = parse_sgzz_accounts_text(accounts_text)
    account_path = resolve_sgzz_accounts_file(accounts_file)
    account_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = accounts_text.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    account_path.write_text(normalized, encoding="utf-8")
    return read_accounts_config(str(account_path))


def detect_sgzz_stage(image: np.ndarray) -> dict[str, Any] | None:
    matches: list[SGZZStageMatch] = []
    for rule in SGZZ_TEMPLATE_RULES:
        template_path = SGZZ_TEMPLATE_DIR / rule.template
        if not template_path.exists():
            continue
        try:
            match = match_template(image, template_path, threshold=rule.threshold)
        except (FileNotFoundError, RuntimeError, cv2.error):
            continue
        if match is None:
            continue
        matches.append(
            SGZZStageMatch(
                key=rule.key,
                stage=rule.stage,
                title=rule.title,
                next_action=rule.next_action,
                score=float(match.score),
                x=match.x,
                y=match.y,
                width=match.width,
                height=match.height,
            )
        )

    if not matches:
        return None

    best = max(matches, key=lambda item: item.score)
    return {
        "label": f"sgzz:{best.stage}",
        "confidence": round(best.score, 3),
        "summary": f"{best.title}; 下一步: {best.next_action}",
        "sgzz": {
            "stage": best.stage,
            "title": best.title,
            "next_action": best.next_action,
            "best": asdict(best),
            "matches": [
                asdict(match)
                for match in sorted(matches, key=lambda item: item.score, reverse=True)[:5]
            ],
        },
    }


def detect_sgzz_from_device(registry: DeviceRegistry, device_id: str | None = None) -> dict[str, Any]:
    bot = build_adb_bot(registry, registry.resolve_device_id(device_id))
    image = bot.screenshot_image()
    stage = detect_sgzz_stage(image)
    if stage is None:
        stage = {
            "label": "sgzz:unknown",
            "confidence": 0.0,
            "summary": "未识别到已封装的三国志起号节点",
            "sgzz": {"stage": "unknown", "title": "未知", "next_action": "检查游戏画面或补充模板"},
        }
    stage["screen"] = {"width": int(image.shape[1]), "height": int(image.shape[0])}
    stage["device"] = bot.client.serial
    return stage


def wait_for_start_entry_screen(
    bot,
    *,
    timeout_seconds: float = 70.0,
    stop_requested: Callable[[], bool] | None = None,
) -> str:
    allowed_stages = {"restore_prompt", "title_select_server", "title_enter"}
    last_stage = "unknown"
    end_at = time() + timeout_seconds
    while time() < end_at:
        if stop_requested is not None and stop_requested():
            raise SGZZStopRequested("SGZZ job stop requested.")
        image = bot.screenshot_image()
        result = detect_sgzz_stage(image)
        if result is not None:
            stage = str(result.get("sgzz", {}).get("stage", "unknown"))
            last_stage = stage
            if stage in allowed_stages:
                return stage
        for _ in range(4):
            if stop_requested is not None and stop_requested():
                raise SGZZStopRequested("SGZZ job stop requested.")
            sleep(0.5)
    raise RuntimeError(
        "SGZZ start-account preflight failed: current screen is not title/server-entry. "
        f"last_stage={last_stage}. Return to the title screen or switch to a fresh account first."
    )


def run_start_account(
    registry: DeviceRegistry,
    *,
    mode: str = "entry",
    device_id: str | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress_logger: Callable[[dict[str, object]], None] | None = None,
) -> str:
    bot, runner = build_sgzz_runner(
        registry,
        device_id,
        stop_requested=stop_requested,
        progress_logger=progress_logger,
    )

    if mode == "entry":
        runner.launch(wait_seconds=8.0)
        wait_for_start_entry_screen(bot, stop_requested=stop_requested)
        return str(
            runner.select_and_enter_latest_s1(
                launch=False,
                launch_wait_seconds=8.0,
                cancel_restore=True,
                season1_taps=2,
                enter=True,
                enter_wait_seconds=5.0,
                queue_wait_seconds=0.0,
            )
        )

    if mode == "bootstrap":
        runner.launch(wait_seconds=8.0)
        wait_for_start_entry_screen(bot, stop_requested=stop_requested)
        runner.select_and_enter_latest_s1(
            launch=False,
            launch_wait_seconds=8.0,
            cancel_restore=True,
            season1_taps=2,
            enter=True,
            enter_wait_seconds=5.0,
            queue_wait_seconds=0.0,
        )
        runner.continue_old_man_until_blocked(max_taps=30, interval_seconds=0.65)
        runner.answer_old_man_quiz(choices=[1, 1, 1, 1, 1], interval_seconds=0.9)
        runner.confirm_avatar()
        runner.submit_random_name()
        runner.continue_old_man_until_blocked(max_taps=10, interval_seconds=0.7)
        runner.select_xiliang_region()
        runner.tap_chapter_next()
        runner.continue_scout_until_blocked(max_taps=20, interval_seconds=0.65)
        runner.continue_zhuge_until_blocked(max_taps=20, interval_seconds=0.65)
        runner.confirm_resource_prompt()
        runner.select_main_city_and_enter()
        runner.recruit_free_twice()
        runner.configure_initial_team()
        return str(runner.record_path)

    raise ValueError(f"Unsupported SGZZ start mode: {mode}")


def run_launch_game(
    registry: DeviceRegistry,
    *,
    device_id: str | None = None,
    stop_requested: Callable[[], bool] | None = None,
    progress_logger: Callable[[dict[str, object]], None] | None = None,
) -> str:
    _bot, runner = build_sgzz_runner(
        registry,
        device_id,
        stop_requested=stop_requested,
        progress_logger=progress_logger,
    )
    runner.launch(wait_seconds=8.0)
    return str(runner.record_path)


def run_account_batch(
    registry: DeviceRegistry,
    *,
    accounts_file: str | None = None,
    selected_account_keys: list[str] | None = None,
    device_id: str | None = None,
    max_cycles_per_account: int | None = None,
    include_gacha: bool = True,
    include_gamecircle_signin: bool = False,
    stop_requested: Callable[[], bool] | None = None,
    progress_logger: Callable[[dict[str, object]], None] | None = None,
) -> str:
    _bot, runner = build_sgzz_runner(
        registry,
        device_id,
        stop_requested=stop_requested,
        progress_logger=progress_logger,
    )
    max_cycles = max_cycles_per_account or 80
    if selected_account_keys is None:
        pending_info = pending_account_keys_for_today(accounts_file)
        selected_account_keys = list(pending_info["account_keys"])
        if progress_logger is not None:
            progress_logger(
                {
                    "type": "state",
                    "state": "account_batch_pending_accounts",
                    "source": "liked_today_filter",
                    "account_count": pending_info["account_count"],
                    "pending_count": pending_info["pending_count"],
                    "skipped_liked_count": pending_info["skipped_liked_count"],
                }
            )
        if not selected_account_keys:
            raise ValueError("No SGZZ accounts are pending today.")

    selected_info = write_selected_accounts_file(accounts_file, selected_account_keys)
    actual_accounts_file = str(selected_info["path"])
    if progress_logger is not None:
        progress_logger(
            {
                "type": "state",
                "state": "account_batch_selected_accounts",
                "path": actual_accounts_file,
                "selected_count": selected_info["account_count"],
                "account_count": selected_info["account_count"],
            }
        )
    return str(
        runner.run_account_batch_remaining_roles_daily_cycle(
            accounts_file=actual_accounts_file,
            max_cycles_per_account=max_cycles,
            include_gacha=include_gacha,
            include_gamecircle_signin=include_gamecircle_signin,
        )
    )


def run_flow_node(
    registry: DeviceRegistry,
    *,
    node: str,
    device_id: str | None = None,
    include_gacha: bool = True,
    include_gamecircle_signin: bool = False,
    stop_requested: Callable[[], bool] | None = None,
    progress_logger: Callable[[dict[str, object]], None] | None = None,
) -> str:
    _bot, runner = build_sgzz_runner(
        registry,
        device_id,
        stop_requested=stop_requested,
        progress_logger=progress_logger,
    )

    if node == "select_latest_s1":
        return str(runner.select_and_enter_latest_s1())
    if node == "continue_old_man":
        return str(runner.continue_old_man_until_blocked())
    if node == "answer_old_man_quiz":
        return str(runner.answer_old_man_quiz(choices=[1, 1, 1, 1, 1]))
    if node == "create_character_xiliang":
        runner.confirm_avatar()
        runner.submit_random_name()
        runner.continue_old_man_until_blocked(max_taps=10)
        runner.select_xiliang_region()
        return str(runner.record_path)
    if node == "chapter_next":
        return str(runner.tap_chapter_next())
    if node == "continue_scout":
        return str(runner.continue_scout_until_blocked())
    if node == "continue_zhuge":
        return str(runner.continue_zhuge_until_blocked())
    if node == "daily_signin_like_gacha":
        runner.launch(wait_seconds=8.0)
        return str(
            runner.run_daily_signin_like_gacha(
                include_gacha=include_gacha,
                include_gamecircle_signin=include_gamecircle_signin,
            )
        )
    return str(runner.run_flow_node(node))


def list_flow_nodes() -> list[dict[str, str]]:
    extra = [
        {
            "node": "select_latest_s1",
            "detect": "标题页/选服弹窗/赛季1标签",
            "action": "启动游戏，进入普通赛季1最新服，点前往征战",
        },
        {
            "node": "continue_old_man",
            "detect": "old_man_marker.png",
            "action": "老者在场时连续点继续",
        },
        {
            "node": "answer_old_man_quiz",
            "detect": "老者问答",
            "action": "默认连续选择顶部选项",
        },
        {
            "node": "create_character_xiliang",
            "detect": "头像确认/进入乱世/落州页",
            "action": "确认头像，提交随机名，选择西凉",
        },
        {
            "node": "chapter_next",
            "detect": "chapter_next_button.png",
            "action": "点章节下一步",
        },
        {
            "node": "continue_scout",
            "detect": "scout_marker.png",
            "action": "斥候剧情连续继续",
        },
        {
            "node": "continue_zhuge",
            "detect": "zhuge_marker.png",
            "action": "诸葛亮剧情连续继续",
        },
    ]
    existing = [dict(item) for item in SGZZ_FLOW_NODES]
    known = {item["node"] for item in extra}
    return extra + [item for item in existing if item["node"] not in known]


@dataclass
class SGZZRemoteJobManager:
    registry: DeviceRegistry
    lock: threading.RLock = field(default_factory=threading.RLock)
    jobs: dict[str, SGZZJobState] = field(default_factory=dict)
    stop_events: dict[str, threading.Event] = field(default_factory=dict)
    log_cleanup_lock: threading.Lock = field(default_factory=threading.Lock)
    log_cleanup_last_at: float = 0.0

    def snapshot(self, device_id: str | None = None) -> dict[str, Any]:
        with self.lock:
            if device_id:
                resolved = self.registry.resolve_device_id(device_id)
                state = self.jobs.get(resolved, SGZZJobState(device_id=resolved))
                payload = asdict(state)
                payload["stop_requested"] = self.stop_events.get(resolved, threading.Event()).is_set()
                payload["nodes"] = list_flow_nodes()
                return payload
            jobs = []
            for state in self.jobs.values():
                payload = asdict(state)
                payload["stop_requested"] = self.stop_events.get(state.device_id, threading.Event()).is_set()
                jobs.append(payload)
        return {"jobs": jobs, "nodes": list_flow_nodes()}

    def request_stop(self, device_id: str | None = None) -> dict[str, Any]:
        targets: list[str]
        with self.lock:
            if device_id:
                targets = [self.registry.resolve_device_id(device_id)]
            else:
                targets = [
                    key
                    for key, state in self.jobs.items()
                    if state.state in {"running", "stopping"}
                ]
            if not targets:
                return {"ok": True, "message": "no sgzz job is running", "jobs": self.snapshot()}
            for target in targets:
                event = self.stop_events.setdefault(target, threading.Event())
                event.set()
                state = self.jobs.setdefault(target, SGZZJobState(device_id=target))
                if state.state in {"running", "stopping"}:
                    state.state = "stopping"
                    state.stop_requested = True
        return {"ok": True, "message": "stop requested", "jobs": self.snapshot()}

    def is_running(self, device_id: str) -> bool:
        try:
            resolved = self.registry.resolve_device_id(device_id)
        except Exception:
            resolved = device_id
        with self.lock:
            state = self.jobs.get(resolved)
            return state is not None and state.state in {"running", "stopping"}

    def start_start_account(self, *, mode: str = "entry", device_id: str | None = None) -> dict[str, Any]:
        return self._start(command="start_account", mode=mode, device_id=device_id)

    def start_launch_game(self, *, device_id: str | None = None) -> dict[str, Any]:
        return self._start(command="launch_game", mode="launch", device_id=device_id)

    def start_node(
        self,
        *,
        node: str,
        device_id: str | None = None,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
    ) -> dict[str, Any]:
        return self._start(
            command="flow_node",
            mode=node,
            device_id=device_id,
            include_gacha=include_gacha if node == "daily_signin_like_gacha" else None,
            include_gamecircle_signin=(
                include_gamecircle_signin
                if node in {"daily_signin_like_gacha", "gamecircle_signin"}
                else None
            ),
        )

    def start_account_batch(
        self,
        *,
        accounts_file: str | None = None,
        device_id: str | None = None,
        max_cycles_per_account: int | None = None,
        include_gacha: bool = True,
        include_gamecircle_signin: bool = False,
        selected_account_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._start(
            command="account_batch",
            mode="account_batch",
            device_id=device_id,
            accounts_file=accounts_file,
            max_cycles_per_account=max_cycles_per_account,
            include_gacha=include_gacha,
            include_gamecircle_signin=include_gamecircle_signin,
            selected_account_keys=selected_account_keys,
        )

    def _append_progress(
        self,
        device_id: str,
        message: str,
        *,
        record_path: str | None = None,
    ) -> None:
        if not message:
            return
        with self.lock:
            state = self.jobs.setdefault(device_id, SGZZJobState(device_id=device_id))
            if record_path:
                state.record_path = record_path
            if state.progress_lines and state.progress_lines[-1] == message:
                return
            state.progress_lines.append(message)
            state.progress_next_seq += 1
            if len(state.progress_lines) > SGZZ_PROGRESS_LINE_LIMIT:
                del state.progress_lines[: len(state.progress_lines) - SGZZ_PROGRESS_LINE_LIMIT]
            state.progress_first_seq = max(
                1,
                state.progress_next_seq - len(state.progress_lines),
            )

    def _publish_progress_event(self, device_id: str, event: dict[str, object]) -> None:
        message = format_sgzz_progress_event(event)
        if event.get("type") == "state" and event.get("state") == "account_batch_account_done":
            account_key = str(event.get("account_key") or "").strip()
            masked_account = str(event.get("account") or "").strip()
            if account_key and bool(event.get("account_like_completed")):
                mark_account_liked_today(account_key, masked_account)
                self._append_progress(device_id, f"今日点赞完成: {masked_account or account_key}")
            elif account_key:
                reason = str(event.get("completion_reason") or "unknown")
                done_count = event.get("daily_like_done_count")
                processed = event.get("processed_cycles")
                self._append_progress(
                    device_id,
                    (
                        f"今日点赞未标记完成: {masked_account or account_key} "
                        f"(reason={reason}, daily_like_done={done_count}, processed={processed})"
                    ),
                )
        if message is None:
            return
        record_path = None
        if event.get("type") == "state" and event.get("state") == "record_file":
            record_path = str(event.get("path") or "") or None
        self._append_progress(device_id, message, record_path=record_path)
        self._maybe_prune_logs(device_id=device_id)

    def _active_run_dirs(self) -> set[Path]:
        active: set[Path] = set()
        with self.lock:
            states = list(self.jobs.values())
        for state in states:
            if state.state not in {"running", "stopping"} or not state.record_path:
                continue
            run_dir = Path(state.record_path).parent
            if run_dir.exists():
                active.add(run_dir.resolve())
        return active

    def _maybe_prune_logs(self, *, device_id: str | None = None, force: bool = False) -> None:
        if not _env_bool("SGZZ_LOG_ROLLING_CLEANUP", True):
            return
        interval_seconds = max(5.0, _env_float("SGZZ_LOG_CLEANUP_INTERVAL_SECONDS", 60.0))
        now = time()
        with self.log_cleanup_lock:
            if not force and now - self.log_cleanup_last_at < interval_seconds:
                return
            self.log_cleanup_last_at = now
            active_run_dirs = self._active_run_dirs()
            summary = prune_project_logs(active_run_dirs)
        if not device_id or not summary.get("deleted_count"):
            return
        self._append_progress(
            device_id,
            (
                "日志滚动清理: "
                f"删除 {summary.get('deleted_mb')} MB / {summary.get('deleted_count')} 项，"
                f"上限 {summary.get('max_total_mb')} MB"
            ),
        )

    def _start(
        self,
        *,
        command: str,
        mode: str,
        device_id: str | None,
        accounts_file: str | None = None,
        max_cycles_per_account: int | None = None,
        include_gacha: bool | None = None,
        include_gamecircle_signin: bool | None = None,
        selected_account_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved = self.registry.resolve_device_id(device_id)
        normalized_selected_keys = (
            [str(key).strip() for key in selected_account_keys if str(key).strip()]
            if selected_account_keys is not None
            else None
        )
        with self.lock:
            current = self.jobs.get(resolved)
            if current is not None and current.state in {"running", "stopping"}:
                return {"ok": False, "error": f"sgzz job already running on {resolved}", "job": asdict(current)}
            stop_event = self.stop_events.setdefault(resolved, threading.Event())
            stop_event.clear()
            self.jobs[resolved] = SGZZJobState(
                device_id=resolved,
                state="running",
                command=command,
                mode=mode,
                accounts_file=accounts_file,
                max_cycles_per_account=max_cycles_per_account,
                include_gacha=include_gacha,
                include_gamecircle_signin=include_gamecircle_signin,
                selected_account_count=(
                    len(normalized_selected_keys)
                    if normalized_selected_keys is not None
                    else None
                ),
                selected_account_keys=normalized_selected_keys,
                started_at=datetime.now().isoformat(timespec="seconds"),
            )

        thread = threading.Thread(
            target=self._run_job,
            args=(
                resolved,
                command,
                mode,
                accounts_file,
                max_cycles_per_account,
                include_gacha,
                include_gamecircle_signin,
                normalized_selected_keys,
            ),
            name=f"adb-sgzz-{resolved}-{command}-{int(time())}",
            daemon=True,
        )
        thread.start()
        heartbeat_thread = threading.Thread(
            target=self._run_heartbeat,
            args=(resolved, command, mode, time()),
            name=f"adb-sgzz-{resolved}-{command}-heartbeat-{int(time())}",
            daemon=True,
        )
        heartbeat_thread.start()
        return {"ok": True, "job": self.snapshot(resolved)}

    def _run_heartbeat(
        self,
        device_id: str,
        command: str,
        mode: str,
        started_monotonic: float,
    ) -> None:
        while True:
            sleep(SGZZ_JOB_HEARTBEAT_SECONDS)
            with self.lock:
                state = self.jobs.get(device_id)
                if state is None or state.state not in {"running", "stopping"}:
                    return
                current_command = state.command or command
                current_mode = state.mode or mode
                line_count = len(state.progress_lines)
            elapsed = int(max(0.0, time() - started_monotonic))
            self._append_progress(
                device_id,
                f"运行心跳: {current_command}/{current_mode} 已运行 {elapsed}s，最近日志缓存 {line_count} 条",
            )
            self._maybe_prune_logs(device_id=device_id)

    def _run_job(
        self,
        device_id: str,
        command: str,
        mode: str,
        accounts_file: str | None,
        max_cycles_per_account: int | None,
        include_gacha: bool | None,
        include_gamecircle_signin: bool | None,
        selected_account_keys: list[str] | None,
    ) -> None:
        stop_event = self.stop_events.setdefault(device_id, threading.Event())
        stop_requested = stop_event.is_set
        progress_logger = lambda event: self._publish_progress_event(device_id, event)
        option_suffix_parts = []
        if include_gacha is not None:
            option_suffix_parts.append(f"抽卡={'开' if include_gacha else '关'}")
        if include_gamecircle_signin is not None:
            option_suffix_parts.append(f"签到={'开' if include_gamecircle_signin else '关'}")
        option_suffix = f" {' '.join(option_suffix_parts)}" if option_suffix_parts else ""
        self._append_progress(device_id, f"任务开始: {command}/{mode}{option_suffix}")
        self._maybe_prune_logs(device_id=device_id, force=True)
        try:
            if command == "start_account":
                record_path = run_start_account(
                    self.registry,
                    mode=mode,
                    device_id=device_id,
                    stop_requested=stop_requested,
                    progress_logger=progress_logger,
                )
            elif command == "flow_node":
                record_path = run_flow_node(
                    self.registry,
                    node=mode,
                    device_id=device_id,
                    include_gacha=True if include_gacha is None else include_gacha,
                    include_gamecircle_signin=(
                        False
                        if include_gamecircle_signin is None
                        else include_gamecircle_signin
                    ),
                    stop_requested=stop_requested,
                    progress_logger=progress_logger,
                )
            elif command == "launch_game":
                record_path = run_launch_game(
                    self.registry,
                    device_id=device_id,
                    stop_requested=stop_requested,
                    progress_logger=progress_logger,
                )
            elif command == "account_batch":
                record_path = run_account_batch(
                    self.registry,
                    accounts_file=accounts_file,
                    selected_account_keys=selected_account_keys,
                    device_id=device_id,
                    max_cycles_per_account=max_cycles_per_account,
                    include_gacha=True if include_gacha is None else include_gacha,
                    include_gamecircle_signin=(
                        False
                        if include_gamecircle_signin is None
                        else include_gamecircle_signin
                    ),
                    stop_requested=stop_requested,
                    progress_logger=progress_logger,
                )
            else:
                raise ValueError(f"Unsupported SGZZ command: {command}")

            self._append_progress(device_id, f"任务完成: {record_path}", record_path=record_path)
            self._maybe_prune_logs(device_id=device_id, force=True)
            with self.lock:
                state = self.jobs.setdefault(device_id, SGZZJobState(device_id=device_id))
                state.state = "done"
                state.finished_at = datetime.now().isoformat(timespec="seconds")
                state.record_path = record_path
                state.stop_requested = False
            stop_event.clear()
        except SGZZStopRequested as exc:
            self._append_progress(device_id, f"任务已停止: {exc}")
            self._maybe_prune_logs(device_id=device_id, force=True)
            with self.lock:
                state = self.jobs.setdefault(device_id, SGZZJobState(device_id=device_id))
                state.state = "stopped"
                state.finished_at = datetime.now().isoformat(timespec="seconds")
                state.error = str(exc)
                state.stop_requested = True
            stop_event.clear()
        except Exception as exc:  # noqa: BLE001 - this is a control service boundary.
            self._append_progress(device_id, f"任务失败: {exc}")
            self._maybe_prune_logs(device_id=device_id, force=True)
            with self.lock:
                state = self.jobs.setdefault(device_id, SGZZJobState(device_id=device_id))
                state.state = "error"
                state.finished_at = datetime.now().isoformat(timespec="seconds")
                state.error = str(exc)
                state.traceback = traceback.format_exc(limit=8)
            stop_event.clear()
