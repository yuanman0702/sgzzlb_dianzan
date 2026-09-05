# ADB Emulator Control Portable

This package is the ADB-only server UI. It does not require installing a control APK in the emulator.

## First Run

1. Install Python 3.10+ on the target computer and add it to PATH.
2. Double-click `install_dependencies.bat`.
3. Double-click `start_server_ui_silent.vbs` to start the UI without a console window.

If you need to see startup errors, run `start_server_ui.bat` instead.

## Included Files

- `adb\adb.exe` and required Windows DLLs are bundled in this directory.
- `remote_app_control\python_server` contains the server UI and HTTP API.
- `emulator_bot` contains the SGZZ automation logic.
- `assets\templates` contains image-recognition templates.
- `sgzz_accounts.txt` is the default account file.
- `sgzz_like_target.txt` stores the target player ID used when an account has no matching friend.

## Use

Start the emulator first, then open the server UI. Click `扫描模拟器`, select the emulator, then click `绑定选中模拟器`.

The service listens on `http://127.0.0.1:8766`.
