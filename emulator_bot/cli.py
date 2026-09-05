from __future__ import annotations

from argparse import ArgumentParser, Namespace
from pathlib import Path
from time import sleep, time
import sys

from .adb_client import AdbClient, AdbError, discover_adb_path
from .airtest_backend import AirtestBackend, check_airtest_available
from .bot import EmulatorBot
from .config import load_config
from .sgzz import (
    Point,
    SGZZStartAccountRunner,
    SGZZ_FLOW_NODES,
    load_sgzz_account_credentials,
    resolve_sgzz_accounts_file,
)
from .state_machine import StateMachine, StateMachineError, StateMachineRunner


def _connect_bot_for_optional_serial(config, serial: str | None = None) -> EmulatorBot:
    if serial:
        config.device_serial = serial
        return EmulatorBot.connect(config)

    try:
        return EmulatorBot.connect(config)
    except AdbError:
        if not config.device_serial:
            raise
        config.device_serial = None
        return EmulatorBot.connect(config)


def _timestamp_name(prefix: str) -> str:
    return f"{prefix}_{int(time())}.png"


def _print_error(exc: Exception) -> None:
    print(f"ERROR: {exc}", file=sys.stderr)


def cmd_doctor(args: Namespace) -> int:
    config = load_config(args.config)
    print(f"Config: {Path(args.config).resolve()}")
    try:
        adb_path = discover_adb_path(config.adb_path)
    except AdbError as exc:
        _print_error(exc)
        print("Tip: set [adb].path in config.toml to LDPlayer's adb.exe.")
        return 1

    print(f"ADB: {adb_path}")
    client = AdbClient(adb_path)
    client.start_server()

    if config.device_serial:
        print(f"Configured device: {config.device_serial}")
    else:
        client.try_auto_connect(config.auto_connect_hosts, config.auto_connect_ports)

    devices = client.list_devices()
    if not devices:
        print("Devices: none")
        return 1

    print("Devices:")
    for device in devices:
        print(f"  - {device.serial}\t{device.state}\t{device.detail}")

    live = [device for device in devices if device.state == "device"]
    if live:
        test_client = AdbClient(adb_path, config.device_serial or live[0].serial)
        try:
            width, height = test_client.get_screen_size()
            print(f"Screen: {width}x{height}")
        except AdbError as exc:
            _print_error(exc)
    return 0


def cmd_screenshot(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    name = args.name or _timestamp_name("screenshot")
    path = bot.save_screenshot(name)
    print(f"Device: {bot.client.serial}")
    print(f"Saved: {path}")
    return 0


def cmd_open_weibo(args: Namespace) -> int:
    config = load_config(args.config)
    package = args.package or config.weibo_package
    bot = EmulatorBot.connect(config)
    print(f"Device: {bot.client.serial}")
    width, height = bot.client.get_screen_size()
    print(f"Screen: {width}x{height}")
    print(f"Launching package: {package}")
    bot.client.launch_package(package)
    sleep(args.wait if args.wait is not None else config.weibo_launch_wait_seconds)
    focus = bot.client.current_focus()
    if focus:
        print(f"Focus: {focus}")
    path = bot.save_screenshot(_timestamp_name("weibo"))
    print(f"Screenshot: {path}")
    return 0


def cmd_tap(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    x, y = bot.tap(args.x, args.y, jitter=0 if args.exact else None)
    print(f"Tapped: {x},{y}")
    return 0


def _save_debug_if_requested(bot: EmulatorBot, args: Namespace, match) -> None:
    if not args.debug:
        return
    from .vision import save_debug_image

    debug_name = args.debug_name or _timestamp_name("debug")
    path = save_debug_image(bot.config.debug_dir / debug_name, bot.screenshot_image(), match)
    print(f"Debug: {path}")


def cmd_click_image(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    match = bot.wait_for_image(
        args.template,
        timeout=args.timeout,
        threshold=args.threshold,
        region=args.region,
    )
    if not match:
        print("Image not found.")
        return 1
    _save_debug_if_requested(bot, args, match)
    x, y = bot.tap(*match.center)
    print(f"Matched: {match.x},{match.y},{match.width},{match.height} score={match.score:.3f}")
    print(f"Tapped: {x},{y}")
    return 0


def cmd_click_color(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    match = bot.wait_for_color(
        args.rgb,
        timeout=args.timeout,
        tolerance=args.tolerance,
        region=args.region,
        min_area=args.min_area,
    )
    if not match:
        print("Color not found.")
        return 1
    _save_debug_if_requested(bot, args, match)
    x, y = bot.tap(*match.center)
    print(f"Matched: {match.x},{match.y},{match.width},{match.height} area={match.score:.1f}")
    print(f"Tapped: {x},{y}")
    return 0


def cmd_run_state_machine(args: Namespace) -> int:
    machine = StateMachine.load(args.file)
    print(f"State machine: {machine.name}")
    print(f"Initial: {machine.initial}")
    print(f"States: {', '.join(machine.states.keys())}")

    if args.dry_run:
        print("Dry run: JSON parsed and validated. No emulator connection was opened.")
        return 0

    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = StateMachineRunner(
        machine,
        bot,
        trace=not args.quiet,
        max_runtime_seconds=args.max_runtime,
        max_steps=args.max_steps,
    )
    result = runner.run()
    print(
        "Result: "
        f"status={result.status}, "
        f"final_state={result.final_state}, "
        f"steps={result.steps}, "
        f"runtime={result.runtime_seconds:.2f}s"
    )
    return 0 if result.status == "terminal" else 1


def cmd_airtest_doctor(args: Namespace) -> int:
    config = load_config(args.config)
    available, message = check_airtest_available()
    if available:
        print(f"Airtest: installed ({message})")
    else:
        print(f"Airtest: missing")
        print(message)
        return 1

    bot = EmulatorBot.connect(config)
    backend = AirtestBackend.from_bot(bot)
    print(f"Device: {bot.client.serial}")
    print(f"URI: {backend.device_uri}")
    if args.connect:
        backend.connect()
        print("Connection: ok")
    return 0


def cmd_sgzz_select_latest_s1(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.select_and_enter_latest_s1(
        launch=not args.no_launch,
        launch_wait_seconds=args.launch_wait,
        cancel_restore=not args.no_cancel_restore,
        season1_taps=args.season1_taps,
        enter=not args.no_enter,
        enter_wait_seconds=args.enter_wait,
        queue_wait_seconds=args.queue_wait,
        queue_poll_seconds=args.queue_poll,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_continue_dialogs(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.continue_dialogs(
        taps=args.taps,
        interval_seconds=args.interval,
        timeout_seconds=args.match_timeout,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_continue_old_man(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.continue_old_man_until_blocked(
        max_taps=args.max_taps,
        interval_seconds=args.interval,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Record: {record_path}")
    return 0


def _parse_choice_sequence(text: str) -> list[int]:
    choices = [int(part.strip()) for part in text.split(",") if part.strip()]
    if not choices:
        raise ValueError("Choice sequence cannot be empty.")
    invalid = [choice for choice in choices if choice not in {1, 2, 3}]
    if invalid:
        raise ValueError(f"Choices must be 1, 2, or 3: {invalid}")
    return choices


def cmd_sgzz_answer_old_man_quiz(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.answer_old_man_quiz(
        choices=_parse_choice_sequence(args.choices),
        interval_seconds=args.interval,
        continue_after=not args.no_continue_after,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_create_character_xiliang(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    if not args.skip_avatar:
        runner.confirm_avatar()
    if not args.skip_name:
        runner.submit_random_name()
        runner.continue_old_man_until_blocked(max_taps=args.old_man_taps)
    if not args.skip_region:
        runner.select_xiliang_region()
    if args.chapter_next:
        runner.tap_chapter_next()
    print(f"Device: {bot.client.serial}")
    print(f"Record: {runner.record_path}")
    return 0


def cmd_sgzz_chapter_next(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.tap_chapter_next()
    print(f"Device: {bot.client.serial}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_continue_scout(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.continue_scout_until_blocked(
        max_taps=args.max_taps,
        interval_seconds=args.interval,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_continue_zhuge(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.continue_zhuge_until_blocked(
        max_taps=args.max_taps,
        interval_seconds=args.interval,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_flow_nodes(args: Namespace) -> int:
    for item in SGZZ_FLOW_NODES:
        print(item["node"])
        print(f"  detect: {item['detect']}")
        print(f"  action: {item['action']}")
    return 0


def cmd_sgzz_flow_node(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.run_flow_node(args.node)
    print(f"Device: {bot.client.serial}")
    print(f"Node: {args.node}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_account_batch(args: Namespace) -> int:
    account_path = resolve_sgzz_accounts_file(args.accounts_file)
    credentials = load_sgzz_account_credentials(account_path)
    config = load_config(args.config)
    bot = _connect_bot_for_optional_serial(config, args.serial)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.run_account_batch_remaining_roles_daily_cycle(
        accounts_file=account_path,
        max_cycles_per_account=args.max_cycles,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Accounts: {len(credentials)} from {account_path}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_probe_land(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.probe_land(Point(args.x, args.y), label=args.label)
    print(f"Device: {bot.client.serial}")
    print(f"Probe: {args.x},{args.y}")
    print(f"Record: {record_path}")
    return 0


def cmd_sgzz_farm_land(args: Namespace) -> int:
    config = load_config(args.config)
    bot = EmulatorBot.connect(config)
    runner = SGZZStartAccountRunner(bot, package=args.package)
    record_path = runner.farm_land(
        Point(args.x, args.y),
        team=args.team,
        wait_arrive_seconds=args.wait_arrive,
    )
    print(f"Device: {bot.client.serial}")
    print(f"Farm: {args.x},{args.y} team={args.team}")
    print(f"Record: {record_path}")
    return 0


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Control LDPlayer through ADB.")
    parser.add_argument("--config", default="config.toml", help="Path to config file.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("doctor", help="Check ADB and connected emulator.")

    screenshot = subparsers.add_parser("screenshot", help="Save emulator screenshot.")
    screenshot.add_argument("--name", help="Output file name under screenshot_dir.")

    open_weibo = subparsers.add_parser("open-weibo", help="Launch Weibo demo.")
    open_weibo.add_argument("--package", help="Override Weibo package name.")
    open_weibo.add_argument(
        "--wait",
        type=float,
        help="Seconds to wait after launching before taking screenshot.",
    )

    tap = subparsers.add_parser("tap", help="Tap absolute emulator coordinates.")
    tap.add_argument("x", type=int)
    tap.add_argument("y", type=int)
    tap.add_argument("--exact", action="store_true", help="Disable click jitter.")

    click_image = subparsers.add_parser(
        "click-image", help="Find a template image and tap its center."
    )
    click_image.add_argument("template", help="Template file under assets/templates.")
    click_image.add_argument("--threshold", type=float, default=0.86)
    click_image.add_argument("--timeout", type=float)
    click_image.add_argument("--region", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    click_image.add_argument("--debug", action="store_true", help="Save debug image.")
    click_image.add_argument("--debug-name", help="Debug image file name.")

    click_color = subparsers.add_parser(
        "click-color", help="Find a color blob and tap its center."
    )
    click_color.add_argument("rgb", type=int, nargs=3, metavar=("R", "G", "B"))
    click_color.add_argument("--tolerance", type=int, default=20)
    click_color.add_argument("--timeout", type=float)
    click_color.add_argument("--region", type=int, nargs=4, metavar=("X", "Y", "W", "H"))
    click_color.add_argument("--min-area", type=int, default=20)
    click_color.add_argument("--debug", action="store_true", help="Save debug image.")
    click_color.add_argument("--debug-name", help="Debug image file name.")

    run_sm = subparsers.add_parser(
        "run-state-machine", help="Run a JSON-defined state machine."
    )
    run_sm.add_argument("file", help="Path to state machine JSON.")
    run_sm.add_argument("--dry-run", action="store_true", help="Validate JSON only.")
    run_sm.add_argument("--quiet", action="store_true", help="Hide transition trace.")
    run_sm.add_argument("--max-runtime", type=float, help="Override max runtime seconds.")
    run_sm.add_argument("--max-steps", type=int, help="Override max loop steps.")

    airtest_doctor = subparsers.add_parser(
        "airtest-doctor", help="Check optional Airtest integration."
    )
    airtest_doctor.add_argument(
        "--connect",
        action="store_true",
        help="Also try to connect Airtest to the selected emulator.",
    )

    sgzz_select = subparsers.add_parser(
        "sgzz-select-latest-s1",
        help="Launch SGZZ and select the newest normal Season 1 server.",
    )
    sgzz_select.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_select.add_argument(
        "--no-launch",
        action="store_true",
        help="Start from the current game screen instead of launching the app.",
    )
    sgzz_select.add_argument(
        "--launch-wait",
        type=float,
        default=8.0,
        help="Seconds to wait after launching the app.",
    )
    sgzz_select.add_argument(
        "--no-cancel-restore",
        action="store_true",
        help="Do not try to dismiss the hidden-role restore prompt.",
    )
    sgzz_select.add_argument(
        "--season1-taps",
        type=int,
        default=2,
        help="Tap the Season 1 tab this many times before choosing the first server.",
    )
    sgzz_select.add_argument(
        "--no-enter",
        action="store_true",
        help="Only select the server, do not tap the title enter button.",
    )
    sgzz_select.add_argument(
        "--enter-wait",
        type=float,
        default=5.0,
        help="Seconds to wait after tapping the title enter button.",
    )
    sgzz_select.add_argument(
        "--queue-wait",
        type=float,
        default=0.0,
        help="Optional seconds to keep taking queue screenshots after entering.",
    )
    sgzz_select.add_argument(
        "--queue-poll",
        type=float,
        default=30.0,
        help="Queue screenshot interval when --queue-wait is used.",
    )

    sgzz_dialogs = subparsers.add_parser(
        "sgzz-continue-dialogs",
        help="Continue SGZZ intro/story dialogs with template-backed taps.",
    )
    sgzz_dialogs.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_dialogs.add_argument("--taps", type=int, default=10)
    sgzz_dialogs.add_argument("--interval", type=float, default=0.65)
    sgzz_dialogs.add_argument("--match-timeout", type=float, default=0.8)

    sgzz_old_man = subparsers.add_parser(
        "sgzz-continue-old-man",
        help="Tap SGZZ old-man dialog continue icon until blocked by choices or exit.",
    )
    sgzz_old_man.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_old_man.add_argument("--max-taps", type=int, default=30)
    sgzz_old_man.add_argument("--interval", type=float, default=0.65)

    sgzz_quiz = subparsers.add_parser(
        "sgzz-answer-old-man-quiz",
        help="Answer SGZZ old-man quiz by choice index sequence.",
    )
    sgzz_quiz.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_quiz.add_argument(
        "--choices",
        default="1,1,1,1,1",
        help="Comma-separated choices, where 1=top, 2=middle, 3=bottom.",
    )
    sgzz_quiz.add_argument("--interval", type=float, default=0.9)
    sgzz_quiz.add_argument(
        "--no-continue-after",
        action="store_true",
        help="Do not continue old-man dialog after the last answer.",
    )

    sgzz_character = subparsers.add_parser(
        "sgzz-create-character-xiliang",
        help="Confirm avatar, submit random name, and choose Xiliang as start region.",
    )
    sgzz_character.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_character.add_argument("--skip-avatar", action="store_true")
    sgzz_character.add_argument("--skip-name", action="store_true")
    sgzz_character.add_argument("--skip-region", action="store_true")
    sgzz_character.add_argument("--old-man-taps", type=int, default=10)
    sgzz_character.add_argument(
        "--chapter-next",
        action="store_true",
        help="Tap chapter next after Xiliang confirmation.",
    )

    sgzz_chapter_next = subparsers.add_parser(
        "sgzz-chapter-next",
        help="Tap the SGZZ chapter page Next button.",
    )
    sgzz_chapter_next.add_argument("--package", default="com.aligames.sgzzlb")

    sgzz_scout = subparsers.add_parser(
        "sgzz-continue-scout",
        help="Tap SGZZ scout dialog continue icon until blocked or the marker exits.",
    )
    sgzz_scout.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_scout.add_argument("--max-taps", type=int, default=20)
    sgzz_scout.add_argument("--interval", type=float, default=0.65)

    sgzz_zhuge = subparsers.add_parser(
        "sgzz-continue-zhuge",
        help="Tap SGZZ Zhuge dialog continue icon until blocked or the marker exits.",
    )
    sgzz_zhuge.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_zhuge.add_argument("--max-taps", type=int, default=20)
    sgzz_zhuge.add_argument("--interval", type=float, default=0.65)

    subparsers.add_parser(
        "sgzz-flow-nodes",
        help="Print recorded SGZZ start-account flow nodes.",
    )

    sgzz_flow_node = subparsers.add_parser(
        "sgzz-flow-node",
        help="Run one recorded SGZZ start-account flow node from the current screen.",
    )
    sgzz_flow_node.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_flow_node.add_argument(
        "node",
        choices=[item["node"] for item in SGZZ_FLOW_NODES],
    )

    sgzz_account_batch = subparsers.add_parser(
        "sgzz-account-batch",
        help="Run SGZZ daily flow for every account in the account config file.",
    )
    sgzz_account_batch.add_argument("--package", default="com.aligames.sgzzlb")
    sgzz_account_batch.add_argument(
        "--serial",
        default=None,
        help="ADB serial to use. If omitted, stale config serials fall back to the first online emulator.",
    )
    sgzz_account_batch.add_argument(
        "--accounts-file",
        default=None,
        help="Account config path. Defaults to sgzz_accounts.txt in the repo root.",
    )
    sgzz_account_batch.add_argument(
        "--max-cycles",
        type=int,
        default=20,
        help="Maximum role cycles per account before failing safe.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return cmd_doctor(args)
        if args.command == "screenshot":
            return cmd_screenshot(args)
        if args.command == "open-weibo":
            return cmd_open_weibo(args)
        if args.command == "tap":
            return cmd_tap(args)
        if args.command == "click-image":
            return cmd_click_image(args)
        if args.command == "click-color":
            return cmd_click_color(args)
        if args.command == "run-state-machine":
            return cmd_run_state_machine(args)
        if args.command == "airtest-doctor":
            return cmd_airtest_doctor(args)
        if args.command == "sgzz-select-latest-s1":
            return cmd_sgzz_select_latest_s1(args)
        if args.command == "sgzz-continue-dialogs":
            return cmd_sgzz_continue_dialogs(args)
        if args.command == "sgzz-continue-old-man":
            return cmd_sgzz_continue_old_man(args)
        if args.command == "sgzz-answer-old-man-quiz":
            return cmd_sgzz_answer_old_man_quiz(args)
        if args.command == "sgzz-create-character-xiliang":
            return cmd_sgzz_create_character_xiliang(args)
        if args.command == "sgzz-chapter-next":
            return cmd_sgzz_chapter_next(args)
        if args.command == "sgzz-continue-scout":
            return cmd_sgzz_continue_scout(args)
        if args.command == "sgzz-continue-zhuge":
            return cmd_sgzz_continue_zhuge(args)
        if args.command == "sgzz-flow-nodes":
            return cmd_sgzz_flow_nodes(args)
        if args.command == "sgzz-flow-node":
            return cmd_sgzz_flow_node(args)
        if args.command == "sgzz-account-batch":
            return cmd_sgzz_account_batch(args)
    except (
        AdbError,
        StateMachineError,
        RuntimeError,
        FileNotFoundError,
        TimeoutError,
        ValueError,
    ) as exc:
        _print_error(exc)
        return 1
    parser.error(f"Unknown command: {args.command}")
    return 2
