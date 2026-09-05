from __future__ import annotations

import argparse
import logging
import os
import sys
import threading
import traceback
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import END, BOTH, LEFT, RIGHT, X, Y, BooleanVar, IntVar, StringVar, Tk, Text
from tkinter import messagebox, ttk
from typing import Any, Callable

from werkzeug.serving import WSGIRequestHandler, make_server

from app import app as flask_app
from app import registry, sgzz_jobs
from remote_bot import LOG_ROOT, REPO_ROOT

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sgzz_service import (
    SGZZ_CLIENT_TYPES,
    clear_account_like_status,
    detect_sgzz_from_device,
    read_accounts_config,
    set_account_client,
    set_account_liked_today,
)

_SINGLE_INSTANCE_MUTEX: int | None = None
_SINGLE_INSTANCE_LOCK_FILE: Any | None = None


def ensure_single_instance(port: int) -> bool:
    """Return False when another UI server instance for the same port already exists."""
    if os.name != "nt":
        return True
    import msvcrt
    import ctypes

    global _SINGLE_INSTANCE_LOCK_FILE
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    lock_file = (LOG_ROOT / f"ui_{port}.lock").open("a+", encoding="utf-8")
    try:
        msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        lock_file.close()
        return False
    _SINGLE_INSTANCE_LOCK_FILE = lock_file

    global _SINGLE_INSTANCE_MUTEX
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p)
    kernel32.CreateMutexW.restype = ctypes.c_void_p

    mutex_name = f"Local\\ADBEmulatorControlServerUI-{port}"
    handle = kernel32.CreateMutexW(None, True, mutex_name)
    if not handle:
        return True
    if ctypes.get_last_error() == 183:
        return False
    _SINGLE_INSTANCE_MUTEX = int(handle)
    return True


class QuietRequestHandler(WSGIRequestHandler):
    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        return

    def log_error(self, format: str, *args: Any) -> None:
        return

    def log_message(self, format: str, *args: Any) -> None:
        return


class FlaskServerThread(threading.Thread):
    def __init__(self, host: str, port: int) -> None:
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        logging.getLogger("werkzeug").setLevel(logging.ERROR)
        self.server = make_server(
            host,
            port,
            flask_app,
            threaded=True,
            request_handler=QuietRequestHandler,
        )
        self.ready = threading.Event()

    def run(self) -> None:
        self.ready.set()
        self.server.serve_forever()

    def shutdown(self) -> None:
        self.server.shutdown()


class ControlPanel:
    def __init__(self, root: Tk, host: str, port: int) -> None:
        self.root = root
        self.host = host
        self.port = port
        self.server: FlaskServerThread | None = None
        self.server_running = BooleanVar(value=False)
        self.selected_device = StringVar()
        self.node_name = StringVar(value="daily_signin_like_gacha")
        self.max_cycles = IntVar(value=80)
        self.include_gacha = BooleanVar(value=True)
        self.include_gamecircle_signin = BooleanVar(value=True)
        self.select_all_accounts = BooleanVar(value=True)
        self.accounts_file = StringVar(value="")
        self.accounts_status = StringVar(value="")
        self.status_line = StringVar(value="服务未启动")
        self.script_status = StringVar(value="")
        self.row_device_ids: dict[str, str] = {}
        self.row_adb_serials: dict[str, str] = {}
        self.adb_devices_cache: list[dict[str, str]] = []
        self.adb_last_refresh_at = 0.0
        self.adb_last_error = ""
        self.last_job_text = ""
        self.job_progress_offsets: dict[str, int] = {}
        self.account_rows: dict[str, dict[str, Any]] = {}
        self.account_row_keys: dict[str, str] = {}
        self.account_selected_by_key: dict[str, bool] = {}
        self.account_client_editor: ttk.Combobox | None = None
        self.accounts_last_error = ""
        self.simplified_mode = False
        self.normal_geometry = "1160x760"

        self.root.title("ADB Emulator Control Server")
        self.root.geometry(self.normal_geometry)
        self.root.minsize(1080, 640)

        self.build_ui()
        self.start_server()
        self.refresh_once(scan_adb=True)
        self.schedule_refresh()

    def build_ui(self) -> None:
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.pack(fill=BOTH, expand=True)

        self.top_frame = ttk.Frame(self.main_frame)
        self.top_frame.pack(fill=X)
        ttk.Label(self.top_frame, text="ADB 模拟器控制服务端", font=("", 15, "bold")).pack(side=LEFT)
        ttk.Label(self.top_frame, textvariable=self.status_line).pack(side=RIGHT)

        self.service_frame = ttk.LabelFrame(self.main_frame, text="服务")
        self.service_frame.pack(fill=X, pady=(10, 8))
        self.start_button = ttk.Button(self.service_frame, text="启动服务", command=self.start_server)
        self.start_button.pack(side=LEFT, padx=6, pady=8)
        self.stop_button = ttk.Button(self.service_frame, text="停止服务", command=self.stop_server)
        self.stop_button.pack(side=LEFT, padx=6, pady=8)
        ttk.Button(self.service_frame, text="打开健康检查", command=self.open_health).pack(side=LEFT, padx=6, pady=8)
        ttk.Button(self.service_frame, text="打开日志目录", command=self.open_log_dir).pack(side=LEFT, padx=6, pady=8)
        self.simplify_button = ttk.Button(self.service_frame, text="简化模式", command=self.toggle_simplified_mode)
        self.simplify_button.pack(side=LEFT, padx=6, pady=8)
        ttk.Label(self.service_frame, text=f"http://127.0.0.1:{self.port}").pack(side=RIGHT, padx=8)

        self.simple_bar = ttk.Frame(self.main_frame)
        ttk.Label(self.simple_bar, textvariable=self.status_line).pack(side=LEFT)
        ttk.Button(self.simple_bar, text="完整模式", command=self.toggle_simplified_mode).pack(side=RIGHT)

        self.body_frame = ttk.PanedWindow(self.main_frame, orient="horizontal", height=390)
        self.body_frame.pack(fill=BOTH, expand=False)

        left = ttk.Frame(self.body_frame)
        right = ttk.Frame(self.body_frame)
        self.body_frame.add(left, weight=7)
        self.body_frame.add(right, weight=4)

        self.build_device_panel(left)
        self.build_control_panel(right)
        self.build_log_panel(self.main_frame)

    def build_device_panel(self, parent: ttk.Frame) -> None:
        device_box = ttk.LabelFrame(parent, text="设备")
        device_box.pack(fill=BOTH, expand=True, padx=(0, 8))

        columns = ("bind", "online", "screen", "frames", "job", "last_seen")
        self.device_tree = ttk.Treeview(device_box, columns=columns, show="tree headings", height=7)
        self.device_tree.heading("#0", text="ADB Serial")
        self.device_tree.heading("bind", text="绑定")
        self.device_tree.heading("online", text="在线")
        self.device_tree.heading("screen", text="尺寸")
        self.device_tree.heading("frames", text="截图")
        self.device_tree.heading("job", text="任务")
        self.device_tree.heading("last_seen", text="最后心跳")
        self.device_tree.column("#0", width=170, minwidth=120, stretch=True)
        self.device_tree.column("bind", width=56, minwidth=46, anchor="center", stretch=False)
        self.device_tree.column("online", width=64, minwidth=54, anchor="center", stretch=False)
        self.device_tree.column("screen", width=76, minwidth=66, anchor="center", stretch=False)
        self.device_tree.column("frames", width=48, minwidth=38, anchor="center", stretch=False)
        self.device_tree.column("job", width=58, minwidth=48, anchor="center", stretch=False)
        self.device_tree.column("last_seen", width=74, minwidth=58, anchor="center", stretch=False)
        self.device_tree.pack(fill=BOTH, expand=True, padx=8, pady=8)
        self.device_tree.bind("<<TreeviewSelect>>", self.on_device_selected)

        row = ttk.Frame(device_box)
        row.pack(fill=X, padx=8, pady=(0, 8))
        ttk.Button(row, text="扫描", command=lambda: self.refresh_once(scan_adb=True)).pack(side=LEFT)
        ttk.Button(row, text="绑定", command=self.bind_selected_device).pack(side=LEFT, padx=6)
        ttk.Button(row, text="截图", command=self.open_latest_screenshot).pack(side=LEFT, padx=6)
        ttk.Button(row, text="检测当前节点", command=self.detect_stage).pack(side=LEFT)

        self.job_text = Text(device_box, height=5, wrap="word")
        self.job_text.pack(fill=X, padx=8, pady=(0, 8))

    def build_control_panel(self, parent: ttk.Frame) -> None:
        sgzz = ttk.LabelFrame(parent, text="SGZZ 脚本")
        sgzz.pack(fill=X, padx=(8, 0), pady=(0, 8))

        row = ttk.Frame(sgzz)
        row.pack(fill=X, padx=8, pady=8)
        self.daily_signin_button = ttk.Button(row, text="点赞全流程", command=self.run_daily_signin)
        self.daily_signin_button.pack(side=LEFT)
        ttk.Checkbutton(row, text="抽卡", variable=self.include_gacha).pack(side=LEFT, padx=(8, 0))
        ttk.Checkbutton(row, text="签到", variable=self.include_gamecircle_signin).pack(side=LEFT, padx=(8, 0))
        ttk.Button(row, text="停止选中设备", command=self.stop_selected_job).pack(side=LEFT, padx=6)
        ttk.Label(sgzz, textvariable=self.script_status).pack(fill=X, padx=8, pady=(0, 8))

        accounts = ttk.LabelFrame(parent, text="账号配置")
        accounts.pack(fill=BOTH, expand=True, padx=(8, 0), pady=(0, 8))

        path_row = ttk.Frame(accounts)
        path_row.pack(fill=X, padx=8, pady=8)
        ttk.Label(path_row, text="账号文件").pack(side=LEFT)
        ttk.Entry(path_row, textvariable=self.accounts_file).pack(side=LEFT, fill=X, expand=True, padx=6)
        ttk.Button(path_row, text="刷新", command=self.load_accounts).pack(side=LEFT)
        ttk.Button(path_row, text="清空点赞", command=self.clear_today_like_status).pack(side=LEFT, padx=(6, 0))

        account_action_row = ttk.Frame(accounts)
        account_action_row.pack(fill=X, padx=8, pady=(0, 6))
        ttk.Checkbutton(
            account_action_row,
            text="全选运行",
            variable=self.select_all_accounts,
            command=self.toggle_all_accounts,
        ).pack(side=LEFT)
        ttk.Label(account_action_row, textvariable=self.accounts_status).pack(side=LEFT, padx=10)

        account_table = ttk.Frame(accounts)
        account_table.pack(fill=BOTH, expand=True, padx=8, pady=(0, 8))
        account_columns = ("selected", "liked", "line", "client", "account", "password")
        self.accounts_tree = ttk.Treeview(
            account_table,
            columns=account_columns,
            show="headings",
            height=9,
            selectmode="browse",
        )
        self.accounts_tree.heading("selected", text="选择")
        self.accounts_tree.heading("liked", text="点赞")
        self.accounts_tree.heading("line", text="行号")
        self.accounts_tree.heading("client", text="客户端")
        self.accounts_tree.heading("account", text="账号")
        self.accounts_tree.heading("password", text="密码")
        self.accounts_tree.column("selected", width=44, minwidth=38, anchor="center", stretch=False)
        self.accounts_tree.column("liked", width=44, minwidth=38, anchor="center", stretch=False)
        self.accounts_tree.column("line", width=42, minwidth=34, anchor="center", stretch=False)
        self.accounts_tree.column("client", width=62, minwidth=54, anchor="center", stretch=False)
        self.accounts_tree.column("account", width=112, minwidth=92, anchor="w", stretch=True)
        self.accounts_tree.column("password", width=42, minwidth=34, anchor="center", stretch=False)
        self.accounts_tree.pack(side=LEFT, fill=BOTH, expand=True)
        accounts_scrollbar = ttk.Scrollbar(
            account_table,
            orient="vertical",
            command=self.accounts_tree.yview,
        )
        accounts_scrollbar.pack(side=RIGHT, fill=Y)
        self.accounts_tree.configure(yscrollcommand=accounts_scrollbar.set)
        self.accounts_tree.bind("<Button-1>", self.on_account_tree_click)
        self.accounts_tree.bind("<space>", self.on_account_tree_space)

        manual = ttk.LabelFrame(parent, text="手动测试")
        manual.pack(fill=X, padx=(8, 0))
        row = ttk.Frame(manual)
        row.pack(fill=X, padx=8, pady=8)
        self.tap_x = IntVar(value=360)
        self.tap_y = IntVar(value=900)
        ttk.Label(row, text="Tap").pack(side=LEFT)
        ttk.Entry(row, textvariable=self.tap_x, width=7).pack(side=LEFT, padx=(6, 2))
        ttk.Entry(row, textvariable=self.tap_y, width=7).pack(side=LEFT, padx=(2, 6))
        ttk.Button(row, text="发送点击", command=self.manual_tap).pack(side=LEFT)
        ttk.Button(row, text="返回键", command=self.manual_back).pack(side=LEFT, padx=6)

    def build_log_panel(self, parent: ttk.Frame) -> None:
        self.log_box = ttk.LabelFrame(parent, text="运行日志")
        self.log_box.pack(fill=BOTH, expand=True, pady=(8, 0))
        self.log_text = Text(self.log_box, height=16, wrap="word")
        self.log_text.pack(fill=BOTH, expand=True, padx=8, pady=8)

    def toggle_simplified_mode(self) -> None:
        self.set_simplified_mode(not self.simplified_mode)

    def set_simplified_mode(self, enabled: bool) -> None:
        if enabled == self.simplified_mode:
            return
        self.simplified_mode = enabled
        if enabled:
            self.normal_geometry = self.root.geometry()
            self.top_frame.pack_forget()
            self.service_frame.pack_forget()
            self.body_frame.pack_forget()
            self.simple_bar.pack(fill=X, pady=(0, 6), before=self.log_box)
            self.root.minsize(520, 260)
            self.root.geometry("640x360")
            self.log("已切换到简化模式")
        else:
            self.simple_bar.pack_forget()
            self.top_frame.pack(fill=X, before=self.log_box)
            self.service_frame.pack(fill=X, pady=(10, 8), before=self.log_box)
            self.body_frame.pack(fill=BOTH, expand=False, before=self.log_box)
            self.root.minsize(1080, 640)
            self.root.geometry(self.normal_geometry or "1160x760")
            self.log("已恢复完整模式")

    def start_server(self) -> None:
        if self.server is not None and self.server_running.get():
            self.log("服务已在运行")
            self.update_service_buttons()
            return
        if hasattr(self, "start_button"):
            self.start_button.configure(state="disabled")
        try:
            self.server = FlaskServerThread(self.host, self.port)
            self.server.start()
            self.server.ready.wait(timeout=2.0)
            self.server_running.set(True)
            self.status_line.set(f"服务运行中: http://127.0.0.1:{self.port}")
            self.log(f"服务已启动: 0.0.0.0:{self.port}")
        except Exception as exc:  # noqa: BLE001 - UI boundary.
            self.server = None
            self.server_running.set(False)
            self.status_line.set("服务启动失败")
            self.log_error("服务启动失败", exc)
            messagebox.showerror("启动失败", str(exc))
        finally:
            self.update_service_buttons()

    def stop_server(self) -> None:
        if self.server is None:
            self.server_running.set(False)
            self.status_line.set("服务未启动")
            self.update_service_buttons()
            return
        try:
            self.server.shutdown()
            self.server = None
            self.server_running.set(False)
            self.status_line.set("服务已停止")
            self.log("服务已停止")
        except Exception as exc:  # noqa: BLE001
            self.log_error("停止服务失败", exc)
        finally:
            self.update_service_buttons()

    def update_service_buttons(self) -> None:
        if not hasattr(self, "start_button") or not hasattr(self, "stop_button"):
            return
        running = self.server is not None and self.server_running.get()
        self.start_button.configure(state="disabled" if running else "normal")
        self.stop_button.configure(state="normal" if running else "disabled")

    def schedule_refresh(self) -> None:
        self.refresh_once(scan_adb=False)
        self.root.after(1000, self.schedule_refresh)

    def refresh_once(self, *, scan_adb: bool = False) -> None:
        self.refresh_devices(scan_adb=scan_adb)
        self.refresh_jobs()

    def refresh_devices(self, *, scan_adb: bool = False) -> None:
        try:
            devices = registry.scan_devices(force=scan_adb)
            self.adb_devices_cache = devices
            if self.adb_last_error:
                self.log("ADB 设备刷新恢复正常")
                self.adb_last_error = ""
        except Exception as exc:  # noqa: BLE001 - keep UI alive without ADB.
            message = str(exc)
            if message != self.adb_last_error:
                self.log(f"ADB 设备刷新失败: {message}")
                self.adb_last_error = message
            devices = registry.list_devices()

        existing = set(self.device_tree.get_children())
        row_ids: list[str] = []
        all_ids: list[str] = []
        preferred_ids: list[str] = []
        self.row_device_ids = {}
        self.row_adb_serials = {}

        for device in devices:
            device_id = str(device.get("device_id") or device.get("serial") or "")
            if not device_id:
                continue
            all_ids.append(device_id)
            if device.get("bound") and device.get("online"):
                preferred_ids.append(device_id)
            row_id = f"adb::{device_id}"
            row_ids.append(row_id)
            self.row_device_ids[row_id] = device_id
            self.row_adb_serials[row_id] = device_id
            status = device.get("status") if isinstance(device.get("status"), dict) else {}
            screen = self.format_screen(device)
            job_state = self.device_job_state(device_id)
            values = (
                "已绑定" if device.get("bound") else "待绑定",
                "ADB在线" if device.get("online") else str(status.get("adb_state") or "离线"),
                screen,
                str(device.get("frame_count") or 0),
                job_state,
                self.format_last_seen(device.get("last_seen_at")),
            )
            if row_id in existing:
                current = self.device_tree.item(row_id)
                if current.get("text") != device_id or tuple(current.get("values") or ()) != values:
                    self.device_tree.item(row_id, text=device_id, values=values)
            else:
                self.device_tree.insert("", END, iid=row_id, text=device_id, values=values)

        for stale in existing - set(row_ids):
            self.device_tree.delete(stale)
        preferred_ids = preferred_ids or all_ids
        selected_device = self.selected_device.get()
        if preferred_ids and selected_device not in all_ids:
            self.selected_device.set(preferred_ids[0])
            self.select_tree_device(f"adb::{preferred_ids[0]}")
        elif selected_device in all_ids:
            self.select_tree_device(f"adb::{selected_device}")
        elif not all_ids:
            self.selected_device.set("")

    @staticmethod
    def format_last_seen(value: object) -> str:
        if not value:
            return ""
        try:
            seen_at = datetime.fromisoformat(str(value))
            elapsed = max(0, int((datetime.now() - seen_at).total_seconds()))
        except ValueError:
            return str(value)
        if elapsed < 10:
            return "刚刚"
        if elapsed < 60:
            rounded = (elapsed // 10) * 10
            return f"{rounded}秒前"
        minutes = elapsed // 60
        if minutes < 60:
            return f"{minutes}分钟前"
        return str(value)

    @staticmethod
    def has_fresh_frame(device: dict[str, Any]) -> bool:
        if bool(device.get("has_fresh_frame")):
            return True
        value = device.get("latest_frame_at")
        if not value:
            return False
        try:
            latest_at = datetime.fromisoformat(str(value))
        except ValueError:
            return False
        return (datetime.now() - latest_at).total_seconds() <= 6.0

    def device_job_state(self, device_id: str) -> str:
        try:
            payload = sgzz_jobs.snapshot(device_id)
        except Exception:
            return "-"
        state = str(payload.get("state") or "idle")
        if state == "running":
            return "运行中"
        if state == "stopping":
            return "停止中"
        if state == "error":
            return "失败"
        if state == "done":
            return "完成"
        if state == "stopped":
            return "已停止"
        return "空闲"

    def refresh_jobs(self) -> None:
        self.refresh_account_like_marks()
        device_id = self.selected_device.get().strip()
        if device_id:
            snapshot = sgzz_jobs.snapshot(device_id)
        else:
            snapshot = sgzz_jobs.snapshot()
        self.update_script_status(snapshot)
        self.append_job_progress(snapshot)
        text = self.format_job(snapshot)
        if text == self.last_job_text:
            return
        self.last_job_text = text
        self.job_text.delete("1.0", END)
        self.job_text.insert(END, text)

    def format_job(self, payload: dict[str, Any]) -> str:
        if "jobs" in payload:
            jobs = payload.get("jobs") or []
            if not jobs:
                return "暂无脚本任务"
            return "\n\n".join(self.format_job(job) for job in jobs)
        lines = [
            f"设备: {payload.get('device_id', self.selected_device.get() or '-')}",
            f"状态: {payload.get('state', 'idle')}",
        ]
        command = payload.get("command")
        mode = payload.get("mode")
        if command:
            lines.append(f"任务: {command}/{mode}")
        if payload.get("include_gacha") is not None:
            lines.append(f"抽卡: {'是' if payload.get('include_gacha') else '否'}")
        if payload.get("include_gamecircle_signin") is not None:
            lines.append(f"签到: {'是' if payload.get('include_gamecircle_signin') else '否'}")
        if payload.get("selected_account_count") is not None:
            lines.append(f"本次账号: {payload.get('selected_account_count')} 个")
        if payload.get("started_at"):
            lines.append(f"开始: {payload['started_at']}")
        if payload.get("finished_at"):
            lines.append(f"结束: {payload['finished_at']}")
        if payload.get("record_path"):
            lines.append(f"记录: {payload['record_path']}")
        if payload.get("error"):
            lines.append(f"错误: {payload['error']}")
        return "\n".join(lines)

    def append_job_progress(self, payload: dict[str, Any]) -> None:
        jobs = payload.get("jobs") if "jobs" in payload else [payload]
        if not isinstance(jobs, list):
            return
        active_keys: set[str] = set()
        for job in jobs:
            if not isinstance(job, dict):
                continue
            lines = job.get("progress_lines") or []
            if not isinstance(lines, list):
                continue
            key = self.job_progress_key(job)
            active_keys.add(key)
            first_seq = job.get("progress_first_seq")
            next_seq = job.get("progress_next_seq")
            try:
                first_seq_int = int(first_seq)
                next_seq_int = int(next_seq)
            except (TypeError, ValueError):
                first_seq_int = 0
                next_seq_int = 0
            seen = self.job_progress_offsets.get(key, first_seq_int)
            if first_seq_int > 0 and next_seq_int > 0:
                if seen < first_seq_int:
                    seen = first_seq_int
                if seen > next_seq_int:
                    seen = first_seq_int
                start_index = max(0, min(len(lines), seen - first_seq_int))
            else:
                if seen > len(lines):
                    seen = 0
                start_index = seen
            device_id = str(job.get("device_id") or "-")
            for line in lines[start_index:]:
                if line:
                    self.log(f"辅助执行[{device_id}]: {line}")
            self.job_progress_offsets[key] = next_seq_int if next_seq_int > 0 else len(lines)

        if len(self.job_progress_offsets) > 50:
            stale_keys = [key for key in self.job_progress_offsets if key not in active_keys]
            for key in stale_keys[:25]:
                self.job_progress_offsets.pop(key, None)

    @staticmethod
    def job_progress_key(job: dict[str, Any]) -> str:
        parts = (
            str(job.get("device_id") or "-"),
            str(job.get("started_at") or "-"),
            str(job.get("command") or "-"),
            str(job.get("mode") or "-"),
        )
        return "|".join(parts)

    def update_script_status(self, payload: dict[str, Any]) -> None:
        if "jobs" in payload:
            jobs = payload.get("jobs") or []
            running = any(job.get("state") in {"running", "stopping"} for job in jobs)
            self.set_daily_button_state(running)
            if not jobs:
                return
            latest = jobs[-1]
        else:
            latest = payload
            running = latest.get("state") in {"running", "stopping"}
            self.set_daily_button_state(running)

        state = str(latest.get("state") or "idle")
        mode = str(latest.get("mode") or "")
        if state == "running":
            self.script_status.set(f"脚本运行中: {mode or '-'}")
        elif state == "stopping":
            self.script_status.set("脚本正在停止")
        elif state == "error":
            self.script_status.set(f"脚本失败: {latest.get('error') or '-'}")
        elif state == "done":
            self.script_status.set("脚本完成")
        elif state == "stopped":
            self.script_status.set("脚本已停止")

    def set_daily_button_state(self, running: bool) -> None:
        if not hasattr(self, "daily_signin_button"):
            return
        self.daily_signin_button.configure(state="disabled" if running else "normal")

    @staticmethod
    def format_screen(device: dict[str, Any]) -> str:
        width = device.get("screen_width")
        height = device.get("screen_height")
        return f"{width}x{height}" if width and height else "-"

    def on_device_selected(self, _event: object) -> None:
        selected = self.device_tree.selection()
        if selected:
            row_id = str(selected[0])
            device_id = self.row_device_ids.get(row_id)
            if device_id:
                self.selected_device.set(device_id)
            elif row_id in self.row_adb_serials:
                self.selected_device.set("")
            self.refresh_jobs()

    def select_tree_device(self, device_id: str) -> None:
        if self.device_tree.exists(device_id):
            self.device_tree.selection_set(device_id)
            self.device_tree.focus(device_id)

    def selected_device_or_warn(
        self,
        *,
        require_screenshot: bool = False,
    ) -> str | None:
        device_id = self.selected_device.get().strip()
        if device_id:
            try:
                snapshot = registry.get_device_snapshot(device_id)
            except Exception as exc:  # noqa: BLE001
                message = f"设备不存在或已断开: {exc}"
                self.log(message)
                messagebox.showwarning("设备不可用", message)
                return None
            if not snapshot.get("online"):
                message = "当前模拟器不在 ADB 在线状态，请重新扫描设备。"
                self.log(message)
                messagebox.showwarning("设备离线", message)
                return None
            if not snapshot.get("bound"):
                message = "当前模拟器还未绑定，请先点击“绑定选中模拟器”。"
                self.log(message)
                messagebox.showwarning("未绑定模拟器", message)
                return None
            if require_screenshot and not self.has_fresh_frame(snapshot):
                try:
                    registry.capture_screenshot(device_id)
                except Exception as exc:  # noqa: BLE001
                    message = f"ADB 截图失败: {exc}"
                    self.log(message)
                    messagebox.showwarning("截图失败", message)
                    return None
            return device_id
        message = "请先扫描并绑定一个 ADB 在线模拟器。"
        self.log(message)
        messagebox.showwarning("未选择设备", message)
        return None

    def selected_serial_or_warn(self) -> str | None:
        selected = self.device_tree.selection()
        if selected:
            row_id = str(selected[0])
            serial = self.row_adb_serials.get(row_id) or self.row_device_ids.get(row_id)
            if serial:
                return serial
        serial = self.selected_device.get().strip()
        if serial:
            return serial
        messagebox.showwarning("未选择模拟器", "请先在设备列表里选中一台 ADB 在线模拟器。")
        return None

    def bind_selected_device(self) -> None:
        serial = self.selected_serial_or_warn()
        if not serial:
            return
        self.run_background(
            f"绑定模拟器 {serial}",
            lambda: registry.bind_device(serial),
        )

    @staticmethod
    def checkbox_text(value: bool) -> str:
        return "[√]" if value else "[ ]"

    def account_values(self, row_id: str) -> tuple[str, str, str, str, str, str]:
        account = self.account_rows.get(row_id, {})
        key = self.account_row_keys.get(row_id, "")
        selected = self.account_selected_by_key.get(key, True)
        liked = bool(account.get("liked_today"))
        password_length = account.get("password_length")
        password_text = f"{password_length}位" if password_length else "-"
        return (
            self.checkbox_text(selected),
            self.checkbox_text(liked),
            str(account.get("line_number") or ""),
            str(account.get("client") or "灵犀"),
            str(account.get("masked_account") or account.get("account") or ""),
            password_text,
        )

    def set_account_rows(self, config: dict[str, Any]) -> None:
        if not hasattr(self, "accounts_tree"):
            return
        accounts = config.get("accounts") if isinstance(config.get("accounts"), list) else []
        existing = set(self.accounts_tree.get_children())
        live_rows: set[str] = set()
        live_keys: set[str] = set()
        liked_count = 0
        pending_count = 0

        for index, account in enumerate(accounts, start=1):
            if not isinstance(account, dict):
                continue
            key = str(account.get("account_key") or "").strip()
            if not key:
                continue
            row_id = f"account::{account.get('line_number') or index}::{key}"
            live_rows.add(row_id)
            live_keys.add(key)
            self.account_rows[row_id] = account
            self.account_row_keys[row_id] = key
            self.account_selected_by_key.setdefault(key, True)
            if bool(account.get("liked_today")):
                liked_count += 1
            elif self.account_selected_by_key.get(key, True):
                pending_count += 1
            values = self.account_values(row_id)
            if row_id in existing:
                if tuple(self.accounts_tree.item(row_id).get("values") or ()) != values:
                    self.accounts_tree.item(row_id, values=values)
            else:
                self.accounts_tree.insert("", END, iid=row_id, values=values)

        for stale in existing - live_rows:
            self.accounts_tree.delete(stale)
            self.account_rows.pop(stale, None)
            self.account_row_keys.pop(stale, None)

        self.account_selected_by_key = {
            key: selected
            for key, selected in self.account_selected_by_key.items()
            if key in live_keys
        }
        self.update_select_all_accounts()
        self.accounts_status.set(
            f"{len(live_rows)} 个账号，待点赞 {pending_count} 个，今日已点赞 {liked_count} 个"
        )
        self.accounts_last_error = ""

    def update_account_row(self, row_id: str) -> None:
        if hasattr(self, "accounts_tree") and self.accounts_tree.exists(row_id):
            self.accounts_tree.item(row_id, values=self.account_values(row_id))

    def update_select_all_accounts(self) -> None:
        keys = list(self.account_selected_by_key)
        self.select_all_accounts.set(bool(keys) and all(self.account_selected_by_key.values()))

    def toggle_all_accounts(self) -> None:
        selected = bool(self.select_all_accounts.get())
        for key in list(self.account_selected_by_key):
            self.account_selected_by_key[key] = selected
        for row_id in self.accounts_tree.get_children():
            self.update_account_row(str(row_id))
        self.refresh_account_counts_from_rows()

    def refresh_account_counts_from_rows(self) -> None:
        total = 0
        liked_count = 0
        pending_count = 0
        for row_id in self.accounts_tree.get_children():
            account = self.account_rows.get(str(row_id), {})
            key = self.account_row_keys.get(str(row_id), "")
            total += 1
            if bool(account.get("liked_today")):
                liked_count += 1
            elif self.account_selected_by_key.get(key, True):
                pending_count += 1
        self.accounts_status.set(
            f"{total} 个账号，待点赞 {pending_count} 个，今日已点赞 {liked_count} 个"
        )

    def on_account_tree_click(self, event: object) -> str | None:
        row_id = self.accounts_tree.identify_row(event.y)  # type: ignore[attr-defined]
        column = self.accounts_tree.identify_column(event.x)  # type: ignore[attr-defined]
        if not row_id:
            return None
        if column == "#1":
            self.toggle_account_selected(str(row_id))
            return "break"
        if column == "#2":
            self.toggle_account_liked(str(row_id))
            return "break"
        if column == "#4":
            self.open_account_client_editor(str(row_id))
            return "break"
        self.close_account_client_editor()
        return None

    def close_account_client_editor(self, editor: ttk.Combobox | None = None) -> None:
        if editor is not None and editor is not self.account_client_editor:
            return
        current = self.account_client_editor
        self.account_client_editor = None
        if current is not None:
            current.destroy()

    def open_account_client_editor(self, row_id: str) -> None:
        account = self.account_rows.get(row_id)
        if not account:
            return
        bounds = self.accounts_tree.bbox(row_id, "client")
        if not bounds:
            return
        self.close_account_client_editor()
        x, y, width, height = bounds
        editor = ttk.Combobox(
            self.accounts_tree,
            values=SGZZ_CLIENT_TYPES,
            state="readonly",
            justify="center",
        )
        editor.set(str(account.get("client") or "灵犀"))
        editor.place(x=x, y=y, width=width, height=height)
        self.account_client_editor = editor
        editor.bind(
            "<<ComboboxSelected>>",
            lambda _event, target=row_id, widget=editor: self.save_account_client(
                target,
                widget.get(),
            ),
        )
        editor.bind("<Escape>", lambda _event, widget=editor: self.close_account_client_editor(widget))
        editor.bind(
            "<FocusOut>",
            lambda _event, widget=editor: self.root.after(
                100,
                lambda: self.close_account_client_editor(widget),
            ),
        )
        editor.focus_set()

    def save_account_client(self, row_id: str, client: str) -> None:
        account = self.account_rows.get(row_id)
        key = self.account_row_keys.get(row_id)
        if not account or not key:
            self.close_account_client_editor()
            return
        current_client = str(account.get("client") or "灵犀")
        if client == current_client:
            self.close_account_client_editor()
            return
        masked_account = str(account.get("masked_account") or account.get("account") or "")
        try:
            config = set_account_client(key, client, self.accounts_file_value())
            self.accounts_file.set(str(config["path"]))
            self.set_account_rows(config)
            self.log(f"账号客户端已更新: {masked_account} -> {client}")
        except Exception as exc:  # noqa: BLE001
            self.log_error("更新账号客户端失败", exc)
            messagebox.showerror("更新失败", str(exc))
        finally:
            self.close_account_client_editor()

    def on_account_tree_space(self, _event: object) -> str | None:
        row_id = str(self.accounts_tree.focus() or "")
        if not row_id:
            return None
        self.toggle_account_selected(row_id)
        return "break"

    def toggle_account_selected(self, row_id: str) -> None:
        key = self.account_row_keys.get(row_id)
        if not key:
            return
        self.account_selected_by_key[key] = not self.account_selected_by_key.get(key, True)
        self.update_account_row(row_id)
        self.update_select_all_accounts()
        self.refresh_account_counts_from_rows()

    def toggle_account_liked(self, row_id: str) -> None:
        account = self.account_rows.get(row_id)
        key = self.account_row_keys.get(row_id)
        if not account or not key:
            return
        liked = not bool(account.get("liked_today"))
        masked_account = str(account.get("masked_account") or account.get("account") or "")
        try:
            set_account_liked_today(key, liked, masked_account)
            account["liked_today"] = liked
            account["liked_at"] = datetime.now().isoformat(timespec="seconds") if liked else None
            self.update_account_row(row_id)
            self.refresh_account_counts_from_rows()
            self.log(f"账号点赞状态已更新: {masked_account} -> {'已完成' if liked else '待点赞'}")
        except Exception as exc:  # noqa: BLE001
            self.log_error("更新账号点赞状态失败", exc)
            messagebox.showerror("更新失败", str(exc))

    def refresh_account_like_marks(self) -> None:
        if not hasattr(self, "accounts_tree"):
            return
        try:
            config = read_accounts_config(self.accounts_file_value())
            self.accounts_file.set(str(config["path"]))
            self.set_account_rows(config)
        except Exception as exc:  # noqa: BLE001
            message = str(exc)
            if message != self.accounts_last_error:
                self.log(f"刷新账号状态失败: {message}")
                self.accounts_last_error = message

    def selected_account_keys_for_run(self) -> list[str] | None:
        self.refresh_account_like_marks()
        keys: list[str] = []
        selected_count = 0
        skipped_liked = 0
        for row_id in self.accounts_tree.get_children():
            account = self.account_rows.get(str(row_id), {})
            key = self.account_row_keys.get(str(row_id), "")
            if not key or not self.account_selected_by_key.get(key, True):
                continue
            selected_count += 1
            if bool(account.get("liked_today")):
                skipped_liked += 1
                continue
            keys.append(key)
        if selected_count <= 0:
            messagebox.showwarning("未选择账号", "请先勾选要运行的账号。")
            return None
        if not keys:
            messagebox.showwarning(
                "没有待点赞账号",
                "已选择账号都勾选为今日已点赞；取消“点赞”列勾选后可重新点赞。",
            )
            return None
        self.log(
            f"本次账号选择: 选中 {selected_count} 个，待点赞 {len(keys)} 个，已点赞跳过 {skipped_liked} 个"
        )
        return keys

    def clear_today_like_status(self) -> None:
        try:
            clear_account_like_status()
            self.refresh_account_like_marks()
            self.log("今日点赞状态已清空")
        except Exception as exc:  # noqa: BLE001
            self.log_error("清空今日点赞状态失败", exc)
            messagebox.showerror("清空失败", str(exc))

    def launch_game(self) -> None:
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        self.run_background(
            "启动游戏",
            lambda: sgzz_jobs.start_launch_game(device_id=device_id),
        )

    def start_entry(self) -> None:
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        self.run_background(
            "入口流程",
            lambda: sgzz_jobs.start_start_account(
                mode="entry",
                device_id=device_id,
            ),
        )

    def run_batch(self) -> None:
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        if not self.save_accounts():
            return
        selected_account_keys = self.selected_account_keys_for_run()
        if selected_account_keys is None:
            return
        self.run_background(
            "完整流程",
            lambda: sgzz_jobs.start_account_batch(
                device_id=device_id,
                accounts_file=self.accounts_file_value(),
                max_cycles_per_account=int(self.max_cycles.get()),
                include_gacha=bool(self.include_gacha.get()),
                include_gamecircle_signin=bool(self.include_gamecircle_signin.get()),
                selected_account_keys=selected_account_keys,
            ),
        )

    def run_node(self) -> None:
        node = self.node_name.get().strip()
        if not node:
            messagebox.showwarning("节点为空", "请填写要运行的节点名。")
            return
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        self.run_background(
            f"运行节点 {node}",
            lambda: sgzz_jobs.start_node(
                node=node,
                device_id=device_id,
                include_gacha=bool(self.include_gacha.get()),
                include_gamecircle_signin=bool(self.include_gamecircle_signin.get()),
            ),
        )

    def run_daily_signin(self) -> None:
        include_gacha = bool(self.include_gacha.get())
        include_gamecircle_signin = bool(self.include_gamecircle_signin.get())
        self.log(
            "点赞全流程按钮已点击，"
            f"抽卡={'开启' if include_gacha else '关闭'}，"
            f"签到={'开启' if include_gamecircle_signin else '关闭'}"
        )
        self.script_status.set("点赞全流程按钮已点击，正在检查设备...")
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        if not self.save_accounts():
            return
        selected_account_keys = self.selected_account_keys_for_run()
        if selected_account_keys is None:
            return
        self.script_status.set("点赞全流程已提交，正在启动账号/角色批量流程...")
        self.set_daily_button_state(True)
        self.run_background(
            "点赞全流程",
            lambda: sgzz_jobs.start_account_batch(
                device_id=device_id,
                accounts_file=self.accounts_file_value(),
                max_cycles_per_account=int(self.max_cycles.get()),
                include_gacha=include_gacha,
                include_gamecircle_signin=include_gamecircle_signin,
                selected_account_keys=selected_account_keys,
            ),
        )

    def stop_selected_job(self) -> None:
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        self.run_background("停止选中设备", lambda: sgzz_jobs.request_stop(device_id))

    def stop_all_jobs(self) -> None:
        self.run_background("停止全部任务", lambda: sgzz_jobs.request_stop(None))

    def manual_tap(self) -> None:
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        x = int(self.tap_x.get())
        y = int(self.tap_y.get())
        self.run_background(
            f"发送点击 {x},{y}",
            lambda: registry.send_command_and_wait(device_id, "tap", x=x, y=y),
        )

    def manual_back(self) -> None:
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        self.run_background(
            "发送返回键",
            lambda: registry.send_command_and_wait(device_id, "keyevent", keycode="KEYCODE_BACK"),
        )

    def detect_stage(self) -> None:
        device_id = self.selected_device_or_warn(require_screenshot=True)
        if not device_id:
            return
        self.run_background("检测当前节点", lambda: detect_sgzz_from_device(registry, device_id))

    def open_latest_screenshot(self) -> None:
        device_id = self.selected_device_or_warn()
        if not device_id:
            return
        try:
            path = registry.capture_screenshot(device_id)
            os.startfile(path)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001
            self.log_error("打开最新截图失败", exc)
            messagebox.showerror("打开失败", str(exc))

    def load_accounts(self) -> None:
        try:
            config = read_accounts_config(self.accounts_file_value())
            self.accounts_file.set(str(config["path"]))
            self.set_account_rows(config)
            self.log(f"已读取账号配置: {config['account_count']} 个账号")
        except Exception as exc:  # noqa: BLE001
            self.log_error("读取账号失败", exc)
            messagebox.showerror("读取账号失败", str(exc))

    def save_accounts(self) -> bool:
        try:
            config = read_accounts_config(self.accounts_file_value())
            self.accounts_file.set(str(config["path"]))
            self.set_account_rows(config)
            if int(config.get("account_count") or 0) <= 0:
                messagebox.showwarning("账号为空", "账号列表为空，请先在账号文件中配置账号。")
                return False
            self.log(f"已确认账号配置: {config['account_count']} 个账号")
            return True
        except Exception as exc:  # noqa: BLE001
            self.log_error("确认账号失败", exc)
            messagebox.showerror("确认账号失败", str(exc))
            return False

    def accounts_file_value(self) -> str | None:
        value = self.accounts_file.get().strip()
        return value or None

    def selected_device_or_error(self) -> str:
        device_id = self.selected_device.get().strip()
        if not device_id:
            raise RuntimeError("No ADB emulator selected.")
        return device_id

    def run_background(self, label: str, action: Callable[[], Any]) -> None:
        self.log(f"{label}...")

        def worker() -> None:
            try:
                result = action()
                self.root.after(0, lambda result=result: self.on_action_done(label, result))
            except Exception as exc:  # noqa: BLE001
                detail = traceback.format_exc(limit=6)
                self.root.after(
                    0,
                    lambda error=exc, detail=detail: self.on_action_error(label, error, detail),
                )

        threading.Thread(target=worker, daemon=True).start()

    def on_action_done(self, label: str, result: Any) -> None:
        self.log(f"{label}完成: {self.compact(result)}")
        self.refresh_once()

    def on_action_error(self, label: str, error: Exception, detail: str) -> None:
        self.log(f"{label}失败: {error}\n{detail}")

    def open_health(self) -> None:
        webbrowser.open(f"http://127.0.0.1:{self.port}/health")

    def open_log_dir(self) -> None:
        LOG_ROOT.mkdir(parents=True, exist_ok=True)
        os.startfile(LOG_ROOT)  # type: ignore[attr-defined]

    def log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(END, f"[{stamp}] {message}\n")
        self.log_text.see(END)

    def log_error(self, label: str, error: Exception) -> None:
        self.log(f"{label}: {error}\n{traceback.format_exc(limit=6)}")

    @staticmethod
    def compact(value: Any) -> str:
        text = str(value)
        return text if len(text) <= 500 else text[:500] + "..."

    def close(self) -> None:
        if self.server is not None:
            self.stop_server()
        self.root.destroy()


def attach_pythonw_logs() -> None:
    executable = Path(sys.executable).name.lower()
    if executable != "pythonw.exe":
        return
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    sys.stdout = (LOG_ROOT / "ui_stdout.log").open("a", encoding="utf-8", buffering=1)
    sys.stderr = (LOG_ROOT / "ui_stderr.log").open("a", encoding="utf-8", buffering=1)


def main() -> int:
    attach_pythonw_logs()
    parser = argparse.ArgumentParser(description="ADB emulator control server UI")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8766)
    args = parser.parse_args()
    if not ensure_single_instance(args.port):
        print(f"ADB emulator control server UI is already running on port {args.port}.")
        return 0

    root = Tk()
    panel = ControlPanel(root, args.host, args.port)
    panel.load_accounts()
    root.protocol("WM_DELETE_WINDOW", panel.close)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
