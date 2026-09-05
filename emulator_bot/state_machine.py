from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from time import sleep, time
from typing import Any, Mapping
import json

from .airtest_backend import AirtestBackend
from .bot import EmulatorBot
from .vision import Match, find_color, match_template, save_debug_image


class StateMachineError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ConditionResult:
    matched: bool
    match: Match | None = None
    detail: str = ""


@dataclass(slots=True)
class RunResult:
    name: str
    status: str
    final_state: str
    steps: int
    runtime_seconds: float
    transitions: list[str] = field(default_factory=list)


class RunContext:
    def __init__(self, runner: "StateMachineRunner") -> None:
        self.runner = runner
        self.last_match: Match | None = None
        self._screenshot = None

    @property
    def bot(self) -> EmulatorBot:
        return self.runner.bot

    @property
    def state_name(self) -> str:
        return self.runner.current_state

    @property
    def state_elapsed_seconds(self) -> float:
        return time() - self.runner.state_entered_at

    def screenshot(self):
        if self._screenshot is None:
            self._screenshot = self.bot.screenshot_image()
        return self._screenshot

    def invalidate_screenshot(self) -> None:
        self._screenshot = None


class StateMachine:
    def __init__(self, spec: Mapping[str, Any], base_dir: Path | None = None) -> None:
        self.spec = dict(spec)
        self.base_dir = base_dir or Path.cwd()
        self.name = str(self.spec.get("name", "state_machine"))
        self.initial = str(self.spec.get("initial", "")).strip()
        self.states = self._mapping("states")
        self.global_transitions = self._list("global_transitions")
        self.tick_interval_seconds = float(self.spec.get("tick_interval_seconds", 0.5))
        self.max_steps = int(self.spec.get("max_steps", 300))
        self.max_runtime_seconds = float(self.spec.get("max_runtime_seconds", 180.0))

    @classmethod
    def load(cls, path: str | Path) -> "StateMachine":
        spec_path = Path(path)
        with spec_path.open("r", encoding="utf-8") as handle:
            spec = json.load(handle)
        if not isinstance(spec, dict):
            raise StateMachineError("State machine JSON must be an object.")
        machine = cls(spec, spec_path.resolve().parent)
        machine.validate()
        return machine

    def _mapping(self, key: str) -> dict[str, Any]:
        value = self.spec.get(key, {})
        if not isinstance(value, dict):
            raise StateMachineError(f"{key} must be an object.")
        return value

    def _list(self, key: str) -> list[Any]:
        value = self.spec.get(key, [])
        if value is None:
            return []
        if not isinstance(value, list):
            raise StateMachineError(f"{key} must be a list.")
        return value

    def validate(self) -> None:
        if not self.initial:
            raise StateMachineError("Missing top-level initial state.")
        if self.initial not in self.states:
            raise StateMachineError(f"Initial state does not exist: {self.initial}")
        if not self.states:
            raise StateMachineError("State machine needs at least one state.")

        for state_name, state in self.states.items():
            if not isinstance(state, dict):
                raise StateMachineError(f"State must be an object: {state_name}")
            self._validate_actions(state.get("on_enter", []), state_name)
            self._validate_actions(state.get("on_tick", []), state_name)
            self._validate_transitions(state.get("transitions", []), state_name)
            timeout_target = state.get("on_timeout")
            if timeout_target and str(timeout_target) not in self.states:
                raise StateMachineError(
                    f"State {state_name} has unknown on_timeout target: {timeout_target}"
                )
        self._validate_transitions(self.global_transitions, "global_transitions")

    def _validate_transitions(self, transitions: Any, owner: str) -> None:
        if transitions is None:
            return
        if not isinstance(transitions, list):
            raise StateMachineError(f"{owner}.transitions must be a list.")
        for index, transition in enumerate(transitions):
            if not isinstance(transition, dict):
                raise StateMachineError(f"{owner}.transitions[{index}] must be an object.")
            target = str(transition.get("target", "")).strip()
            if not target:
                raise StateMachineError(f"{owner}.transitions[{index}] is missing target.")
            if target not in self.states:
                raise StateMachineError(
                    f"{owner}.transitions[{index}] has unknown target: {target}"
                )
            self._validate_condition(transition.get("when", {"type": "always"}), owner)
            self._validate_actions(transition.get("actions", []), owner)

    def _validate_condition(self, condition: Any, owner: str) -> None:
        if not isinstance(condition, dict):
            raise StateMachineError(f"{owner} condition must be an object.")
        kind = str(condition.get("type", "always"))
        known = {
            "all",
            "always",
            "airtest_image",
            "any",
            "color",
            "focus_contains",
            "image",
            "never",
            "not",
            "state_elapsed",
        }
        if kind not in known:
            raise StateMachineError(f"{owner} condition has unknown type: {kind}")
        if kind in {"all", "any"}:
            checks = condition.get("conditions", [])
            if not isinstance(checks, list):
                raise StateMachineError(f"{owner} {kind}.conditions must be a list.")
            for child in checks:
                self._validate_condition(child, owner)
        elif kind == "not":
            self._validate_condition(condition.get("condition", {}), owner)

    def _validate_actions(self, actions: Any, owner: str) -> None:
        if actions is None:
            return
        if not isinstance(actions, list):
            raise StateMachineError(f"{owner} actions must be a list.")
        known = {
            "airtest_click_image",
            "airtest_snapshot",
            "click_color",
            "click_image",
            "keyevent",
            "launch_package",
            "log",
            "screenshot",
            "sleep",
            "swipe",
            "tap",
            "tap_match",
        }
        for index, action in enumerate(actions):
            if not isinstance(action, dict):
                raise StateMachineError(f"{owner} action[{index}] must be an object.")
            kind = str(action.get("type", ""))
            if kind not in known:
                raise StateMachineError(f"{owner} action[{index}] has unknown type: {kind}")


class StateMachineRunner:
    def __init__(
        self,
        machine: StateMachine,
        bot: EmulatorBot,
        *,
        trace: bool = True,
        dry_run: bool = False,
        max_runtime_seconds: float | None = None,
        max_steps: int | None = None,
    ) -> None:
        self.machine = machine
        self.bot = bot
        self.trace = trace
        self.dry_run = dry_run
        self.current_state = machine.initial
        self.state_entered_at = time()
        self.started_at = time()
        self.steps = 0
        self.transitions: list[str] = []
        self.max_runtime_seconds = (
            machine.max_runtime_seconds
            if max_runtime_seconds is None
            else max_runtime_seconds
        )
        self.max_steps = machine.max_steps if max_steps is None else max_steps
        self._airtest: AirtestBackend | None = None

    def run(self) -> RunResult:
        self.started_at = time()
        self._enter_state(self.machine.initial)

        while True:
            state = self._state(self.current_state)
            if bool(state.get("terminal", False)):
                return self._result("terminal")
            if self.steps >= self.max_steps:
                return self._result("max_steps")
            if time() - self.started_at >= self.max_runtime_seconds:
                return self._result("max_runtime")

            self.steps += 1
            context = RunContext(self)

            timeout_target = self._timeout_target(state)
            if timeout_target:
                self._transition(timeout_target, "timeout", context)
                continue

            if self._try_transitions(self.machine.global_transitions, context, "global"):
                continue

            transitions = state.get("transitions", [])
            if self._try_transitions(transitions, context, self.current_state):
                continue

            self._run_actions(state.get("on_tick", []), context)
            sleep(self._tick_interval(state))

    def _result(self, status: str) -> RunResult:
        return RunResult(
            name=self.machine.name,
            status=status,
            final_state=self.current_state,
            steps=self.steps,
            runtime_seconds=time() - self.started_at,
            transitions=list(self.transitions),
        )

    def _state(self, name: str) -> Mapping[str, Any]:
        return self.machine.states[name]

    def _enter_state(self, name: str) -> None:
        self.current_state = name
        self.state_entered_at = time()
        self._trace(f"STATE -> {name}")
        context = RunContext(self)
        self._run_actions(self._state(name).get("on_enter", []), context)

    def _transition(self, target: str, reason: str, context: RunContext) -> None:
        source = self.current_state
        line = f"{source} -> {target} ({reason})"
        self.transitions.append(line)
        self._trace(f"TRANSITION {line}")
        self._enter_state(target)

    def _try_transitions(
        self, transitions: Any, context: RunContext, owner: str
    ) -> bool:
        if not transitions:
            return False
        for transition in transitions:
            result = self._eval_condition(
                transition.get("when", {"type": "always"}),
                context,
            )
            if not result.matched:
                continue
            context.last_match = result.match
            self._run_actions(transition.get("actions", []), context)
            self._transition(str(transition["target"]), owner, context)
            return True
        return False

    def _timeout_target(self, state: Mapping[str, Any]) -> str | None:
        timeout = state.get("timeout_seconds")
        target = state.get("on_timeout")
        if timeout is None or not target:
            return None
        if time() - self.state_entered_at >= float(timeout):
            return str(target)
        return None

    def _tick_interval(self, state: Mapping[str, Any]) -> float:
        return float(state.get("tick_interval_seconds", self.machine.tick_interval_seconds))

    def _eval_condition(self, condition: Mapping[str, Any], context: RunContext) -> ConditionResult:
        kind = str(condition.get("type", "always"))

        if kind == "always":
            return ConditionResult(True, detail="always")
        if kind == "never":
            return ConditionResult(False, detail="never")
        if kind == "state_elapsed":
            seconds = float(condition.get("seconds", 0))
            matched = context.state_elapsed_seconds >= seconds
            return ConditionResult(matched, detail=f"state_elapsed>={seconds}")
        if kind == "focus_contains":
            text = str(condition.get("text", ""))
            focus = "" if self.dry_run else context.bot.client.current_focus()
            return ConditionResult(text in focus, detail=focus)
        if kind == "image":
            match = self._find_image(context, condition)
            return ConditionResult(match is not None, match=match, detail="image")
        if kind == "airtest_image":
            match = self._find_airtest_image(condition)
            return ConditionResult(
                match is not None,
                match=match,
                detail="airtest_image",
            )
        if kind == "color":
            match = self._find_color(context, condition)
            return ConditionResult(match is not None, match=match, detail="color")
        if kind == "all":
            first_match: Match | None = None
            for child in condition.get("conditions", []):
                result = self._eval_condition(child, context)
                if not result.matched:
                    return ConditionResult(False, detail="all")
                first_match = first_match or result.match
            return ConditionResult(True, match=first_match, detail="all")
        if kind == "any":
            for child in condition.get("conditions", []):
                result = self._eval_condition(child, context)
                if result.matched:
                    return ConditionResult(True, match=result.match, detail="any")
            return ConditionResult(False, detail="any")
        if kind == "not":
            result = self._eval_condition(condition.get("condition", {}), context)
            return ConditionResult(not result.matched, detail="not")

        raise StateMachineError(f"Unknown condition type: {kind}")

    def _run_actions(self, actions: Any, context: RunContext) -> None:
        if not actions:
            return
        for action in actions:
            self._run_action(action, context)

    def _run_action(self, action: Mapping[str, Any], context: RunContext) -> None:
        kind = str(action.get("type", ""))

        if kind == "log":
            self._trace(str(action.get("message", "")))
            return
        if kind == "sleep":
            seconds = float(action.get("seconds", 0))
            self._trace(f"sleep {seconds:.2f}s")
            if not self.dry_run:
                sleep(seconds)
                context.invalidate_screenshot()
            return
        if kind == "launch_package":
            package = str(action.get("package", "")).strip()
            if not package:
                raise StateMachineError("launch_package action requires package.")
            self._trace(f"launch {package}")
            if not self.dry_run:
                context.bot.client.launch_package(package)
                context.invalidate_screenshot()
            return
        if kind == "tap":
            x, y = int(action["x"]), int(action["y"])
            jitter = action.get("jitter")
            self._trace(f"tap {x},{y}")
            if not self.dry_run:
                context.bot.tap(x, y, jitter=None if jitter is None else int(jitter))
                context.invalidate_screenshot()
            return
        if kind == "tap_match":
            match = context.last_match
            if not match:
                self._trace("tap_match skipped: no match")
                return
            x, y = match.center
            x += int(action.get("offset_x", 0))
            y += int(action.get("offset_y", 0))
            jitter = action.get("jitter")
            self._trace(f"tap_match {x},{y}")
            if not self.dry_run:
                context.bot.tap(x, y, jitter=None if jitter is None else int(jitter))
                context.invalidate_screenshot()
            return
        if kind == "swipe":
            values = [int(action[key]) for key in ("x1", "y1", "x2", "y2")]
            duration = int(action.get("duration_ms", 300))
            self._trace(f"swipe {values[0]},{values[1]} -> {values[2]},{values[3]}")
            if not self.dry_run:
                context.bot.swipe(*values, duration_ms=duration)
                context.invalidate_screenshot()
            return
        if kind == "keyevent":
            keycode = action["keycode"]
            self._trace(f"keyevent {keycode}")
            if not self.dry_run:
                context.bot.client.keyevent(keycode)
                context.invalidate_screenshot()
            return
        if kind == "screenshot":
            name = action.get("name")
            self._trace("screenshot")
            if not self.dry_run:
                path = context.bot.save_screenshot(str(name) if name else None)
                self._trace(f"saved {path}")
                context.invalidate_screenshot()
            return
        if kind == "airtest_snapshot":
            name = action.get("name")
            self._trace("airtest_snapshot")
            if not self.dry_run:
                path = None
                if name:
                    path = context.bot.config.screenshot_dir / str(name)
                saved = self._airtest_backend().snapshot(path)
                if saved:
                    self._trace(f"saved {saved}")
                context.invalidate_screenshot()
            return
        if kind == "click_image":
            match = self._find_image(context, action)
            if not match:
                self._trace("click_image skipped: not found")
                return
            context.last_match = match
            self._tap_match_or_debug(context, action, match)
            return
        if kind == "airtest_click_image":
            match = self._find_airtest_image(action)
            if not match:
                self._trace("airtest_click_image skipped: not found")
                return
            context.last_match = match
            self._trace(f"airtest_touch {match.center[0]},{match.center[1]}")
            if not self.dry_run:
                self._airtest_backend().touch(*match.center)
                context.invalidate_screenshot()
            return
        if kind == "click_color":
            match = self._find_color(context, action)
            if not match:
                self._trace("click_color skipped: not found")
                return
            context.last_match = match
            self._tap_match_or_debug(context, action, match)
            return

        raise StateMachineError(f"Unknown action type: {kind}")

    def _tap_match_or_debug(
        self, context: RunContext, action: Mapping[str, Any], match: Match
    ) -> None:
        self._save_debug(context, action, match)
        x, y = match.center
        x += int(action.get("offset_x", 0))
        y += int(action.get("offset_y", 0))
        jitter = action.get("jitter")
        self._trace(f"tap match {x},{y}")
        if not self.dry_run:
            context.bot.tap(x, y, jitter=None if jitter is None else int(jitter))
            context.invalidate_screenshot()

    def _find_image(self, context: RunContext, spec: Mapping[str, Any]) -> Match | None:
        template = spec.get("template")
        if not template:
            raise StateMachineError("image condition/action requires template.")
        threshold = float(spec.get("threshold", 0.86))
        region = self._region(spec.get("region"))
        if self.dry_run:
            return None
        template_path = self._template_path(str(template))
        match = match_template(
            context.screenshot(),
            template_path,
            threshold=threshold,
            region=region,
        )
        self._save_debug(context, spec, match)
        return match

    def _find_airtest_image(self, spec: Mapping[str, Any]) -> Match | None:
        template = spec.get("template")
        if not template:
            raise StateMachineError("airtest_image condition/action requires template.")
        threshold = float(spec.get("threshold", 0.86))
        if self.dry_run:
            return None
        return self._airtest_backend().exists_template(
            self._template_path(str(template)),
            threshold=threshold,
        )

    def _find_color(self, context: RunContext, spec: Mapping[str, Any]) -> Match | None:
        rgb = spec.get("rgb")
        if not isinstance(rgb, Sequence) or isinstance(rgb, (str, bytes)):
            raise StateMachineError("color condition/action requires rgb list.")
        tolerance = int(spec.get("tolerance", 20))
        region = self._region(spec.get("region"))
        min_area = int(spec.get("min_area", 20))
        if self.dry_run:
            return None
        match = find_color(
            context.screenshot(),
            rgb=[int(value) for value in rgb],
            tolerance=tolerance,
            region=region,
            min_area=min_area,
        )
        self._save_debug(context, spec, match)
        return match

    def _save_debug(
        self, context: RunContext, spec: Mapping[str, Any], match: Match | None
    ) -> None:
        debug_name = spec.get("debug_name")
        if not debug_name or self.dry_run:
            return
        path = context.bot.config.debug_dir / str(debug_name)
        save_debug_image(path, context.screenshot(), match)
        self._trace(f"debug {path}")

    def _template_path(self, template: str) -> Path:
        path = Path(template)
        if path.is_absolute():
            return path
        local = self.machine.base_dir / path
        if local.exists():
            return local
        return self.bot.config.template_dir / path

    def _airtest_backend(self) -> AirtestBackend:
        if self._airtest is None:
            self._airtest = AirtestBackend.from_bot(self.bot)
        return self._airtest

    @staticmethod
    def _region(value: Any) -> list[int] | None:
        if value is None:
            return None
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            raise StateMachineError("region must be [x, y, width, height].")
        if len(value) != 4:
            raise StateMachineError("region must have 4 values: [x, y, width, height].")
        return [int(item) for item in value]

    def _trace(self, message: str) -> None:
        if self.trace:
            print(f"[{self.machine.name}] {message}")
