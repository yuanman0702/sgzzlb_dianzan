# Android Emulator Bot

A small Python framework for controlling LDPlayer through ADB.

## Quick start

```powershell
Copy-Item config.example.toml config.toml
python main.py doctor
python main.py open-weibo
python main.py screenshot
```

If ADB cannot be found automatically, set `adb.path` in `config.toml`.

Common LDPlayer package for Weibo:

```toml
[demo.weibo]
package = "com.sina.weibo"
```

## Optional vision dependencies

Image matching and color matching require:

```powershell
python -m pip install -r requirements.txt
```

## Useful commands

```powershell
python main.py doctor
python main.py screenshot --name home.png
python main.py open-weibo --package com.sina.weibo
python main.py tap 360 900
python main.py click-image button_start.png --threshold 0.86 --timeout 5
python main.py click-color 255 210 60 --tolerance 25 --region 100 300 600 900
python main.py run-state-machine state_machines/browser_demo.json
python main.py airtest-doctor
python main.py sgzz-select-latest-s1
```

## Airtest

Airtest is optional. The framework can use it for image recognition and touch while
keeping the JSON state machine as the high-level game logic.

```powershell
python -m pip install -r requirements-airtest.txt
python main.py airtest-doctor --connect
```

Airtest connection settings live in `config.toml` under `[airtest]`. If
`device_uri` is blank, the framework builds one from the selected ADB serial.

Airtest-specific state machine condition/action types:

```json
{
  "transitions": [
    {
      "target": "battle",
      "when": {
        "type": "airtest_image",
        "template": "start.png",
        "threshold": 0.86
      },
      "actions": [
        {"type": "tap_match"}
      ]
    }
  ],
  "on_tick": [
    {
      "type": "airtest_click_image",
      "template": "attack.png",
      "threshold": 0.82
    }
  ]
}
```

## State machines

State machines are JSON files with states, actions, and transitions.

```json
{
  "name": "game_demo",
  "initial": "home",
  "global_transitions": [
    {
      "target": "home",
      "when": {"type": "image", "template": "close_popup.png"},
      "actions": [{"type": "tap_match"}]
    }
  ],
  "states": {
    "home": {
      "on_tick": [
        {"type": "click_image", "template": "start.png", "threshold": 0.86}
      ],
      "transitions": [
        {"target": "battle", "when": {"type": "image", "template": "battle.png"}}
      ]
    },
    "battle": {
      "on_tick": [
        {"type": "tap", "x": 640, "y": 1120}
      ],
      "transitions": [
        {"target": "reward", "when": {"type": "image", "template": "victory.png"}}
      ]
    },
    "reward": {
      "on_tick": [
        {"type": "click_image", "template": "claim.png"}
      ],
      "transitions": [
        {"target": "home", "when": {"type": "state_elapsed", "seconds": 5}}
      ]
    }
  }
}
```

For game automation, put common interruption handlers such as popups or disconnect
dialogs in `global_transitions`, then keep each screen or gameplay phase as one state.

Supported condition types: `always`, `never`, `image`, `color`, `focus_contains`,
`state_elapsed`, `all`, `any`, `not`.

Supported action types: `launch_package`, `tap`, `tap_match`, `swipe`, `keyevent`,
`screenshot`, `sleep`, `click_image`, `click_color`, `log`.

Screenshots are saved under `logs/screenshots`.
Debug images are saved under `logs/debug`.

## SGZZ start-account flow

The SGZZ helper is a game-specific runner built on top of the generic ADB and
vision framework. It records every tap and screenshot under `logs/sgzz_runs`.

```powershell
python main.py sgzz-select-latest-s1
python main.py sgzz-account-batch --max-cycles 20
```

Useful options:

```powershell
python main.py sgzz-select-latest-s1 --no-launch
python main.py sgzz-select-latest-s1 --season1-taps 2
python main.py sgzz-select-latest-s1 --queue-wait 300 --queue-poll 30
```

Stable UI samples are stored in `assets/templates/sgzz`. The runner uses those
templates to recognize title buttons, the server selector, Season 1, and queue
popups, then falls back to recorded coordinates when a template is not visible.

For multi-account daily runs, put one account per line in `sgzz_accounts.txt`
using `account#password#client`. Supported client names are `灵犀`, `小米`,
`九游`, `华为`, and `QQ`. The client field is optional and defaults to `灵犀`,
so existing `account#password` files remain valid. `sgzz-account-batch` logs
into each account in order, runs every remaining role until the repeated role
identity stop condition is hit, then switches to the next account.

Put the target player's numeric ID in `sgzz_like_target.txt`. The runner uses it
to send a friend request when a role does not yet have the configured like target.
Both local files and `config.toml` are ignored by Git; the repository contains
only safe example files.
