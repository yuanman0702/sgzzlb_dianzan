from __future__ import annotations

import argparse
import json
import logging
from typing import Any

from flask import Flask, jsonify, request, send_file

from remote_bot import DeviceRegistry, LOG_ROOT
from sgzz_service import (
    SGZZRemoteJobManager,
    clear_account_like_status,
    detect_sgzz_from_device,
    read_account_like_status,
    read_accounts_config,
    set_account_liked_today,
    write_accounts_config,
)


app = Flask(__name__)
registry = DeviceRegistry(LOG_ROOT)
sgzz_jobs = SGZZRemoteJobManager(registry)


def parse_bool_option(value: Any, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if not text:
        return default
    if text in {"1", "true", "yes", "y", "on", "是", "开启"}:
        return True
    if text in {"0", "false", "no", "n", "off", "否", "关闭"}:
        return False
    raise ValueError(f"invalid boolean value: {value}")


def request_bool_option(payload: dict[str, Any], names: tuple[str, ...], *, default: bool) -> bool:
    for name in names:
        if name in payload:
            return parse_bool_option(payload.get(name), default=default)
    for name in names:
        if name in request.args:
            return parse_bool_option(request.args.get(name), default=default)
    return default


def request_account_keys(payload: dict[str, Any]) -> list[str] | None:
    raw = payload.get("selected_account_keys")
    if raw is None:
        raw = payload.get("account_keys")
    if raw is None:
        return None
    if isinstance(raw, str):
        return [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]
    if isinstance(raw, list):
        return [str(part).strip() for part in raw if str(part).strip()]
    raise ValueError("selected_account_keys must be a list or comma-separated string")


def request_device_id(payload: dict[str, Any]) -> str | None:
    return str(payload.get("device_id") or request.args.get("device_id") or "").strip() or None


@app.get("/health")
def health() -> Any:
    try:
        devices = registry.scan_devices(force=False)
        return jsonify(
            {
                "ok": True,
                "service": "adb-emulator-control-python",
                "devices": devices,
                "log_root": str(LOG_ROOT),
                "adb_path": registry.adb_path,
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify(
            {
                "ok": False,
                "service": "adb-emulator-control-python",
                "error": str(exc),
                "log_root": str(LOG_ROOT),
            }
        ), 500


@app.get("/api/devices")
def list_devices() -> Any:
    include_commands = request.args.get("commands", "").lower() in {"1", "true", "yes"}
    force = request.args.get("scan", "1").lower() not in {"0", "false", "no"}
    try:
        devices = registry.scan_devices(force=force)
        return jsonify({"ok": True, "devices": devices, "adb_path": registry.adb_path})
    except Exception as exc:  # noqa: BLE001
        del include_commands
        return jsonify({"ok": False, "error": str(exc), "devices": registry.list_devices()}), 500


@app.post("/api/devices/scan")
def scan_devices() -> Any:
    try:
        return jsonify({"ok": True, "devices": registry.scan_devices(force=True)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 500


@app.post("/api/devices/connect")
def connect_device() -> Any:
    payload = request.get_json(silent=True) or {}
    serial = str(payload.get("serial") or request.args.get("serial") or "").strip()
    if not serial:
        return jsonify({"ok": False, "error": "missing serial"}), 400
    try:
        return jsonify({"ok": True, "device": registry.connect_device(serial)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/devices/<path:device_id>/bind")
def bind_device(device_id: str) -> Any:
    try:
        return jsonify({"ok": True, "device": registry.bind_device(device_id)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/api/devices/<path:device_id>/unbind")
def unbind_device(device_id: str) -> Any:
    try:
        return jsonify({"ok": True, "device": registry.unbind_device(device_id)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/api/devices/<path:device_id>")
def get_device(device_id: str) -> Any:
    try:
        return jsonify(
            {
                "ok": True,
                "device": registry.get_device_snapshot(device_id, include_commands=True),
            }
        )
    except KeyError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 404


@app.get("/api/devices/<path:device_id>/latest")
def latest_frame(device_id: str) -> Any:
    try:
        path = registry.capture_screenshot(device_id)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 404
    return send_file(path)


@app.post("/api/devices/<path:device_id>/command")
def send_manual_command(device_id: str) -> Any:
    payload = request.get_json(silent=True) or {}
    command_type = str(payload.pop("type", "")).strip()
    if not command_type:
        return jsonify({"ok": False, "error": "missing command type"}), 400
    try:
        message = registry.send_command_and_wait(device_id, command_type, **payload)
        return jsonify({"ok": True, "message": message})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/sgzz/status")
def sgzz_status() -> Any:
    device_id = request.args.get("device_id") or None
    jobs = sgzz_jobs.snapshot(device_id)
    return jsonify({"ok": True, "devices": registry.list_devices(), "jobs": jobs})


@app.post("/sgzz/stop")
def sgzz_stop() -> Any:
    payload = request.get_json(silent=True) or {}
    device_id = request_device_id(payload)
    return jsonify(sgzz_jobs.request_stop(device_id))


@app.get("/sgzz/accounts")
def sgzz_get_accounts() -> Any:
    accounts_file = request.args.get("accounts_file") or None
    try:
        return jsonify({"ok": True, "config": read_accounts_config(accounts_file)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/sgzz/accounts")
def sgzz_save_accounts() -> Any:
    payload = request.get_json(silent=True) or {}
    accounts_file = str(payload.get("accounts_file") or "").strip() or None
    accounts_text = str(payload.get("accounts_text") or "")
    try:
        return jsonify({"ok": True, "config": write_accounts_config(accounts_text, accounts_file)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/sgzz/accounts/like-status")
def sgzz_account_like_status() -> Any:
    return jsonify({"ok": True, "status": read_account_like_status()})


@app.post("/sgzz/accounts/clear-like-status")
def sgzz_clear_account_like_status() -> Any:
    return jsonify({"ok": True, "status": clear_account_like_status()})


@app.post("/sgzz/accounts/set-like-status")
def sgzz_set_account_like_status() -> Any:
    payload = request.get_json(silent=True) or {}
    account_key = str(payload.get("account_key") or "").strip()
    masked_account = str(payload.get("masked_account") or "").strip()
    try:
        liked = parse_bool_option(payload.get("liked"), default=False)
        return jsonify(
            {
                "ok": True,
                "status": set_account_liked_today(account_key, liked, masked_account),
            }
        )
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.get("/sgzz/detect")
def sgzz_detect() -> Any:
    device_id = request.args.get("device_id") or None
    try:
        return jsonify({"ok": True, "result": detect_sgzz_from_device(registry, device_id)})
    except Exception as exc:  # noqa: BLE001
        return jsonify({"ok": False, "error": str(exc)}), 400


@app.post("/sgzz/start-game")
def sgzz_start_game() -> Any:
    payload = request.get_json(silent=True) or {}
    device_id = request_device_id(payload)
    result = sgzz_jobs.start_launch_game(device_id=device_id)
    status = 200 if result.get("ok") else 409
    return jsonify(result), status


@app.post("/sgzz/start-account")
def sgzz_start_account() -> Any:
    payload = request.get_json(silent=True) or {}
    mode = str(payload.get("mode") or request.args.get("mode") or "entry")
    device_id = request_device_id(payload)
    result = sgzz_jobs.start_start_account(mode=mode, device_id=device_id)
    status = 200 if result.get("ok") else 409
    return jsonify(result), status


@app.post("/sgzz/run-account-batch")
def sgzz_run_account_batch() -> Any:
    payload = request.get_json(silent=True) or {}
    device_id = request_device_id(payload)
    accounts_file = str(payload.get("accounts_file") or "").strip() or None
    max_cycles_raw = payload.get("max_cycles_per_account") or payload.get("max_cycles")
    max_cycles = int(max_cycles_raw) if max_cycles_raw not in {None, ""} else None
    try:
        include_gacha = request_bool_option(
            payload,
            ("include_gacha", "run_gacha", "gacha"),
            default=True,
        )
        include_gamecircle_signin = request_bool_option(
            payload,
            (
                "include_gamecircle_signin",
                "run_gamecircle_signin",
                "gamecircle_signin",
                "signin",
            ),
            default=False,
        )
        selected_account_keys = request_account_keys(payload)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    result = sgzz_jobs.start_account_batch(
        device_id=device_id,
        accounts_file=accounts_file,
        max_cycles_per_account=max_cycles,
        include_gacha=include_gacha,
        include_gamecircle_signin=include_gamecircle_signin,
        selected_account_keys=selected_account_keys,
    )
    status = 200 if result.get("ok") else 409
    return jsonify(result), status


@app.post("/sgzz/run-node")
def sgzz_run_node() -> Any:
    payload = request.get_json(silent=True) or {}
    node = str(payload.get("node") or request.args.get("node") or "").strip()
    device_id = request_device_id(payload)
    if not node:
        return jsonify({"ok": False, "error": "missing node"}), 400
    try:
        include_gacha = request_bool_option(
            payload,
            ("include_gacha", "run_gacha", "gacha"),
            default=True,
        )
        include_gamecircle_signin = request_bool_option(
            payload,
            (
                "include_gamecircle_signin",
                "run_gamecircle_signin",
                "gamecircle_signin",
                "signin",
            ),
            default=False,
        )
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    result = sgzz_jobs.start_node(
        node=node,
        device_id=device_id,
        include_gacha=include_gacha,
        include_gamecircle_signin=include_gamecircle_signin,
    )
    status = 200 if result.get("ok") else 409
    return jsonify(result), status


def main() -> int:
    parser = argparse.ArgumentParser(description="ADB emulator control Python server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8766)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    print(f"ADB Emulator Control server: http://127.0.0.1:{args.port}")
    print(f"Device list: http://127.0.0.1:{args.port}/api/devices")
    print(json.dumps({"host": args.host, "port": args.port}, ensure_ascii=False))
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
